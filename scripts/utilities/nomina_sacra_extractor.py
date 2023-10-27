import json
import pandas as pd
from bs4 import BeautifulSoup
import os
import glob
import difflib
import re
import numpy as np

book_dict = {
    "1CO": "B07",
    "1JO": "B23",
    "1PE": "B21",
    "1TH": "B13",
    "1TI": "B15",
    "2CO": "B08",
    "2JO": "B24",
    "2PE": "B22",
    "2TH": "B14",
    "2TI": "B16",
    "3JO": "B25",
    "ACT": "B05",
    "COL": "B12",
    "EPH": "B10",
    "GAL": "B09",
    "HEB": "B19",
    "JAM": "B20",
    "JOH": "B04",
    "JUD": "B26",
    "LUK": "B03",
    "MAR": "B02",
    "MAT": "B01",
    "PHM": "B18",
    "PHP": "B11",
    "REV": "B27",
    "ROM": "B06",
    "TIT": "B17",
}

# Merging the BYZ CSVs
# Specify the directory where your CSV files are located
directory_path = "../../byz_csv"

# Create an empty list to store individual DataFrames
dfs = []

# Iterate through each file in the directory
for filename in os.listdir(directory_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(directory_path, filename)

        # Read each CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Add a new column with the source file name
        df["book_sigla"] = filename[:-4]
        df["book"] = book_dict[filename[:-4]]

        # Append the DataFrame to the list
        dfs.append(df)

# Concatenate all DataFrames into a single DataFrame
byz_dataframe = pd.concat(dfs, ignore_index=True)
byz_dataframe["code_verse"] = (
    byz_dataframe["book"]
    + "K"
    + byz_dataframe["chapter"].astype(str)
    + "V"
    + byz_dataframe["verse"].astype(str)
)

byz_dataframe = byz_dataframe.rename(columns={"text": "byz_verse_text"})

byz_dict = dict(zip(byz_dataframe["code_verse"], byz_dataframe["byz_verse_text"]))

# byz_dataframe.to_csv(directory_path + '/BYZ.csv', index=False)


def parse_manuscript_for_nomina_sacra(manuscript_id, manuscripts_directory):
    manuscript_id = str(manuscript_id)

    print("Parsing manuscript", manuscript_id)

    # Define the XML file path
    xml_file = manuscripts_directory + "/" + manuscript_id + ".xml"

    # Read the XML file
    with open(xml_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Define the XML file path
    xml_file = manuscripts_directory + "/" + manuscript_id + ".xml"

    # Read the XML file
    with open(xml_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Parse the XML content with BeautifulSoup
    soup = BeautifulSoup(xml_content, "xml")

    w_tags = soup.find_all("w")

    # Read abbreviations equivalences
    abbreviations_equivalences = pd.read_csv("../abbreviations_equivalences.csv")
    abbreviations_equivalences = abbreviations_equivalences.fillna("")

    def find_nomina_sacra(w_tag):
        target_tag = w_tag.find("abbr")
        if target_tag:
            if target_tag["type"] == "nomSac":
                if (
                    target_tag.text
                    not in abbreviations_equivalences["abbreviations"].unique()
                ):
                    print(target_tag.text)
                    for par in target_tag.parents:
                        if par.name == "ab":
                            verse_code_manuscript = par["n"]
                    verse_text_raw = byz_dict[verse_code_manuscript]
                    # Split the input string into words
                    words = verse_text_raw.split()
                    # Extract words starting and ending with the same letters as the nomen sacrum
                    selected_words = [
                        word
                        for word in words
                        if word.startswith(target_tag.text[0])
                        and word.endswith(target_tag.text[-1])
                    ]
                    return pd.DataFrame(
                        [
                            {
                                "abbreviations": target_tag.text,
                                "spelled_out": "",
                                "code_verse": verse_code_manuscript,
                                "manuscript": manuscript_id,
                                "byz_verse_text": " ".join(selected_words),
                            }
                        ]
                    )
                else:
                    return pd.DataFrame(
                        [{"abbreviations": "", "spelled_out": "", "manuscript": ""}]
                    )
            else:
                return pd.DataFrame(
                    [{"abbreviations": "", "spelled_out": "", "manuscript": ""}]
                )
        else:
            return pd.DataFrame(
                [{"abbreviations": "", "spelled_out": "", "manuscript": ""}]
            )

    for w_tag in w_tags:
        abbreviations_equivalences = pd.concat(
            [abbreviations_equivalences, find_nomina_sacra(w_tag)]
        )

    abbreviations_equivalences = abbreviations_equivalences.drop_duplicates(
        subset=["abbreviations"]
    )
    abbreviations_equivalences.to_csv("../abbreviations_equivalences.csv", index=False)


# Read Liste
liste = pd.read_csv("../../raw_data/liste/liste.csv", dtype={"docID": int})

# Get the current directory
current_directory = os.getcwd()

# Go up two folders
parent_directory = os.path.dirname(os.path.dirname(current_directory))

# Define the path to the manuscripts folder
manuscripts_directory = os.path.join(parent_directory, "raw_data", "manuscripts")

manuscript_ids = list(liste["docID"].unique().astype(int).astype(str))
for manuscript_id in manuscript_ids:
    if int(manuscript_id) > 30278:
        try:
            parse_manuscript_for_nomina_sacra(manuscript_id, manuscripts_directory)
        except:
            print("Error, skipping")
