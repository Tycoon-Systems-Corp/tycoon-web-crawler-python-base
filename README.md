## Python script for web scraping
This Scraper will only work on Linux/MacOS since it uses Playwright so if you work on Windows you will have to leverage Ubuntu on WSL to run properly

## Installation

- copy and create .env file from .env.example and set creds value
cp .env.example .env

- create virtual environment
    pip install virtualenv

    Either run:
    python -m virtualenv scraper
    or
    virtualenv scraper

- activate virtual environment
    source ./scraper/Scripts/activate
    or
    source ./scraper/bin/activate

- Install all Requirements. If you have permissions problems try adding "--user" as arguement
pip install -r requirements.txt

- Install playwright dependencies while virtual env activated
playwright install

# gRPC Server
source ./scraper/Scripts/activate
cd tycoon_crawler/tycoon_crawler/spiders
python tycoon_spider.py ignore --server

## TODO:
- Ensure server can queue many urls
- Parallelism


## Execution
```
cd tycoon_crawler/tycoon_crawler/spiders
python tycoon_spider.py https://www.ikea.com
```

# Quick start
source ./scraper/Scripts/activate
cd tycoon_crawler/tycoon_crawler/spiders
python tycoon_spider.py https://midnightstudios.live/products/midnight-x-needles-track-jacket-blue



# start celery
celery -A tycoon_spider worker --loglevel=info