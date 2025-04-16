import requests
from bs4 import BeautifulSoup
import re

# RSS feed URL
RSS_URL = "https://www.moneycontrol.com/rss/MCtopnews.xml"

# Get RSS content
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(RSS_URL, headers=headers)
if response.status_code != 200:
    print("Failed to fetch RSS feed")
    exit()

# Parse RSS feed
soup = BeautifulSoup(response.content, features="xml")
items = soup.find_all("item")

FIXED_PREFIX = "Trade Spotlight: How should you trade "

def extract_stocks_from_url(url):
    pattern = re.compile(r"trade-spotlight-how-should-you-trade-(.*?)-on-")
    match = pattern.search(url)
    if match:
        tokens = match.group(1).split('-')
        ignore = {"and", "others", ""}
        return [token.capitalize() for token in tokens if token.lower() not in ignore]
    return []

# Collect matching links
stock_links = []
for item in items:
    title = item.title.text
    link = item.link.text

    if title.lower().startswith("trade spotlight:"):
        stock_links.append(link)

# Extract stocks
aggregate_stocks = set()
for link in stock_links:
    stocks = extract_stocks_from_url(link)
    if stocks:
        print(f"Found in link: {link}")
        print("Stocks:", stocks)
        aggregate_stocks.update(stocks)

# Output
print("\nFinal Stock List:")
if not aggregate_stocks:
    print("No stocks found.")
else:
    for stock in sorted(aggregate_stocks):
        print("-", stock)