"""
How to run this program:

HTML filing -> English text
python translate_disclosure_google_v3.py --infile filing.html --outfile filing_en.txt --assume_html --project_id YOUR_PROJECT_ID

Plain text filing -> English text
python translate_disclosure_google_v3.py --infile filing.txt --outfile filing_en.txt --project_id YOUR_PROJECT_ID

If you KNOW the source language (optional)
python translate_disclosure_google_v3.py --infile filing.txt --outfile filing_en.txt --project_id YOUR_PROJECT_ID --source ja

Auth (recommended: Application Default Credentials):
- Local dev: gcloud auth application-default login
- Service account: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
"""

import os
import re
import time
import argparse
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

# Google auth for ADC -> OAuth2 access token
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest


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


# --------- Google Translation v3 (Advanced) ---------
def get_adc_access_token(scopes: Optional[List[str]] = None) -> str:
    """
    Uses Application Default Credentials (ADC) to get an OAuth2 access token.
    """
    if scopes is None:
        # Cloud Translation v3 accepts cloud-platform / cloud-translation scopes.
        # Using cloud-platform is common for server-to-server usage.
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    creds, _ = google.auth.default(scopes=scopes)
    if not creds.valid or creds.expired:
        creds.refresh(GoogleAuthRequest())
    return creds.token


def google_translate_chunk_v3(
    chunk: str,
    project_id: str,
    location: str = "global",
    target_lang: str = "en",
    source_lang: Optional[str] = None,
    mime_type: str = "text/plain",
    timeout: int = 60,
    max_retries: int = 6,
    backoff_s: float = 1.6,
    api_key: Optional[str] = None,
) -> str:
    """
    Cloud Translation v3 REST: projects.locations.translateText
    POST https://translation.googleapis.com/v3/projects/{project}/locations/{location}:translateText
    Body: { "contents": [...], "mimeType": "...", "targetLanguageCode": "...", "sourceLanguageCode": "..."? }
    """
    url = f"https://translation.googleapis.com/v3/projects/{project_id}/locations/{location}:translateText"
    params = {}
    if api_key:
        # Some Google APIs support API keys; if you provide one, we attach it.
        # If your project requires OAuth, omit api_key and use ADC instead.
        params["key"] = api_key

    body = {
        "contents": [chunk],
        "mimeType": mime_type,
        "targetLanguageCode": target_lang,
    }
    if source_lang:
        body["sourceLanguageCode"] = source_lang

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            headers = {"Content-Type": "application/json"}

            # Prefer OAuth via ADC unless user explicitly supplies an API key.
            if not api_key:
                token = get_adc_access_token()
                headers["Authorization"] = f"Bearer {token}"

            resp = requests.post(url, params=params, json=body, headers=headers, timeout=timeout)

            # Retry transient/rate limit errors
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff_s * attempt)
                continue

            resp.raise_for_status()
            payload = resp.json()

            translations = payload.get("translations", [])
            if not translations:
                raise RuntimeError(f"Unexpected Google response: {payload}")

            # Each item has translatedText (and detectedLanguageCode if source omitted)
            return translations[0].get("translatedText", "")

        except Exception as e:
            last_err = e
            time.sleep(backoff_s * attempt)

    raise RuntimeError(f"Google Translate v3 failed after {max_retries} retries: {last_err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True, help="Path to input .txt or .html")
    ap.add_argument("--outfile", required=True, help="Path to output English .txt")
    ap.add_argument("--assume_html", action="store_true", help="Treat input as HTML and strip tags")
    ap.add_argument("--project_id", required=True, help="Google Cloud project ID")
    ap.add_argument("--location", default="global", help='Location for Translation API (default: "global")')
    ap.add_argument("--source", default=None, help="Optional source language code (e.g., ja, de, fr). If omitted, Google auto-detects.")
    ap.add_argument("--target", default="en", help="Target language code (default: en)")
    ap.add_argument("--max_chars", type=int, default=6000, help="Chunk size in characters (default: 6000)")
    ap.add_argument("--sleep", type=float, default=0.15, help="Sleep between chunks")
    ap.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds (default: 60)")
    ap.add_argument("--api_key", default=None, help="Optional API key (if your setup supports it). Otherwise use ADC.")
    args = ap.parse_args()

    raw = read_input(args.infile)

    # If the input is HTML:
    # - You can either (A) send HTML directly to Google with mimeType text/html, or
    # - (B) strip tags and send plain text.
    #
    # Your original behavior strips tags. We'll keep that behavior *and* set mimeType accordingly:
    # - If assume_html: we strip to text, but you can flip the two lines below if you prefer sending raw HTML.
    if args.assume_html:
        text = html_to_text(raw)
        mime_type = "text/plain"
        # If you'd rather send raw HTML and let the API handle it, use:
        # text = raw
        # mime_type = "text/html"
    else:
        text = raw
        mime_type = "text/plain"

    chunks = chunk_text(text, max_chars=args.max_chars)
    print(f"Chunks: {len(chunks)}")

    out_parts: List[str] = []
    for i, ch in enumerate(chunks, 1):
        translated = google_translate_chunk_v3(
            ch,
            project_id=args.project_id,
            location=args.location,
            target_lang=args.target,
            source_lang=args.source,
            mime_type=mime_type,
            timeout=args.timeout,
            api_key=args.api_key,
        )
        out_parts.append(translated)
        print(f"[{i}/{len(chunks)}] translated {len(ch)} chars")
        time.sleep(args.sleep)

    with open(args.outfile, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_parts))

    print(f"Done: {args.outfile}")


if __name__ == "__main__":
    main()
    
