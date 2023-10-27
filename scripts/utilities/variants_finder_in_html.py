import json
import pandas as pd
from bs4 import BeautifulSoup
import os
import glob
import difflib
import re
import numpy as np

def levenshtein_distance(s1, s2):
    len_s1 = len(s1)
    len_s2 = len(s2)

    # Create a matrix to store the distances
    dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    # Initialize the first row and column
    for i in range(len_s1 + 1):
        dp[i][0] = i
    for j in range(len_s2 + 1):
        dp[0][j] = j

    # Fill in the matrix using dynamic programming
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    return dp[len_s1][len_s2]


htmls_path = "../../docs/collations/"

dfs = []
for filename in os.listdir(htmls_path):
    if filename.endswith(".html"):
        manuscript_id = filename[:-5]
        html_file_path = os.path.join(htmls_path, manuscript_id + '.html')
        print('Processing', filename)
        
        # Read the XML file
        with open(html_file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all tags with class "greek-added" and "greek-omitted" in any order
        contiguous_tags = []
        for tag in soup.find_all(["span", "p"]):
            if 'greek-added' in tag.get('class', []) or 'greek-omitted' in tag.get('class', []):
                contiguous_tags.append(tag)

        # Create a list of dictionaries to store the data
        data = []

        # Organize the tags into the list of dictionaries
        for i in range(1, len(contiguous_tags)):
            if 'greek-added' in contiguous_tags[i-1].get('class', []):
                data.append({"Greek-Omitted": contiguous_tags[i].text, "Greek-Added": contiguous_tags[i-1].text})
            elif 'greek-added' in contiguous_tags[i].get('class', []):
                data.append({"Greek-Omitted": contiguous_tags[i-1].text, "Greek-Added": contiguous_tags[i].text})

        # Create a Pandas DataFrame from the list of dictionaries
        df = pd.DataFrame(data)
        df['levenshtein_distance'] = df.apply(lambda row: levenshtein_distance(row['Greek-Omitted'], row['Greek-Added']), axis=1)
        df = df[df['levenshtein_distance']==1]

        # Print the Pandas DataFrame
        dfs.append(df)
        #print(df)

dfs = pd.concat(dfs)
dfs = dfs.sort_values(by=['Greek-Omitted'])
dfs = dfs.drop_duplicates()

def char_diff(a, b):
    differ = difflib.Differ()
    diff = list(differ.compare(a, b))
    return ''.join(diff)

# Apply the char_diff function to the DataFrame
dfs['character_difference'] = dfs.apply(lambda row: char_diff(row['Greek-Omitted'], row['Greek-Added']), axis=1)

def variant_type(difference):
    if '- ο+ ω' in difference:
        return 'ο and ω'
    elif 'θ  ε  ι+ ν' in difference:
        return 'movable ν'
    elif 'σ  ι+ ν' in difference:
        return 'movable ν'
    elif '- η+ ι' in difference:
        return 'η and ι'
    elif 'β- β+' in difference:
        return 'removal of double β'
    elif '- ν  ν' in difference:
        return 'removal of double ν'
    elif 'μ- μ' in difference:
        return 'removal of double μ'
    elif '- ε  ι' in difference:
        return 'standard ει, nonstandard ι'
    elif '+ ε  ι' in difference:
        return 'standard ι, nonstandard ει'
    elif 'λ+ λ' in difference:
        return 'λ gemination'
    elif '- κ  κ' in difference:
        return 'removal of double κ'
    else:
        return None
    

dfs['variant_type'] = dfs['character_difference'].apply(variant_type)
    
dfs = dfs.dropna()


dfs.to_csv('html_variants.csv', index=False)
print(dfs)
