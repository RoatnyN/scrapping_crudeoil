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
    options.add_argument("--headless=new") # Use the modern headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
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
        
        # 💡 CRITICAL FIX: Use the 'pre' tag content to get clean XML
        # When Chrome loads raw XML, it often displays it within a <pre> tag.
        # Finding the content of this tag gives the raw text, minimizing HTML wrapping issues.
        try:
            xml_element = driver.find_element(by=webdriver.common.by.By.TAG_NAME, value="pre")
            page_source = xml_element.text
            
            if not page_source:
                # Fallback to the previous method if <pre> is empty or not found
                page_source = driver.execute_script("return document.documentElement.outerHTML;")
                print("Warning: Used document.documentElement.outerHTML as a fallback.")
        except Exception:
            # Final fallback, simply grab the entire page source
            page_source = driver.page_source
            print("Warning: Used driver.page_source as a final fallback.")


        # --- Debugging Check (Highly Recommended) ---
        # Temporarily uncomment this line to see the first 500 characters of the source
        # print(f"--- DEBUG XML SOURCE START ---\n{page_source[:500]}\n--- DEBUG XML SOURCE END ---")
        # If this shows XML tags (<...>), the extraction is working. 
        # If it shows <html> or Chrome's viewer tags, the extraction is likely failing.
        # --------------------------------------------
        
        # Parse the XML data
        root = ET.fromstring(page_source)

        extracted_data = []
        
        # Correct XPath for the actual element names within the namespace
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
            print("CRITICAL ERROR: Extracted zero data points. XML parsing likely failed due to unclean source.")
            
        return extracted_data

    except ET.ParseError as pe:
        print(f"CRITICAL XML PARSING ERROR: {pe}")
        print("This usually means the 'page_source' is not valid XML.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        return None

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file in the repository root."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        # If data is empty, ensure the file is NOT created. This is correct behavior.
        return

    try:
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
