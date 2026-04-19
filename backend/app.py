from flask import Flask, request, jsonify
from flask_cors import CORS
import html
import os
import pickle
import re
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import numpy as np

app = Flask(__name__)
CORS(app)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model", "model.pkl")
vectorizer_path = os.path.join(current_dir, "model", "vectorizer.pkl")

model = None
vectorizer = None

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "for",
    "from", "has", "have", "he", "in", "is", "it", "its", "of", "on", "or",
    "she", "that", "the", "their", "this", "to", "was", "were", "will", "with",
    "about", "after", "all", "also", "am", "any", "because", "before", "can",
    "did", "do", "does", "had", "her", "hers", "him", "his", "if", "into",
    "just", "more", "most", "new", "not", "now", "our", "out", "over", "said",
    "say", "says", "than", "them", "they", "too", "under", "up", "we", "what",
    "when", "where", "which", "who", "why", "you", "your"
}

SUPPORT_CUES = {
    "confirmed", "confirms", "report", "reports", "reported", "according",
    "official", "officials", "announced", "announcement", "shows", "showed",
    "found", "finds", "reveals", "reveal", "study", "data", "evidence", "says"
}

OPPOSE_CUES = {
    "false", "fake", "debunked", "debunks", "debunk", "misleading", "denies",
    "deny", "denied", "refutes", "refuted", "no evidence", "hoax", "untrue",
    "incorrect", "wrong", "baseless", "fabricated", "not true"
}

HIGH_CREDIBILITY_SOURCES = {
    "reuters": 1.0,
    "associated press": 0.99,
    "ap news": 0.99,
    "bbc": 0.97,
    "bbc news": 0.97,
    "the guardian": 0.95,
    "financial times": 0.95,
    "wall street journal": 0.95,
    "the new york times": 0.94,
    "washington post": 0.94,
    "npr": 0.92,
    "pbs": 0.92,
    "bloomberg": 0.93,
    "cnn": 0.9,
    "abc news": 0.9,
    "cbs news": 0.9,
    "nbc news": 0.9,
    "al jazeera": 0.9,
    "usa today": 0.88,
    "hindustan times": 0.86,
    "the hindu": 0.89,
    "indian express": 0.88,
    "times of india": 0.84,
    "ndtv": 0.85,
}


def load_models():
    global model, vectorizer
    try:
        with open(model_path, "rb") as model_file:
            model = pickle.load(model_file)
        with open(vectorizer_path, "rb") as vectorizer_file:
            vectorizer = pickle.load(vectorizer_file)
        print("Models loaded successfully.")
    except Exception as exc:
        print(f"Warning: model fallback unavailable: {exc}")


load_models()


def normalize_whitespace(value):
    return re.sub(r"\s+", " ", value or "").strip()


def tokenize(text):
    return [
        token for token in re.findall(r"[a-zA-Z0-9']+", (text or "").lower())
        if token not in STOP_WORDS and len(token) > 2
    ]


def extract_claim_focus(text, max_terms=8):
    tokens = tokenize(text)
    if not tokens:
        return []
    counts = Counter(tokens)
    ranked = [token for token, _ in counts.most_common(max_terms)]
    return ranked


def build_search_queries(text):
    cleaned = normalize_whitespace(text)
    focus_terms = extract_claim_focus(cleaned, max_terms=6)

    queries = [cleaned[:180]]
    if focus_terms:
        queries.append(" ".join(focus_terms))
    if len(focus_terms) >= 3:
        queries.append(" ".join(focus_terms[:3]) + " fact check")

    deduped = []
    seen = set()
    for query in queries:
        normalized = query.lower()
        if query and normalized not in seen:
            seen.add(normalized)
            deduped.append(query)
    return deduped[:3]


def html_to_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_whitespace(value)


def parse_published_at(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def recency_weight(published_at):
    if published_at is None:
        return 0.78
    age_days = max((datetime.now(timezone.utc) - published_at).days, 0)
    if age_days <= 2:
        return 1.0
    if age_days <= 7:
        return 0.94
    if age_days <= 30:
        return 0.86
    if age_days <= 90:
        return 0.76
    return 0.66


def source_weight(source_name, link):
    source_name = (source_name or "").lower()
    for known_source, weight in HIGH_CREDIBILITY_SOURCES.items():
        if known_source in source_name:
            return weight

    hostname = (urlparse(link).hostname or "").lower().replace("www.", "")
    for known_source, weight in HIGH_CREDIBILITY_SOURCES.items():
        compact_name = known_source.replace(" ", "")
        compact_host = hostname.replace(".", "")
        if compact_name in compact_host:
            return weight
    return 0.72


def fetch_google_news(query, limit=8):
    rss_url = (
        "https://news.google.com/rss/search?q="
        f"{quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    )
    request = Request(
        rss_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    )

    with urlopen(request, timeout=12) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall("./channel/item")[:limit]:
        title = normalize_whitespace(item.findtext("title", default=""))
        link = normalize_whitespace(item.findtext("link", default=""))
        description = html_to_text(item.findtext("description", default=""))
        source_node = item.find("source")
        source_name = normalize_whitespace(source_node.text if source_node is not None else "")
        published_at = parse_published_at(item.findtext("pubDate", default=""))

        items.append(
            {
                "title": title,
                "link": link,
                "snippet": description,
                "source": source_name or (urlparse(link).hostname or "Unknown source"),
                "published_at": published_at,
            }
        )

    return items


def dedupe_articles(articles, limit=10):
    deduped = []
    seen = set()
    for article in articles:
        key = (
            article["link"].lower(),
            re.sub(r"[^a-z0-9]+", "", article["title"].lower())[:120],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(article)
        if len(deduped) >= limit:
            break
    return deduped


def classify_stance(claim_text, article):
    claim_tokens = set(tokenize(claim_text))
    article_text = f"{article['title']} {article['snippet']}"
    article_tokens = set(tokenize(article_text))
    overlap = len(claim_tokens & article_tokens)
    overlap_ratio = overlap / max(len(claim_tokens), 1)

    lower_article_text = article_text.lower()
    support_hits = sum(cue in lower_article_text for cue in SUPPORT_CUES)
    oppose_hits = sum(cue in lower_article_text for cue in OPPOSE_CUES)
    fact_check_bonus = 0.12 if "fact check" in lower_article_text else 0.0

    relevance = min(1.0, overlap_ratio * 1.5 + (0.18 if overlap >= 3 else 0))
    source_reliability = source_weight(article["source"], article["link"])
    freshness = recency_weight(article["published_at"])

    support_score = (
        relevance * 0.52
        + support_hits * 0.12
        + source_reliability * 0.18
        + freshness * 0.1
    )
    oppose_score = (
        relevance * 0.42
        + oppose_hits * 0.16
        + source_reliability * 0.18
        + freshness * 0.12
        + fact_check_bonus
    )

    if oppose_hits and support_hits:
        oppose_score += 0.04

    if relevance < 0.12:
        stance = "unrelated"
        strength = round(relevance * 100, 1)
    elif oppose_score - support_score > 0.12:
        stance = "oppose"
        strength = round(min(1.0, oppose_score) * 100, 1)
    elif support_score - oppose_score > 0.08:
        stance = "support"
        strength = round(min(1.0, support_score) * 100, 1)
    else:
        stance = "mixed"
        strength = round(min(1.0, (support_score + oppose_score) / 2) * 100, 1)

    article["stance"] = stance
    article["strength"] = strength
    article["relevance"] = round(relevance * 100, 1)
    article["source_weight"] = round(source_reliability, 2)
    article["freshness_weight"] = round(freshness, 2)
    article["published_label"] = (
        article["published_at"].strftime("%d %b %Y") if article["published_at"] else "Date unavailable"
    )
    return article


def get_model_signal(text):
    if model is None or vectorizer is None:
        return None

    vectorized_text = vectorizer.transform([text])
    prediction = model.predict(vectorized_text)[0]
    probabilities = model.predict_proba(vectorized_text)[0]
    confidence = float(np.max(probabilities))
    return {
        "label": str(prediction),
        "confidence": round(confidence * 100, 2),
    }


def aggregate_analysis(claim_text, articles, model_signal):
    counts = Counter(article["stance"] for article in articles)

    support_weight = sum(
        article["source_weight"] * article["freshness_weight"] * (article["strength"] / 100)
        for article in articles
        if article["stance"] == "support"
    )
    oppose_weight = sum(
        article["source_weight"] * article["freshness_weight"] * (article["strength"] / 100)
        for article in articles
        if article["stance"] == "oppose"
    )
    mixed_weight = sum(
        article["source_weight"] * article["freshness_weight"] * (article["strength"] / 100)
        for article in articles
        if article["stance"] == "mixed"
    )

    evidence_total = support_weight + oppose_weight + mixed_weight
    if evidence_total <= 0:
        verdict = "Insufficient live evidence"
        confidence = model_signal["confidence"] * 0.65 if model_signal else 32.0
        summary = "Live coverage did not return enough relevant articles, so the result leans on fallback analysis."
    else:
        balance = support_weight - oppose_weight
        certainty = min(0.96, abs(balance) / max(evidence_total, 0.01) + min(len(articles), 8) * 0.03)
        model_bonus = 0.0

        if model_signal:
            if model_signal["label"].lower() == "real" and balance > 0:
                model_bonus = 0.04
            elif model_signal["label"].lower() != "real" and balance < 0:
                model_bonus = 0.04

        confidence = round(min(0.98, certainty + model_bonus) * 100, 1)

        if balance > 0.55:
            verdict = "Likely supported"
            summary = "Most credible sources align with the pasted claim."
        elif balance < -0.45:
            verdict = "Likely disputed"
            summary = "Credible coverage leans against the pasted claim or flags it as misleading."
        elif mixed_weight > max(support_weight, oppose_weight) * 0.75:
            verdict = "Mixed reporting"
            summary = "Coverage exists, but the reporting is split or too nuanced for a clean verdict."
        else:
            verdict = "Needs manual review"
            summary = "The evidence is too balanced or too weak to issue a strong verdict."

    top_sources = [
        {
            "title": article["title"],
            "source": article["source"],
            "link": article["link"],
            "snippet": article["snippet"],
            "stance": article["stance"],
            "strength": article["strength"],
            "publishedAt": article["published_label"],
        }
        for article in sorted(
            articles,
            key=lambda item: (
                item["stance"] == "support" or item["stance"] == "oppose",
                item["strength"],
                item["source_weight"],
            ),
            reverse=True,
        )[:8]
    ]

    support_count = counts.get("support", 0)
    oppose_count = counts.get("oppose", 0)
    mixed_count = counts.get("mixed", 0)
    unrelated_count = counts.get("unrelated", 0)

    return {
        "claim": normalize_whitespace(claim_text),
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "evidence": {
            "support": support_count,
            "oppose": oppose_count,
            "mixed": mixed_count,
            "unrelated": unrelated_count,
            "weightedSupport": round(support_weight, 2),
            "weightedOppose": round(oppose_weight, 2),
        },
        "modelSignal": model_signal,
        "sources": top_sources,
    }


def analyze_claim(text):
    queries = build_search_queries(text)
    collected_articles = []
    fetch_errors = []

    for query in queries:
        try:
            collected_articles.extend(fetch_google_news(query))
        except Exception as exc:
            fetch_errors.append(str(exc))

    deduped_articles = dedupe_articles(collected_articles)
    analyzed_articles = [classify_stance(text, article) for article in deduped_articles]
    model_signal = get_model_signal(text)
    analysis = aggregate_analysis(text, analyzed_articles, model_signal)
    analysis["queries"] = queries
    analysis["searchStatus"] = "partial" if fetch_errors and analyzed_articles else "ok"
    analysis["fallbackUsed"] = not analyzed_articles
    if fetch_errors:
        analysis["debug"] = {
            "searchErrors": fetch_errors[:2]
        }
    return analysis


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "No text provided. Please send JSON with a 'text' key."}), 400

        news_text = normalize_whitespace(data["text"])
        if not news_text:
            return jsonify({"error": "Text cannot be empty."}), 400

        result = analyze_claim(news_text)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
