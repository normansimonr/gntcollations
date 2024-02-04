import re
import collatex
import difflib
import pandas as pd
import roman
import json
import itertools

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

# Analysis


def extract_text_between_substrings(text, book_name):
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
    df[["parsed_greek", "coordinates"]] = df[0].str.extract(
        r"^(.*?)(\[\d+:\d+\]\{.*?\})$"
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
    df = df[["chapter", "verse", "parsed_greek"]]
    if str(chapter) in df["chapter"].unique():
        if str(verse) in df[df["chapter"] == str(chapter)]["verse"].unique():
            return df[(df["chapter"] == str(chapter)) & (df["verse"] == str(verse))]
    else:
        return None


##### Reading in the data

yaml_section = """
---
format: html
editor: 
    markdown: 
        wrap: 72
---
"""

for book_name in ["The Gospel of Mark"]:  # manuscript_attestation.keys():
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
        "Second Timoty": "2TI",
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
        "Phillipians": "PHP",
        "Revelation": "REV",
        "Romans": "ROM",
        "Titus": "TIT",
    }

    byz = pd.read_csv(f"../byz_csv/{byz_book_abbrs[book_name]}.csv")

    book_qmd_string = yaml_section + f"\n\n# {book_name}\n\n"

    for chapter in [15]:  # manuscript_attestation[book_name].keys():
        print(f"Processing chapter {chapter}")
        verses = manuscript_attestation[book_name][chapter].keys()

        chapter_qmd_string = f"## Chapter {chapter}\n\n"

        for verse in [19]:  # verses:
            print(f"Processing verse {chapter}:{verse}")
            manuscripts_attesting_this_verse = manuscript_attestation[book_name][
                chapter
            ][verse]

            verse_attestation = []

            for manuscript_id in manuscripts_attesting_this_verse:
                # print("Processing", manuscript_id)
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
                    parsed_greek = this_verse_text_and_coordinates["parsed_greek"].iloc[
                        0
                    ]

                    # Replacing unclear and supplied words

                    verse_attestation.append(
                        [
                            manuscript_id,
                            chapter,
                            verse,
                            parsed_greek,
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

            verse_attestation.append(["Byz", chapter, verse, byz_verse])

            verse_attestation = pd.DataFrame(verse_attestation)
            verse_attestation.columns = [
                "manuscript_id",
                "chapter",
                "verse",
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

            # Collation
            # Cleaning the texts
            def clean_text(text):
                pattern_omitted = r"\[[^\]]+\]\{\.greek-omitted\}"
                cleaned_string = re.sub(pattern_omitted, "", text)
                pattern_supplied = r"\[[^\]]+\]\{\.greek-supplied\}"
                cleaned_string = re.sub(pattern_supplied, "U", cleaned_string)
                pattern_unclear = r"\[[^\]]+\]\{\.unclear\}"
                cleaned_string = re.sub(pattern_unclear, "U", cleaned_string)
                cleaned_string = cleaned_string.replace("{.greek-added}", "")
                cleaned_string = cleaned_string.replace(
                    "{.greek-abbr}", ""
                )  # Removing the nomina sacra marker
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

            corrected_temp["parsed_greek_clean"] = corrected_temp[
                "parsed_greek_clean"
            ].apply(remove_corrections)
            corrected_temp["uncorrected_reconstructed"] = True

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

            # Removing fragmentary manuscripts
            def define_if_too_fragmentary(text):
                num_words = len(text.split())
                words_unclear_or_supplied = []
                for word in text.split():
                    if "U" in word:
                        words_unclear_or_supplied.append(word)
                num_words_unclear_or_supplied = len(words_unclear_or_supplied)
                threshold = 0.6
                if (num_words_unclear_or_supplied / num_words) > threshold:
                    return True
                else:
                    return False

            verse_attestation["too_fragmentary"] = verse_attestation[
                "parsed_greek_clean"
            ].apply(define_if_too_fragmentary)

            fragmentary_manuscripts = verse_attestation[
                verse_attestation["too_fragmentary"]
            ]
            non_fragmentary_manuscripts = verse_attestation[
                ~verse_attestation["too_fragmentary"]
            ]

            num_manuscripts_attesting_this_verse_corrected = len(
                non_fragmentary_manuscripts[
                    non_fragmentary_manuscripts["has_corrections"]
                ]
            )

            # Manuscript groups
            manuscript_groups = (
                non_fragmentary_manuscripts[["manuscript_id", "parsed_greek_clean"]]
                .groupby("parsed_greek_clean")["manuscript_id"]
                .apply(list)
                .reset_index()
            )
            manuscript_groups["group_size"] = manuscript_groups["manuscript_id"].apply(
                len
            )
            manuscript_groups = manuscript_groups.sort_values(
                by=["group_size"], ascending=False
            )

            manuscript_groups["contains_byz"] = manuscript_groups[
                "manuscript_id"
            ].apply(lambda x: True if "Byz" in x else False)

            unanimous_group = manuscript_groups[manuscript_groups["contains_byz"]]
            unanimous_group["manuscript_id"] = unanimous_group["manuscript_id"].apply(
                lambda mlist: [x for x in mlist if x != "Byz"]
            )  # Removing Byz to avoid counting it as a witness
            unanimous_group["group_size"] = unanimous_group["manuscript_id"].apply(len)
            unanimous_group_badge = (
                f"→**unanimous**~{byz_book_abbrs[book_name].lower()}.{chapter}.{verse}~"
            )
            unanimous_group["group_name"] = unanimous_group_badge

            manuscript_groups = manuscript_groups[~manuscript_groups["contains_byz"]]

            middle_sized_groups = manuscript_groups[
                manuscript_groups["group_size"] >= 2
            ]
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
            middle_sized_groups["group_name"] = index_chars[: len(middle_sized_groups)]

            one_sized_groups = manuscript_groups[manuscript_groups["group_size"] == 1]
            one_sized_groups["group_name"] = one_sized_groups["manuscript_id"].apply(
                lambda x: x[0]
            )

            manuscript_groups = pd.concat(
                [unanimous_group, middle_sized_groups, one_sized_groups]
            )

            # print(manuscript_groups)

            collation = collatex.Collation()

            for index, row in manuscript_groups.iterrows():
                print(
                    book_name,
                    chapter,
                    verse,
                    row["group_name"],
                    row["parsed_greek_clean"],
                )
                collation.add_plain_witness(
                    row["group_name"], row["parsed_greek_clean"]
                )

            collatex_output = collatex.collate(
                collation, layout="vertical", near_match=True, segmentation=False
            )

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
                df = pd.DataFrame(data[1:], columns=data[0])

                return df

            alignment_table = collatex_output_to_df(collatex_output).T

            # Removing unwanted NAs
            alignment_table = alignment_table.fillna("-")
            alignment_table = alignment_table.replace("-", pd.NA).dropna(
                axis=1, how="all"
            )
            alignment_table.columns = range(len(alignment_table.columns))
            alignment_table = alignment_table.fillna("•")

            # Find the base column (Byz)
            byz_column_base = alignment_table.loc[unanimous_group_badge]

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

            ##### Counting the manuscripts and ignoring fragmentary ones

            num_witnesses_attesting_this_verse_including_corrected = (
                len(verse_attestation) - 1
            )  # We subtract one to avoid counting Byz as a manuscript

            num_fragmentary_manuscripts_this_verse = len(fragmentary_manuscripts)

            # Determining which Byzantine readings are not attested in the sample
            # TO DO

            ##### Creating the QMD code

            liste = pd.read_csv(
                "../raw_data/liste/liste.csv", usecols=["docID", "origLate"]
            )
            liste["docID"] = liste["docID"].astype(int).astype(str)

            # Function to convert year to century
            def year_to_century(year):
                return (year - 1) // 100 + 1

            liste["century_late"] = liste["origLate"].astype(int).apply(year_to_century)
            liste["century_late_roman"] = liste["century_late"].apply(roman.toRoman)

            def format_manuscript_coincidences_for_quarto(manuscript_coincidence):
                formatted_manuscript_coincidence = []
                standalone_manuscript_ids = []
                corrected_manuscripts_ids = []
                for coincidence in manuscript_coincidence:
                    if coincidence[0] == "→":
                        formatted_manuscript_coincidence.append(coincidence)
                    elif "^c^" in coincidence:
                        corrected_manuscripts_ids.append(coincidence)
                    else:
                        standalone_manuscript_ids.append(coincidence)

                formatted_manuscript_coincidence = " ".join(
                    formatted_manuscript_coincidence
                )

                standalone_manuscripts = liste[
                    liste["docID"].isin(standalone_manuscript_ids)
                ]
                standalone_manuscripts = (
                    standalone_manuscripts[["docID", "century_late"]]
                    .groupby("century_late", group_keys=False)["docID"]
                    .apply(list)
                    .reset_index()
                )

                def add_link_to_manuscript_id(manuscript_id):
                    if "^c^" in manuscript_id:
                        manuscript_id = manuscript_id.replace("^c^", "")
                        manuscript_handle = manuscript_id + "^c^"
                    else:
                        manuscript_handle = manuscript_id

                    if "^c^" in manuscript_handle:
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

                standalone_manuscripts_formatted_string = ""
                if len(standalone_manuscripts) > 0:
                    standalone_manuscripts["formatted_ids"] = (
                        standalone_manuscripts["docID"]
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

                corrected_manuscripts_formatted_string = ""
                if len(corrected_manuscripts_ids) > 0:
                    corrected_manuscripts_formatted_string = (
                        "[Corr.]{.correction-label-apparatus}: "
                        + " ".join(
                            add_link_to_manuscript_id(manuscript_id)
                            for manuscript_id in corrected_manuscripts_ids
                        )
                    )

                first_separator = ""
                second_separator = ""

                if len(formatted_manuscript_coincidence.strip()) > 0:
                    first_separator = " || "

                if len(standalone_manuscripts_formatted_string.strip()) > 0:
                    if len(corrected_manuscripts_formatted_string.strip()) > 0:
                        second_separator = " || "

                return (
                    formatted_manuscript_coincidence
                    + first_separator
                    + standalone_manuscripts_formatted_string
                    + second_separator
                    + corrected_manuscripts_formatted_string
                )

            textual_units["formatted_manuscript_coincidence"] = textual_units[
                "manuscript_coincidence"
            ].apply(format_manuscript_coincidences_for_quarto)

            ##### Creating the QMD

            byz_qmd_string = f"\n\n### Verse {chapter}:{verse}\n\n"

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
                byz_qmd_string = byz_qmd_string + "["
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

            initial_callout = (
                '::: {.callout-note  collapse="true" icon="false"}\n## Witness counts\n'
            )

            num_manuscripts_attesting_this_verse_not_including_corrected = (
                num_witnesses_attesting_this_verse_including_corrected
                - num_manuscripts_attesting_this_verse_corrected
            )

            this_verse_collation_string = (
                this_verse_collation_string
                + initial_callout
                + f"Number of manuscripts that contain this verse: {num_manuscripts_attesting_this_verse_not_including_corrected}\n\n"
            )

            if num_fragmentary_manuscripts_this_verse > 0:
                manuscripts_exluded_too_fragmentary = fragmentary_manuscripts[
                    "manuscript_id"
                ].to_list()
                manuscripts_exluded_too_fragmentary_string = (
                    f"Manuscripts *ignored* due to being too fragmentary ({num_fragmentary_manuscripts_this_verse}): "
                    + format_manuscript_coincidences_for_quarto(
                        manuscripts_exluded_too_fragmentary
                    )
                )
                this_verse_collation_string = (
                    this_verse_collation_string
                    + "\n\n"
                    + manuscripts_exluded_too_fragmentary_string
                    + "\n"
                )

            if num_manuscripts_attesting_this_verse_corrected > 0:
                manuscripts_duplicated_corrected = verse_attestation[
                    verse_attestation["has_corrections"]
                    & ~verse_attestation["uncorrected_reconstructed"]
                ]["manuscript_id"].to_list()
                manuscripts_duplicated_corrected_string = (
                    f"Manuscripts *included twice* due to having corrected hands ({num_manuscripts_attesting_this_verse_corrected}): "
                    + format_manuscript_coincidences_for_quarto(
                        manuscripts_duplicated_corrected
                    )
                )
                this_verse_collation_string = (
                    this_verse_collation_string
                    + "\n\n"
                    + manuscripts_duplicated_corrected_string
                    + "\n"
                )

            num_witnesses_included_in_collation = (
                num_manuscripts_attesting_this_verse_not_including_corrected
                - num_fragmentary_manuscripts_this_verse
                + num_manuscripts_attesting_this_verse_corrected
            )

            witnesses_taken_into_account_string = f"**Number of witnesses that were taken into account in the collation: {num_witnesses_included_in_collation}**\n\n(The total number of witnesses is calculated as the total manuscripts minus the fragmentary manuscripts plus the corrected hands.)"
            this_verse_collation_string = (
                this_verse_collation_string
                + "\n\n"
                + witnesses_taken_into_account_string
                + "\n\n"
            )

            final_callout = "\n:::\n\n"

            this_verse_collation_string = this_verse_collation_string + final_callout

            #######################################
            #######################################
            ## Creating the nomina sacra callout ##
            #######################################
            #######################################
            if is_abbreviation_present:
                this_verse_collation_string = (
                    this_verse_collation_string
                    + '::: {.callout-warning collapse="true" icon="false"}\n## *Nomina sacra* or abbreviations\nPlease note that one or more of the manuscripts contains *nomina sacra* which have been spelled out by our automated algorithm. This process is very accurate, but occasional mistakes can happen, especially with obscure or uncommon *nomina sacra*. In case of doubt about the actual reading of a *nomen sacrum*, please consult the original transcripts or facsimiles.\n:::\n\n'
                )

            ######################################
            ######################################
            ## Creating the corrections callout###
            ######################################
            ######################################

            if num_manuscripts_attesting_this_verse_corrected > 0:
                this_verse_collation_string = (
                    this_verse_collation_string
                    + '::: {.callout-important collapse="true" icon="false"}\n## Potentially inaccurate\nOne or more of the witnesses included in the collation are corrected. Due to the limitations of the TEI-XML format, it is not possible to automatically reconstruct the corrected hand perfectly. For this reason, the apparatus may display inaccuracies. The corrected hands have been marked with a ? symbol in order to highlight this uncertainty.\n:::\n\n'
                )

            ######################################
            ######################################
            ##### Creating the groups callout ####
            ######################################
            ######################################

            unanimous_group_size = unanimous_group["group_size"].iloc[0]
            middle_sized_groups_size = middle_sized_groups["group_size"].sum()
            one_sized_groups_size = one_sized_groups["group_size"].sum()

            initial_callout = (
                '::: {.callout-tip collapse="true" icon="false"}\n## Witness groups\n\n'
            )

            initial_callout = (
                initial_callout
                + f"The below groups show witnesses that share identical texts for the entire verse. That is, any two witnesses belong in the same group if their texts are identical for the entire verse. There are {unanimous_group_size + middle_sized_groups_size} witnesses in groups for this verse. For these, the apparatus lists the group instead of the individual witnesses. The group names are assigned automatically and their composition may change as new manuscripts are added to the collation in future. The remaining witnesses ({one_sized_groups_size}) attest to singular texts for the entire verse and are therefore not part of any group. These non-aligned witnesses are individually shown in the apparatus.\n"
            )

            # Unanimous group
            manuscripts_verse_identical_to_byz_string = f"\n**Witnesses that attest a verse identical with Byz^RP^, or 'unanimous' ({unanimous_group_badge}) group ({unanimous_group_size})**: "

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
                    other_groups_string = (
                        other_groups_string
                        + f"{row['group_name']} **group**, attesting to {row['parsed_greek_clean']}, ({row['group_size']}): {format_manuscript_coincidences_for_quarto(row['manuscript_id'])}\n\n"
                    )

            this_verse_collation_string = (
                this_verse_collation_string + "\n\n" + other_groups_string + ":::\n\n"
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

            apparatus_string = ""

            for position in range(len(byz_column_base)):
                footnote_marker = position + 1

                # Byzantine reading
                witnesses_supporting_this_byzantine_reading = textual_units[
                    (textual_units["position"] == position)
                    & (textual_units["is_byzantine"] == True)
                ]["manuscript_coincidence"].iloc[0]

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

        book_qmd_string = book_qmd_string + chapter_qmd_string

    with open(
        f"../apparatus/{book_name.lower().replace(' ','_')}.qmd", "w", encoding="utf-8"
    ) as file:
        file.write(book_qmd_string)
