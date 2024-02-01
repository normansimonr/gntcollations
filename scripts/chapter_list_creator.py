import pandas as pd
import os
from bs4 import BeautifulSoup
import json


# Define the path to the subfolder
folder_path = "manuscript_verses_logs"

# Get a list of all CSV files in the folder
csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]

# Initialize an empty list to hold the dataframes
df_list = []

# Loop over the list of csv files and read each one into a dataframe
for file in csv_files:
    file_path = os.path.join(folder_path, file)
    df = pd.read_csv(file_path)
    df_list.append(df)

# Concatenate all dataframes in the list into a single dataframe
master_df = pd.concat(df_list, ignore_index=True)

# master_df["verse"] = pd.to_numeric(master_df["verse"], errors="coerce")
# master_df.dropna(subset=["verse"], inplace=True)
# master_df["verse"] = master_df["verse"].astype(int)

master_df = master_df.sort_values(
    by=["book", "chapter_number", "verse_number", "manuscript_id"]
)

# Remove rows where 'verse_number' is greater than 100. Some XML files have verses with the number 295 and 999 (and maybe others)
master_df = master_df[master_df["verse_number"] <= 100]

master_df["links_to_collations"] = master_df["manuscript_id"].apply(
    lambda x: "[" + str(x) + "](collations/" + str(x) + ".qmd)"
)


############################################
############################################
######## SAVING JSON FOR APPARATUS #########
############################################
############################################

# Adding book names
book_dict = {
    "B07": "First Corinthians",
    "B23": "First John",
    "B21": "First Peter",
    "B13": "First Thessalonians",
    "B15": "First Timothy",
    "B08": "Second Corinthians",
    "B24": "Second John",
    "B22": "Second Peter",
    "B14": "Second Thessalonians",
    "B16": "Second Timothy",
    "B25": "Third John",
    "B05": "Acts",
    "B12": "Colossians",
    "B10": "Ephesians",
    "B09": "Galatians",
    "B19": "Hebrews",
    "B20": "James",
    "B04": "The Gospel of John",
    "B26": "Jude",
    "B03": "The Gospel of Luke",
    "B02": "The Gospel of Mark",
    "B01": "The Gospel of Matthew",
    "B18": "Philemon",
    "B11": "Philippians",
    "B27": "Revelation",
    "B06": "Romans",
    "B17": "Titus",
    "B00": "No book",
}

relation_for_apparatus = master_df[
    ["book", "chapter_number", "verse_number", "manuscript_id"]
]
relation_for_apparatus["book_name"] = relation_for_apparatus["book"].replace(book_dict)

dictionary_for_apparatus = {}
for book_name in relation_for_apparatus["book_name"].unique():
    dictionary_for_apparatus[book_name] = {}
    this_book = relation_for_apparatus[relation_for_apparatus["book_name"] == book_name]
    for chapter in this_book["chapter_number"].unique():
        dictionary_for_apparatus[book_name][str(chapter)] = {}
        this_chapter = this_book[this_book["chapter_number"] == chapter]
        for verse in this_chapter["verse_number"].unique():
            this_verse = this_chapter[this_chapter["verse_number"] == verse]
            manuscripts_for_this_verse = (
                this_verse[["verse_number", "manuscript_id"]]
                .groupby("verse_number")["manuscript_id"]
                .apply(list)
            )
            dictionary_for_apparatus[book_name][str(chapter)][
                str(verse)
            ] = manuscripts_for_this_verse.iloc[0]


# Specify the file path for the JSON file
file_path = "../apparatus/manuscript_verse_relation.json"

# Open the file in write mode and use json.dump() to write the dictionary to the file with pretty formatting

with open(file_path, "w") as f:
    json.dump(dictionary_for_apparatus, f, indent=4)


############################################
############################################
##### GENERATING THE CHAPTER LIST QMD ######
############################################
############################################

master_df = (
    master_df.drop(columns=["verse_number"])
    .drop_duplicates()
    .sort_values(by=["manuscript_id"])
)

# Does not include verse information
grouped_df = (
    master_df.groupby(["book", "chapter_number"])["links_to_collations"]
    .apply(list)
    .reset_index()
)
grouped_df["links_to_collations"] = grouped_df["links_to_collations"].apply(
    lambda x: ", ".join(x)
)

text_to_save = ""

for group in grouped_df.groupby("book"):
    book_to_show = group[0]
    book_to_show = book_dict[book_to_show]
    text_to_save = text_to_save + "## " + str(book_to_show) + "\n\n"
    for chgroup in group[1].groupby("chapter_number"):
        chapter_to_show = chgroup[0]
        text_to_save = text_to_save + "### Chapter " + str(chapter_to_show) + "\n\n"
        text_to_save = text_to_save + chgroup[1]["links_to_collations"].iloc[0] + "\n\n"

head = f"""---
title: "Chapters"
author: ""
date: ""
---

This page contains a list of the chapters of the books of the New Testament whose texts are attested in the manuscripts that have been transcribed by the INTF. Not all the manuscripts of the [*Liste*](liste.qmd) are shown below as most of them have not been transcribed.

Some transcriptions contain chapters not listed here. Those chapters are not shown because their transcriptions contain markup errors in the original XML files. There is at least one manuscript that contains Mark, Luke and John, but is only shown to have Mark. This is because in this transcription, the texts of Luke and John lack important XML tags and are therefore not detected by our algorithm.

"""

text_to_save = head + text_to_save

with open("../chapters.qmd", "w") as file:
    file.write(text_to_save)
