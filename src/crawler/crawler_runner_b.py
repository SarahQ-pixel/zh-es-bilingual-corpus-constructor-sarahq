import core.bootstrap

import yaml
import json
import shutil
from pathlib import Path
import time
import subprocess
import sys

from src.crawler.playwright import render_page


def load_config():
    with open("config/crawler_config.yaml", "r") as f:
        return yaml.safe_load(f)


config = load_config()
raw_dir = Path(config["output"]["raw_html_dir"])
rendered_dir = Path(config["output"]["rendered_html_dir"])
json_dir = Path(config["output"]["extracted_pages_dir"])

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


def crawler_runner_b():
    print(">>> CRWLER AND RENDERER STARTED") #TEST

    urls = load_urls()
    max_urls = config["crawler_runner"]["max_urls"]
    urls = urls[:max_urls]

    for url in urls:
        print(f">>> START SCRAPY FOR {url}") #TEST
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.crawler.scrapy_runner_b",
                url
            ],
            check=True
        )
        print(f">>> FINISHED SCRAPY FOR {url}") #TEST

    print(">>> RENDERER STARTED") #TEST

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

    print(">>> RENDERER FINISHED") #TEST


if __name__ == "__main__":
    crawler_runner_b()