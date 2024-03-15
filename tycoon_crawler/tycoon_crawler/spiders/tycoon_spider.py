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


class Url(Base):
    __tablename__ = "urls"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    raw = Column(String)
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
            good_domain = self.insert_url(url)
            if not good_domain:
                self.logger.error(
                    f"URL {url} Could not extract good domain from url"
                )
                break

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

        print("View Response", response)

        # Extracting links to other pages
        for link in response.css("a::attr(href)").getall():
            absolute_url = urljoin(response.url, link)
            if absolute_url.startswith("javascript:"):
                continue  # Ignore JavaScript links
            if absolute_url not in self.visited_urls:
                print("Run Req", absolute_url)
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
        query = self.session.query(Url).filter(
            Url.domain == url, func.date(Url.lastScrape) >= three_months_ago_date
        )
        return self.session.query(query.exists()).scalar()

    def insert_url(self, url, extracted_data=None):
        # Insert a new URL into the database
        pattern = r"(?::\/\/)?([a-zA-Z0-9.-]+?)(?:\/|$)"
        match = re.search(pattern, url, re.IGNORECASE)
        print("Match", match, "Url", url)
        if match:
            use_domain = match.group(1)
            print("Domain", use_domain)
            new_url_kwargs = {
                'domain': use_domain,
                'raw': url,
                'lastScrape': datetime.now()
            }
            if extracted_data is not None:
                new_url_kwargs['meta'] = extracted_data
            print("New Url", new_url_kwargs)
            new_url = Url(**new_url_kwargs)
            self.session.add(new_url)
            self.session.commit()
            return True
        else:
            return False

    def update_meta(self, url, extracted_data):
        # Update meta for a given URL in the database
        print("Updating Meta", url)
        urlRec = self.session.query(Url).filter(Url.raw == url).first()
        if urlRec:
            urlRec.meta = extracted_data
            self.session.commit()
        else:
            print("No Match Add New", url)
            self.insert_url(url, extracted_data)
