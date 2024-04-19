#!/bin/bash

# Activate the virtual environment
source ./scraper/bin/activate

# Change directory to the spiders directory
cd tycoon_crawler/tycoon_crawler/spiders

# Run the Python script
python tycoon_spider.py ignore --server

