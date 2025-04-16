import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import requests

def get_free_https_proxies_from_urls(url_list):
    """
    Scrape free HTTPS proxies from multiple URLs.
    Each page is expected to have a table with id 'proxylisttable'.
    Returns a list of proxies in the format 'https://IP:PORT'.
    """
    proxies = set()
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36")
    }
    for url in url_list:
        try:
            print(f"Fetching proxies from: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', id='proxylisttable')
            if table is None:
                print(f"No proxy table found at {url}")
                continue
            tbody = table.find('tbody')
            if not tbody:
                continue
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    if https.lower() == 'yes':
                        proxy = f"https://{ip}:{port}"
                        proxies.add(proxy)
        except Exception as e:
            print(f"Error fetching proxies from {url}: {e}")
    return list(proxies)

# List of proxy source URLs
proxy_urls = [
    "https://free-proxy-list.net/",
    "https://www.sslproxies.org/",
    "https://us-proxy.org/"
]

free_proxies = get_free_https_proxies_from_urls(proxy_urls)
if free_proxies:
    # Pick the first proxy from the collected list
    chosen_proxy = free_proxies[0]
    print("Using free proxy:", chosen_proxy)
else:
    chosen_proxy = None
    print("No free proxies found. Proceeding without proxy.")

# Set up Chrome options using undetected_chromedriver
options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.headless = True  # Run headless

# Mimic a real user agent
user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/115.0.0.0 Safari/537.36")
options.add_argument(f"user-agent={user_agent}")

# Add the chosen proxy (if any) to Chrome options
if chosen_proxy:
    options.add_argument(f"--proxy-server={chosen_proxy}")

# Append the Hot Stocks hash so that the content loads automatically
URL = "https://www.moneycontrol.com/markets/stock-ideas/research/#hot-stocks/"
print(f"🚀 Opening: {URL}")

# Initialize the driver. undetected_chromedriver handles chromedriver automatically.
driver = uc.Chrome(options=options)
driver.get(URL)

# Allow extra time for the page (including dynamic content) to load.
time.sleep(7)

try:
    # Wait up to 30 seconds for the Hot Stocks container to be present.
    hot_section_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.HotStock_hotStockMain__acv4S"))
    )
    print("✅ 'Hot Stocks' section loaded.")
except Exception as e:
    print("❌ Failed to load 'Hot Stocks' section:", e)
    driver.quit()
    exit()

# Get the page source and quit the driver.
html = driver.page_source
driver.quit()

# Parse the HTML with BeautifulSoup.
soup = BeautifulSoup(html, "html.parser")
hot_section = soup.find("div", class_="HotStock_hotStockMain__acv4S")
if not hot_section:
    print("❌ 'Hot Stocks' section not found in parsed HTML.")
    exit()

# Extract headlines (anchor texts) that mention "trade spotlight" (case-insensitive).
headlines = []
for a in hot_section.find_all("a", href=True):
    text = a.get_text(strip=True)
    if "trade spotlight" in text.lower():
        headlines.append(text)

if not headlines:
    print("❌ No headlines containing 'trade spotlight' were found.")
    exit()

print("Extracted Headlines:")
for headline in headlines:
    print("📰", headline)

# Use a regex to extract candidate stock names.
# The regex matches words starting with an uppercase letter and at least 3 characters long.
ignore = {"Trade", "Spotlight", "How", "Should", "You", "On", "And", "Others"}
stocks = set()
for title in headlines:
    tokens = re.findall(r"\b[A-Z][a-zA-Z&.\-]{2,}\b", title)
    stocks.update(token for token in tokens if token not in ignore)

print("\n📈 Final Stock List:")
if stocks:
    for s in sorted(stocks):
        print("•", s)
else:
    print("No stocks found.")
