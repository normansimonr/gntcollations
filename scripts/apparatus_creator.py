import re
import collatex
import difflib
import pandas as pd

third_john_manuscript_attestation = {
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

byz = pd.read_csv('../byz_csv/3JO.csv')

for chapter in third_john_manuscript_attestation.keys():
    verses = third_john_manuscript_attestation[chapter].keys()

    for verse in verses:
        manuscripts_attesting_this_verse = third_john_manuscript_attestation[chapter][
            verse
        ]

        verse_attestation = []

        for manuscript_id in manuscripts_attesting_this_verse:
            print("Processing", manuscript_id)
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
        
        byz_verse = byz[(byz['chapter']==chapter) & (byz['verse']==verse)]['text'].to_list()
        
        if len(byz_verse) == 0:
            byz_verse = 'G'
        else:
            byz_verse = byz_verse[0]
        
        verse_attestation.append([
               'Byz',
               chapter,
               verse,
               byz_verse
           ]
        )
        
        verse_attestation = pd.DataFrame(verse_attestation)
        verse_attestation.columns = ['manuscript_id', 'chapter', 'verse', 'parsed_greek']
        verse_attestation['manuscript_id'] = verse_attestation['manuscript_id'].astype(str)
        
        # Grouping the DataFrame by specified columns and aggregating the manuscript_id column
        grouped = verse_attestation.groupby(['chapter', 'verse', 'parsed_greek'])['manuscript_id']

        # Applying aggregation functions to the grouped data
        collation_for_this_verse = grouped.agg(manuscript_list=lambda x: list(x), manuscript_count=lambda x: len(set(x)))

        # Resetting the index to convert the grouped structure back to a DataFrame
        collation_for_this_verse = collation_for_this_verse.reset_index()
        
        # Determining if Byz is the majority reading
        collation_for_this_verse['includes_byz'] = collation_for_this_verse['manuscript_list'].astype(str).str.contains('Byz')
        collation_for_this_verse['includes_byz'] = collation_for_this_verse['includes_byz'].astype(int)
        
        collation_for_this_verse['manuscript_count'] = collation_for_this_verse['manuscript_count'] - collation_for_this_verse['includes_byz']
        
        count_manuscripts_attestation = collation_for_this_verse['manuscript_count'].sum()
        
        if (count_manuscripts_attestation % 2) == 0: # Determining the majority threshold depending on if the manuscript count is even or odd
            majority_threshold = count_manuscripts_attestation/2
        else:
            majority_threshold = (count_manuscripts_attestation+1)/2
        
        
        
        
        # Collation
        # Cleaning the texts
        def clean_text(text):
            pattern_omitted = r'\[[^\]]+\]\{\.greek-omitted\}'
            cleaned_string = re.sub(pattern_omitted, '', text)
            pattern_supplied = r'\[[^\]]+\]\{\.greek-supplied\}'
            cleaned_string = re.sub(pattern_supplied, 'U', cleaned_string)
            pattern_unclear = r'\[[^\]]+\]\{\.unclear\}'
            cleaned_string = re.sub(pattern_unclear, 'U', cleaned_string)
            cleaned_string = cleaned_string.replace('{.greek-added}', '')
            cleaned_string = cleaned_string.replace('{.greek-abbr}', 'A')
            cleaned_string = cleaned_string.replace(']{.corr}', 'C')
            cleaned_string = cleaned_string.replace('[―]{.gap}', '')
            cleaned_string = cleaned_string.replace(']', '')
            cleaned_string = cleaned_string.replace('[', '')
            
            # Removing repeated ? and spaces
            cleaned_string = re.sub(r'U+', 'U', cleaned_string)
            cleaned_string = re.sub(r' +', ' ', cleaned_string)
            
            return cleaned_string
        
        collation_for_this_verse['parsed_greek_clean'] = collation_for_this_verse['parsed_greek'].apply(clean_text)
        
        collation = collatex.Collation()
        
        for index, row in collation_for_this_verse.iterrows():
            collation.add_plain_witness(', '.join(str(item) for item in row['manuscript_list']), row['parsed_greek_clean'])
        
        collatex_output = collatex.collate(collation, layout="vertical", near_match=True, segmentation=False)
        
        def collatex_output_to_df(collatex_output):
            collatex_output = str(collatex_output)
            rows = collatex_output.split('\n')
            data = []
            for row in rows:
                if row.startswith('|'):
                    row = row.strip('|')
                    row = [cell.strip() for cell in row.split('|') if cell.strip()]
                    data.append(row)

            # Create a DataFrame from the extracted data
            df = pd.DataFrame(data[1:], columns=data[0])

            return df
        
        alignment_table = collatex_output_to_df(collatex_output)
        
        for index, row in alignment_table.iterrows():
            textual_unit = row.reset_index()
            textual_unit.columns = ['manuscript_list', 'reading']
            textual_unit = textual_unit.groupby('reading')['manuscript_list'].agg(list)
            print(verse, textual_unit)
        
        #print(alignment_table)        
        
        collation_for_this_verse.to_csv(str(verse) + '_test.csv')

# print(manuscripts_attesting_this_verse)
