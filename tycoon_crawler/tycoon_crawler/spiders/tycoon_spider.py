import os
import scrapy
from urllib.parse import urlparse, urljoin
from urllib import robotparser
import ssl
import uuid
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from sqlalchemy import func, DateTime
import re
import json

load_dotenv()

Base = declarative_base()


class Domain(Base):
    __tablename__ = "urls"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String)
    lastScrape = Column(DateTime(timezone=True), default=datetime.now)
    product = Column(JSON)
    price = Column(JSON)
    meta = Column(JSON)


class TycoonSpider(scrapy.Spider):
    name = "TycoonSpider"

    def __init__(self, url):
        self.start_urls = [url]
        self.allowed_domains = [urlparse(url).netloc]
        self.visited_urls = set()

        # Setup SQLAlchemy
        DATABASE_URL = os.getenv("DATABASE_URL")
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        super().__init__()

        # Check if the URL exists in the database before starting
        if self.check_url_exists(url):
            self.logger.info(
                f"URL {url} already exists in the database, skipping scraping"
            )
            self.start_urls = []

    def start_requests(self):
        # Get URL from command line argument
        for url in self.start_urls:
            rp = robotparser.RobotFileParser()  # Use robotparser from urllib
            rp.set_url(f"{url}/robots.txt")
            rp.read()
            if not rp.can_fetch("*", url):
                self.logger.error(f"Crawling not allowed for {url} by robots.txt")
                continue

            # Check if the URL exists in the database
            if self.check_url_exists(url):
                self.logger.info(
                    f"URL {url} already exists in the database, skipping scraping"
                )
                break

            # Insert the URL into the database
            self.insert_url(url)

            yield scrapy.Request(
                url=url, callback=self.parse, errback=self.error_handler
            )

    def parse(self, response):
        # Check if the page is a log-in or authentication page
        if self.is_login_page(response):
            self.logger.info(f"Ignoring log-in page: {response.url}")
            return

        # Extract data from the current page
        extracted_data = self.extract_data(response)

        # Insert the entire response into the database
        self.update_meta(response.url, extracted_data)

        self.visited_urls.add(response.url)
        yield extracted_data

        # Extracting links to other pages
        for link in response.css("a::attr(href)").getall():
            absolute_url = urljoin(response.url, link)
            if absolute_url.startswith("javascript:"):
                continue  # Ignore JavaScript links
            if absolute_url not in self.visited_urls:
                yield scrapy.Request(
                    url=absolute_url, callback=self.parse, errback=self.error_handler
                )

    def extract_data(self, response):
        # Extracting data from the page
        meta_tags = {}
        og_tags = {}
        for tag in response.css("meta"):
            property_ = tag.xpath("@property").get()
            content = tag.xpath("@content").get()
            if property_ and re.match(r"^((product)s?)\b", property_, re.IGNORECASE):
                if property_.startswith("og:"):
                    og_tags[property_[3:]] = content
                elif property_.startswith("product:"):
                    meta_tags[property_[8:]] = content

        return {
            "title": response.css("title::text").get(),
            "url": response.url,
            "paragraphs": response.css("p::text").getall(),
            "headings": response.css("h1::text, h2::text, h3::text").getall(),
            "meta_tags": meta_tags,
            "og_tags": og_tags,
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

    def check_url_exists(self, url):
        # Calculate date representing 3 months ago
        three_months_ago_date = datetime.now().date() - timedelta(days=3 * 30)

        # Check if the URL domain exists in the database and was last scraped over 3 months ago
        query = self.session.query(Domain).filter(
            Domain.domain == url, func.date(Domain.lastScrape) >= three_months_ago_date
        )
        return self.session.query(query.exists()).scalar()

    def insert_url(self, url):
        # Insert a new URL into the database
        new_domain = Domain(domain=url, lastScrape=datetime.now())
        self.session.add(new_domain)
        self.session.commit()

    def update_meta(self, url, extracted_data):
        # Update meta for a given URL in the database
        domain = self.session.query(Domain).filter(Domain.domain == url).first()
        if domain:
            domain.meta = extracted_data
            self.session.commit()
