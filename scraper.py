from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import xml.etree.ElementTree as ET
import os

# --- Configuration ---
XML_URL = "https://www.opec.org/basket/basketDayArchives.xml"
OUTPUT_FILENAME = "opec_basket_data.csv"
FIELDNAMES = ["Date", "Price", "Currency"]
NAMESPACE = {'ns': 'http://tempuri.org/basketDayArchives.xsd'}

def get_webdriver():
    """Configures and initializes a headless Chrome WebDriver."""
    options = Options()
    
    # 1. Essential arguments for running headless on a Linux server (GitHub Actions Ubuntu runner)
    options.add_argument("--headless")              # Run without a GUI
    options.add_argument("--no-sandbox")            # Bypass OS security model (required on some systems)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080")  # Set a defined viewport size
    
    # 2. Use webdriver_manager to automatically download the correct ChromeDriver version
    # This avoids hardcoding the path and makes it compatible with GitHub Actions
    service = Service(ChromeDriverManager().install())
    
    # 3. Initialize the WebDriver
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver initialized successfully in headless mode.")
    return driver

def scrape_data(driver):
    """Navigates to the URL, scrapes the XML page source, and extracts data."""
    try:
        driver.get(XML_URL)
        print(f"Navigated to {XML_URL}")
        
        # Give the page a moment to load and execute any required JavaScript
        time.sleep(5)
        
        # Get the page source (XML data)
        page_source = driver.page_source
        
        # Parse the XML data
        root = ET.fromstring(page_source)

        extracted_data = []
        for entry in root.findall(".//ns:BasketList", NAMESPACE):
            date = entry.get("data")
            value = entry.get("val")
            extracted_data.append({"Date": date, "Price": value, "Currency": "USD"})

        print(f"Extracted {len(extracted_data)} data points.")
        return extracted_data

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        return

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Scraped data successfully written to {filename}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    driver = None
    try:
        driver = get_webdriver()
        data = scrape_data(driver)
        write_data_to_csv(data, OUTPUT_FILENAME, FIELDNAMES)
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
