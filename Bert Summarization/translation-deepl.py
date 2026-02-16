"""
How to run this program:

HTML filing -> English text
python translate_disclosure_google_v3.py --infile filing.html --outfile filing_en.txt --assume_html --project_id YOUR_PROJECT_ID

Plain text filing -> English text
python translate_disclosure_google_v3.py --infile filing.txt --outfile filing_en.txt --project_id YOUR_PROJECT_ID

If you KNOW the source language (optional; can improve accuracy/speed)
python translate_disclosure_google_v3.py --infile filing.txt --outfile filing_en.txt --project_id YOUR_PROJECT_ID --source ja
"""


import os
import re
import time
import argparse
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


# --------- I/O + cleaning ---------
def read_input(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def html_to_text(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")

    # Remove scripts/styles that pollute filings
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")

    # Normalize whitespace a bit
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# --------- chunking ---------
def chunk_text(text: str, max_chars: int) -> List[str]:
    """
    Chunk by paragraphs first (double newlines), then hard-split if needed.
    max_chars should be conservative to avoid API payload limits/timeouts.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if buf:
            chunks.append("\n\n".join(buf))
            buf = []
            buf_len = 0

    for p in paragraphs:
        if len(p) > max_chars:
            flush()
            for start in range(0, len(p), max_chars):
                chunks.append(p[start : start + max_chars])
            continue

        extra = (2 if buf else 0)  # for "\n\n"
        if buf_len + len(p) + extra <= max_chars:
            buf.append(p)
            buf_len += len(p) + extra
        else:
            flush()
            buf.append(p)
            buf_len = len(p)

    flush()
    return chunks


# --------- DeepL API ---------
def deepl_endpoint(use_free_api: bool) -> str:
    # DeepL free uses api-free.deepl.com; paid uses api.deepl.com
    return "https://api-free.deepl.com/v2/translate" if use_free_api else "https://api.deepl.com/v2/translate"


def deepl_translate_chunk(
    chunk: str,
    api_key: str,
    target_lang: str = "EN-US",
    source_lang: Optional[str] = None,
    use_free_api: bool = True,
    timeout: int = 60,
    max_retries: int = 6,
    backoff_s: float = 1.6,
    preserve_formatting: bool = True,
) -> str:
    """
    DeepL Translation API: POST /v2/translate with auth_key, text, target_lang, (optional source_lang).
    Docs: https://www.deepl.com/docs-api
    """
    url = deepl_endpoint(use_free_api)
    data = {
        "auth_key": api_key,
        "text": chunk,  # DeepL accepts repeated text params too; one chunk is fine
        "target_lang": target_lang,
    }
    if source_lang:
        data["source_lang"] = source_lang
    if preserve_formatting:
        data["preserve_formatting"] = "1"

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=data, timeout=timeout)

            # Handle rate limits / transient errors
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff_s * attempt)
                continue

            resp.raise_for_status()
            payload = resp.json()

            translations = payload.get("translations", [])
            if not translations:
                raise RuntimeError(f"Unexpected DeepL response: {payload}")

            return translations[0].get("text", "")

        except Exception as e:
            last_err = e
            time.sleep(backoff_s * attempt)

    raise RuntimeError(f"DeepL failed after {max_retries} retries: {last_err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Path to input .txt or .html")
    ap.add_argument("--outfile", required=True, help="Path to output English .txt")
    ap.add_argument("--assume_html", action="store_true", help="Treat input as HTML and strip tags")
    ap.add_argument("--source", default=None, help="Optional source language (e.g., DE, FR, JA). If omitted, DeepL auto-detects.")
    ap.add_argument("--target", default="EN-US", help="DeepL target language code (default: EN-US)")
    ap.add_argument("--max_chars", type=int, default=6000, help="Chunk size in characters (default: 6000)")
    ap.add_argument("--sleep", type=float, default=0.15, help="Sleep between chunks")
    ap.add_argument("--use_paid", action="store_true", help="Use paid endpoint (api.deepl.com) instead of free (api-free.deepl.com)")
    args = ap.parse_args()

    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        raise SystemExit("Missing DEEPL_API_KEY env var. Set it and re-run.")

    raw = read_input(args.infile)
    text = html_to_text(raw) if args.assume_html else raw

    chunks = chunk_text(text, max_chars=args.max_chars)
    print(f"Chunks: {len(chunks)}")

    out_parts: List[str] = []
    for i, ch in enumerate(chunks, 1):
        translated = deepl_translate_chunk(
            ch,
            api_key=api_key,
            target_lang=args.target,
            source_lang=args.source,
            use_free_api=not args.use_paid,
        )
        out_parts.append(translated)
        print(f"[{i}/{len(chunks)}] translated {len(ch)} chars")
        time.sleep(args.sleep)

    with open(args.outfile, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_parts))

    print(f"Done: {args.outfile}")


if __name__ == "__main__":
    main()
