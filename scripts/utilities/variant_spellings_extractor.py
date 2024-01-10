import json
import copy
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


def parse_manuscript_for_spelling_variants(manuscript_id, manuscripts_directory):
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

    # Read spelling equivalences
    spelling_equivalences = pd.read_csv("../spelling_equivalences.csv")
    spelling_equivalences = spelling_equivalences.fillna("")

    def find_spelling_variant(w_tag):
        nonstandard = ""
        standard = ""
        explanation = ""
        if w_tag.text not in spelling_equivalences["nonstandard"].unique():
            for par in w_tag.parents:
                if par.name == "ab":
                    if "n" not in list(par.attrs):
                        return pd.DataFrame(
                            [{"nonstandard": "", "standard": "", "manuscript": ""}]
                        )
                    else:
                        verse_code_manuscript = par["n"]
            byz_verse_text_raw = byz_dict[verse_code_manuscript].split()
            # Variant detection
            nonstandard = copy.deepcopy(w_tag.text)
            # print(nonstandard, nonstandard.replace('ι', 'ει'))
            if ("ι" in nonstandard) and (
                nonstandard.replace("ι", "ει") in byz_verse_text_raw
            ):
                standard = copy.deepcopy(nonstandard).replace("ι", "ει")
                explanation = "nonstandard ι, standard ει"
            elif ("ει" in nonstandard) and (
                nonstandard.replace("ει", "ι") in byz_verse_text_raw
            ):
                standard = copy.deepcopy(nonstandard).replace("ει", "ι")
                explanation = "nonstandard ει, standard ι"
            elif ("αι" in nonstandard) and (
                nonstandard.replace("αι", "ε") in byz_verse_text_raw
            ):
                standard = copy.deepcopy(nonstandard).replace("αι", "ε")
                explanation = "nonstandard αι, standard ε"
            else:
                nonstandard = ""
            # if nonstandard != "":
            #    print(nonstandard, standard, explanation)
            return pd.DataFrame(
                [
                    {
                        "nonstandard": nonstandard,
                        "standard": standard,
                        "explanation": explanation,
                        "code_verse": verse_code_manuscript,
                        "manuscript": manuscript_id,
                        "byz_verse_text": " ".join(byz_verse_text_raw),
                    }
                ]
            )
        else:
            return pd.DataFrame([{"nonstandard": "", "standard": "", "manuscript": ""}])

    for w_tag in w_tags:
        try:
            spelling_equivalences = pd.concat(
                [spelling_equivalences, find_spelling_variant(w_tag)]
            )
        except:
            print("There was a problem with a word, skipping.")

    spelling_equivalences = spelling_equivalences.drop_duplicates(
        subset=["nonstandard"]
    )
    spelling_equivalences.to_csv("../spelling_equivalences.csv", index=False)


# Read Liste
liste = pd.read_csv("../../raw_data/liste/liste.csv", dtype={"docID": int})

# Get the current directory
current_directory = os.getcwd()

# Go up two folders
parent_directory = os.path.dirname(os.path.dirname(current_directory))

# Define the path to the manuscripts folder
manuscripts_directory = os.path.join(parent_directory, "raw_data", "manuscripts")

manuscript_ids = list(liste["docID"].unique().astype(int).astype(str))
# manuscript_ids = [10066]

for manuscript_id in manuscript_ids:
    if True:  # int(manuscript_id) > 30069:
        try:
            parse_manuscript_for_spelling_variants(manuscript_id, manuscripts_directory)
        except:
            print("Error, skipping")
