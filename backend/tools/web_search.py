from ddgs import DDGS


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
    Extract readable text from a webpage using DDGS.
    """
    try:
        with DDGS() as ddgs:
            page = ddgs.extract(url, fmt="text_markdown")

        content = page.get("content", "")

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        return {
            "url": page.get("url", url),
            "content": content,
            "success": bool(content.strip()),
        }

    except Exception as error:
        print(f"Page extraction warning for {url}: {error}")
        return {
            "url": url,
            "content": "",
            "success": False,
        }


if __name__ == "__main__":

    q = "latest FDA approved melanoma treatment 2026 site:fda.gov"

    data = search_web(q)

    for i, item in enumerate(data, 1):
        print("=" * 60)
        print(i)
        print(item["title"])
        print(item["url"])
        print(item["snippet"])
