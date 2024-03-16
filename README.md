## Python script for web scraping
This Scraper will only work on Linux/MacOS since it uses Playwright so if you work on Windows you will have to leverage Ubuntu on WSL to run properly

## Installation

- create virtual environment
    pip install virtualenv

    Either run:
    python -m virtualenv scraper
    or
    virtualenv scraper

- activate virtual environment
    source ./scraper/Scripts/activate

- Install all Requirements
pip install -r requirements.txt

- copy and create .env file from .env.example and set creds value

- Install playwright dependencies while virtual env activated
playwright install


## TODO:
- Extract products and price


## Execution
```

scrapy crawl TycoonSpider -a url=https://www.fashionnova.com

```

