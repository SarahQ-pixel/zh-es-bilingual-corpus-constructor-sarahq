import yaml
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
from scrapy import signals


def load_config():
    with open("config/crawler_config.yaml", "r") as f:
        return yaml.safe_load(f)


class WebSpider(scrapy.Spider):
    name = "web_spider"

    config = load_config()
    allowed_domains = config["scrapy"]["allowed_domains"]

    def __init__(self, urls, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls
        self.config = config
        self.output_dir = Path(config["output"]["raw_html_dir"])
        self.exclude_url_patterns = config["scrapy"].get(
            "exclude_url_patterns",
            []
        )
        self.exclude_url_patterns = config["scrapy"].get(
            "exclude_url_patterns",
            []
        )
        self.traversal_only_patterns = config["scrapy"].get(
            "traversal_only_patterns",
            []
        )
        
    def has_javascript(self, response):
        if response.css("script"):
            return True
        js_event_attrs = ["onclick", "onerror", "onload", "onmouseover", "onchange", "onsubmit"]
        for attr in js_event_attrs:
            if response.xpath(f"//*[@{attr}]"):
                return True
        return False

    def parse(self, response):
        url = response.url

        if any(p in url for p in self.exclude_url_patterns):
            return

        is_traversal_only = any(
            pattern in url
            for pattern in self.traversal_only_patterns
        )

        if not is_traversal_only:
            filename = self.config["output"]["output_filename_prefix"] + hashlib.md5(url.encode()).hexdigest() + ".html"
            path = self.output_dir / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                f.write(response.text)
            item = {
                "url": url,
                "raw_html_path": str(path),
                "has_js": self.has_javascript(response),
                "crawl_timestamp": datetime.now(timezone.utc).isoformat()
            }

            yield item

        links = LinkExtractor(
            allow_domains=self.allowed_domains if hasattr(self, "allowed_domains") else None
        ).extract_links(response)

        for link in links:
            if any(
                pattern in link.url
                for pattern in self.exclude_url_patterns
            ):
                continue

            yield scrapy.Request(
                url=link.url,
                callback=self.parse,
            )

def run_scrapy(urls):
    config = load_config()

    results = []

    process = CrawlerProcess(settings={
        "ROBOTSTXT_OBEY": config["scrapy"]["robotstxt_obey"],
        "DOWNLOAD_DELAY": config["scrapy"]["download_delay"],
        "CONCURRENT_REQUESTS": config["scrapy"]["concurrent_requests"],
        "LOG_LEVEL": config["scrapy"]["log_level"],
        "DEPTH_LIMIT": config["scrapy"]["depth_limit"],
        "USER_AGENT": config["scrapy"]["user_agent"],
        "CLOSESPIDER_PAGECOUNT": config["scrapy"]["closespider_pagecount"]
    })

    def collect_item(item, response, spider):
        results.append(item)

    process.crawl(
        WebSpider,
        urls=urls,
        config=config
    )

    crawler = process.crawlers.pop()

    crawler.signals.connect(
        collect_item,
        signals.item_scraped
    )

    process.start()
    
    return results