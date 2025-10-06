import requests
import csv
import xml.etree.ElementTree as ET
import os

# --- Configuration ---
XML_URL = "https://www.opec.org/basket/basketDayArchives.xml"
OUTPUT_FILENAME = "opec_basket_data.csv"
FIELDNAMES = ["Date", "Price", "Currency"]
# The XML uses a default namespace, which is defined at the root: xmlns="http://tempuri.org/basketDayArchives.xsd"
# We reference it here. The 'ns' prefix can be anything.
NAMESPACE = {'ns': 'http://tempuri.org/basketDayArchives.xsd'}

def fetch_xml_data():
    """Fetches the XML content directly using the requests library."""
    try:
        print(f"Fetching XML data directly from {XML_URL}...")
        response = requests.get(XML_URL, timeout=10)
        response.raise_for_status()  # Check for bad status codes (4xx or 5xx)
        print("Successfully retrieved XML content.")
        return response.content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None

def parse_xml_data(xml_content):
    """Parses the XML content and extracts the required data points."""
    if not xml_content:
        return None

    try:
        # Parse the XML data from the byte string
        root = ET.fromstring(xml_content)

        extracted_data = []
        # CRUCIAL FIX: XPath must target the correct element name (BasketList) 
        # and correctly access the child elements (Date and Value) within the namespace.
        for entry in root.findall(".//ns:BasketList", NAMESPACE):
            # FIX: Get the text content of the child elements, not attributes.
            date_element = entry.find('ns:Date', NAMESPACE)
            value_element = entry.find('ns:Value', NAMESPACE)
            
            date = date_element.text if date_element is not None else 'N/A'
            value = value_element.text if value_element is not None else 'N/A'
            
            # Only append if both crucial fields were found
            if date != 'N/A' and value != 'N/A':
                extracted_data.append({"Date": date, "Price": value, "Currency": "USD"})

        print(f"Extracted {len(extracted_data)} data points.")
        return extracted_data

    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during XML parsing: {e}")
        return None

def write_data_to_csv(data, filename, fieldnames):
    """Writes the list of dictionaries to a CSV file."""
    if not data:
        print("No data to write. Aborting CSV creation.")
        return

    # FIX: The file is now guaranteed to be written to the current working directory (repo root)
    try:
        # Use 'os.path.join' for best cross-platform compatibility, though simple 'filename' is fine here
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Scraped data successfully written to {file_path}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    # 1. Fetch the XML content
    xml_content = fetch_xml_data()

    if xml_content:
        # 2. Parse the content
        data = parse_xml_data(xml_content)
        
        # 3. Write to CSV
        write_data_to_csv(data, OUTPUT_FILENAME, FIELDNAMES)

    print("Scraping process finished.")
