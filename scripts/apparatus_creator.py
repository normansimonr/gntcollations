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
            byz_verse = ''
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
        
        
        ### Collation
        collation_for_this_verse = verse_attestation.groupby(['chapter', 'verse', 'parsed_greek'])['manuscript_id'].apply(list)
        
        is_byzantine_majority = 
        
        
        print(verse_attestation)
        print(collation_for_this_verse)
        
        
        collation_for_this_verse.to_csv(str(verse) + '_test.csv')

# print(manuscripts_attesting_this_verse)
