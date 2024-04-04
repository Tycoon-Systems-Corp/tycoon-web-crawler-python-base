import os
import sys
import re
import uuid

from datetime import datetime, timedelta
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, String, DateTime, JSON, ARRAY, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request

import product_tools

load_dotenv()

Base = declarative_base()


class Url(Base):
    __tablename__ = "urls"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    raw = Column(String)
    domain = Column(String)
    lastScrape = Column(DateTime(timezone=True), default=datetime.now)
    product = Column(JSON)
    price = Column(JSON)
    images = Column(ARRAY(JSON))
    meta = Column(JSON)


class ProxyMiddleware(object):
    def process_request(self, request, spider):
        # Replace 'PROXY_ENDPOINT' and 'PROXY_PORT' with your actual proxy details
        proxy_url = f"http://{os.getenv('PROXY_USER')}:{os.getenv('PROXY_PASSWORD')}@{os.getenv('PROXY_ENDPOINT')}:{os.getenv('PROXY_PORT')}"
        request.meta["proxy"] = proxy_url


class TycoonSpider(Spider):
    name = "tycoon_spider"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
            "__main__.ProxyMiddleware": 100,
        }
    }

    def __init__(self, *args, **kwargs):
        super(TycoonSpider, self).__init__(*args, **kwargs)
        self.start_urls = [kwargs.get("url")]
        self.visited_urls = set()
        # Initialize database connection
        DATABASE_URL = os.getenv("DATABASE_URL")
        self.engine = create_engine(DATABASE_URL)

        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def check_url_exists(self, url):
        # Calculate date representing 3 months ago
        three_months_ago_date = datetime.now().date() - timedelta(days=3 * 30)

        # Check if the URL domain exists in the database and was last scraped over 3 months ago
        query = self.session.query(Url).filter(
            Url.domain == url, func.date(Url.lastScrape) >= three_months_ago_date
        )
        return self.session.query(query.exists()).scalar()

    def insert_url(self, url, extracted_data=None):
        # Insert a new URL into the database
        pattern = r"(?::\/\/)?([a-zA-Z0-9.-]+?)(?:\/|$)"
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            use_domain = match.group(1)
            new_url_kwargs = {
                "domain": use_domain,
                "raw": url,
                "lastScrape": datetime.now(),
            }
            if extracted_data is not None:
                new_url_kwargs["meta"] = extracted_data["meta"]
                new_url_kwargs["product"] = extracted_data["product"]
                new_url_kwargs["images"] = extracted_data["images"]
                new_url_kwargs["price"] = extracted_data["price"]
            new_url = Url(**new_url_kwargs)
            self.session.add(new_url)
            self.session.commit()
            return True
        else:
            return False

    def update_meta(self, url, extracted_data):
        # Update meta for a given URL in the database
        urlRec = self.session.query(Url).filter(Url.raw == url).first()
        if urlRec:
            urlRec.meta = extracted_data['meta']
            urlRec.product = extracted_data['product']
            urlRec.images = extracted_data['images']
            urlRec.price = extracted_data['price']
            self.session.commit()
        else:
            self.insert_url(url, extracted_data)

    def parse(self, response):
        print("Start Parse")
        # Check if the page is a log-in or authentication page
        if self.is_login_page(response):
            self.logger.info(f"Ignoring log-in page: {response.url}")
            return

        print("Extracting")
        # Extract data from the current page using Playwright
        extracted_data = self.extract_data_with_playwright(response)

        # Insert the entire response into the database
        self.update_meta(response.url, extracted_data)

        print("Adding Url", response.url)
        self.visited_urls.add(response.url)
        yield extracted_data

        print("View Response", response)

        # Extracting links to other pages
        for link in response.css("a::attr(href)").getall():
            absolute_url = response.urljoin(link)
            if absolute_url.startswith("javascript:"):
                continue  # Ignore JavaScript links
            if absolute_url not in self.visited_urls:
                print("Run Req", absolute_url)
                self.visited_urls.add(
                    absolute_url
                )  # Avoid re-scrape now that we're running request for this link
                yield Request(
                    url=absolute_url,
                    callback=self.parse,
                    errback=self.error_handler,
                    meta={"playwright": True},
                )

    def extract_data_with_playwright(self, response):
        # Import Playwright inside the method to avoid issues with asynchronous execution
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(response.url)

            # Extracting data using Playwright
            title = page.title()
            paragraphs = page.query_selector_all("p")
            headings = page.query_selector_all("h1, h2, h3")

            # Convert Playwright elements to text
            paragraphs_text = [p.text_content() for p in paragraphs]
            headings_text = [h.text_content() for h in headings]

            product_likely = product_tools.detect_product_likely(page)
            print(f"Is Product?", product_likely)
            product_data = {
                "product": {},
                "price": {},
                "images": []
            }
            if product_likely.get('likelihood') and product_likely["likelihood"] > 51:
                product_data = product_tools.get_product_data(page, product_likely)

            # Print output for debugging
            if os.getenv('LOG_OUTPUT') == 'True':
                with open('../../../output.txt', 'a', encoding="utf-8") as f:
                    f.write(page.content())

            # Close the browser
            browser.close()

            return {
                "meta": {
                    "title": title,
                    "url": response.url,
                    "paragraphs": paragraphs_text,
                    "headings": headings_text,
                },
                "product": product_data["product"],
                "price": product_data["price"],
                "images": product_data["images"]
                # Add more fields as needed
            }

    def error_handler(self, failure):
        # Handling various exceptions
        self.logger.error(f"Error: {failure.getErrorMessage()}")

    def is_login_page(self, response):
        # Implement logic to detect log-in or authentication pages
        # Example: Check if the URL contains 'login' or 'auth'
        if "login" in response.url or "auth" in response.url:
            return True
        # Add more conditions as needed
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <url>")
        sys.exit(1)

    url_to_scrape = sys.argv[1]

    process = CrawlerProcess(
        settings={
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        }
    )
    process.crawl(TycoonSpider, url=url_to_scrape)
    process.start()
