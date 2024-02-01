import pandas as pd
import os
from bs4 import BeautifulSoup
import json


# Specify the file path
file_path = "../apparatus/manuscript_verse_relation.json"

# Read the JSON file into a dictionary
with open(file_path, "r") as file:
    data_dict = json.load(file)

# Creating the file names
file_names_dictionary = {}
for book_name, value in data_dict.items():
    book_name_prefix = book_name.lower().replace(" ", "_")
    files_for_this_book = []
    for chapter in value.keys():
        if int(chapter) != 0:
            file_name = f"{book_name_prefix}/{book_name_prefix}_{chapter}.pdf"
            files_for_this_book.append({chapter: file_name})
    file_names_dictionary[book_name] = files_for_this_book

fixed_text = """---
title: "Apparatus"
author: ""
date: ""
---

This page contains links to apparatuses of the books of the New Testament, taking Maurice A. Robinson and William Pierpont's Byzantine Textform [-@ntrp18] (primary line) as the base text.

All the witnesses that have a transcription available for a verse were included in the respective verse's collation. **We only include the transcriptions published by the Institute for New Testament Textual Research at the University of Münster, [INTF](https://ntvmr.uni-muenster.de/)**. This means that for some books, most notably the Gospel of John, the number of available witnesses is very low. We may add the transcriptions of the International Greek New Testament Project, [IGNTP](https://itseeweb.cal.bham.ac.uk/igntp/transcriptions.html), in future (the IGNTP have published a number of transcriptions of Johannine manuscripts and of the Pauline corpus). If you happen to know how to program in Python and would like to contribute the code to include those transcriptions in this website, feel free to fork the [repo](https://github.com/normansimonr/gntcollations) and open a pull request.

Each apparatus shows which witnesses were collated. Corrected hands are treated as witnesses of their own, but with a caveat. For example, let the text of a manuscript be πολλα ειχον γραφειν [γραψαι]{.corr} (γραψαι is the correction). In this case the uncorrected hand is clearly πολλα ειχον γραφειν. The *corrected* hand, however, can be reconstructed by the computer as either πολλα ειχον γραφειν γραψαι or πολλα ειχον γραψαι. The decision as to the appropriate reconstruction must be made by a human expert. This algorithmic collation includes both the corrected words and the corrections in the corrected hands (thus, πολλα ειχον γραφειν γραψαι instead of πολλα ειχον γραψαι in the example), but this may lead to imperfect witness counts if the algorithmic reconstruction is wrong. Due to this we advise the reader to consult the individual collations by clicking on the manuscript\'s number or refer to the original transcripts or facsimiles.

Where there is unanimous support for the entire Byzantine verse in one or more manuscripts, a note has been added listing the witnesses under a group called 'unanimous'.

Each reading of the Byzantine primary line is followed by a fraction in parenthesis, representing the number of witnesses that support it (including corrected hands if any) as a ratio of the total number of witnesses included in the collation. For instance, (5/6) means that five of the six collated witnesses support the reading.

Readings that are unclear or incomplete in the original manuscripts are marked with a bracketed ? symbol in the apparatus at the place where the letters are uncertain. When a witness is too fragmentary it is ignored from the collation of that particular verse and a note is added.

Manuscript identifiers are followed by the century that was assigned by the INTF as the manuscript's latest estimated date (see also the [*Liste*](liste.qmd)). For instance, Codex Sinaiticus' latest estimated date is AD 399, which is the fourth century, and its identifier is 20001. In consequence, this manuscript appears in the apparatuses as ['20001(IV)'](collations/20001.qmd). Corrected hands appear with a superscript c, like this: ['20001^c^(IV)'](collations/20001.qmd).

## Book list
"""

ia_url = "https://archive.org/details/gntcollations_apparatuses_byzantine/2.0.0/"
# ia_url = ''

generated_text = ""
for book_name in file_names_dictionary.keys():
    generated_text = generated_text + f"\n### {book_name}\n\n"
    for chapter_and_filename in file_names_dictionary[book_name]:
        chapter = list(chapter_and_filename.keys())[0]
        chapter_markdown = f"[{chapter}]({ia_url + chapter_and_filename[chapter]})"
        generated_text = generated_text + " " + chapter_markdown
    generated_text = generated_text + "\n\n"

text_to_save = fixed_text + generated_text

with open("../apparatus.qmd", "w") as file:
    file.write(text_to_save)
