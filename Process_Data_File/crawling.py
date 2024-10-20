import requests
from bs4 import BeautifulSoup
import re
import csv
import os

# Base URL with a placeholder for page numbers
base_url = "https://geokeo.com/database/town/vn/{}/"

# Define the number of pages you want to scrape
num_pages = 50 # Adjust this to the number of pages you want to crawl

# Filename for the CSV
csv_filename = "extracted_data.csv"

# Load existing data from the CSV file (if it exists)
existing_data = {}
if os.path.exists(csv_filename):
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            existing_data[row["Name"]] = row  # Use the 'Name' column as a key for easy lookup

# List to store new data (only unique entries)
new_data = []

# Loop through each page
for page_num in range(1, num_pages + 1):
    # Generate the URL for each page
    url = base_url.format(page_num)
    print(f"Scraping page {page_num}...")

    # Fetch the page
    response = requests.get(url)

    # Check if the page was retrieved successfully
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find the table by class
        table = soup.find('table', {'class': 'table table-hover table-bordered'})
        
        # Check if the table exists
        if table:
            # Find all rows in the table body
            rows = table.find('tbody').find_all('tr')
            
            # Loop over each row
            for row in rows:
                # Find all columns in the row
                cols = row.find_all('td')
                
                # Extract the necessary columns
                latitude = cols[3].text.strip()
                longitude = cols[4].text.strip()
                other_names = cols[5].text.strip()

                # Extract the "name" from the "Other Language Names" column using regex
                name_match = re.search(r'"name"\s*=>\s*"([^"]+)"', other_names)
                name = name_match.group(1) if name_match else "N/A"

                # Check if the name already exists in the existing data
                if name not in existing_data:
                    # Append the data to the list of new entries
                    new_data.append([name, latitude, longitude])
                else:
                    print(f"Data for {name} already exists. Skipping...")
        else:
            print(f"Table not found on page {page_num}!")
    else:
        print(f"Failed to retrieve page {page_num}. Status code: {response.status_code}")

# Write or update the CSV file
with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # If file is empty or just created, write the header first
    if os.stat(csv_filename).st_size == 0:
        writer.writerow(["Name", "Latitude", "Longitude"])  # Write header if the file is new or empty
    
    # Write new rows
    writer.writerows(new_data)

print(f"Data scraping and updating completed. New entries added: {len(new_data)}")
