# pip install undetected-chromedriver pyvirtualdisplay selenium-stealth beautifulsoup4 tabulate
from pyvirtualdisplay import Display
import undetected_chromedriver as uc
import time
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import re
from tabulate import tabulate

# -----------------------------------------------------------------------------
# Step 1: Set up a virtual display (requires Xvfb installed on your system)
display = Display(visible=0, size=(1920, 1080))
display.start()
print("Virtual display started.")

# -----------------------------------------------------------------------------
# Step 2: Configure undetected‑chromedriver options with stealth settings.
options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
# Use non-headless mode inside the virtual display so that it behaves like a normal browser.
options.headless = False
# Use a realistic user-agent that matches your installed Chrome version (here Chrome 135)
user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/135.0.7049.84 Safari/537.36")
options.add_argument(f"user-agent={user_agent}")
# Minimize automation flags
options.add_argument("--disable-blink-features=AutomationControlled")
# Specify Chrome binary location (confirmed on your system)
options.binary_location = "/usr/bin/google-chrome"

URL = "https://www.moneycontrol.com/markets/stock-ideas/research/#hot-stocks/"
print("Opening URL:", URL)

# Launch Chrome using undetected_chromedriver and specify the main version (135)
try:
    driver = uc.Chrome(options=options, version_main=135)
except Exception as err:
    print("Error launching Chrome:", err)
    display.stop()
    exit()

# Activate selenium-stealth to mask automation fingerprints.
try:
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    print("Stealth mode activated.")
except Exception as e:
    print("Error activating stealth mode:", e)

# -----------------------------------------------------------------------------
# Step 3: Open the URL and allow time for dynamic content to load.
driver.get(URL)
time.sleep(30)  # Adjust the sleep time if necessary.

# Grab the page source.
html = driver.page_source
driver.quit()
display.stop()
print("Virtual display stopped.")

# -----------------------------------------------------------------------------
# Step 4: Parse the page using BeautifulSoup to extract headlines containing "Trade Spotlight:".
soup = BeautifulSoup(html, "html.parser")

# Try to locate anchor tags with the class that holds headline text.
headline_anchors = soup.find_all("a", class_="FeaturedRes_titleBig__baIh3")
# If not found by class, try a fallback: any anchor containing "trade spotlight:" in its text.
if not headline_anchors:
    headline_anchors = soup.find_all(lambda tag: tag.name == "a" and "trade spotlight:" in tag.get_text(strip=True).lower())

# Extract headlines that contain "trade spotlight:" (case-insensitive).
headlines = []
for anchor in headline_anchors:
    text = anchor.get_text(strip=True)
    if "trade spotlight:" in text.lower():
        headlines.append(text)

if not headlines:
    print("No headlines found containing 'Trade Spotlight:'. Exiting.")
    exit()

print("\nExtracted Headlines:")
for h in headlines:
    print("📰", h)

# -----------------------------------------------------------------------------
# Step 5: Extract candidate stock names using a regex.
# We assume candidate stock names are words that start with an uppercase letter and are at least 3 characters long.
ignore = {"Trade", "Spotlight", "How", "Should", "You", "On", "And", "Others"}
stock_set = set()
for title in headlines:
    tokens = re.findall(r"\b[A-Z][a-zA-Z&.\-]{2,}\b", title)
    stock_set.update(token for token in tokens if token not in ignore)

stocks = sorted(list(stock_set))
if not stocks:
    print("No candidate stock names extracted.")
    exit()

# -----------------------------------------------------------------------------
# Step 6: Display the extracted candidate stock names in a table
table_data = [[s] for s in stocks]
print("\nExtracted Candidate Stock Names:")
print(tabulate(table_data, headers=["Stock"], tablefmt="github"))
