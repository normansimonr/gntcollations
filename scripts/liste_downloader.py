import requests
from requests.exceptions import Timeout
import os
import glob

# Get the current directory
current_directory = os.getcwd()

# Go up one folder
parent_directory = os.path.dirname(current_directory)

# Define the path to the manuscripts folder
liste_directory = os.path.join(parent_directory, "raw_data", "liste")

url = "https://ntvmr.uni-muenster.de/community/vmr/api//metadata/liste/search/?&featureCode=Liste&sessionHash=&gaNum=&lang=g&detail=shelfInstance&format=csv"

try:
    # Set a timeout of 300 seconds (5 minutes)
    response = requests.get(url, timeout=600)
    response.raise_for_status()  # Raise an exception for any HTTP errors

    # Check if the response content is not empty
    if response.content:
        # You can save the content to a file or process it as needed
        with open(liste_directory + "/" + "liste.csv", "wb") as f:
            f.write(response.content)
        print("Liste downloaded successfully!")
    else:
        print("No data received from the URL.")

except Timeout:
    print("Request timed out after 10 minutes.")
except Exception as e:
    print(f"An error occurred: {str(e)}")
