from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import xml.etree.ElementTree as ET
import os

# --- Configuration for GitHub Actions ---
XML_URL = "https://www.opec.org/basket/basketDayArchives.xml"
OUTPUT_FILENAME = "opec_basket_data.csv"
FIELDNAMES = ["Date", "Price", "Currency"]
# The XML uses a default namespace. We must register it.
NAMESPACE = {'ns': 'http://tempuri.org/basketDayArchives.xsd'}

def get_webdriver():
    """Configures and initializes a headless Chrome WebDriver for GitHub Actions."""
    options = Options()
    
    # 💡 FIX 1: Essential headless mode and sandbox arguments for CI/CD runners
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # 💡 FIX 2: Use webdriver_manager to handle driver path dynamically
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    print("WebDriver initialized successfully in headless mode.")
    return driver

def scrape_data(driver):
    """Navigates to the URL, scrapes the XML page source, and extracts data."""
    try:
        driver.get(XML_URL)
        print(f"Navigated to {XML_URL}")
        time.sleep(5) 
        
        # 💡 FIX 3 (CRITICAL): Use the 'pre' tag content to get clean XML 
        # This bypasses the HTML wrapper Chrome puts around raw XML files.
        try:
            # Try to find the content of the <pre> tag
            xml_element = driver.find_element(by=webdriver.common.by.By.TAG_NAME, value="pre")
            page_source = xml_element.text
            print("Successfully extracted XML from <pre> tag.")
        except Exception:
            # Fallback to the full page source if the <pre> tag method fails
            page_source = driver.page_source
            print("Warning: Fell back to full page source. XML parsing might be fragile.")


        # Parse the XML data
        root = ET.fromstring(page_source)

        extracted_data = []
        
        # 💡 FIX 4: Correctly target NESTED ELEMENTS (<ns:Date>, <ns:Value>) and their .text
        for entry in root.findall(".//ns:BasketList", NAMESPACE):
            date_element = entry.find('ns:Date', NAMESPACE)
            value_element = entry.find('ns:Value', NAMESPACE)
            
            date = date_element.text if date_element is not None else 'N/A'
            value = value_element.text if value_element is not None else 'N/A'
            
            if date != 'N/A' and value != 'N/A':
                extracted_data.append({"Date": date, "Price": value, "Currency": "USD"})

        count = len(extracted_data)
        print(f"Extracted {count} data points.")
        if count == 0:
            print("CRITICAL ERROR: Extracted zero data points. XML parsing likely failed.")
            
        return extracted_data

    except ET.ParseError as pe:
        print(f"CRITICAL XML PARSING ERROR: {pe}")
        print("This usually means the 'page_source' is not clean XML (contains HTML tags).")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return None

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file in the repository root."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        return

    try:
        # 💡 FIX 5: Save to the local working directory (the GitHub Actions runner)
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
        write_data_to_csv(data, OUTPUT_FILENAME, FIELDNAMES)
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
