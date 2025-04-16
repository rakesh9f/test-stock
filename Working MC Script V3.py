# -------------------- Your Reduced Script --------------------
from pyvirtualdisplay import Display
import undetected_chromedriver as uc
import time
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from tabulate import tabulate
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------------------------------------------------------
# Step 1: Set up a virtual display (requires Xvfb installed)
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
options.headless = False  # Running non-headless within virtual display
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
# Step 3: Open the research page and allow content to load.
driver.get(URL)
time.sleep(30)
html = driver.page_source
driver.quit()
display.stop()
print("Virtual display stopped.")

# -----------------------------------------------------------------------------
# Step 4: Parse the research page to extract only the today's headline.
soup = BeautifulSoup(html, "html.parser")
headline_anchors = soup.find_all("a", class_="FeaturedRes_titleBig__baIh3")
if not headline_anchors:
    headline_anchors = soup.find_all(lambda tag: tag.name == "a" and "trade spotlight:" in tag.get_text(strip=True).lower())

# Compute today's date string (e.g. "April 15").
today_str = datetime.now().strftime("%B %d").replace(" 0", " ")
today_headlines = []
for anchor in headline_anchors:
    text = anchor.get_text(strip=True)
    if "trade spotlight:" in text.lower() and today_str in text:
        today_headlines.append(anchor)  # Keep the entire anchor element

if not today_headlines:
    print("No headline matching today's date found. Exiting.")
    exit()

print("\nExtracted Headline (for today):")
print("📰", today_headlines[0].get_text(strip=True))

# -------------------- New Function: Fetch Today's Article Stocks (Expanded Content) --------------------
def fetch_today_trade_stocks(filtered_anchors):
    """
    Using the filtered headline anchors (only today's headline), open today's article using
    a headless driver configured with page_load_strategy="eager" (to avoid waiting for all resources),
    wait explicitly for key elements, remove interfering overlays/ads, click the "Read More" button,
    and then extract all stock names from the expanded content.
    Returns a list of stock names if found, else None.
    """
    target_anchor = filtered_anchors[0]
    article_url = target_anchor.get("href")
    print("\nToday's article URL:", article_url)

    # Configure driver with page load strategy 'eager' to reduce waiting time.
    options_article = uc.ChromeOptions()
    options_article.add_argument("--no-sandbox")
    options_article.add_argument("--disable-dev-shm-usage")
    options_article.add_argument("--disable-gpu")
    options_article.add_argument("--window-size=1920,1080")
    options_article.headless = True
    options_article.add_argument(f"user-agent={user_agent}")
    options_article.add_argument("--disable-blink-features=AutomationControlled")
    options_article.binary_location = "/usr/bin/google-chrome"
    options_article.page_load_strategy = "eager"  # Use eager strategy

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

    # Increase timeout and use explicit wait instead of fixed sleep.
    article_driver.set_page_load_timeout(180)
    try:
        article_driver.get(article_url)
    except Exception as e:
        print("Error while loading article using get():", e)
    
    try:
        # Wait until the "Read More" button is present (max 60 sec)
        wait = WebDriverWait(article_driver, 60)
        read_more_btn = wait.until(EC.presence_of_element_located((By.ID, "readmorearticle")))
    except Exception as e:
        print("Timeout waiting for Read More button:", e)
        read_more_btn = None

    # Remove interfering overlays or ads.
    try:
        article_driver.execute_script("""
            var overlay = document.querySelector('.wzrk-overlay');
            if (overlay) { overlay.remove(); }
            var ads = document.querySelectorAll('.ads-div-detect');
            for (var i=0; i<ads.length; i++) { ads[i].remove(); }
        """)
    except Exception:
        pass

    # If the "Read More" button was found, scroll to it and click.
    if read_more_btn:
        try:
            article_driver.execute_script("arguments[0].scrollIntoView(true);", read_more_btn)
            ActionChains(article_driver).move_to_element(read_more_btn).click(read_more_btn).perform()
            # Wait a bit for the expanded content.
            time.sleep(10)
        except Exception as e:
            print("Read More button click error:", e)
    else:
        print("Read More button not located; proceeding without expansion.")

    # Retrieve updated page source.
    try:
        article_html = article_driver.page_source
    except Exception:
        article_html = article_driver.execute_script("return document.documentElement.outerHTML;")
    article_driver.quit()

    article_soup = BeautifulSoup(article_html, "html.parser")
    # Extract stock names from <strong> tags containing an <a> tag.
    stock_names = []
    strong_tags = article_soup.find_all("strong")
    for tag in strong_tags:
        a_tag = tag.find("a")
        if a_tag:
            name = a_tag.get_text(strip=True)
            if name and name not in stock_names:
                stock_names.append(name)
    return stock_names if stock_names else None

# -------------------- Invoke the Function and Display Today's Stocks --------------------
today_stocks = fetch_today_trade_stocks(today_headlines)
if today_stocks:
    print("\nToday's Trade Spotlight Stocks (from article expanded content):")
    print(tabulate([[s] for s in today_stocks], headers=["Stock"], tablefmt="github"))
else:
    print("\nToday's Trade Spotlight article stocks could not be retrieved.")
