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
# The XML uses a default namespace. We must register it for ElementTree to find elements.
NAMESPACE = {'ns': 'http://tempuri.org/basketDayArchives.xsd'}

def get_webdriver():
    """Configures and initializes a headless Chrome WebDriver."""
    options = Options()
    
    # Essential arguments for running headless on GitHub Actions (Ubuntu runner)
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Use webdriver_manager for automatic driver management
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver initialized successfully in headless mode.")
    return driver

def scrape_data(driver):
    """Navigates to the URL, gets the page source, and extracts data with corrected XML parsing."""
    try:
        driver.get(XML_URL)
        print(f"Navigated to {XML_URL}")
        
        # Give the page a moment to load
        time.sleep(5) 
        
        # Get the page source. For XML, the full outerHTML is often the cleanest source
        # after the browser has rendered the page.
        page_source = driver.execute_script("return document.documentElement.outerHTML;")
        
        # Parse the XML data
        root = ET.fromstring(page_source)

        extracted_data = []
        
        # FIX: The XML structure uses <BasketList> tags containing <Date> and <Value> children.
        # The XPath must correctly reference these elements within the defined namespace.
        for entry in root.findall(".//ns:BasketList", NAMESPACE):
            # Find the child elements for Date and Value
            date_element = entry.find('ns:Date', NAMESPACE)
            value_element = entry.find('ns:Value', NAMESPACE)
            
            # Extract text, providing a fallback for safety
            date = date_element.text if date_element is not None else 'N/A'
            value = value_element.text if value_element is not None else 'N/A'
            
            # Only append if data extraction was successful
            if date != 'N/A' and value != 'N/A':
                extracted_data.append({"Date": date, "Price": value, "Currency": "USD"})

        print(f"Extracted {len(extracted_data)} data points.")
        if len(extracted_data) == 0:
            print("WARNING: Extracted zero data points. Check the XML parsing logic/XPath.")
            
        return extracted_data

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file in the repository root."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        return

    try:
        # FIX: The filename is passed directly, guaranteeing it is written to the CWD (repo root)
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Scraped data successfully written to {file_path}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    driver = None
    try:
        driver = get_webdriver()
        data = scrape_data(driver)
        # This function guarantees the file is saved as 'opec_basket_data.csv' in the root.
        write_data_to_csv(data, OUTPUT_FILENAME, FIELDNAMES) 
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
