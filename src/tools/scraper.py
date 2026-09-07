"""Web scraping and text extraction tool."""
from __future__ import annotations

import logging
import re
import urllib.request
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _clean_html_text(html_content: str) -> str:
    """Strip scripts, styles, and markup tags to extract clean text."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except ImportError:
        # Regex-based fallback cleaner
        cleaned = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        text = re.sub(r"\s+", " ", cleaned).strip()

    return text


def scrape_url_content(url: str, max_length: int = 2500) -> Dict[str, Any]:
    """Fetch and parse clean text from a URL.

    Args:
        url: Web target URL.
        max_length: Character limit for text payload to save token space.

    Returns:
        Structured content payload with url, title, and cleaned text.
    """
    if not url or not url.startswith(("http://", "https://")):
        return {
            "url": url,
            "title": "Invalid URL",
            "content": "",
            "success": False,
            "error": "URL must start with http:// or https://",
        }

    try:
        # Try using httpx if available, else urllib
        try:
            import httpx
            headers = {"User-Agent": "AutonomousResearchEngine/1.0 (Research Bot)"}
            with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
                response = client.get(url)
                html_body = response.text
                status_code = response.status_code
        except ImportError:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AutonomousResearchEngine/1.0 (Research Bot)"}
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                html_body = resp.read().decode("utf-8", errors="ignore")
                status_code = resp.status

        if status_code >= 400:
            return {
                "url": url,
                "title": "HTTP Error",
                "content": "",
                "success": False,
                "error": f"HTTP status {status_code}",
            }

        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", html_body, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Scraped Document"

        # Clean body
        cleaned_text = _clean_html_text(html_body)
        truncated_text = cleaned_text[:max_length]
        if len(cleaned_text) > max_length:
            truncated_text += " ... [truncated]"

        return {
            "url": url,
            "title": title,
            "content": truncated_text,
            "success": True,
            "error": None,
        }

    except Exception as exc:
        logger.warning(f"Failed to scrape {url}: {exc}")
        return {
            "url": url,
            "title": "Extraction Failed",
            "content": "",
            "success": False,
            "error": str(exc),
        }
