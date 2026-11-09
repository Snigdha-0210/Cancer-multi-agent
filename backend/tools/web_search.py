from ddgs import DDGS
import requests


def search_web(query: str, max_results: int = 5):
    results = []

    with DDGS() as ddgs:
        search_results = ddgs.text(
            query,
            max_results=max_results,
            backend="bing",
        )

        for r in search_results:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })

    return results



def extract_webpage(url: str):
    """
    Extract readable webpage content using DDGS
    and retrieve original HTML for metadata extraction.
    """
    content = ""
    html = ""
    extracted_url = url

    # Step 1: Extract readable content using DDGS
    try:
        with DDGS() as ddgs:
            page = ddgs.extract(url, fmt="text_markdown")

        content = page.get("content", "")

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        extracted_url = page.get("url", url)

    except Exception as error:
        print(f"DDGS extraction warning for {url}: {error}")

    # Step 2: Retrieve original HTML for date metadata
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
                )
            },
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "text/html" in content_type or "application/xhtml+xml" in content_type:
            html = response.text

    except requests.RequestException as error:
        print(f"HTML retrieval warning for {url}: {error}")

    return {
        "url": extracted_url,
        "content": content,
        "html": html,
        "success": bool(content.strip()),
    }
