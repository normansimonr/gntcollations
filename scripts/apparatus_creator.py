import re
import collatex
import difflib
import pandas as pd
import roman

third_john_manuscript_attestation = (
    {  # This dictionary was manually created by inspecting the manuscripts one by one
        1: {
            1: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            2: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            3: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            4: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            5: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            6: [10074, 20001, 20002, 20003, 20020, 20044, 30424, 30630],
            7: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            8: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            9: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            10: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            11: [20001, 20002, 20003, 20020, 20044, 30424, 30630],
            12: [10074, 20001, 20002, 20003, 20020, 20044, 20251, 30424, 30630],
            13: [20001, 20002, 20003, 20020, 20044, 20251, 30424, 30630],
            14: [20001, 20002, 20003, 20020, 20044, 20251, 30424, 30630],
            15: [20001, 20002, 20003, 20020, 20044, 20251, 30424, 30630],
        }
    }
)


# Analysis


def extract_text_between_substrings(text):
    start_substring = "## Third John"
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
        raise ValueError("Starting substring '## Third John' not found")


def extract_verse_from_qmd(qmd_content, chapter, verse):
    this_books_content = extract_text_between_substrings(qmd_content)
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

byz = pd.read_csv("../byz_csv/3JO.csv")

yaml_section = """
---
format: html
editor: 
  markdown: 
    wrap: 72
---
"""

book_qmd_string = yaml_section + "\n\n# Third John\n\n"

for chapter in third_john_manuscript_attestation.keys():
    print(f"Processing chapter {chapter}")
    verses = third_john_manuscript_attestation[chapter].keys()

    chapter_qmd_string = f"## Chapter {chapter}\n\n"

    for verse in verses:
        print(f"Processing verse {chapter}:{verse}")
        manuscripts_attesting_this_verse = third_john_manuscript_attestation[chapter][
            verse
        ]

        verse_attestation = []

        for manuscript_id in manuscripts_attesting_this_verse:
            # print("Processing", manuscript_id)
            # Read the QMD file
            with open(
                "../collations/" + str(manuscript_id) + ".qmd", "r", encoding="utf-8"
            ) as file:
                qmd_content = file.read()

            this_verse_text_and_coordinates = extract_verse_from_qmd(
                qmd_content, chapter, verse
            )

            if isinstance(this_verse_text_and_coordinates, pd.DataFrame):
                parsed_greek = this_verse_text_and_coordinates["parsed_greek"].iloc[0]

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
        verse_attestation["manuscript_id"] = verse_attestation["manuscript_id"].astype(
            str
        )

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

        num_manuscripts_attesting_this_verse_corrected = len(
            verse_attestation[verse_attestation["has_corrections"]]
        )

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

        def add_stars(row):
            if "C" in row["parsed_greek_clean"]:
                return row["manuscript_id"] + "^\*^"
            else:
                return row["manuscript_id"]

        verse_attestation["manuscript_id"] = verse_attestation.apply(add_stars, axis=1)
        verse_attestation["parsed_greek_clean"] = verse_attestation[
            "parsed_greek_clean"
        ].str.replace(
            "C", ""
        )  # Removing the C marker from the starred hands

        verse_attestation = pd.concat([verse_attestation, corrected_temp])
        del corrected_temp

        collation = collatex.Collation()

        for index, row in verse_attestation.iterrows():
            collation.add_plain_witness(row["manuscript_id"], row["parsed_greek_clean"])

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
        alignment_table = alignment_table.replace("-", pd.NA).dropna(axis=1, how="all")
        alignment_table.columns = range(len(alignment_table.columns))
        alignment_table = alignment_table.fillna("•")

        # Merging contiguous unanimous attestations
        alignment_table = alignment_table.T

        # Function to check if all elements in a row are identical
        def is_unanimous(row):
            return row.nunique() == 1

        # Create a new column 'is_unanimous'
        alignment_table["is_unanimous"] = alignment_table.apply(is_unanimous, axis=1)

        # Function to split DataFrame into chunks based on 'is_unanimous' column
        def split_dataframe(df):
            chunks = []
            temp_chunk = []
            for index, row in df.iterrows():
                if row["is_unanimous"]:
                    temp_chunk.append(row[:-1])
                else:
                    if temp_chunk:
                        chunks.append(pd.DataFrame(temp_chunk))
                        temp_chunk = []
                    chunks.append(pd.DataFrame([row[:-1]]))
            if temp_chunk:
                chunks.append(pd.DataFrame(temp_chunk))
            return chunks

        # Function to merge rows within each chunk and concatenate contents
        def merge_rows_within_chunks(chunks):
            merged_chunks = []
            for chunk in chunks:
                if (
                    len(chunk) > 1
                ):  # If there is a contiguous number of words that are unanimous
                    byz_chunk = " ".join(chunk["Byz"].to_list())
                    for column in chunk.columns:
                        chunk[column].iloc[:] = byz_chunk
                    chunk = chunk.drop_duplicates()
                merged_chunks.append(chunk)
            return merged_chunks

        # Split DataFrame into chunks based on 'is_unanimous' and merge rows within each chunk
        split_chunks = split_dataframe(alignment_table)
        merged_rows = merge_rows_within_chunks(split_chunks)

        # Concatenate the chunks back into a single DataFrame
        alignment_table = pd.concat(merged_rows, ignore_index=True)
        alignment_table = alignment_table.T

        # Find the string containing 'Byz'
        col_that_includes_byz = [
            string for string in alignment_table.index if "Byz" in string
        ]

        if len(col_that_includes_byz) == 1:
            col_that_includes_byz = col_that_includes_byz[0]
        else:
            raise ValueError(
                "No unique string found containing 'Byz' or multiple strings found."
            )

        byz_column_base = alignment_table.loc[col_that_includes_byz]

        textual_units = []
        for column_name in alignment_table.columns:
            textual_unit = alignment_table[column_name].reset_index()
            textual_unit.columns = ["manuscript_list", "reading"]
            textual_unit = (
                textual_unit.groupby("reading")["manuscript_list"].agg(list).to_frame()
            )
            textual_unit["position"] = column_name
            textual_units.append(textual_unit)

        textual_units = pd.concat(textual_units)
        textual_units["is_byzantine"] = textual_units["manuscript_list"].apply(
            lambda x: True if "Byz" in x else False
        )

        # Determining which manuscripts have a text identical to Byz
        verse_attestation["verse_identical_to_byz"] = (
            verse_attestation["parsed_greek_clean"] == byz_verse
        )
        manuscripts_verse_identical_to_byz = verse_attestation[
            verse_attestation["verse_identical_to_byz"] == True
        ]["manuscript_id"]
        manuscripts_verse_identical_to_byz = list(manuscripts_verse_identical_to_byz)
        manuscripts_verse_identical_to_byz.pop(
            manuscripts_verse_identical_to_byz.index("Byz")
        )

        ##### Counting the manuscripts and ignoring fragmentary ones

        num_manuscripts_attesting_this_verse = (
            len(verse_attestation) - 1
        )  # We subtract one to avoid counting Byz as a manuscript

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

        num_fragmentary_manuscripts_this_verse = (
            verse_attestation["too_fragmentary"].astype(int).sum()
        )

        # Determining if Byz is the majority text in this verse
        num_manuscripts_included_in_collation = (
            num_manuscripts_attesting_this_verse
            - num_fragmentary_manuscripts_this_verse
        )

        if (num_manuscripts_included_in_collation % 2) == 0:
            majority_rule_threshold = (num_manuscripts_included_in_collation / 2) + 1
        else:
            majority_rule_threshold = (num_manuscripts_included_in_collation + 1) / 2

        textual_units["num_manuscripts_supporting_this_reading"] = textual_units[
            "manuscript_list"
        ].apply(len)
        textual_units["num_manuscripts_supporting_this_reading"] = textual_units[
            "num_manuscripts_supporting_this_reading"
        ] - textual_units["is_byzantine"].astype(int)
        textual_units["is_majority_reading"] = (
            textual_units["num_manuscripts_supporting_this_reading"]
            >= majority_rule_threshold
        )

        if (
            len(
                textual_units[
                    textual_units["is_byzantine"]
                    & ~textual_units["is_majority_reading"]
                ]
            )
            == 0
        ):
            byzantine_is_majority_in_this_verse = True
        else:
            byzantine_is_majority_in_this_verse = False

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

        def format_manuscript_id_for_quarto(manuscript_id):
            if manuscript_id == "Byz":
                return manuscript_id
            elif "^\*^" in manuscript_id:
                manuscript_id = manuscript_id.replace("^\*^", "")
                manuscript_handle = manuscript_id + "^\*^"
            else:
                manuscript_handle = manuscript_id

            roman_century = liste[liste["docID"] == manuscript_id][
                "century_late_roman"
            ].iloc[0]

            manuscript_handle = manuscript_handle + "(" + roman_century + ")"

            if "^\*^" in manuscript_handle:
                manuscript_handle = "*" + manuscript_handle + "?*"

            url = f"https://www.gntcollations.com/collations/{manuscript_id}.html"

            return (
                "[[" + manuscript_handle + "](" + url + ")]{.apparatus-manuscript-link}"
            )

        ##### Assign a string to the below variable if you want to add a Majority Text marker

        if num_manuscripts_attesting_this_verse_corrected > 0:
            majority_siglum = ""
        elif byzantine_is_majority_in_this_verse:
            majority_siglum = ""
        else:
            majority_siglum = ""

        byz_qmd_string = f"\n\n### Verse {chapter}:{verse}{majority_siglum}\n\n"

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

        ######################################
        ######################################
        ## Creating the witness count callout#
        ######################################
        ######################################

        initial_callout = (
            '::: {.callout-note  collapse="true" icon="false"}\n## Witness counts\n'
        )

        num_manuscripts_attesting_this_verse_minus_corrected = (
            num_manuscripts_attesting_this_verse
            - num_manuscripts_attesting_this_verse_corrected
        )

        this_verse_collation_string = (
            this_verse_collation_string
            + initial_callout
            + f"Number of manuscripts that contain this verse: {num_manuscripts_attesting_this_verse_minus_corrected}\n\n"
        )

        if num_fragmentary_manuscripts_this_verse > 0:
            manuscripts_exluded_too_fragmentary = verse_attestation[
                verse_attestation["too_fragmentary"]
            ]["manuscript_id"].to_list()
            manuscripts_exluded_too_fragmentary_string = (
                f"Manuscripts *ignored* due to being too fragmentary ({num_fragmentary_manuscripts_this_verse}): "
                + " ".join(
                    [
                        format_manuscript_id_for_quarto(item)
                        for item in manuscripts_exluded_too_fragmentary
                    ]
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
                + " ".join(
                    [
                        format_manuscript_id_for_quarto(item)
                        for item in manuscripts_duplicated_corrected
                    ]
                )
            )
            this_verse_collation_string = (
                this_verse_collation_string
                + "\n\n"
                + manuscripts_duplicated_corrected_string
                + "\n"
            )

        hands_taken_into_account = f"**Number of witnesses that were taken into account in the collation: {num_manuscripts_included_in_collation}**\n\n(The total number of witnesses is calculated as the total manuscripts minus the fragmentary manuscripts plus the corrected hands.)"
        this_verse_collation_string = (
            this_verse_collation_string + "\n\n" + hands_taken_into_account + "\n\n"
        )

        final_callout = "\n:::\n"

        this_verse_collation_string = this_verse_collation_string + final_callout

        ######################################
        ######################################
        ### Creating the unanimous callout####
        ######################################
        ######################################
        if len(manuscripts_verse_identical_to_byz) > 0:
            initial_callout = (
                '::: {.callout-tip collapse="true" icon="false"}\n## Unanimous group\n'
            )
            manuscripts_verse_identical_to_byz_string = f"\nManuscripts that attest a verse identical with Byz^RP^, or 'unanimous' group ({len(manuscripts_verse_identical_to_byz)}): "

            manuscripts_verse_identical_to_byz_string = (
                manuscripts_verse_identical_to_byz_string
                + " ".join(
                    [
                        format_manuscript_id_for_quarto(item)
                        for item in manuscripts_verse_identical_to_byz
                    ]
                )
            )

            this_verse_collation_string = (
                this_verse_collation_string
                + initial_callout
                + manuscripts_verse_identical_to_byz_string
                + "\n\n:::\n\n"
            )

        ######################################
        ######################################
        ## Creating the nomina sacra callout##
        ######################################
        ######################################
        if is_abbreviation_present:
            this_verse_collation_string = (
                this_verse_collation_string
                + '::: {.callout-warning collapse="true" icon="false"}\n## *Nomina sacra* or abbreviations\nPlease note that one or more of the manuscripts contains *nomina sacra* which have been spelled out by our automated algorithm. This process is very accurate, but occasional mistakes can happen, especially with obscure or uncommon *nomina sacra*. In case of doubt about the actual reading of a *nomen sacrum*, please consult the original transcripts or facsimiles.\n:::\n'
            )

        ######################################
        ######################################
        ## Creating the corrections callout###
        ######################################
        ######################################

        if num_manuscripts_attesting_this_verse_corrected > 0:
            this_verse_collation_string = (
                this_verse_collation_string
                + '::: {.callout-important collapse="true" icon="false"}\n## Potentially inaccurate\nOne or more of the witnesses included in the collation are corrected. Due to the limitations of the TEI-XML format, it is not possible to automatically reconstruct the corrected hand perfectly. For this reason, the apparatus may display inaccuracies. For example, let the text of a manuscript be πολλα ειχον γραφειν [γραψαι]{.corr} (γραψαι is the correction). In this case the uncorrected hand is clearly πολλα ειχον γραφειν. The *corrected* hand, however, can be reconstructed by the computer as either πολλα ειχον γραφειν γραψαι or πολλα ειχον γραψαι. The decision as to the appropriate reconstruction must be made by a human expert. This algorithmic collation includes both the corrected words and the corrections in the corrected hands (thus, πολλα ειχον γραφειν γραψαι instead of πολλα ειχον γραψαι in the example), but this may lead to imperfect witness counts if the algorithmic reconstruction is wrong. Due to this we advise the reader to consult the individual collations by clicking on the manuscript\'s number or refer to the original transcripts or facsimiles.\n\nThe corrected hands in the apparatus have been marked with a ? symbol in order to highlight this uncertainty.\n:::\n'
            )

        ######################################
        ######################################
        ###### Creating the apparatus ########
        ######################################
        ######################################
        variants_string = ""
        for position in range(len(byz_column_base)):
            footnote_marker = position + 1
            witnesses_supporting_this_byzantine_reading = textual_units[
                (textual_units["position"] == position)
                & (textual_units["is_byzantine"] == True)
            ]["manuscript_list"].iloc[0]

            witnesses_supporting_this_byzantine_reading.pop(
                witnesses_supporting_this_byzantine_reading.index("Byz")
            )

            if (
                len(manuscripts_verse_identical_to_byz) > 0
            ):  # If there is an unanimous group
                unanimous_string = " *unan.* +"
                witnesses_supporting_this_byzantine_reading_outside_unanimous = []
                for witness in witnesses_supporting_this_byzantine_reading:
                    if witness not in manuscripts_verse_identical_to_byz:
                        witnesses_supporting_this_byzantine_reading_outside_unanimous.append(
                            witness
                        )
            else:
                unanimous_string = ""
                witnesses_supporting_this_byzantine_reading_outside_unanimous = (
                    witnesses_supporting_this_byzantine_reading
                )

            variants_string = (
                variants_string
                + "\n"
                + str(footnote_marker)
                + ". "
                + "**"
                + byz_column_base[position].replace("EMPTY", "•")
                + f"]** ({len(witnesses_supporting_this_byzantine_reading)}/{num_manuscripts_included_in_collation})"
                + f"{unanimous_string} "
                + " ".join(
                    [
                        format_manuscript_id_for_quarto(item)
                        for item in witnesses_supporting_this_byzantine_reading_outside_unanimous
                    ]
                )
                + "\n\n"
            )
            variants_at_this_textual_unit = textual_units[
                (textual_units["position"] == position)
                & (textual_units["is_byzantine"] == False)
            ]

            if len(variants_at_this_textual_unit) > 0:
                for reading, row in variants_at_this_textual_unit.iterrows():
                    reading = reading.replace("U", "[[?]]{.apparatus-uncertain}")

                    if reading == "•":
                        reading = "*either missing or lacuna*"
                    variants_string = (
                        variants_string
                        + "    * "
                        + reading
                        + ": "
                        + " ".join(
                            [
                                format_manuscript_id_for_quarto(item)
                                for item in row["manuscript_list"]
                            ]
                        )
                        + "\n"
                    )

        this_verse_collation_string = this_verse_collation_string + variants_string

        chapter_qmd_string = chapter_qmd_string + this_verse_collation_string

    book_qmd_string = book_qmd_string + chapter_qmd_string

with open("../apparatus/third_john.qmd", "w", encoding="utf-8") as file:
    file.write(book_qmd_string)

###### PONER EN ALGUNA PARTE EL UMBRAL DE FRAGMENTARIO
