import re
import collatex
import difflib
import pandas as pd
import roman
import numpy as np
import json
import itertools
import copy
from datetime import datetime
import os

# Hiding the annoying SettingWithCopyWarning
pd.options.mode.chained_assignment = None  # default='warn'

file_path = "../apparatus/manuscript_verse_relation.json"

# Open the JSON file in read mode and use json.load() to load it into a Python dictionary
with open(file_path, "r") as f:
    manuscript_attestation_strings = json.load(f)

# Converting chapters and verses to integers
manuscript_attestation = {}

for book_name in manuscript_attestation_strings.keys():
    manuscript_attestation[book_name] = {}
    for chapter in manuscript_attestation_strings[book_name].keys():
        manuscript_attestation[book_name][int(chapter)] = {}
        for verse in manuscript_attestation_strings[book_name][chapter].keys():
            manuscript_attestation[book_name][int(chapter)][
                int(verse)
            ] = manuscript_attestation_strings[book_name][chapter][verse]

# Removing verses with ID 0. These are normally incipits and create incorrect behaviour in the code
verses_to_remove_from_attestation = []
for book_name in manuscript_attestation.keys():
    for chapter in manuscript_attestation[book_name].keys():
        for verse in manuscript_attestation[book_name][chapter].keys():
            if verse == 0:
                verses_to_remove_from_attestation.append([book_name, chapter, verse])

for rem in verses_to_remove_from_attestation:
    del manuscript_attestation[rem[0]][rem[1]][rem[2]]

empty_chapters = (
    []
)  # If the chapter was left totally empty, remove it (eg. 17th chapter of Mark, which doesn't exist)
for book_name in manuscript_attestation.keys():
    for chapter in manuscript_attestation[book_name].keys():
        if len(manuscript_attestation[book_name][chapter].keys()) == 0:
            empty_chapters.append([book_name, chapter])

for rem in empty_chapters:
    del manuscript_attestation[rem[0]][rem[1]]

# Analysis


def extract_text_between_substrings(text, book_name):
    # print(text)
    # exit()
    start_substring = "## " + book_name
    end_substring = "\n## "

    start_index = text.find(start_substring)
    if start_index != -1:
        end_index = text.find(end_substring, start_index + len(start_substring))
        if end_index != -1:
            extracted_text = text[start_index + len(start_substring) : end_index]
        else:
            extracted_text = text[start_index + len(start_substring) :]
        return extracted_text
    else:
        raise ValueError(f"Starting substring '## {book_name}' not found")


def extract_verse_from_qmd(qmd_content, book_name, chapter, verse):
    this_books_content = extract_text_between_substrings(qmd_content, book_name)
    lines = this_books_content.strip().split("\n")
    df = pd.DataFrame(lines).replace("", pd.NA).dropna()
    df = df[~df[0].str.startswith("###")]  # Removing chapter marks
    pattern = r" \| instance no\. ([0-9]+)]{\.aside}"  # Detecting the instance numbers
    df["instance"] = df[0].str.extract(pattern)
    replacement = "]{.aside}"
    df[0] = df[0].str.replace(pattern, replacement, regex=True)
    df[0] = df[0].str.replace(
        " *(lacunose)*]{.lacunose}]{.aside}", "]]{.aside}", regex=False
    )
    df["instance"] = df["instance"].infer_objects().fillna(1).astype(int)
    df[["parsed_greek", "coordinates"]] = df[0].str.extract(
        r"^(.*?)(\[\[?\d+:\d+\]?\]\{[^\}]*\})$"
    )

    df = df.drop(columns=[0])

    df["coordinates"] = (
        df["coordinates"]
        .str.replace("[", "", regex=False)
        .str.replace(" *(lacunose)*]{.lacunose}", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.replace("{", "", regex=False)
        .str.replace("}", "", regex=False)
        .str.replace(".aside", "", regex=False)
    )

    df[["chapter", "verse"]] = df["coordinates"].str.split(":", expand=True)
    df["verse"] = df["verse"].str.strip()
    df = df[["chapter", "verse", "instance", "parsed_greek"]]
    if str(chapter) in df["chapter"].unique():
        if str(verse) in df[df["chapter"] == str(chapter)]["verse"].unique():
            return df[(df["chapter"] == str(chapter)) & (df["verse"] == str(verse))]
    else:
        return None


##### Reading in the data

# Defining the fragmentary threshold
fragmentary_threshold = 0.6


books_to_process = [
    item
    for item in manuscript_attestation.keys()
    if item
    not in [
        "Leave this if you want to process all books; replace with a list of the already processed books if you want to avoid re-processing them"
    ]
]

# books_to_process = ['Second Timothy', 'Philippians']

for book_name in books_to_process:
    byz_book_abbrs = {
        "First Corinthians": "1CO",
        "First John": "1JO",
        "First Peter": "1PE",
        "First Thessalonians": "1TH",
        "First Timothy": "1TI",
        "Second Corinthians": "2CO",
        "Second John": "2JO",
        "Second Peter": "2PE",
        "Second Thessalonians": "2TH",
        "Second Timothy": "2TI",
        "Third John": "3JO",
        "Acts": "ACT",
        "Colossians": "COL",
        "Ephesians": "EPH",
        "Galatians": "GAL",
        "Hebrews": "HEB",
        "James": "JAM",
        "The Gospel of John": "JOH",
        "Jude": "JUD",
        "The Gospel of Luke": "LUK",
        "The Gospel of Mark": "MAR",
        "The Gospel of Matthew": "MAT",
        "Philemon": "PHM",
        "Philippians": "PHP",
        "Revelation": "REV",
        "Romans": "ROM",
        "Titus": "TIT",
    }

    byz = pd.read_csv(f"../byz_csv/{byz_book_abbrs[book_name]}.csv")

    for chapter in manuscript_attestation[book_name].keys():
        print(f"Processing {book_name} chapter {chapter}")
        verses = manuscript_attestation[book_name][chapter].keys()

        # To avoid re-processing files that already exist in the apparatus folder
        if os.path.exists(
            f"../apparatus/{book_name.lower().replace(' ','_')}_{chapter}.qmd"
        ):
            print(
                "\t This chapter is already in the apparatus folder, so I am skipping it"
            )
            continue

        yaml_section = f"""
---
format:
    pdf:
        documentclass: scrreprt
title: {book_name}
subtitle: Chapter {chapter}
author: www.gntcollations.com
abstract: "*A collation of the Robinson-Pierpont 2018 text against all transcribed Greek New Testament witnesses*"
date: now
date-format: long
toc: true
toc-depth: 3
editor: 
    markdown: 
        wrap: 72
---
"""

        chapter_qmd_string = (
            yaml_section
            + f"""

# Note

* Most manuscripts have not been transcribed and in consequence these apparatuses contain only a sample of the extant corpus.

* The collations and apparatuses have been created using automated algorithms and may in consequence display occasional imprecisions, especially in word alignment when there is significant textual variation in a verse. Please use them for indicative purposes only.

* Some manuscripts contain a verse more than once. This often involved splitting a verse and placing each segment on a different section of the manuscript. We have implemented an algorithm that reconstructs the complete verse from the separate segments. Reconstructed verses are shown between round brackets. For example, 40844(1&2) is the verse as it was attested in 40844 in a reconstruction that merged instances 1 and 2. Given that these are automated reconstructions, manual double-checks are advised. Sometimes it is not possible to safely reconstruct a verse and the witnesses where this is the case are not included in the collation (to see the specific witnesses that could not be reconstructed, please consult the witness counts for each verse).

* Corrected witnesses (marked with a superscript letter *c*) are reconstructed automatically and may display inaccuracies. They are shown with a ? sign to reflect this uncertainty. A corrected witness is included in the apparatus if its text is present in at least another witness, ie, if it does not attest to a singular reading.

* A witness is ignored if {int(fragmentary_threshold*100)}% or more of the words that it contains of the specific verse are uncertain.
{{{{< pagebreak >}}}}

Website version {{{{< var version >}}}}, witness transcriptions up-to-date as of {{{{< var listeupdated >}}}}. More information at [www.gntcollations.com](www.gntcollations.com). Collations created by Norman Simon Rodriguez.
"""
        )

        for verse in verses:
            print(f"Processing verse {book_name} {chapter}:{verse}")
            manuscripts_attesting_this_verse = manuscript_attestation[book_name][
                chapter
            ][verse]

            verse_attestation = []

            for manuscript_id in manuscripts_attesting_this_verse:
                # Read the QMD file
                with open(
                    "../collations/" + str(manuscript_id) + ".qmd",
                    "r",
                    encoding="utf-8",
                ) as file:
                    qmd_content = file.read()

                this_verse_text_and_coordinates = extract_verse_from_qmd(
                    qmd_content, book_name, chapter, verse
                )

                if isinstance(this_verse_text_and_coordinates, pd.DataFrame):
                    for index, row in this_verse_text_and_coordinates.iterrows():
                        verse_attestation.append(
                            [
                                manuscript_id,
                                chapter,
                                verse,
                                row["instance"],
                                row["parsed_greek"],
                            ]
                        )

            # Adding the Byzantine text

            byz_verse = byz[(byz["chapter"] == chapter) & (byz["verse"] == verse)][
                "text"
            ].to_list()

            if len(byz_verse) == 0:
                byz_verse = "EMPTY"
            else:
                byz_verse = byz_verse[0]

            verse_attestation.append(
                ["Byz", chapter, verse, 1, byz_verse]
            )  # The number 1 is the attestation counter. Byz attests to each verse only once

            verse_attestation = pd.DataFrame(verse_attestation)

            verse_attestation.columns = [
                "manuscript_id",
                "chapter",
                "verse",
                "instance",
                "parsed_greek",
            ]
            verse_attestation["manuscript_id"] = verse_attestation[
                "manuscript_id"
            ].astype(str)

            # Check if '.greek-abbr' is a substring in any cell of all columns
            # We don't show nomina sacra, so it's important to alert the reader
            is_abbreviation_present = (
                verse_attestation["parsed_greek"].str.contains(".greek-abbr").any()
            )

            ###########################################
            ###########################################
            ################ Collation ################
            ###########################################
            ###########################################
            # Cleaning the texts
            def clean_text(text):
                text = text.replace("\n", " ")
                pattern_omitted = r"\[([^\]]*?)(?:\]\{[^\}]*?\})*\]\{\.greek-omitted\}"
                cleaned_string = re.sub(pattern_omitted, "", text)
                pattern_supplied = (
                    r"\[([^\]]*?)(?:\]\{[^\}]*?\})*\]\{\.greek-supplied\}"
                )
                cleaned_string = re.sub(pattern_supplied, "U", cleaned_string)
                pattern_unclear = r"\[[^\]]+\]\{\.unclear\}"
                cleaned_string = re.sub(pattern_unclear, "U", cleaned_string)
                cleaned_string = cleaned_string.replace("{.greek-added}", "")
                cleaned_string = cleaned_string.replace("{.greek-abbr}", "")
                cleaned_string = cleaned_string.replace("]{.corr}", "C")
                cleaned_string = cleaned_string.replace("[―]{.gap}", "GAP")
                cleaned_string = cleaned_string.replace("]", "")
                cleaned_string = cleaned_string.replace("[", "")

                # Removing repeated ? and spaces
                cleaned_string = re.sub(r"U+", "U", cleaned_string)
                cleaned_string = re.sub(r" +", " ", cleaned_string)

                return cleaned_string

            verse_attestation["parsed_greek_clean"] = verse_attestation[
                "parsed_greek"
            ].apply(clean_text)

            verse_attestation = verse_attestation.drop(columns=["parsed_greek"])

            byz_verse_size = len(
                verse_attestation[verse_attestation["manuscript_id"] == "Byz"][
                    "parsed_greek_clean"
                ].iloc[0]
            )

            def determine_if_similar_size_to_byz_verse(parsed_greek_clean):
                difference = abs(len(parsed_greek_clean) - byz_verse_size)
                percentage_difference = difference / byz_verse_size
                if (
                    percentage_difference < 0.2
                ):  # If the differences in size is not too great
                    return True
                else:
                    return False

            verse_attestation["similar_size_to_byz_verse"] = verse_attestation[
                "parsed_greek_clean"
            ].apply(determine_if_similar_size_to_byz_verse)

            verse_attestation_grouped = verse_attestation.groupby("manuscript_id")

            keep_these_groups = (
                []
            )  # Reconstructing the verses that are split between several instances, and ignoring the ones we can't reconstruct
            omit_these_witnesses_due_to_several_confusing_instances = []
            for group in verse_attestation_grouped:
                if len(group[1]) == 1:  # No need to reconstruct, there is no splitting
                    keep_these_groups.append(group[1])
                elif (
                    len(group[1]["parsed_greek_clean"].unique()) == 1
                ):  # If all the instances are equal
                    if (
                        group[1]["similar_size_to_byz_verse"].sum() > 0
                    ):  # If the instances have roughly the same size as Byz
                        keep_these_groups.append(
                            group[1].drop_duplicates(subset=["manuscript_id"])
                        )
                    else:
                        omit_these_witnesses_due_to_several_confusing_instances.append(
                            group[1]["manuscript_id"].iloc[0]
                        )
                else:
                    reconstructed = " ".join(group[1]["parsed_greek_clean"].to_list())
                    reconstructed = re.sub(r"\s+", " ", reconstructed)
                    if determine_if_similar_size_to_byz_verse(
                        reconstructed
                    ):  # If the reconstruction has roughly the same size as Byz
                        _ = {
                            "manuscript_id": group[1]["manuscript_id"].iloc[0],
                            "chapter": group[1]["chapter"].iloc[0],
                            "verse": group[1]["verse"].iloc[0],
                            "instance": "&".join(
                                group[1]["instance"].astype(str).to_list()
                            ),
                            "parsed_greek_clean": reconstructed,
                            "similar_size_to_byz_verse": True,
                        }

                        keep_these_groups.append(pd.DataFrame([_]))
                        del _
                    else:
                        omit_these_witnesses_due_to_several_confusing_instances.append(
                            group[1]["manuscript_id"].iloc[0]
                        )

            verse_attestation = pd.concat(keep_these_groups)
            verse_attestation = verse_attestation.drop(
                columns=["similar_size_to_byz_verse"]
            )

            # Adding corrected hands as manuscripts of their own

            verse_attestation["has_corrections"] = verse_attestation[
                "parsed_greek_clean"
            ].str.contains("C")
            verse_attestation["uncorrected_reconstructed"] = False

            corrected_temp = verse_attestation[verse_attestation["has_corrections"]]

            def remove_corrections(text):
                words = text.split()
                uncorrected = []
                for word in words:
                    if "C" not in word:
                        uncorrected.append(word)
                return " ".join(uncorrected)

            corrected_temp.loc[:, "parsed_greek_clean"] = corrected_temp[
                "parsed_greek_clean"
            ].apply(remove_corrections)
            corrected_temp.loc[:, "uncorrected_reconstructed"] = True

            def add_cs(row):
                if "C" in row["parsed_greek_clean"]:
                    return row["manuscript_id"] + "^c^"
                else:
                    return row["manuscript_id"]

            verse_attestation["manuscript_id"] = verse_attestation.apply(add_cs, axis=1)
            verse_attestation["parsed_greek_clean"] = verse_attestation[
                "parsed_greek_clean"
            ].str.replace(
                "C", ""
            )  # Removing the C marker from the corrected hands

            verse_attestation = pd.concat([verse_attestation, corrected_temp])
            del corrected_temp

            verse_attestation["parsed_greek_clean"] = verse_attestation[
                "parsed_greek_clean"
            ].str.strip()

            # Removing empty texts that are not the Byzantine witness
            condition = (
                len(verse_attestation["parsed_greek_clean"].str.split()) == 0
            ) | (verse_attestation["parsed_greek_clean"] == "")
            condition = (condition) & (verse_attestation["manuscript_id"] != "Byz")
            condition = ~condition
            verse_attestation = verse_attestation[condition]

            # Marking manuscripts with more than one instance of the verse
            # The correction marker always comes BEFORE the instance counter
            verse_attestation["manuscript_id"] = verse_attestation[
                ["manuscript_id", "instance"]
            ].apply(
                lambda row: row["manuscript_id"]
                if row["instance"] == 1
                else row["manuscript_id"] + "(" + str(row["instance"]) + ")",
                axis=1,
            )

            # Removing fragmentary manuscripts
            def define_if_too_fragmentary(text):
                num_words = len(text.split())
                words_unclear_or_supplied = []
                for word in text.split():
                    if "U" in word:
                        words_unclear_or_supplied.append(word)
                num_words_unclear_or_supplied = len(words_unclear_or_supplied)
                if (num_words_unclear_or_supplied / num_words) > fragmentary_threshold:
                    return True
                else:
                    return False

            verse_attestation["too_fragmentary"] = verse_attestation[
                "parsed_greek_clean"
            ].apply(define_if_too_fragmentary)

            fragmentary_witnesses = verse_attestation[
                verse_attestation["too_fragmentary"]
            ]
            non_fragmentary_witnesses = verse_attestation[
                ~verse_attestation["too_fragmentary"]
            ]

            # Witness groups
            witness_groups = (
                non_fragmentary_witnesses[["manuscript_id", "parsed_greek_clean"]]
                .groupby("parsed_greek_clean")["manuscript_id"]
                .apply(list)
                .reset_index()
            )

            witness_groups["group_size"] = witness_groups["manuscript_id"].apply(len)
            witness_groups = witness_groups.sort_values(
                by=["group_size"], ascending=False
            )

            witness_groups["contains_byz"] = witness_groups["manuscript_id"].apply(
                lambda x: True if "Byz" in x else False
            )

            unanimous_group = witness_groups[witness_groups["contains_byz"]]
            unanimous_group.loc[:, "manuscript_id"] = unanimous_group[
                "manuscript_id"
            ].apply(
                lambda mlist: [x for x in mlist if x != "Byz"]
            )  # Removing Byz to avoid counting it as a witness
            unanimous_group.loc[:, "group_size"] = unanimous_group[
                "manuscript_id"
            ].apply(len)
            unanimous_group_badge = (
                f"→**unanimous**~{byz_book_abbrs[book_name].lower()}.{chapter}.{verse}~"
            )
            unanimous_group.loc[:, "group_name"] = unanimous_group_badge

            witness_groups = witness_groups[~witness_groups["contains_byz"]]

            middle_sized_groups = witness_groups[witness_groups["group_size"] >= 2]
            num_repeats = (
                len(middle_sized_groups) // 26 + 1
            )  # Calculate the number of times the alphabet has to repeat. This is to generate the alphabetical group indexes
            alphabet = [
                chr(i) for i in range(97, 123)
            ]  # Create a list of alphabetical characters, a to z
            char_cycle = itertools.cycle(
                alphabet
            )  # Create a generator to cycle through the characters
            index_chars = []
            for i in range(num_repeats):
                index_chars.extend(
                    [
                        f"→**{(char * (i + 1)).upper()}**~{byz_book_abbrs[book_name].lower()}.{chapter}.{verse}~"
                        for char in alphabet
                    ]
                )
            middle_sized_groups.loc[:, "group_name"] = index_chars[
                : len(middle_sized_groups)
            ]

            one_sized_groups = witness_groups[witness_groups["group_size"] == 1]
            one_sized_groups.loc[:, "group_name"] = one_sized_groups[
                "manuscript_id"
            ].apply(lambda x: x[0])

            # Detecting and removing non-aligned corrected witnesses
            one_sized_groups.loc[:, "is_corrected_witness"] = one_sized_groups[
                "group_name"
            ].apply(lambda x: True if "^c^" in x else False)

            ignored_corrected_non_aligned_witnesses = one_sized_groups[
                one_sized_groups["is_corrected_witness"]
            ]

            one_sized_groups = one_sized_groups[
                ~one_sized_groups["is_corrected_witness"]
            ]

            witness_groups = pd.concat(
                [unanimous_group, middle_sized_groups, one_sized_groups]
            )

            collation = collatex.Collation()

            for index, row in witness_groups.iterrows():
                collation.add_plain_witness(
                    row["group_name"], row["parsed_greek_clean"]
                )

            collatex_output = collatex.collate(
                collation, layout="horizontal", near_match=True, segmentation=False
            )

            collatex_output = str(collatex_output)
            # Specify the file path where you want to save the text file
            file_path = "output.txt"

            # Open the file in write mode and write the content of collatex_output to it
            with open(file_path, "w") as file:
                file.write(collatex_output)

            def collatex_output_to_df(collatex_output):
                collatex_output = str(collatex_output)
                rows = collatex_output.split("\n")
                data = []
                for row in rows:
                    if row.startswith("|"):
                        row = row.strip("|")
                        row = [cell.strip() for cell in row.split("|") if cell.strip()]
                        data.append(row)

                # Create a DataFrame from the extracted data
                df = pd.DataFrame(data).set_index(0)
                df.columns = range(0, df.shape[1])
                df.index.name = "manuscript_id"
                return df

            alignment_table = collatex_output_to_df(collatex_output)

            # Removing unwanted NAs
            alignment_table = alignment_table.fillna("-")
            alignment_table = alignment_table.replace("-", pd.NA).dropna(
                axis=1, how="all"
            )
            alignment_table.columns = range(len(alignment_table.columns))

            alignment_table = alignment_table.fillna("•")

            # alignment_table.to_csv(f"{verse}.csv")

            # Find the base column (Byz)
            byz_column_base = alignment_table.loc[unanimous_group_badge]

            # Merging empty textual units. if A is not empty, B is empty and C is not empty, the result is A, BC.
            columns_to_merge_in_alignment_table = []

            for index, row in pd.DataFrame(byz_column_base).iterrows():
                if row.iloc[0] == "•":
                    if index == len(byz_column_base) - 1:
                        columns_to_merge_in_alignment_table.append([index - 1, index])
                    else:
                        columns_to_merge_in_alignment_table.append([index, index + 1])

            columns_to_merge_in_alignment_table = (
                pd.Series(columns_to_merge_in_alignment_table)
                .drop_duplicates()
                .to_list()
            )
            columns_to_merge_in_alignment_table.reverse()

            for merge_this_pair in columns_to_merge_in_alignment_table:
                alignment_table[merge_this_pair[0]] = (
                    alignment_table[merge_this_pair[0]]
                    + " "
                    + alignment_table[merge_this_pair[1]]
                )
                alignment_table = alignment_table.drop(columns=[merge_this_pair[1]])

            for col in alignment_table.columns:
                alignment_table[col] = (
                    alignment_table[col]
                    .str.replace("•", " ")
                    .str.replace("\s+", " ", regex=True)
                    .str.strip()
                    .replace("", "•")
                )

            alignment_table.columns = range(len(alignment_table.columns))

            # Check that the last textual unit is not an empty unit in Byz
            byz_column_base = alignment_table.loc[unanimous_group_badge]

            if byz_column_base.iloc[-1] == "•":
                alignment_table[len(byz_column_base) - 2] = (
                    alignment_table[len(byz_column_base) - 2]
                    + " "
                    + alignment_table[len(byz_column_base) - 1]
                )
                alignment_table = alignment_table.drop(
                    columns=[len(byz_column_base) - 1]
                )
                alignment_table[len(byz_column_base) - 2] = (
                    alignment_table[len(byz_column_base) - 2]
                    .str.replace("•", " ")
                    .str.replace("\s+", " ", regex=True)
                    .str.strip()
                    .replace("", "•")
                )

            alignment_table.columns = range(len(alignment_table.columns))
            byz_column_base = alignment_table.loc[unanimous_group_badge]

            # alignment_table.to_csv("test.csv")

            # Agglomerating the coincidences

            textual_units = []
            for column_name in alignment_table.columns:
                textual_unit = alignment_table[column_name].reset_index()
                textual_unit.columns = ["manuscript_coincidence", "reading"]
                textual_unit = (
                    textual_unit.groupby("reading")["manuscript_coincidence"]
                    .agg(list)
                    .to_frame()
                )
                textual_unit["position"] = column_name
                textual_units.append(textual_unit)

            textual_units = pd.concat(textual_units)
            textual_units["is_byzantine"] = textual_units[
                "manuscript_coincidence"
            ].apply(lambda x: True if unanimous_group_badge in x else False)

            # Determining which manuscripts have a text identical to Byz
            manuscripts_verse_identical_to_byz = unanimous_group["manuscript_id"].iloc[
                0
            ]

            ##### Creating the QMD code

            liste = pd.read_csv(
                "../raw_data/liste/liste.csv", usecols=["docID", "origLate"]
            )
            liste["docID"] = liste["docID"].astype(int).astype(str)

            # Function to convert year to century
            def year_to_century(year):
                return (year - 1) // 100 + 1

            liste["century_late"] = liste["origLate"].astype(int).apply(year_to_century)
            # liste["century_late_roman"] = liste["century_late"].apply(roman.toRoman)

            def format_manuscript_coincidences_for_quarto(manuscript_coincidence):
                def add_link_to_manuscript_id(manuscript_element):
                    if "^c^" in manuscript_element:
                        manuscript_handle = manuscript_element
                        manuscript_id = manuscript_element[0:5]
                    elif (
                        "(" in manuscript_element
                    ):  # If it is an additional instance of a verse
                        manuscript_handle = manuscript_element
                        manuscript_id = manuscript_element[0:5]
                    else:
                        manuscript_id = manuscript_element
                        manuscript_handle = manuscript_element

                    if (
                        "^c^" in manuscript_handle
                    ):  # Adding the CSS style for corrected witnesses
                        manuscript_handle = (
                            "[" + manuscript_handle + "?]{.apparatus-corrected}"
                        )

                    url = (
                        f"https://www.gntcollations.com/collations/{manuscript_id}.html"
                    )

                    return (
                        "[["
                        + manuscript_handle
                        + "]("
                        + url
                        + ")]{.apparatus-manuscript-link}"
                    )

                if len(manuscript_coincidence) == 0:
                    return "None"
                else:
                    witness_group_coincidence = []  # Witness groups don't need parsing
                    corrected_manuscripts_ids = (
                        []
                    )  # Corrected witnesses don't have a date, so we parse them separately
                    standalone_manuscript_ids = []

                    for coincidence in manuscript_coincidence:
                        if coincidence[0] == "→":
                            witness_group_coincidence.append(coincidence)
                        elif "^c^" in coincidence:
                            corrected_manuscripts_ids.append(coincidence)
                        elif "(" in coincidence:
                            standalone_manuscript_ids.append(
                                [coincidence.split("(")[0], coincidence]
                            )
                        else:
                            standalone_manuscript_ids.append([coincidence, coincidence])

                    # Corrected manuscripts
                    corrected_manuscripts_ids = (
                        pd.Series(corrected_manuscripts_ids, dtype="str")
                        .sort_values(ascending=True)
                        .to_list()
                    )
                    corrected_manuscripts_formatted_string = ""
                    if len(corrected_manuscripts_ids) > 0:
                        corrected_manuscripts_formatted_string = (
                            "[Corr.]{.correction-label-apparatus}: "
                            + " ".join(
                                add_link_to_manuscript_id(manuscript_id)
                                for manuscript_id in corrected_manuscripts_ids
                            )
                        )

                    standalone_manuscripts = pd.DataFrame(
                        standalone_manuscript_ids,
                        columns=["manuscript_id", "manuscript_handle"],
                    )
                    standalone_manuscripts = pd.merge(
                        standalone_manuscripts,
                        liste,
                        left_on="manuscript_id",
                        right_on="docID",
                        how="left",
                    )
                    standalone_manuscripts = (
                        standalone_manuscripts.drop_duplicates()
                    )  # Some items in the Liste appear more than once
                    standalone_manuscripts = standalone_manuscripts.sort_values(
                        by=["manuscript_id"], ascending=True
                    )

                    standalone_manuscripts = (
                        standalone_manuscripts[
                            ["docID", "manuscript_handle", "century_late"]
                        ]
                        .groupby("century_late", group_keys=False)["manuscript_handle"]
                        .apply(list)
                        .reset_index()
                    )

                    standalone_manuscripts_formatted_string = ""
                    if len(standalone_manuscripts) > 0:
                        standalone_manuscripts["formatted_ids"] = (
                            standalone_manuscripts["manuscript_handle"]
                            .apply(
                                lambda mlist: [
                                    add_link_to_manuscript_id(manuscript_id)
                                    for manuscript_id in mlist
                                ]
                            )
                            .apply(lambda x: " ".join(x))
                        )
                        standalone_manuscripts["formatted_text_for_this_century"] = (
                            "["
                            + standalone_manuscripts["century_late"]
                            .apply(roman.toRoman)
                            .str.lower()
                            + "]{.century-apparatus}: "
                            + standalone_manuscripts["formatted_ids"]
                        )
                        standalone_manuscripts_formatted_string = " ".join(
                            standalone_manuscripts["formatted_text_for_this_century"]
                        )

                    witness_group_coincidence_string = " ".join(
                        witness_group_coincidence
                    )

                    first_separator = ""
                    second_separator = ""

                    if len(witness_group_coincidence_string.strip()) > 0:
                        if len(standalone_manuscripts_formatted_string.strip()) > 0:
                            first_separator = " ║ "
                        elif len(corrected_manuscripts_formatted_string.strip()) > 0:
                            first_separator = " ║ "
                        else:
                            pass

                    if len(standalone_manuscripts_formatted_string.strip()) > 0:
                        if len(corrected_manuscripts_formatted_string.strip()) > 0:
                            second_separator = " ║ "

                    final_string = (
                        witness_group_coincidence_string
                        + first_separator
                        + standalone_manuscripts_formatted_string
                        + second_separator
                        + corrected_manuscripts_formatted_string
                    )
                    return final_string

            textual_units["formatted_manuscript_coincidence"] = textual_units[
                "manuscript_coincidence"
            ].apply(format_manuscript_coincidences_for_quarto)

            ##### Creating the QMD

            byz_qmd_string = "{{< pagebreak >}}" + f"\n\n# Verse {chapter}:{verse}\n\n"

            if (
                verse_attestation[verse_attestation["manuscript_id"] == "Byz"][
                    "parsed_greek_clean"
                ].iloc[0]
                == "EMPTY"
            ):
                this_verse_collation_string = (
                    byz_qmd_string + "**This verse is not present in Byz^RP^**\n\n"
                )
            else:
                byz_qmd_string = byz_qmd_string + "*Byz^RP^:* ["
                for position in range(len(byz_column_base)):
                    footnote_marker = position + 1
                    byz_qmd_string = (
                        byz_qmd_string
                        + byz_column_base[position]
                        + "^**"
                        + str(footnote_marker)
                        + "**^ "
                    )

                this_verse_collation_string = (
                    byz_qmd_string + "]{.apparatus-byzatine-primary-line}\n\n"
                )

            ########################################
            ########################################
            ## Creating the witness count callout ##
            ########################################
            ########################################

            # The data table
            witness_counts_table = []

            # Number of witnesses that are ignored due to including several instances of the verse that could not be merged
            num_omitted_witnesses_several_verse_instances = len(
                omit_these_witnesses_due_to_several_confusing_instances
            )

            # Number of transcribed manuscripts attesting this verse

            witnesses_that_have_this_verse_includes_corrections = verse_attestation[
                (verse_attestation["manuscript_id"] != "Byz")
            ]

            witnesses_that_have_this_verse_not_includes_corrections = verse_attestation[
                (
                    ~verse_attestation["manuscript_id"].apply(
                        lambda x: True if "^c^" in x else False
                    )
                )
                & (verse_attestation["manuscript_id"] != "Byz")
            ]

            num_manuscripts_attesting_this_verse = len(
                witnesses_that_have_this_verse_not_includes_corrections
            )

            num_manuscripts_attesting_this_verse = (
                num_manuscripts_attesting_this_verse
                + num_omitted_witnesses_several_verse_instances
            )

            witness_counts_table.append(
                [
                    "Number of transcribed manuscripts that contain this verse",  # Description
                    num_manuscripts_attesting_this_verse,  # Count
                    "For manuscript lists see the apparatus and the witness groups",  # Manuscript list
                ]
            )

            # Witnesses ignored for attesting the verse more than once, with unsuccessful reconstruction

            witness_counts_table.append(
                [
                    "Number of witnesses that are *ignored* for including the verse more than once (reconstruction unsuccessful)",  # Description
                    num_omitted_witnesses_several_verse_instances,  # Count
                    format_manuscript_coincidences_for_quarto(
                        omit_these_witnesses_due_to_several_confusing_instances
                    ),  # Manuscript list
                ]
            )

            # Corrected witnesses that ARE included

            witnesses_corrected_this_verse = (
                witnesses_that_have_this_verse_includes_corrections[
                    (
                        witnesses_that_have_this_verse_includes_corrections[
                            "has_corrections"
                        ]
                    )
                    & (
                        ~witnesses_that_have_this_verse_includes_corrections[
                            "uncorrected_reconstructed"
                        ]
                    )
                ]["manuscript_id"].to_list()
            )

            witnesses_included_corrected = []
            for w in witnesses_corrected_this_verse:
                if len(ignored_corrected_non_aligned_witnesses) == 0:
                    pass
                elif (
                    w in ignored_corrected_non_aligned_witnesses["group_name"].to_list()
                ):
                    pass
                else:
                    witnesses_included_corrected.append(w)

            num_witnesses_attesting_this_verse_corrected = len(
                witnesses_included_corrected
            )

            witness_counts_table.append(
                [
                    "Corrected witnesses *included* in the apparatus",  # Description
                    num_witnesses_attesting_this_verse_corrected,  # Count
                    format_manuscript_coincidences_for_quarto(
                        witnesses_included_corrected
                    ),  # Manuscript list
                ]
            )

            # Fragmentary witnesses

            fragmentary_witnesses_including_this_verse = (
                witnesses_that_have_this_verse_includes_corrections[
                    witnesses_that_have_this_verse_includes_corrections[
                        "too_fragmentary"
                    ]
                ]
            )
            num_fragmentary_witnesses_this_verse = len(
                fragmentary_witnesses_including_this_verse
            )

            witnesses_exluded_too_fragmentary = (
                fragmentary_witnesses_including_this_verse["manuscript_id"].to_list()
            )

            witness_counts_table.append(
                [
                    f"Witnesses *ignored* due to being too fragmentary",  # Description
                    num_fragmentary_witnesses_this_verse,  # Count
                    format_manuscript_coincidences_for_quarto(
                        witnesses_exluded_too_fragmentary
                    ),  # Manuscript list
                ]
            )

            witnesses_that_have_this_verse_not_includes_corrections_minus_fragmentary = witnesses_that_have_this_verse_not_includes_corrections[
                ~witnesses_that_have_this_verse_not_includes_corrections[
                    "too_fragmentary"
                ]
            ]

            # Corrected hands that are IGNORED
            if len(ignored_corrected_non_aligned_witnesses) > 0:
                witnesses_corrected_ignored = ignored_corrected_non_aligned_witnesses[
                    "group_name"
                ].to_list()
            else:
                witnesses_corrected_ignored = []
            num_corrected_ignored = len(witnesses_corrected_ignored)

            witness_counts_table.append(
                [
                    "Corrected witnesses *ignored* from the apparatus^[These corrected witnesses offer singular readings for the entire verse, which may indicate that our automated algorithm reconstructed them incorrectly. We are ignoring them from the collation in order to reduce the risk of displaying inaccurate results (the *uncorrected* witness may itself be included in the apparatus).]",  # Description
                    num_corrected_ignored,  # Count
                    format_manuscript_coincidences_for_quarto(
                        witnesses_corrected_ignored
                    ),  # Manuscript list
                ]
            )

            witnesses_that_have_this_verse_not_includes_corrections_minus_fragmentary_minus_corignored = witnesses_that_have_this_verse_not_includes_corrections_minus_fragmentary[
                ~witnesses_that_have_this_verse_not_includes_corrections_minus_fragmentary[
                    "manuscript_id"
                ].isin(
                    pd.Series(witnesses_corrected_ignored, dtype="object").apply(
                        lambda x: x.replace("^c^", "")
                    )
                )
            ]

            # Count of witnesses included in the apparatus

            num_witnesses_included_in_collation = (
                num_manuscripts_attesting_this_verse
                - num_omitted_witnesses_several_verse_instances
                - num_fragmentary_witnesses_this_verse
                + num_witnesses_attesting_this_verse_corrected
            )

            witness_counts_table.append(
                [
                    f"**Number of witnesses that were taken into account in the collation**^[The total number of witnesses is calculated as the total manuscripts ({num_manuscripts_attesting_this_verse}) minus the witnesses that attest to the verse more than once and where the verse could not be reconstructed ({num_omitted_witnesses_several_verse_instances}) minus the fragmentary witnesses ({num_fragmentary_witnesses_this_verse}) plus the included corrected witnesses ({num_witnesses_attesting_this_verse_corrected}).]",  # Description
                    f"**{num_witnesses_included_in_collation}**",  # Count
                    "For manuscript lists see the apparatus and the witness groups",  # Manuscript list
                ]
            )

            witness_counts_table = pd.DataFrame(
                witness_counts_table,
                columns=["Description", "Count", "Manuscript list"],
            )

            this_verse_collation_string = (
                this_verse_collation_string
                # + '::: {.callout-note  collapse="true" icon="false"}\n## Witness counts\n'
                + "## Witness counts\n"
                + "\n\n"
                + witness_counts_table.to_markdown(index=False)
                # + "\n:::\n\n"
                + '\n: {tbl-colwidths="[40,20,40]"}\n\n'
            )

            #######################################
            #######################################
            ## Creating the nomina sacra callout ##
            #######################################
            #######################################
            if is_abbreviation_present:
                this_verse_collation_string = (
                    this_verse_collation_string
                    + '::: {.callout-important collapse="true" icon="false"}\n## *Nomina sacra* or abbreviations\nPlease note that one or more of the witnesses contains *nomina sacra* which have been spelled out by our automated algorithm. This process is very accurate, but occasional mistakes can happen, especially with obscure or uncommon *nomina sacra*. In case of doubt about the actual reading of a *nomen sacrum*, please consult the original transcripts or facsimiles.\n:::\n\n'
                )

            ####################################################
            ####################################################
            ##### Creating the earliest attestation callout ####
            ####################################################
            ####################################################

            # Function to determine earliest century
            def find_earliest_century(manuscript_list, type_data):
                if type_data == "unanimous":
                    manuscript_list = manuscript_list[0]
                elif type_data == "individual":
                    extended_m_list = []
                    for group_name in manuscript_list:
                        _ = witness_groups[witness_groups["group_name"] == group_name][
                            "manuscript_id"
                        ].iloc[0]
                        for man in _:
                            extended_m_list.append(man)
                    manuscript_list = extended_m_list
                elif type_data == "verse":
                    manuscript_list.remove("Byz")

                centuries = []
                for m in manuscript_list:
                    if (
                        "^c^" in m
                    ):  # Corrected hands don't have dates associated with them
                        centuries.append(pd.NA)
                    else:
                        if "(" in m:
                            m = m.split("(")[
                                0
                            ]  # Manuscripts that have several instances of the same verse. We only need the manuscript id at this moment in order to obtain the centuries
                        centuries.append(
                            liste[liste["docID"] == m]["century_late"].iloc[0]
                        )

                if len(centuries) == 0:
                    if type_data == "unanimous":
                        return "*Byzantine text not attested in its entirety in any of the collated manuscripts*"
                    elif type_data == "individual":
                        return "*Byzantine reading not attested in its entirety in any of the collated manuscripts*"
                    elif type_data == "verse":
                        return "*Verse not attested in any of the collated manuscripts*"
                else:
                    if np.isnan(pd.Series(centuries).min()):
                        return "*The text is present only in a corrected hand and does not have a date associated to it*"
                    else:
                        return (
                            "["
                            + roman.toRoman(int(pd.Series(centuries).min())).lower()
                            + "]{.century-apparatus}"
                        )

            # Complete verse
            earliest_attestation_complete_verse = find_earliest_century(
                unanimous_group["manuscript_id"].to_list(), "unanimous"
            )

            # Individual readings
            earliest_attestation_readings = []
            for position in range(len(byz_column_base)):
                byzantine_reading = byz_column_base.iloc[position]
                witnesses_supporting_this_byzantine_reading = textual_units[
                    (textual_units["position"] == position)
                    & (textual_units["is_byzantine"] == True)
                ]["manuscript_coincidence"].iloc[0]
                earliest_attestation_readings.append(
                    [byzantine_reading, witnesses_supporting_this_byzantine_reading]
                )

            earliest_attestation_readings = pd.DataFrame(
                earliest_attestation_readings, columns=["Reading", "manuscript_list"]
            )

            _ = []
            for index, row in earliest_attestation_readings.iterrows():
                _.append(find_earliest_century(row["manuscript_list"], "individual"))

            earliest_attestation_readings["Earliest attestation (century)"] = _
            del _

            # Existence of verse
            earliest_attestation_existence_verse = find_earliest_century(
                verse_attestation["manuscript_id"].to_list(), "verse"
            )

            this_verse_collation_string = (
                this_verse_collation_string
                # + '::: {.callout-warning collapse="true" icon="false"}\n## Earliest attestation\n'
                + "## Earliest attestation\n"
                + "**Note:** Most manuscripts have not been transcribed yet. In consequence, the below information is based only on the limited sample available at the moment of creating the apparatus.\n\n"
                + f"* Earliest attestation (century) of the *existence* of this verse (including fragmentary manuscripts): {earliest_attestation_existence_verse}.\n\n"
                + f"* Earliest attestation (century) of the *complete, verbatim text* of the Byzantine texform for this verse in a transcribed manuscript: {earliest_attestation_complete_verse}.\n\n"
                + "Below is the earliest attestation of each *individual Byzantine reading*:\n\n"
                + earliest_attestation_readings[
                    ["Reading", "Earliest attestation (century)"]
                ].to_markdown(index=False)
                # + "\n:::\n\n"
                + "\n\n"
            )

            ######################################
            ######################################
            ##### Creating the groups callout ####
            ######################################
            ######################################

            unanimous_group_size = unanimous_group["group_size"].iloc[0]
            middle_sized_groups_size = middle_sized_groups["group_size"].sum()
            if len(one_sized_groups) > 0:
                one_sized_groups_size = one_sized_groups["group_size"].sum()
            else:
                one_sized_groups_size = 0

            initial_callout = (
                #'::: {.callout-tip collapse="true" icon="false"}\n## Witness groups\n\n'
                "## Witness groups\n\n"
            )

            initial_callout = (
                initial_callout
                + f"The below groups show witnesses that share identical texts for the entire verse. That is, any two witnesses belong in the same group if their texts are identical for the entire verse. There are {unanimous_group_size + middle_sized_groups_size} witnesses in groups for this verse. For these, the apparatus lists the group instead of the individual witnesses. The group names are assigned automatically and their composition may change as new manuscripts are added to the collation in future. The remaining witnesses ({one_sized_groups_size}) attest to singular texts for the entire verse and are therefore not part of any group. These non-aligned witnesses are individually shown in the apparatus.\nManuscript identifiers are shown preceded by the century of their estimated date (latest estimated date).\n"
            )

            # Unanimous group
            manuscripts_verse_identical_to_byz_string = f"\n\n* {unanimous_group_badge} **group**, ie witnesses that attest a verse identical with Byz^RP^  **({unanimous_group_size})**: "

            if unanimous_group["group_size"].iloc[0] > 0:
                manuscripts_verse_identical_to_byz_string = (
                    manuscripts_verse_identical_to_byz_string
                    + format_manuscript_coincidences_for_quarto(
                        unanimous_group["manuscript_id"].iloc[0]
                    )
                )
            else:
                manuscripts_verse_identical_to_byz_string = (
                    manuscripts_verse_identical_to_byz_string + "None."
                )

            this_verse_collation_string = (
                this_verse_collation_string
                + initial_callout
                + manuscripts_verse_identical_to_byz_string
            )

            # Other groups
            other_groups_string = ""
            if middle_sized_groups_size > 0:
                for index, row in middle_sized_groups.iterrows():
                    attests_to_temp = (
                        row["parsed_greek_clean"]
                        .replace("U", "[[?]]{.apparatus-uncertain}")
                        .replace("GAP", "[—]{.gap}")
                    )
                    other_groups_string = (
                        other_groups_string
                        + f"* {row['group_name']} **group**, attesting to {attests_to_temp} ({row['group_size']}): {format_manuscript_coincidences_for_quarto(row['manuscript_id'])}\n\n"
                    )
                    del attests_to_temp

            this_verse_collation_string = (
                this_verse_collation_string
                + "\n\n"
                + other_groups_string
                + "\n\n"  # ":::\n\n"
            )

            ######################################
            ######################################
            ###### Creating the apparatus ########
            ######################################
            ######################################

            def calculate_num_witnesses_supporting_this_reading(manuscript_coincidence):
                witness_count = 0
                for coincidence in manuscript_coincidence:
                    if coincidence == unanimous_group_badge:
                        witness_count = witness_count + unanimous_group_size
                    elif coincidence in middle_sized_groups["group_name"].unique():
                        witness_count = (
                            witness_count
                            + middle_sized_groups[
                                middle_sized_groups["group_name"] == coincidence
                            ]["group_size"].iloc[0]
                        )
                    else:
                        witness_count = witness_count + 1
                return witness_count

            apparatus_string = "## Apparatus\n\n"

            for position in range(len(byz_column_base)):
                footnote_marker = position + 1

                # Byzantine reading
                witnesses_supporting_this_byzantine_reading = textual_units[
                    (textual_units["position"] == position)
                    & (textual_units["is_byzantine"] == True)
                ]["manuscript_coincidence"].iloc[0]

                if unanimous_group_size == 0:
                    witnesses_supporting_this_byzantine_reading.remove(
                        unanimous_group_badge
                    )

                num_witnesses_supporting_this_byzantine_reading = (
                    calculate_num_witnesses_supporting_this_reading(
                        witnesses_supporting_this_byzantine_reading
                    )
                )

                apparatus_string = (
                    apparatus_string
                    + "\n"
                    + str(footnote_marker)
                    + ". "
                    + "**"
                    + byz_column_base[position].replace("EMPTY", "•")
                    + f"]** ({num_witnesses_supporting_this_byzantine_reading}/{num_witnesses_included_in_collation}) "
                    + format_manuscript_coincidences_for_quarto(
                        witnesses_supporting_this_byzantine_reading
                    )
                    + "\n\n"
                )

                # Non-byzantine readings
                variants_at_this_textual_unit = textual_units[
                    (textual_units["position"] == position)
                    & (textual_units["is_byzantine"] == False)
                ]

                if len(variants_at_this_textual_unit) > 0:
                    for reading, row in variants_at_this_textual_unit.iterrows():
                        reading = reading.replace("U", "[[?]]{.apparatus-uncertain}")
                        reading = reading.replace("GAP", "[—]{.gap}")

                        if reading == "•":
                            reading = "*either missing or lacuna*"
                        apparatus_string = (
                            apparatus_string
                            + "    * "
                            + reading
                            + ": "
                            + format_manuscript_coincidences_for_quarto(
                                row["manuscript_coincidence"]
                            )
                            + "\n"
                        )

            this_verse_collation_string = this_verse_collation_string + apparatus_string

            chapter_qmd_string = chapter_qmd_string + this_verse_collation_string

        with open(
            f"../apparatus/{book_name.lower().replace(' ','_')}_{chapter}.qmd",
            "w",
            encoding="utf-8",
        ) as file:
            file.write(chapter_qmd_string)
