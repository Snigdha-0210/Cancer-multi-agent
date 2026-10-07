from ddgs import DDGS


def search_web(query: str, max_results: int = 5):
    results = []

    with DDGS() as ddgs:
        search_results = ddgs.text(
            query,
            max_results=max_results
        )

        for r in search_results:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })

    return results


if __name__ == "__main__":

    q = "latest FDA approved melanoma treatment 2026 site:fda.gov"

    data = search_web(q)

    for i, item in enumerate(data, 1):
        print("=" * 60)
        print(i)
        print(item["title"])
        print(item["url"])
        print(item["snippet"])