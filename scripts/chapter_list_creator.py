import pandas as pd
import os
from bs4 import BeautifulSoup

collations_path = "../collations/"
xmls_path = "../raw_data/manuscripts/"

# Create an empty list to store individual DataFrames
dfs = []

# Iterate through each file in the directory
for filename in os.listdir(collations_path):
    if filename.endswith(".qmd"):
        manuscript_id = filename[:-4]
        print("Processing manuscript", manuscript_id)
        xml_path = os.path.join(xmls_path, manuscript_id + '.xml')        
        
        # Read the XML file
        with open(xml_path, "r", encoding="utf-8") as file:
            xml_content = file.read()

        # Parse the XML content with BeautifulSoup
        soup = BeautifulSoup(xml_content, "xml")

        ab_tags = soup.find_all("ab")
        
        verse_ids_in_this_manuscript = []        
        for ab_tag in ab_tags:
            if ab_tag.attrs != None:
                if 'n' in ab_tag.attrs:
                    verse_ids_in_this_manuscript.append(str(ab_tag['n']))
        
        verse_ids_in_this_manuscript = pd.DataFrame(verse_ids_in_this_manuscript)
        verse_ids_in_this_manuscript.columns = ['verse_id']
        verse_ids_in_this_manuscript[['book', 'chapter_verse']] = verse_ids_in_this_manuscript['verse_id'].str.split('K', expand=True)
        verse_ids_in_this_manuscript['book'] = verse_ids_in_this_manuscript['book'].str.replace('B','')
        verse_ids_in_this_manuscript[['chapter', 'verse']] = verse_ids_in_this_manuscript['chapter_verse'].str.split('V', expand=True)
        verse_ids_in_this_manuscript = verse_ids_in_this_manuscript.drop(columns=['verse_id', 'chapter_verse', 'verse'])
        
        # Converting to integers, removing non-integer chapters or verses
        verse_ids_in_this_manuscript['book'] = pd.to_numeric(verse_ids_in_this_manuscript['book'], errors='coerce')
        verse_ids_in_this_manuscript['chapter'] = pd.to_numeric(verse_ids_in_this_manuscript['chapter'], errors='coerce')
        verse_ids_in_this_manuscript = verse_ids_in_this_manuscript.dropna()
        
        verse_ids_in_this_manuscript['book'] = verse_ids_in_this_manuscript['book'].astype(int)
        verse_ids_in_this_manuscript['chapter'] = verse_ids_in_this_manuscript['chapter'].astype(int)
        
        # Removing chapters that are number zero
        verse_ids_in_this_manuscript = verse_ids_in_this_manuscript[verse_ids_in_this_manuscript['chapter'] != 0]
        
        # Removing duplicates
        verse_ids_in_this_manuscript = verse_ids_in_this_manuscript.drop_duplicates()
        
        # Adding the manuscript id
        verse_ids_in_this_manuscript['manuscript_id'] = manuscript_id
        dfs.append(verse_ids_in_this_manuscript)
        #print(verse_ids_in_this_manuscript)
        
master_df = pd.concat(dfs)
master_df = master_df.sort_values(by=['book', 'chapter', 'manuscript_id'])

master_df['links_to_collations'] = master_df['manuscript_id'].apply(lambda x: '[' + x + '](collations/' + x + '.qmd)')

grouped_df = master_df.groupby(['book', 'chapter'])['links_to_collations'].apply(list).reset_index()
grouped_df['links_to_collations'] = grouped_df['links_to_collations'].apply(lambda x: ', '.join(x))


# Adding book names
book_dict = {
    7: "First Corinthians",
    23: "First John",
    21: "First Peter",
    13: "First Thessalonians",
    15: "First Timothy",
    8: "Second Corinthians",
    24: "Second John",
    22: "Second Peter",
    14: "Second Thessalonians",
    16: "Second Timoty",
    25: "Third John",
    5: "Acts",
    12: "Colossians",
    10: "Ephesians",
    9: "Galatians",
    19: "Hebrews",
    20: "James",
    4: "The Gospel of John",
    26: "Jude",
    3: "The Gospel of Luke",
    2: "The Gospel of Mark",
    1: "The Gospel of Matthew",
    18: "Philemon",
    11: "Phillipians",
    27: "Revelation",
    6: "Romans",
    17: "Titus",
    0   : "No book",
}


text_to_save = ""

for group in grouped_df.groupby('book'):
    book_to_show = group[0]
    book_to_show = book_dict[book_to_show]
    text_to_save = text_to_save + '## ' + str(book_to_show) + '\n\n'
    for chgroup in group[1].groupby('chapter'):
        chapter_to_show = chgroup[0]
        text_to_save = text_to_save + '### Chapter ' + str(chapter_to_show) + '\n\n'
        text_to_save = text_to_save + chgroup[1]['links_to_collations'].iloc[0] + '\n\n'

head = f"""---
title: "Chapters"
author: ""
date: ""
---

This page contains a list of the chapters of the books of the New Testament whose texts are attested in the manuscripts that have been transcribed by the INTF. Not all the manuscripts of the [*Liste*](liste.qmd) are shown below as most of them have not been transcribed.

"""

text_to_save = head + text_to_save

with open("../chapters.qmd", "w") as file:
    file.write(text_to_save)
