# -------------------- Your Existing Working Script --------------------
from pyvirtualdisplay import Display
import undetected_chromedriver as uc
import time
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import re
from tabulate import tabulate
from datetime import datetime

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
options.headless = False  # Run non-headless (within virtual display)
user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/135.0.7049.84 Safari/537.36")
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.binary_location = "/usr/bin/google-chrome"

URL = "https://www.moneycontrol.com/markets/stock-ideas/research/#hot-stocks/"
print("Opening URL:", URL)

try:
    driver = uc.Chrome(options=options, version_main=135)
except Exception as err:
    print("Error launching Chrome:", err)
    display.stop()
    exit()

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
# Step 3: Open the research URL and allow time for dynamic content to load.
driver.get(URL)
time.sleep(10)

html = driver.page_source
driver.quit()
display.stop()
print("Virtual display stopped.")

# -----------------------------------------------------------------------------
# Step 4: Parse the research page using BeautifulSoup to extract headlines that contain "Trade Spotlight:".
soup = BeautifulSoup(html, "html.parser")

headline_anchors = soup.find_all("a", class_="FeaturedRes_titleBig__baIh3")
if not headline_anchors:
    headline_anchors = soup.find_all(lambda tag: tag.name == "a" and "trade spotlight:" in tag.get_text(strip=True).lower())

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
# Step 5: Extract candidate stock names from the headlines (from research page).
ignore = {"Trade", "Spotlight", "How", "Should", "You", "On", "And", "Others"}
stock_set = set()
for title in headlines:
    tokens = re.findall(r"\b[A-Z][a-zA-Z&.\-]{2,}\b", title)
    stock_set.update(token for token in tokens if token not in ignore)

stocks = sorted(list(stock_set))
if not stocks:
    print("No candidate stock names extracted.")
    exit()

table_data = [[s] for s in stocks]
print("\nExtracted Candidate Stock Names (from headlines):")
print(tabulate(table_data, headers=["Stock"], tablefmt="github"))

# -------------------- End of Existing Script --------------------


# -------------------- New Function: Fetch Today's Article Stocks (Expanded Content) --------------------
def fetch_today_trade_stocks(headline_anchors):
    """
    Identify today's Trade Spotlight article by matching today's date (e.g., "April 15")
    among the headline anchors. Open that article with stealth enabled, click the "Read More" button,
    and then extract all stock names from the expanded content.
    Returns a list of stock names if successful; otherwise, returns None.
    """
    # Format today's date (e.g., "April 15")
    today_str = datetime.now().strftime("%B %d").replace(" 0", " ")
    target_anchor = None
    for a in headline_anchors:
        if today_str in a.get_text(strip=True):
            target_anchor = a
            break
    if target_anchor is None:
        return None

    article_url = target_anchor.get("href")
    print("\nToday's article URL:", article_url)

    # Set up a headless driver for the article page.
    options_article = uc.ChromeOptions()
    options_article.add_argument("--no-sandbox")
    options_article.add_argument("--disable-dev-shm-usage")
    options_article.add_argument("--disable-gpu")
    options_article.add_argument("--window-size=1920,1080")
    options_article.headless = True
    options_article.add_argument(f"user-agent={user_agent}")
    options_article.add_argument("--disable-blink-features=AutomationControlled")
    options_article.binary_location = "/usr/bin/google-chrome"

    try:
        article_driver = uc.Chrome(options=options_article, version_main=135)
    except Exception:
        return None

    try:
        stealth(
            article_driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception:
        pass

    # Extend the page load timeout.
    article_driver.set_page_load_timeout(150)
    try:
        article_driver.get(article_url)
        time.sleep(30)  # Wait for the article page to load.
    except Exception as e:
        print("Error while loading article:", e)
        try:
            article_html = article_driver.execute_script("return document.documentElement.outerHTML;")
            time.sleep(5)
        except Exception:
            article_driver.quit()
            return None
    # Attempt to click the "Read More" button if it exists.
    try:
        from selenium.webdriver.common.by import By
        read_more_btn = article_driver.find_element(By.ID, "readmorearticle")
        if read_more_btn:
            read_more_btn.click()
            time.sleep(10)  # Allow time for the expanded content to load.
    except Exception as e:
        # If the button isn't found or clickable, continue.
        print("Read More button not found or could not be clicked:", e)
    # Get the updated page source after clicking "Read More".
    article_html = article_driver.page_source
    article_driver.quit()

    # Parse the expanded article content.
    article_soup = BeautifulSoup(article_html, "html.parser")
    # Find all <strong> tags that contain an <a> tag (each representing a stock).
    stock_names = []
    strong_tags = article_soup.find_all("strong")
    for tag in strong_tags:
        a_tag = tag.find("a")
        if a_tag:
            name = a_tag.get_text(strip=True)
            if name and name not in stock_names:
                stock_names.append(name)

    return stock_names if stock_names else None

# -------------------- Invoke the New Function and Display Today's Stocks --------------------
today_stocks = fetch_today_trade_stocks(headline_anchors)
if today_stocks:
    print("\nToday's Trade Spotlight Stocks (from article expanded content):")
    print(tabulate([[s] for s in today_stocks], headers=["Stock"], tablefmt="github"))
else:
    print("\nToday's Trade Spotlight article stocks could not be retrieved.")
