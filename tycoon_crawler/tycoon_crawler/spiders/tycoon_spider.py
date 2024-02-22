import scrapy
from urllib.parse import urlparse, urljoin
from urllib import robotparser
import ssl

class TycoonSpider(scrapy.Spider):
    name = 'TycoonSpider'

    def __init__(self, url):
        self.start_urls = [url]
        self.allowed_domains = [urlparse(url).netloc]
        self.visited_urls = set()
        super().__init__()

    def start_requests(self):
        # Get URL from command line argument
        for url in self.start_urls:
            rp = robotparser.RobotFileParser()  # Use robotparser from urllib
            rp.set_url(f"{url}/robots.txt")
            rp.read()
            if not rp.can_fetch("*", url):
                self.logger.error(f"Crawling not allowed for {url} by robots.txt")
                continue
            yield scrapy.Request(url=url, callback=self.parse, errback=self.error_handler)

    def parse(self, response):
        # Check if the page is a log-in or authentication page
        if self.is_login_page(response):
            self.logger.info(f"Ignoring log-in page: {response.url}")
            return

        # Extract data from the current page
        self.visited_urls.add(response.url)
        yield self.extract_data(response)

        # Extracting links to other pages
        for link in response.css('a::attr(href)').getall():
            absolute_url = urljoin(response.url, link)
            if absolute_url.startswith('javascript:'):
                continue  # Ignore JavaScript links
            if absolute_url not in self.visited_urls:
                yield scrapy.Request(url=absolute_url, callback=self.parse, errback=self.error_handler)

    def extract_data(self, response):
        # Extracting data from the page
        meta_tags = {}
        og_tags = {}
        for tag in response.css('meta'):
            name = tag.xpath('@name').get()
            content = tag.xpath('@content').get()
            property_ = tag.xpath('@property').get()
            if name:
                meta_tags[name] = content
            if property_:
                og_tags[property_] = content
        return {
            'title': response.css('title::text').get(),
            'url': response.url,
            'paragraphs': response.css('p::text').getall(),
            'headings': response.css('h1::text, h2::text, h3::text').getall(),
            'meta_tags': meta_tags,
            'og_tags': og_tags,
            # Add more fields as needed
        }

    def error_handler(self, failure):
        # Handling various exceptions
        self.logger.error(f"Error: {failure.getErrorMessage()}")

    def is_login_page(self, response):
        # Implement logic to detect log-in or authentication pages
        # Example: Check if the URL contains 'login' or 'auth'
        if 'login' in response.url or 'auth' in response.url:
            return True
        # Add more conditions as needed
        return False
