"""
Maroon OSINT Swarm — Open Source Intelligence Spider Network (v4.0)
Codex §4.5: Scrapy spider network for public data collection.
Geopolitical, market, and demographic data scraping.
All extracted data feeds directly into Palantir Bronze layer.
"""
import scrapy
from scrapy.crawler import CrawlerProcess
import hashlib
import json
from datetime import datetime, timezone


class BasePalantirSpider(scrapy.Spider):
    """Base spider class that implements the Palantir Mandate for telemetry."""

    def emit_telemetry(self, event_type: str, payload: dict):
        """Emit telemetry to Palantir Lake (log-based in standalone mode)."""
        envelope = {
            "source": "maroon-osint-swarm",
            "spider": self.name,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
            "verification_status": "PENDING_MERKLE_HASH",
        }
        self.logger.info(f"[Telemetry] {json.dumps(envelope, default=str)}")

    def compute_hash(self, data: dict) -> str:
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha512(canonical.encode()).hexdigest()


class CensusDataSpider(BasePalantirSpider):
    """Scrapes U.S. Census Bureau demographic data for community analysis."""
    name = "census_demographics"
    allowed_domains = ["census.gov", "data.census.gov"]
    start_urls = ["https://data.census.gov/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 2.0,
        "USER_AGENT": "MaroonOSINT/4.0 (+https://maroontechnologies.org/bot)",
    }

    def parse(self, response):
        self.emit_telemetry("census_page_scraped", {"url": response.url, "status": response.status})
        # Extract demographic data tables
        tables = response.css("table")
        for table in tables:
            headers = table.css("th::text").getall()
            rows = table.css("tr")
            for row in rows:
                cells = row.css("td::text").getall()
                if cells:
                    record = dict(zip(headers, cells)) if headers else {"raw": cells}
                    record["source_url"] = response.url
                    record["content_hash"] = self.compute_hash(record)
                    yield record


class EconomicIndicatorSpider(BasePalantirSpider):
    """Scrapes public economic indicators (BLS, FRED) for market analysis."""
    name = "economic_indicators"
    allowed_domains = ["bls.gov", "fred.stlouisfed.org"]
    start_urls = ["https://www.bls.gov/news.release/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3.0,
        "USER_AGENT": "MaroonOSINT/4.0 (+https://maroontechnologies.org/bot)",
    }

    def parse(self, response):
        self.emit_telemetry("economic_page_scraped", {"url": response.url, "status": response.status})
        # Extract press release links
        for link in response.css("a[href*='nr']::attr(href)").getall():
            yield response.follow(link, callback=self.parse_release)

    def parse_release(self, response):
        title = response.css("h1::text, h2::text").get("").strip()
        body = " ".join(response.css("p::text").getall()).strip()
        if title and body:
            record = {
                "title": title,
                "body": body[:2000],
                "source_url": response.url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": self.compute_hash({"title": title, "url": response.url}),
            }
            self.emit_telemetry("economic_release_extracted", {"title": title, "url": response.url})
            yield record


class OpportunityZoneSpider(BasePalantirSpider):
    """Scrapes Opportunity Zone data for real estate acquisition intelligence."""
    name = "opportunity_zones"
    allowed_domains = ["cdfifund.gov", "opportunitydb.com"]
    start_urls = ["https://opportunitydb.com/zones/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3.0,
        "USER_AGENT": "MaroonOSINT/4.0 (+https://maroontechnologies.org/bot)",
    }

    def parse(self, response):
        self.emit_telemetry("oz_page_scraped", {"url": response.url, "status": response.status})
        for zone in response.css(".zone-card, .zone-item, tr"):
            tract = zone.css(".tract::text, td:first-child::text").get("").strip()
            state = zone.css(".state::text, td:nth-child(2)::text").get("").strip()
            if tract:
                record = {
                    "census_tract": tract,
                    "state": state,
                    "source_url": response.url,
                    "content_hash": self.compute_hash({"tract": tract, "state": state}),
                }
                yield record


class PublicContractsSpider(BasePalantirSpider):
    """Scrapes government contract awards for sovereign procurement intelligence."""
    name = "public_contracts"
    allowed_domains = ["usaspending.gov", "sam.gov"]
    start_urls = ["https://www.usaspending.gov/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3.0,
        "USER_AGENT": "MaroonOSINT/4.0 (+https://maroontechnologies.org/bot)",
    }

    def parse(self, response):
        self.emit_telemetry("contracts_page_scraped", {"url": response.url, "status": response.status})
        for item in response.css(".award-result, .result-item"):
            title = item.css(".title::text, h3::text").get("").strip()
            amount = item.css(".amount::text, .value::text").get("").strip()
            if title:
                yield {
                    "title": title,
                    "amount": amount,
                    "source_url": response.url,
                    "content_hash": self.compute_hash({"title": title}),
                }


# ---------------------------------------------------------------------------
# Scrapy Settings for the Swarm
# ---------------------------------------------------------------------------

SCRAPY_SETTINGS = {
    "BOT_NAME": "maroon-osint-swarm",
    "ROBOTSTXT_OBEY": True,
    "CONCURRENT_REQUESTS": 4,
    "DOWNLOAD_DELAY": 2.0,
    "USER_AGENT": "MaroonOSINT/4.0 (+https://maroontechnologies.org/bot)",
    "LOG_LEVEL": "INFO",
    "FEEDS": {
        "output/%(name)s_%(time)s.jsonl": {
            "format": "jsonlines",
            "encoding": "utf-8",
        },
    },
    "ITEM_PIPELINES": {},
}


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    spider_map = {
        "census": CensusDataSpider,
        "economic": EconomicIndicatorSpider,
        "opportunity_zones": OpportunityZoneSpider,
        "contracts": PublicContractsSpider,
    }

    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    process = CrawlerProcess(settings=SCRAPY_SETTINGS)

    if target == "all":
        for spider_cls in spider_map.values():
            process.crawl(spider_cls)
    elif target in spider_map:
        process.crawl(spider_map[target])
    else:
        print(f"Unknown spider: {target}")
        print(f"Available: {', '.join(spider_map.keys())}, all")
        sys.exit(1)

    print(f"[OSINT Swarm] Launching spider(s): {target}")
    process.start()
