import os
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import xml.etree.ElementTree as ET

# --- Configuration for GitHub Actions ---
DATA_DIR_NAME = "data"
OUTPUT_FILENAME = "opec_basket_data.csv"
URL = "https://www.opec.org/basket/basketXML.xml"
FIELD_NAMES = ["date", "price"]

def get_webdriver():
    """Configures and returns a headless Chrome WebDriver for GitHub Actions."""
    print("Setting up Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")      # Standard headless mode
    chrome_options.add_argument("--no-sandbox")    # Necessary for running in containerized environments
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return None

def scrape_data(driver, url):
    """Navigates to the XML URL, waits for the content, and extracts the raw XML text."""
    print(f"Navigating to URL: {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        pre_element = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        raw_xml_text = pre_element.text
        print("Raw XML content extracted.")
        return raw_xml_text

    except Exception as e:
        print(f"Error during scraping or element location: {e}")
        return None
    finally:
        driver.quit()
        print("WebDriver closed.")

def parse_xml_data(xml_text):
    """Parses the raw XML text into a list of dictionaries."""
    data = []
    if not xml_text:
        return data

    try:
        root = ET.fromstring(xml_text)
        
        for date_element in root.findall('Date'):
            date_key = list(date_element.keys())[0]  # Gets the attribute name (e.g., '20230101')
            price = date_element.text              # Gets the price value
            
            data.append({
                "date": date_key,
                "price": price
            })
            
        print(f"Successfully parsed {len(data)} data points.")
        return data

    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        return []
    except Exception as e:
        print(f"General parsing error: {e}")
        return []

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file in the data directory of the repository."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        return

    try:
        # Ensure the data directory exists
        os.makedirs(DATA_DIR_NAME, exist_ok=True)
        print(f"Data directory checked/created: {DATA_DIR_NAME}")
        
        # Save the file in the data directory
        file_path = os.path.join(DATA_DIR_NAME, filename) 
        
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"Scraped data successfully written to {file_path}")
        
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    driver = get_webdriver()
    if driver:
        xml_content = scrape_data(driver, URL)
        
        if xml_content:
            parsed_data = parse_xml_data(xml_content)
            # Write new data to the data/ folder, overwriting the old file.
            write_data_to_csv(parsed_data, OUTPUT_FILENAME, FIELD_NAMES)
