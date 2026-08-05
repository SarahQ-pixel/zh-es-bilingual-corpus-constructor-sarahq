import sys
import json
from pathlib import Path

from src.crawler.scrapy_b import run_scrapy


def parse_url_segments(url):
    url = url.replace("https://", "").replace("http://", "")
    return url.split("/")


def main():
    url = sys.argv[1]

    print(f">>> SCRAPY RUNNER STARTED: {url}")

    results = run_scrapy([url])

    json_dir = Path("data/extracted_pages")
    json_dir.mkdir(parents=True, exist_ok=True)

    for item in results:

        raw_html_path = item["raw_html_path"]

        schema_item = {
            "url": item["url"],
            "raw_html_path": raw_html_path,
            "rendered_html_path": "nnnn",
            "language": "nnnn",
            "crawl_timestamp": item["crawl_timestamp"],
            "url_segments": parse_url_segments(item["url"]),
            "has_js": item["has_js"]
        }

        json_path = json_dir / f"{Path(raw_html_path).stem}.json"

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(
                schema_item,
                f,
                ensure_ascii=False,
                indent=2
            )

    print(f">>> SCRAPY RUNNER FINISHED: {url}")


if __name__ == "__main__":
    main()