import json
import pandas as pd
from bs4 import BeautifulSoup
import os
import glob
import difflib
import re
import numpy as np


def parse_manuscript(
    manuscript_id,
    manuscripts_directory,
    abbreviations_equivalences,
    spelling_standardisation,
):
    """
    Parses XML manuscript to generate a Pandas DataFrame
    in which each row is a verse and the transcriptions are
    provided as XML strings.
    """
    manuscript_id = str(manuscript_id)

    print("Parsing manuscript", manuscript_id)

    # Define the XML file path
    xml_file = manuscripts_directory + "/" + manuscript_id + ".xml"

    # Read the XML file
    with open(xml_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Parse the XML content with BeautifulSoup
    soup = BeautifulSoup(xml_content, "xml")

    # Detecting duplicated verses and marking each instance
    verses_ab_tags = soup.find_all("ab", recursive=True, attrs={"n": True})

    for ab_tag in verses_ab_tags:
        verses_with_n_equal_to_this_tag_n = [
            tag for tag in verses_ab_tags if tag.get("n") == ab_tag["n"]
        ]
        for i, tag in enumerate(verses_with_n_equal_to_this_tag_n, start=1):
            tag["instance"] = i

    # Find all <app> tags without an 'n' attribute
    app_tags = soup.find_all("app", recursive=True)
    for index, app_tag in enumerate(app_tags, start=1):
        if "n" not in app_tag.attrs:
            app_tag["n"] = str(index)

    # Find all <rdg> tags
    rdg_tags = soup.find_all("rdg", recursive=True)

    # Find all <w> tags in the adjusted soup
    w_tags = soup.find_all("w")

    # Removing junk tags
    for w_tag in w_tags:
        # note tags
        note_tags = w_tag.find_all("note")
        for note_tag in note_tags:
            note_tag.extract()
        # pc tags
        pc_tags = w_tag.find_all("pc")
        for pc_tag in pc_tags:
            pc_tag.extract()
        # lb tags
        lb_tags = w_tag.find_all("lb")
        for lb_tag in lb_tags:
            lb_tag.unwrap()
        # cb tags
        cb_tags = w_tag.find_all("cb")
        for cb_tag in cb_tags:
            cb_tag.unwrap()
        # pb tags
        pb_tags = w_tag.find_all("pb")
        for pb_tag in pb_tags:
            pb_tag.unwrap()
        # hi tags
        hi_tags = w_tag.find_all("hi")
        for hi_tag in hi_tags:
            hi_tag.unwrap()
        # ex tags
        ex_tags = w_tag.find_all("ex")
        for ex_tag in ex_tags:
            ex_tag.unwrap()

    # Define function to spell out nomina sacra
    def spell_out_abbreviations(w_tag, abbreviations_equivalences):
        target_tag = w_tag.find("abbr")
        if target_tag:
            if target_tag.text in abbreviations_equivalences["abbreviations"].unique():
                target_tag.string = abbreviations_equivalences[
                    abbreviations_equivalences["abbreviations"] == target_tag.text
                ]["spelled_out"].iloc[0]

    def standardise_spelling(w_tag, spelling_equivalences):
        # Ignore words that have inner XML structure, as we don't want to disrupt that
        if not w_tag.find():
            if w_tag.text in spelling_equivalences["nonstandard"].unique():
                w_tag.string = spelling_equivalences[
                    spelling_equivalences["nonstandard"] == w_tag.text
                ]["standard"].iloc[0]

    # Create a list of dictionaries with parent information
    w_tag_dicts = []
    for w_tag in w_tags:
        if manuscript_id != "BYZ":
            spell_out_abbreviations(w_tag, abbreviations_equivalences)
            if spelling_standardisation:
                standardise_spelling(w_tag, spelling_equivalences)
        # Getting the data from the parents of the tag
        parent_dict = {}
        current = w_tag.parent
        while current:
            if current.name:
                if current.name == "div" and current.get("type") == "book":
                    if current.get("n")[0] == "B":
                        parent_dict["book"] = current.get("n")
                    else:
                        parent_dict["book"] = "B" + str(current.get("n")).zfill(
                            2
                        )  # Some books are just numbers
                elif current.name == "div" and current.get("type") == "chapter":
                    parent_dict["chapter"] = current.get("n")
                elif current.name == "div" and current.get("type") == "incipit":
                    parent_dict["incipit"] = current.get("n")
                elif current.name == "ab":
                    parent_dict["verse"] = current.get("n")
                    parent_dict["instance"] = current.get("instance")
                elif current.name == "app":
                    parent_dict["app"] = current.get("n")
                elif current.name == "rdg":
                    parent_dict["type"] = current.get("type")
                    parent_dict["hand"] = current.get("hand")
                else:
                    parent_dict[current.name] = current.attrs
            current = current.parent
        w_tag_dict = {"w_tag": str(w_tag), "parents": parent_dict}
        w_tag_dicts.append(w_tag_dict)

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(w_tag_dicts)

    # Flatten the 'parents' column into separate columns
    df = pd.json_normalize(df["parents"]).merge(df, left_index=True, right_index=True)

    # Define the columns to remove
    columns_to_remove = []

    for col_rem in [
        "parents",
        "text.xml:lang",
        "TEI.xmlns",
        "seg.type",
        "seg.subtype",
        "seg.n",
    ]:
        if col_rem in df.columns:
            columns_to_remove.append(col_rem)

    # Remove the specified columns
    df = df.drop(columns=columns_to_remove)

    # Add an order by column
    df["orderby"] = range(1, len(df) + 1)

    # Reorganize the remaining columns in the desired order

    column_order = []
    for col_reorg in [
        "orderby",
        "book",
        "incipit",
        "chapter",
        "verse",
        "instance",
        "app",
        "type",
        "hand",
        "w_tag",
    ]:
        if col_reorg not in df.columns:
            df[col_reorg] = None
        column_order.append(col_reorg)
    df = df[column_order]

    # Mark corrected hands as such
    def mark_as_corrected(type_input, w_tag):
        if type_input == "corr":
            return (
                w_tag.replace("<w>", "<w><corr>")
                .replace("</w>", "</corr></w>")
                .replace("<w/>", "<w><corr><corr></w>")
            )
        else:
            return w_tag

    df["w_tag"] = df.apply(
        lambda row: mark_as_corrected(row["type"], row["w_tag"]), axis=1
    )

    # Removing empty tags from BYZ
    if manuscript_id == "BYZ":
        df["w_tag"] = df["w_tag"].str.replace("<w/>", "")

    # Group by 'book', 'chapter', and 'verse' and aggregate 'w_tag' into a list
    grouped_df = (
        df.groupby(
            ["book", "chapter", "verse", "instance", "incipit"],
            dropna=False,
            group_keys=False,
        )["w_tag"]
        .apply(list)
        .reset_index()
    )

    # Detect which verses have lacunae
    if manuscript_id != "BYZ":
        verse_tags = soup.find_all("ab", recursive=True)
        verses_with_lacunae = []
        for verse_tag in verse_tags:
            lacunae_tags = verse_tag.find_all("gap", recursive=False)
            if len(lacunae_tags) > 0:
                if "n" in verse_tag.attrs:
                    verses_with_lacunae.append(verse_tag["n"])

        lac_df = []
        for verse in grouped_df["verse"]:
            if verse in verses_with_lacunae:
                lac_df.append(True)
            else:
                lac_df.append(False)

        grouped_df["lacunae"] = lac_df

    # print(grouped_df)
    return grouped_df


def collate_manuscript_against_byz(manuscript_id, manuscripts_directory, liste):
    """
    Collates a manuscript against Byz.
    """
    # Finding the manuscript's metadata
    liste["primaryName"] = liste["primaryName"].fillna("")
    common_name = list(
        liste[liste["docID"].astype(int).astype(str) == str(int(manuscript_id))][
            "primaryName"
        ].unique()
    )[0]
    if common_name[0] == "L":  # Adding the fancy lectionary L
        common_name = common_name.replace("L", "*ℓ*-")
    elif common_name[0] == "P":  # Adding the fancy papyrus P
        common_name = common_name.replace("P", "𝔓^")
        common_name = common_name + "^"

    common_name = common_name.replace(".0", "")

    overlay = parse_manuscript(
        manuscript_id,
        manuscripts_directory,
        abbreviations_equivalences,
        False,  # Don't standardise spelling
    )

    merged = pd.merge(  # Aligns the verses of Byz and overlay
        byz,
        overlay,
        on=["book", "chapter", "verse"],
        how="outer",
        suffixes=("_byz", "_overlay"),
    )
    merged = merged.dropna(
        subset=["w_tag_overlay"]
    )  # This is done so that only extant verses are shown.
    merged["w_tag_byz"] = merged["w_tag_byz"].fillna("")

    def collate_verse(verse, byz_verse, overlay_verse):
        byz_text = " ".join(byz_verse).replace("\n", "")
        overlay_text = " ".join(overlay_verse).replace("\n", "")

        def extract_tag_texts(text):
            soup = BeautifulSoup(text, "html.parser")
            tag_list = soup.find_all("w")
            text_clean = []
            for w in tag_list:
                text_clean.append(w.text)
            return " ".join(text_clean)

        byz_text_clean = extract_tag_texts(byz_text)
        overlay_text_clean = extract_tag_texts(overlay_text)

        # Removing word markers and line break tags
        def remove_junk_strings(tag_string):
            tag_string = tag_string.replace(' part="F"', "")
            tag_string = tag_string.replace(' part="I"', "")
            tag_string = tag_string.replace('<lb break="no"></lb>', "")
            tag_string = tag_string.replace('<lb break="no"/>', "")
            tag_string = tag_string.replace("<lb/>", "")
            return tag_string

        overlay_text = remove_junk_strings(overlay_text)

        def collate_tagged(byz_text_clean, overlay_text, overlay_text_clean):
            # Split the strings into words
            words1 = byz_text_clean.split()
            words2 = overlay_text_clean.split()

            # Create a Differ object
            differ = difflib.Differ()

            # Compute the differences between the words
            diff = differ.compare(words1, words2)

            # Initialize empty lists for the DataFrame columns
            column_byz = []
            column_overlay = []
            operation = []  # To store the operation (e.g., ' ', '-', '+')

            # Iterate through the differences and populate the lists
            for line in diff:
                if (
                    line[0] != "?"
                ):  # This line tells us where the words differ (character index). Useful maybe for the future, but not for now
                    operation.append(line[0])
                if line[0] == " ":
                    column_byz.append(line[2:])
                    column_overlay.append(line[2:])
                elif line[0] == "-":
                    column_byz.append(line[2:])
                    column_overlay.append("")
                elif line[0] == "+":
                    column_byz.append("")
                    column_overlay.append(line[2:])

            # Create a DataFrame from the lists
            df_coll = pd.DataFrame(
                {
                    "byz_text_clean": column_byz,
                    "overlay_text_clean": column_overlay,
                    "operation": operation,
                }
            )

            # Add overlay_text again to the dataframe, but being mindful of the gaps due to the diffs between byz and overlay

            words_in_overlay_text = BeautifulSoup(overlay_text, "html.parser")
            words_in_overlay_text = words_in_overlay_text.find_all("w")

            # print(words_in_overlay_text, len(words_in_overlay_text))
            # print(df_coll["overlay_text_clean"])

            i = 0
            overlay_text_reconstituted = []
            for text_clean in df_coll["overlay_text_clean"]:
                if text_clean != "":
                    # print(words_in_overlay_text, len(words_in_overlay_text))
                    # print(df_coll["overlay_text_clean"])
                    overlay_text_reconstituted.append(str(words_in_overlay_text[i]))
                    i = i + 1
                else:
                    overlay_text_reconstituted.append("")

            df_coll["overlay_text"] = overlay_text_reconstituted

            # Obtaining the definitive collation
            df_coll = df_coll.astype(str).replace("", np.nan)
            df_coll["collated_text"] = df_coll["overlay_text"].fillna(
                df_coll["byz_text_clean"]
            )
            df_coll["collated_text"] = df_coll["collated_text"].fillna("")

            definitive_collation = []
            added_words = []
            omitted_words = []
            for row in df_coll.iterrows():
                if row[1]["operation"] == "+":
                    definitive_collation.append(
                        "<greek-added>" + row[1]["collated_text"] + "</greek-added>"
                    )
                    added_words.append(row[1]["collated_text"])
                elif row[1]["operation"] == "-":
                    definitive_collation.append(
                        "<greek-omitted>" + row[1]["collated_text"] + "</greek-omitted>"
                    )
                    omitted_words.append(row[1]["collated_text"])
                else:
                    definitive_collation.append(row[1]["collated_text"])

            definitive_collation_string = " ".join(definitive_collation)

            # Print potential instances of iotacism

            # added_word_tags = BeautifulSoup(
            #    " ".join(added_words), "html.parser"
            # ).find_all("w")

            # for added_word_tag in added_word_tags:
            #    if "ει" in added_word_tag.text:
            #        # print(added_word_tag.text, "\t", added_word_tag.text.replace('ι','ει'))
            #        if added_word_tag.text.replace("ει", "ι") in omitted_words:
            #            print(
            #                added_word_tag.text, added_word_tag.text.replace("ει", "ι")
            #            )

            return definitive_collation_string

        return collate_tagged(byz_text_clean, overlay_text, overlay_text_clean)

    # Adding the collation to the merged dataframe
    merged["collations"] = merged.apply(
        lambda row: collate_verse(row["verse"], row["w_tag_byz"], row["w_tag_overlay"]),
        axis=1,
    )

    # Replacing empty incipits with empty strings
    merged["incipit_overlay"] = merged["incipit_overlay"].fillna("")

    # Preprocessing the collation for Quarto
    def preprocess_collation_for_quarto(collation):
        # Removing junk tags

        if "<w" in collation:
            w_soup = BeautifulSoup(collation, "html.parser")
            w_tags = w_soup.find_all("w")
            for w_tag in w_tags:
                collation = collation.replace(str(w_tag), str(w_tag.decode_contents()))

        # Replacing tags with the new syntax

        if "<corr" in collation:
            corr_soup = BeautifulSoup(collation, "html.parser")
            corr_tags = corr_soup.find_all("corr")
            for corr_tag in corr_tags:
                corr_replacement = "[" + str(corr_tag.decode_contents()) + "]{.corr}"
                collation = collation.replace(str(corr_tag), corr_replacement)

        if "<abbr" in collation:
            abbr_soup = BeautifulSoup(collation, "html.parser")
            abbr_tags = abbr_soup.find_all("abbr")
            for abbr_tag in abbr_tags:
                abbr_replacement = (
                    "[" + str(abbr_tag.decode_contents()) + "]{.greek-abbr}"
                )
                collation = collation.replace(str(abbr_tag), abbr_replacement)

        if "<unclear" in collation:
            unclear_soup = BeautifulSoup(collation, "html.parser")
            unclear_tags = unclear_soup.find_all("unclear")
            for unclear_tag in unclear_tags:
                unclear_replacement = (
                    "[" + str(unclear_tag.decode_contents()) + "]{.unclear}"
                )
                collation = collation.replace(str(unclear_tag), unclear_replacement)

        if "<gap" in collation:
            gap_soup = BeautifulSoup(collation, "html.parser")
            gap_tags = gap_soup.find_all("gap")
            for gap_tag in gap_tags:
                collation = collation.replace(str(gap_tag), "[―]{.gap}")

        if "<supplied" in collation:
            supplied_soup = BeautifulSoup(collation, "html.parser")
            supplied_tags = supplied_soup.find_all("supplied")
            for supplied_tag in supplied_tags:
                supplied_replacement = (
                    "[" + str(supplied_tag.decode_contents()) + "]{.greek-supplied}"
                )
                collation = collation.replace(str(supplied_tag), supplied_replacement)

        if "<greek-added" in collation:
            greek_added_soup = BeautifulSoup(collation, "html.parser")
            greek_added_tags = greek_added_soup.find_all("greek-added")
            for greek_added_tag in greek_added_tags:
                greek_added_replacement = (
                    "[" + str(greek_added_tag.decode_contents()) + "]{.greek-added}"
                )
                collation = collation.replace(
                    str(greek_added_tag), greek_added_replacement
                )

        if "<greek-omitted" in collation:
            greek_omitted_soup = BeautifulSoup(collation, "html.parser")
            greek_omitted_tags = greek_omitted_soup.find_all("greek-omitted")
            for greek_omitted_tag in greek_omitted_tags:
                greek_omitted_replacement = (
                    "[" + str(greek_omitted_tag.decode_contents()) + "]{.greek-omitted}"
                )
                collation = collation.replace(
                    str(greek_omitted_tag), greek_omitted_replacement
                )

        if ("<" in collation) or (">" in collation):
            raise Exception("I detected forbidden characters in", collation)

        return collation

    merged["collations_quarto"] = merged["collations"].apply(
        preprocess_collation_for_quarto
    )

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

    merged = merged.dropna(subset=["book", "chapter", "verse"], how="any")

    merged["book_name"] = merged["book"].replace(book_dict)

    # Adding book, chapter and verse numbers
    def add_numerical_book(book):
        # print(book)
        return int(book[1:])

    def add_numerical_chapter(chapter, incipit_overlay):
        if incipit_overlay[-7:] == "incipit":
            return -1
        else:
            return int(chapter.split("K")[1])

    def add_numerical_verse(verse, incipit_overlay):
        if incipit_overlay[-7:] == "incipit":
            return -1
        elif verse.split("V")[1].isdigit():
            return int(verse.split("V")[1])
        else:
            return 999

    def extract_string_verse(verse, incipit_overlay):
        if verse == "":
            return verse
        elif incipit_overlay[-7:] == "incipit":
            return ""
        else:
            return verse.split("V")[1]

    merged["book_number"] = merged["book"].apply(add_numerical_book)

    merged["chapter_number"] = merged.apply(
        lambda row: add_numerical_chapter(row["chapter"], row["incipit_overlay"]),
        axis=1,
    )
    merged["verse_string_extracted"] = merged.apply(
        lambda row: extract_string_verse(row["verse"], row["incipit_overlay"]), axis=1
    )
    merged["verse_number"] = merged.apply(
        lambda row: add_numerical_verse(row["verse"], row["incipit_overlay"]), axis=1
    )
    merged = merged.drop(columns=["instance_byz"])
    merged = merged.rename(columns={"instance_overlay": "instance"})
    merged = merged.sort_values(
        by=["book_number", "chapter_number", "verse_number", "instance"]
    )

    # Adding book changes
    merged["book_change"] = ""

    previous_book = None
    for index, row in merged.iterrows():
        current_book = row["book_number"]
        if current_book != previous_book:
            merged.at[index, "book_change"] = current_book
            previous_book = current_book

    # Adding chapter changes
    merged["chapter_change"] = ""

    previous_chapter = None
    for index, row in merged.iterrows():
        current_chapter = row["chapter_number"]
        if current_chapter != previous_chapter:
            merged.at[index, "chapter_change"] = current_chapter
            previous_chapter = current_chapter

    def add_coordinates_metadata(
        book_name,
        book_change,
        chapter_change,
        chapter_number,
        verse_string_extracted,
        verse_number,
        instance,
        incipit,
        collation_quarto,
        lacunae,
    ):
        if instance > 1:
            verse_string_extracted = (
                f"{verse_string_extracted} | instance no. {int(instance)}"
            )

        prefix = ""
        suffix = ""

        if book_change != "":
            prefix = prefix + "## " + book_name + "\n\n"

        if incipit[-7:] == "incipit":
            if lacunae == True:
                suffix = "[[incipit *(lacunose)*]{.lacunose}]{.aside}\n"

            else:
                suffix = "[incipit]{.aside}\n"
        else:
            if lacunae == True:
                suffix = (
                    "[["
                    + str(chapter_number)
                    + ":"
                    + verse_string_extracted
                    + " *(lacunose)*]{.lacunose}]{.aside}\n"
                )
            else:
                suffix = (
                    "["
                    + str(chapter_number)
                    + ":"
                    + verse_string_extracted
                    + "]{.aside}\n"
                )

        if chapter_change != "":
            if incipit[-7:] != "incipit":
                prefix = prefix + "### Chapter " + str(chapter_change) + "\n\n"

        return prefix + collation_quarto + suffix

    merged["collations_quarto"] = merged.apply(
        lambda row: add_coordinates_metadata(
            row["book_name"],
            row["book_change"],
            row["chapter_change"],
            row["chapter_number"],
            row["verse_string_extracted"],
            row["verse_number"],
            row["instance"],
            row["incipit_overlay"],
            row["collations_quarto"],
            row["lacunae"],
        ),
        axis=1,
    )

    manuscript_qmd = f"""---
title: "Collation of Byz^RP^ vs {manuscript_id} ({common_name})"
author: ""
date: ""
toc: true
toc-title: Contents
---

::: {{.callout-note appearance="minimal" icon="false" collapse="true"}}
# Links to official texts

Read {common_name} in the INTF website [here](https://ntvmr.uni-muenster.de/manuscript-workspace?docID={manuscript_id}).

Download the Robinson-Pierpont 2018 edition of the Byzantine textform [here](https://web.archive.org/web/20210413060536/https://byzantinetext.com/wp-content/uploads/2021/03/robinson-pierpont-2018-gnt-edition.pdf).


:::


::: {{.callout-note appearance="minimal" icon="false" collapse="true"}}
# Conventions

| Description                                                              	| Examples                           	|
|--------------------------------------------------------------------------	|------------------------------------	|
| Word in both Byz^RP^ and {common_name}                                   	| λογος                              	|
| {common_name} *adds* (word not present in Byz^RP^)                       	| [λογος]{{.greek-added}}            	|
| {common_name} *omits* (word present in Byz^RP^)                          	| [λογος]{{.greek-omitted}}          	|
| Text fragmentary, supplied by transcriber of {common_name}               	| [λογος]{{.greek-supplied}}         	|
| Text unclear, supplied by transcriber of {common_name}                   	| [λογος]{{.unclear}}                	|
| Corrector's hand is superscript (corrector agrees with Byz^RP^)          	| [λογος]{{.corr}}                   	|
| Corrector's hand is superscript (corrector adds, not present in Byz^RP^) 	| [[λογος]{{.corr}}]{{.greek-added}} 	|
| {common_name} abbreviates *nomen sacrum*                                 	| [θεος]{{.greek-abbr}}            	|
| Gap in {common_name}                                                     	| [―]{{.gap}}                        	|
:::

"""

    for collated_verse in merged["collations_quarto"]:
        manuscript_qmd = manuscript_qmd + collated_verse + "\n"

    log_for_manuscript_verse_relation = merged[
        ["book", "chapter_number", "verse_number"]
    ]
    log_for_manuscript_verse_relation["manuscript_id"] = manuscript_id
    log_for_manuscript_verse_relation = log_for_manuscript_verse_relation[
        ["manuscript_id", "book", "chapter_number", "verse_number"]
    ]

    log_for_manuscript_verse_relation.to_csv(
        f"manuscript_verses_logs/{manuscript_id}.csv", index=False
    )

    with open(f"../collations/{manuscript_id}.qmd", "w") as file:
        file.write(manuscript_qmd)


# Get the current directory
current_directory = os.getcwd()

# Go up one folder
parent_directory = os.path.dirname(current_directory)

# Define the path to the manuscripts folder
manuscripts_directory = os.path.join(parent_directory, "raw_data", "manuscripts")

# Define the path to the processed CSVs folder
csvs_directory = os.path.join(parent_directory, "processed_manuscripts")

# Read abbreviations equivalences
abbreviations_equivalences = pd.read_csv("abbreviations_equivalences.csv")

# Read spelling equivalences
spelling_equivalences = pd.read_csv("spelling_equivalences.csv")

# Read Liste
liste = pd.read_csv("../raw_data/liste/liste.csv", dtype={"docID": int})

byz = parse_manuscript("BYZ", manuscripts_directory, abbreviations_equivalences, False)


# Make a list of the manuscripts

# List all files in the folders
files = os.listdir(manuscripts_directory)
files_collations_qmd = os.listdir("../collations")

# Filter for .xml files
xml_files = [file for file in files if file.endswith(".xml")]

# Filter for .qmd files
qmd_files = [file for file in files_collations_qmd if file.endswith(".qmd")]

# Some manuscripts have XML errors
manuscripts_with_xml_errors = pd.read_csv("manuscripts_with_xml_errors.csv")
manuscripts_with_xml_errors = list(
    manuscripts_with_xml_errors["manuscript_id"].astype(str)
)


manuscript_ids = []
for xml_file in xml_files:
    if "BYZ" in xml_file:
        pass
    else:
        manuscript_ids.append(xml_file.replace(".xml", ""))

# manuscript_ids = ['10046', '20001', '20002', '20003', '10016', '10061', '40169']

for manuscript_id in manuscript_ids:
    with open(manuscripts_directory + "/" + manuscript_id + ".xml", "r") as file:
        file_contents = file.read()

        man_soup = BeautifulSoup(file_contents, "xml")
        word_tags = man_soup.find_all("w")

        if manuscript_id + ".qmd" in qmd_files:
            collate_manuscript_against_byz(manuscript_id, manuscripts_directory, liste)
            # print("\t", manuscript_id, "already present in folder, skipping")
        elif manuscript_id in manuscripts_with_xml_errors:
            print("\t", manuscript_id, "has XML errors, skipping")
        elif "No Transcription Available" in file_contents:
            print("\t", manuscript_id, "has no transcription available, skipping")
        elif len(word_tags) == 0:
            print("\t", manuscript_id, "has no words available, skipping")
        else:
            # try:
            collate_manuscript_against_byz(manuscript_id, manuscripts_directory, liste)
            # except:
            #    print("Error in processing", manuscript_id)
            #    with open('manuscripts_with_xml_errors.csv', 'a') as file:
            #        file.write(manuscript_id + '\n')
