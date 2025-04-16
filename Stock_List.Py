import requests
import pandas as pd
import io

def get_nse_stock_list_from_csv():
    """
    Downloads the NSE listed equities CSV from the NSE archives,
    parses it, and returns a DataFrame with two columns: "Stock Name" and "Symbol".
    
    URL used: https://archives.nseindia.com/content/equities/EQUITY_L.csv
    """
    # Updated CSV URL from the NSE archives.
    csv_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    
    # Create a session and set headers.
    session = requests.Session()
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/85.0.4183.83 Safari/537.36"),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }
    session.headers.update(headers)
    
    try:
        # First request: Hit the homepage to obtain cookies.
        home_response = session.get("https://www.nseindia.com", timeout=10)
        home_response.raise_for_status()
        
        # Now fetch the CSV file from archives.
        csv_response = session.get(csv_url, timeout=30)
        csv_response.raise_for_status()
    except Exception as e:
        print("Error fetching data from NSE website:", e)
        return None

    try:
        csv_data = csv_response.content.decode('utf-8')
    except Exception as e:
        print("Error decoding CSV data:", e)
        return None

    try:
        df = pd.read_csv(io.StringIO(csv_data))
    except Exception as e:
        print("Error parsing CSV data:", e)
        return None

    # Inspect the DataFrame columns.
    # Typically, the CSV includes columns: "SYMBOL", "NAME OF COMPANY", "SERIES", etc.
    try:
        df = df[['SYMBOL', 'NAME OF COMPANY']]
        df.columns = ["Symbol", "Stock Name"]  # Rename columns for clarity.
    except Exception as e:
        print("Error extracting required columns:", e)
        return None

    return df

# Example usage:
df_nse = get_nse_stock_list_from_csv()
if df_nse is not None:
    print("List of NSE Stocks (Company and Symbol):")
    #print(df_nse.head(20))
    print (df_nse)
else:
    print("Could not retrieve the NSE stock list.")
