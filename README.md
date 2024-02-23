## Python script for web scraping

## Installation
- create virtual environment
    pip install virtualenv

    Either run:
    python -m virtualenv scraper
    or
    virtualenv scraper

- activate virtual environment
    source ./scraper/Scripts/activate

- pip install -r requirements.txt
- copy and create .env file from .env.example and set creds value

## TODO:

- Save data in Postgres. Maybe save S3 as well

## Execution
```

scrapy crawl TycoonSpider -a url=https://www.fashionnova.com

```

