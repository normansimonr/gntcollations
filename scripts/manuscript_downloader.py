import requests
import os
import pandas as pd
import time

# Get the current directory
current_directory = os.getcwd()

# Go up one folder
parent_directory = os.path.dirname(current_directory)

# Define the path to the manuscripts folder
manuscripts_directory = os.path.join(parent_directory, "raw_data", "manuscripts")

# Define the path to the liste folder
liste_directory = os.path.join(parent_directory, "raw_data", "liste")

# Your list of manuscript IDs
manuscript_list = (
    pd.read_csv(liste_directory + "/liste.csv", usecols=["docID"])
    .squeeze("columns")
    .astype(int)
    .unique()
    .tolist()
)

# Base URL for downloading XMLs
base_url = "https://ntvmr.uni-muenster.de/community/vmr/api/transcript/get/?docID="

# Delay in seconds between requests
delay_seconds = 0  # You can adjust this as needed

# Loop through the manuscript IDs and download XMLs
for manuscript_id in manuscript_list:
    xml_file_path = os.path.join(manuscripts_directory, f"{manuscript_id}.xml")

    # Check if the XML file already exists
    if not os.path.exists(xml_file_path):
        print("Attempting to download", manuscript_id)
        # Construct the full URL with the manuscript ID
        full_url = f"{base_url}{manuscript_id}&pageID=ALL&format=teiraw"

        # Send a GET request to the URL
        response = requests.get(full_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Get the content of the response (the XML)
            xml_content = response.text

            # Save the XML content to a file
            with open(xml_file_path, "w", encoding="utf-8") as xml_file:
                xml_file.write(xml_content)

            print(f"\tDownloaded XML for manuscript ID: {manuscript_id}")
        else:
            print(f"Failed to download XML for manuscript ID: {manuscript_id}")

        # Add a delay before making the next request
        time.sleep(delay_seconds)
    else:
        print(f"XML for manuscript ID {manuscript_id} already exists, skipping.")
