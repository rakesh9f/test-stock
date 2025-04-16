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
import requests  # Already used for Telegram messaging

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
# Step 4: Parse the research page to extract only today's headline.
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
            # Wait a bit for the expanded content to load.
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

# -------------------- New Function: Fetch Groww Blog Stocks --------------------
def fetch_groww_blog_stocks():
    """
    Fetch the Groww blog article from the URL constructed using the target title:
        "stocks-to-watch-today-16th-april-2025"
    and extract stock names from the section under the <h2> header
    "Key Stocks in Focus". Each record is expected to be inside a <p> tag containing a
    <strong><a> tag with the stock name.
    Returns a list of stock names if found, else None.
    """
    target_title = "stocks-to-watch-today-16th-april-2025"
    url = f"https://groww.in/blog/{target_title}"
    print("\nFetching Groww blog stocks from URL:", url)
    
    # Configure options for a headless driver
    options_groww = uc.ChromeOptions()
    options_groww.add_argument("--no-sandbox")
    options_groww.add_argument("--disable-dev-shm-usage")
    options_groww.add_argument("--disable-gpu")
    options_groww.add_argument("--window-size=1920,1080")
    options_groww.headless = True
    options_groww.add_argument(f"user-agent={user_agent}")
    options_groww.add_argument("--disable-blink-features=AutomationControlled")
    options_groww.binary_location = "/usr/bin/google-chrome"
    
    try:
        driver_groww = uc.Chrome(options=options_groww, version_main=135)
    except Exception as e:
        print("Error launching Groww driver:", e)
        return None
    
    try:
        stealth(
            driver_groww,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception:
        pass
    
    try:
        driver_groww.get(url)
        time.sleep(30)  # Wait for the page to load
    except Exception as e:
        print("Error loading Groww blog page:", e)
        driver_groww.quit()
        return None
        
    html_groww = driver_groww.page_source
    driver_groww.quit()
    
    soup_groww = BeautifulSoup(html_groww, "html.parser")
    
    # Find the <h2> header that contains "Key Stocks in Focus"
    key_header = None
    for header in soup_groww.find_all("h2"):
        if header.find("strong") and "Key Stocks in Focus" in header.find("strong").get_text(strip=True):
            key_header = header
            break
    
    if not key_header:
        print("Header 'Key Stocks in Focus' not found on Groww blog.")
        return None
    
    # Retrieve subsequent <p> tags that contain stock records.
    # In this page, each <p> tag after the header (until an unrelated <p> is found) should
    # contain a stock record.
    paragraphs = key_header.find_next_siblings("p")
    stocks = []
    
    for p in paragraphs:
        # Check if this paragraph has a <strong><a> element.
        strong_element = p.find("strong")
        if strong_element:
            a_element = strong_element.find("a")
            if a_element:
                stock_name = a_element.get_text(strip=True)
                # Some paragraphs contain commas after the name; remove trailing punctuation.
                stock_name = stock_name.strip(" ,")
                if stock_name and stock_name not in stocks:
                    stocks.append(stock_name)
            else:
                # If no <a> tag is found, skip this paragraph.
                continue
        else:
            # If the paragraph does not conform to expected structure, we assume the section ended.
            break
    
    return stocks if stocks else None


def fetch_ndtvprofit_stocks():
    """
    Fetches the NDTVProfit article relevant for today.
    
    The article URL is constructed dynamically using today’s month and day.
    For example, if today is April 16, the URL becomes:
    
        https://www.ndtvprofit.com/markets/stock-market-today-all-you-need-to-know-going-into-trade-on-april-16-3

    The function then parses the page (using BeautifulSoup) to extract the stock names 
    from the "Stocks To Watch" section. It returns a list of stock names if found; otherwise, None.
    """
    # Construct article URL based on today's date.
    # For example, for April 16, the URL will be:
    # https://www.ndtvprofit.com/markets/stock-market-today-all-you-need-to-know-going-into-trade-on-april-16-3
    month = datetime.now().strftime("%B").lower()       # e.g., "april"
    day = datetime.now().strftime("%d").lstrip("0")       # e.g., "16" (if today is "16")
    article_title = f"stock-market-today-all-you-need-to-know-going-into-trade-on-{month}-{day}-3"
    url = f"https://www.ndtvprofit.com/markets/{article_title}"
    print("\nFetching NDTVProfit stocks from URL:", url)

    # Configure the driver for NDTVProfit with a headless setting and stealth options.
    options_ndtv = uc.ChromeOptions()
    options_ndtv.add_argument("--no-sandbox")
    options_ndtv.add_argument("--disable-dev-shm-usage")
    options_ndtv.add_argument("--disable-gpu")
    options_ndtv.add_argument("--window-size=1920,1080")
    options_ndtv.headless = True
    options_ndtv.add_argument(f"user-agent={user_agent}")
    options_ndtv.add_argument("--disable-blink-features=AutomationControlled")
    options_ndtv.binary_location = "/usr/bin/google-chrome"

    try:
        driver_ndtv = uc.Chrome(options=options_ndtv, version_main=135)
    except Exception as e:
        print("Error launching NDTVProfit driver:", e)
        return None

    try:
        stealth(
            driver_ndtv,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception:
        pass

    try:
        driver_ndtv.get(url)
        time.sleep(30)  # Allow some time for the page to load.
    except Exception as e:
        print("Error loading NDTVProfit page:", e)
        driver_ndtv.quit()
        return None

    html_ndtv = driver_ndtv.page_source
    driver_ndtv.quit()

    soup_ndtv = BeautifulSoup(html_ndtv, "html.parser")
    
    # Find the <h2> element that contains "Stocks To Watch"
    h2_element = soup_ndtv.find("h2", string=lambda t: t and "Stocks To Watch" in t)
    if not h2_element:
        print("No 'Stocks To Watch' header found in NDTVProfit article.")
        return None

    # Look for the next <ul> element that follows this <h2>.
    ul_element = h2_element.find_next("ul")
    if not ul_element:
        print("No list found following the 'Stocks To Watch' header.")
        return None

    ndtv_stocks = []
    # Each list item (<li>) in the <ul> should have a <p> that contains a <strong> tag.
    for li in ul_element.find_all("li"):
        p_tag = li.find("p")
        if p_tag:
            strong_tag = p_tag.find("strong")
            if strong_tag:
                stock_name = strong_tag.get_text(strip=True)
                # Remove any trailing colon
                if stock_name.endswith(":"):
                    stock_name = stock_name[:-1].strip()
                if stock_name and stock_name not in ndtv_stocks:
                    ndtv_stocks.append(stock_name)
    return ndtv_stocks if ndtv_stocks else None


def Result_stock_5paisa():
    """
    Fetches forthcoming results from 5paisa from the URL:
       https://www.5paisa.com/forthcoming-results
    Parses the table with id "pennystocktable" to extract:
       "Company Name" and "Result Date".
    Then filters the records and returns only those records for dates:
       N-1, N, or N+1 (where N is the current date).
    
    Returns:
       A list of tuples: [(Company Name, Result Date), ...] or None if no matching records.
    """
    url = "https://www.5paisa.com/forthcoming-results"
    print("\nFetching forthcoming results from 5paisa URL:", url)
    
    # Configure a headless driver with stealth options.
    options_5paisa = uc.ChromeOptions()
    options_5paisa.add_argument("--no-sandbox")
    options_5paisa.add_argument("--disable-dev-shm-usage")
    options_5paisa.add_argument("--disable-gpu")
    options_5paisa.add_argument("--window-size=1920,1080")
    options_5paisa.headless = True
    options_5paisa.add_argument(f"user-agent={user_agent}")
    options_5paisa.add_argument("--disable-blink-features=AutomationControlled")
    options_5paisa.binary_location = "/usr/bin/google-chrome"
    
    try:
        driver_5paisa = uc.Chrome(options=options_5paisa, version_main=135)
    except Exception as e:
        print("Error launching 5paisa driver:", e)
        return None

    try:
        # Activate stealth mode on the new driver.
        stealth(
            driver_5paisa,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception:
        pass

    try:
        driver_5paisa.get(url)
        time.sleep(30)  # Wait for the page to load.
    except Exception as e:
        print("Error loading the 5paisa page:", e)
        driver_5paisa.quit()
        return None

    html_5paisa = driver_5paisa.page_source
    driver_5paisa.quit()

    from bs4 import BeautifulSoup
    soup_5paisa = BeautifulSoup(html_5paisa, "html.parser")
    # Find the table by id.
    table = soup_5paisa.find("table", id="pennystocktable")
    if not table:
        print("Table with id 'pennystocktable' not found.")
        return None

    # Get current date (N) as a date object.
    from datetime import datetime, timedelta
    current_date = datetime.now().date()
    # Accept rows where result_date is within N-1, N, or N+1.
    acceptable_dates = {current_date - timedelta(days=1), current_date, current_date + timedelta(days=1)}

    results = []
    tbody = table.find("tbody")
    if not tbody:
        print("Tbody element not found in table.")
        return None

    rows = tbody.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        # Get the company name from the first cell
        a_tag = cells[0].find("a", class_="compname")
        if a_tag:
            company_name = a_tag.get_text(strip=True)
        else:
            continue

        # Get the result date from the second cell.
        date_text = cells[1].get_text(strip=True)
        # Clean the text (for example, "17 Apr 2025")
        try:
            result_date_obj = datetime.strptime(date_text, "%d %b %Y").date()
        except Exception as e:
            # If date conversion fails, skip this row.
            continue

        if result_date_obj in acceptable_dates:
            results.append((company_name, date_text))
    
    if results:
        return results
    else:
        return None


def nse_trading_holidays_check():
    """
    Fetches the NSE Trading Holidays for the current year from a predetermined URL (for 2025 in this example)
    and creates a set of holiday dates (as date objects) by parsing the table.
    
    The function then compares today’s date with the holiday set and weekend.
    If today is a weekend or a holiday, it returns False (i.e. do not trigger the trading logic).
    Otherwise, it returns True.
    
    Assumptions:
       - The URL is fixed for the current year (e.g., 2025) and the title "List of NSE Trading Holidays 2025" is used.
       - The table has rows with the result date in the format "February 26, 2025", etc.
    """
    from datetime import datetime
    import requests
    from bs4 import BeautifulSoup

    # Ensure the current year matches the year in your holiday list; otherwise, skip processing.
    current_year = datetime.now().year
    # For this example, we expect the holiday list for 2025.
    if current_year != 2025:
        print(f"Holiday list available only for 2025; current year is {current_year}.")
        return True

    url = "https://www.ndtvprofit.com/markets/"  # Replace with the actual URL if different.
    # If you have a dedicated URL for holidays, use that.
    # For this example, we assume the holidays are available in the table by id "pennystocktable3" as provided.
    # (You might need to update the URL to the actual page that contains the holiday table.)
    # For our sample, we'll assume that the data is provided via a local string or request:
    # Here we simulate by using a local HTML snippet; in a production system, you might use requests.get(url)
    
    # For demonstration, let's assume you already have the HTML content (replace this with your request if needed)
    # For example:
    try:
        response = requests.get(url)
        html_content = response.text
    except Exception as e:
        print("Error fetching holiday page:", e)
        # In case of error, allow the program to continue further.
        return True

    soup_holidays = BeautifulSoup(html_content, "html.parser")
    # Locate the table with id "pennystocktable3"
    table = soup_holidays.find("table", id="pennystocktable3")
    if not table:
        print("NSE holiday table not found.")
        return True

    holiday_dates = set()
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            # The first cell contains the date in the format "February 26, 2025"
            date_text = cells[0].get_text(strip=True)
            try:
                holiday_date = datetime.strptime(date_text, "%B %d, %Y").date()
                holiday_dates.add(holiday_date)
            except Exception as e:
                print("Error parsing date:", date_text, e)
                continue

    # Now, check if today's date is in the holiday list or if it's a weekend.
    today = datetime.now().date()
    weekday = today.weekday()  # Monday is 0, Sunday is 6.
    if weekday in (5, 6):   # Saturday or Sunday.
        print("Today is a weekend.")
        return False
    if today in holiday_dates:
        print("Today is an NSE Trading Holiday:", today)
        return False

    # For debugging, print the holiday dates.
    # print("Holiday dates:", holiday_dates)
    return True

# Check if NSE Holiday then do not Run
if nse_trading_holidays_check():
    print("Proceed with trading logic (today is a working day).")

# -------------------- Invoke the Functions and Display the Results --------------------

    # Example invocation:
    result_5paisa = Result_stock_5paisa()
    if result_5paisa:
        from tabulate import tabulate
        output_table_5paisa = tabulate(result_5paisa, headers=["Company Name", "Date"], tablefmt="github")
        print("\nResults from 5paisa (for N-1, N, N+1):")
        print(output_table_5paisa)
    else:
        print("\nNo forthcoming results retrieved for the specified dates.")

# Fetch stocks from Moneycontrol's today's Trade Spotlight article.
    today_stocks = fetch_today_trade_stocks(today_headlines)
    if today_stocks:
        output_table = tabulate([[s] for s in today_stocks], headers=["Moneycontrol Stocks"], tablefmt="github")
        print("\nToday's Trade Spotlight Stocks (from Moneycontrol article expanded content):")
        print(output_table)
    else:
        print("\nToday's Trade Spotlight article stocks could not be retrieved from Moneycontrol.")

# Example invocation:
    groww_stocks = fetch_groww_blog_stocks()
    if groww_stocks:
        from tabulate import tabulate
        output_table_groww = tabulate([[s] for s in groww_stocks], headers=["Groww Blog Stocks"], tablefmt="github")
        print("\nGroww Blog Stocks (from the 'stocks-to-watch-today-16th-april-2025' article):")
        print(output_table_groww)
    else:
        print("\nGroww Blog Stocks could not be retrieved.")


# Example invocation:
    ndtv_stocks = fetch_ndtvprofit_stocks()
    if ndtv_stocks:
        from tabulate import tabulate
        output_table_ndtv = tabulate([[s] for s in ndtv_stocks], headers=["NDTVProfit Stocks"], tablefmt="github")
        print("\nNDTVProfit Stocks (from the article):")
        print(output_table_ndtv)
    else:
        print("\nNDTVProfit Stocks could not be retrieved.")

else:
    print("Do NOT trigger trading logic (today is a holiday or weekend).")
