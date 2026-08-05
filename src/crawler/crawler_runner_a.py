import core.bootstrap

import yaml
import json
import shutil
from pathlib import Path
import time

from src.crawler.scrapy_a import run_scrapy
from src.crawler.playwright import render_page


def load_config():
    with open("config/crawler_config.yaml", "r") as f:
        return yaml.safe_load(f)


config = load_config()
raw_dir = Path(config["output"]["raw_html_dir"])
rendered_dir = Path(config["output"]["rendered_html_dir"])
json_dir = Path("data/extracted_pages")

raw_dir.mkdir(parents=True, exist_ok=True)
rendered_dir.mkdir(parents=True, exist_ok=True)
json_dir.mkdir(parents=True, exist_ok=True)

def load_urls():
    url_file = config["crawler_runner"]["url_source"]
    with open(url_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_url_segments(url):
    url = url.replace("https://", "").replace("http://", "")
    return url.split("/")


def run_pipeline():
    print(">>> CRWLER AND RENDERER STARTED") #TEST

    urls = load_urls()
    max_urls = config["crawler_runner"]["max_urls"]
    urls = urls[:max_urls]

    print(">>> SCRAPY STAGE STARTED") #TEST
    scrapy_results = run_scrapy(urls)

    json_dir.mkdir(parents=True, exist_ok=True)

    for item in scrapy_results:
        url = item["url"]
        raw_html_path = item["raw_html_path"]
        has_js = item.get("has_js", False)
        timestamp = item.get("crawl_timestamp")

        url_segments = parse_url_segments(url)

        schema_item = {
            "url": url,
            "raw_html_path": raw_html_path,
            "rendered_html_path": "nnnn",   
            "language": "nnnn",            
            "crawl_timestamp": timestamp,
            "url_segments": url_segments,
            "has_js": has_js
        }

        json_path = json_dir / f"{Path(raw_html_path).stem}.json"

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(schema_item, f, ensure_ascii=False, indent=2)

    print(">>> SCRAPY STAGE FINISHED") #TEST

    for json_file in json_dir.glob("*.json"):

        with json_file.open("r", encoding="utf-8") as f:
            item = json.load(f)

        url = item["url"]
        raw_html_path = item["raw_html_path"]
        has_js = item.get("has_js", False)

        if has_js and config["playwright"]["enabled"]:
            try:
                pw_result = render_page(
                    url,
                    rendered_dir,
                    config
                )
                rendered_html_path = pw_result[
                    "rendered_html_path"
                ]
                time.sleep(
                    config["crawler_runner"]["render_delay"]
                )
            except Exception as e:
                print(
                    f">>> PLAYWRIGHT FAILED: {url}"
                )
                print(
                    f">>> ERROR: {e}"
                )
                filename = Path(raw_html_path).name        
                rendered_html_path = (
                    rendered_dir / filename
                )
                shutil.copy(
                    raw_html_path,
                    rendered_html_path
                )

                rendered_html_path = str(
                    rendered_html_path
                )
        else:
            filename = Path(raw_html_path).name

            rendered_html_path = (
                rendered_dir / filename
            )

            shutil.copy(
                raw_html_path,
                rendered_html_path
            )

            rendered_html_path = str(
                rendered_html_path
            )

        item["rendered_html_path"] = rendered_html_path

        with json_file.open("w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2)

    print(">>> CRWLER AND RENDERER FINISHED") #TEST


if __name__ == "__main__":
    run_pipeline()