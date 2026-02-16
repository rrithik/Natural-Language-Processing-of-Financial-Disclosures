import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ----------------------------
# Gemini response schema
# ----------------------------
class CategorizeResponse(BaseModel):
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str


# ----------------------------
# Date extraction (optional)
# ----------------------------
DATE_PATTERNS = [
    re.compile(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b"),  # YYYY-MM-DD
    re.compile(r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](20\d{2})\b"),  # MM/DD/YYYY
]

def extract_date(text: str) -> str:
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        g = m.groups()
        if len(g[0]) == 4:  # YYYY-MM-DD
            return f"{g[0]}-{g[1]}-{g[2]}"
        return f"{g[2]}-{g[0]}-{g[1]}"
    return ""


# ----------------------------
# Parser A: tuple lines like
# (3, '0.159*"agreement" + 0.113*"target" + ...')
# Here, weights are term weights within the topic.
# We'll convert to a per-topic score by taking the MAX term weight in that topic line.
# ----------------------------
TUPLE_LINE_RE = re.compile(r"(?m)^\(\s*(\d+)\s*,\s*'(.+)'\s*\)\s*$")
TOKEN_RE_A = re.compile(r'(\d+(?:\.\d+)?)\s*\*\s*"([^"]+)"')

def parse_format_a(text: str) -> Dict[int, List[Tuple[str, float]]]:
    topics: Dict[int, List[Tuple[str, float]]] = {}
    for m in TUPLE_LINE_RE.finditer(text):
        tid = int(m.group(1))
        body = m.group(2)
        tokens = [(term, float(w)) for (w, term) in TOKEN_RE_A.findall(body)]
        if tokens:
            tokens.sort(key=lambda x: x[1], reverse=True)
            topics[tid] = tokens
    return topics


# ----------------------------
# Parser B: "TOPIC KEYWORDS" style:
# 🔹 Topic 0:
#    participant (0.084)
# ----------------------------
TOPIC_HEADER_RE_B = re.compile(r"(?m)^\s*(?:🔹\s*)?Topic\s+(\d+)\s*:\s*$", re.IGNORECASE)
TOKEN_RE_B = re.compile(r"(?m)^\s*([A-Za-z0-9_]+)\s*\((\d+(?:\.\d+)?)\)\s*$")

def parse_format_b(text: str) -> Dict[int, List[Tuple[str, float]]]:
    topics: Dict[int, List[Tuple[str, float]]] = {}
    headers = list(TOPIC_HEADER_RE_B.finditer(text))
    if not headers:
        return topics

    for i, h in enumerate(headers):
        tid = int(h.group(1))
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]

        tokens = [(term, float(w)) for term, w in TOKEN_RE_B.findall(block)]
        if tokens:
            tokens.sort(key=lambda x: x[1], reverse=True)
            topics[tid] = tokens

    return topics


# ----------------------------
# Unified parse: try both formats
# ----------------------------
def parse_topics_any(text: str) -> Dict[int, List[Tuple[str, float]]]:
    topics = parse_format_b(text)
    if topics:
        return topics
    return parse_format_a(text)


# ----------------------------
# Build a compact summary string for Gemini categorization
# ----------------------------
def build_topic_summary(topics: Dict[int, List[Tuple[str, float]]], top_topics: int = 8, top_terms: int = 8) -> str:
    if not topics:
        return "No topics parsed."

    ranked = sorted(
        topics.items(),
        key=lambda kv: kv[1][0][1] if kv[1] else 0.0,
        reverse=True
    )[:top_topics]

    lines: List[str] = []
    for tid, terms in ranked:
        terms = terms[:top_terms]
        term_str = ", ".join([f"{t}:{w:.3f}" for t, w in terms])
        lines.append(f"Topic {tid}: {term_str}")
    return "\n".join(lines)


# ----------------------------
# Convert parsed topics -> "topic distribution" rows
# We define Proportion as the strongest token weight in each topic block,
# since your formats provide per-topic term weights (not doc-topic probabilities).
# This still matches your example CSV structure exactly.
# ----------------------------
def topic_distribution_from_parsed(topics: Dict[int, List[Tuple[str, float]]]) -> List[Tuple[int, float]]:
    dist: List[Tuple[int, float]] = []
    for tid, terms in topics.items():
        if not terms:
            continue
        # strongest term weight as a stable per-topic score
        top_weight = max(w for _, w in terms)
        dist.append((tid, float(top_weight)))
    dist.sort(key=lambda x: x[1], reverse=True)
    return dist


# ----------------------------
# Gemini categorize
# ----------------------------
def categorize_with_gemini(client, model: str, topic_summary: str) -> CategorizeResponse:
    prompt = f"""
You are categorizing documents using their BERTopic topic keyword/weight outputs.

Return ONE concise category name.

Topic info:
{topic_summary}
""".strip()

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CategorizeResponse,
            temperature=0.0,
        ),
    )
    return CategorizeResponse(**json.loads(resp.text))


def main():
    bert_dir = Path("bert-summaries")
    out_categorized = Path("categorized_documents.csv")
    out_long = Path("topic_proportions.csv")

    if not bert_dir.exists():
        raise FileNotFoundError(f"Folder not found: {bert_dir.resolve()}")

    files = sorted(bert_dir.glob("*.txt"))
    if not files:
        raise ValueError(f"No .txt files found in: {bert_dir.resolve()}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY environment variable.")
    client = genai.Client(api_key=api_key)

    categorized_rows: List[Dict[str, object]] = []
    long_rows: List[Dict[str, object]] = []

    for doc_idx, p in enumerate(files):
        text = p.read_text(encoding="utf-8", errors="replace")

        date = extract_date(text)
        parsed_topics = parse_topics_any(text)

        topic_summary = build_topic_summary(parsed_topics)
        dist = topic_distribution_from_parsed(parsed_topics)

        # 1) Categorize (one row per doc)
        result = categorize_with_gemini(client, model="gemini-2.5-flash", topic_summary=topic_summary)

        categorized_rows.append({
            "Document": doc_idx,
            "FileName": p.name,
            "Date": date,
            "ParsedTopicCount": len(parsed_topics),
            "TopicSummary": topic_summary,
            "Category": result.category,
            "Confidence": float(result.confidence),
            "Rationale": result.rationale,
        })

        # 2) Long-format topic distribution (many rows per doc)
        for topic_id, prop in dist:
            terms = parsed_topics.get(topic_id, [])
            
            # Build topic name from top 3 terms
            topic_name = ", ".join([t for t, _ in terms[:3]]) if terms else ""

            long_rows.append({
                "Document": doc_idx,
                "FileName": p.name,
                "Date": date,
                "Topic": topic_id,
                "TopicName": topic_name,
                "Proportion": prop,
            })


        print(f"[{doc_idx+1}/{len(files)}] {p.name} -> {result.category} ({result.confidence:.2f})")
        time.sleep(0.15)

    # Write categorized CSV
    with out_categorized.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Document", "FileName", "Date", "ParsedTopicCount", "TopicSummary", "Category", "Confidence", "Rationale"]
        )
        writer.writeheader()
        writer.writerows(categorized_rows)

    # Write long CSV in the exact structure of your example:
    # Document, FileName, Date, Topic, Proportion 
    with out_long.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Document", "FileName", "Date", "Topic", "TopicName", "Proportion"]

        )
        writer.writeheader()
        writer.writerows(long_rows)

    print(f"\nDone.")
    print(f"- Categorized CSV: {out_categorized.resolve()}")
    print(f"- Long topic CSV:  {out_long.resolve()}")


if __name__ == "__main__":
    main()
