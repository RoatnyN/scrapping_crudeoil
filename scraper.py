from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import xml.etree.ElementTree as ET
import os

# Set Chrome Options
options = Options()
options.add_argument("--headless")  # Run in headless mode for CI
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

# Initialize WebDriver using webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    # URL to scrape
    url = "https://www.opec.org/basket/basketDayArchives.xml"
    driver.get(url)

    # Wait for the page to load completely
    time.sleep(5)

    # Get the page source (XML data)
    page_source = driver.page_source
    print("Page source fetched successfully.")

    # Parse the XML data
    tree = ET.ElementTree(ET.fromstring(page_source))
    root = tree.getroot()

    # Extract the relevant data
    namespace = {'ns': 'http://tempuri.org/basketDayArchives.xsd'}

    extracted_data = []
    for entry in root.findall(".//ns:BasketList", namespace):
        date = entry.get("data")
        value = entry.get("val")
        extracted_data.append({"Date": date, "Price": value, "Currency": "USD"})

    # Define the path to save the CSV file in the data directory
    output_path = os.path.join("data", "opec_basket_data.csv")

    # Write extracted data to a CSV file in the data directory
    with open(output_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Date", "Price", "Currency"])
        writer.writeheader()
        writer.writerows(extracted_data)

    print(f"Scraped data has been written to {output_path}")

finally:
    driver.quit()
