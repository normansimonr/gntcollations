import pandas as pd
import os

num_spelling_variants = len(pd.read_csv("spelling_equivalences.csv"))
num_nomina_sacra = len(pd.read_csv("abbreviations_equivalences.csv"))
num_manuscripts_errors = len(pd.read_csv("manuscripts_with_xml_errors.csv"))


# Importing and formatting the Liste

cols_to_keep = [
    "docID",
    "primaryName",
    "origEarly",
    "origLate",
    "shelfInstances.shelfInstance.contentOverview",
]
datatypes = {
    "docID": str,
    "primaryName": str,
    "origEarly": float,
    "origLate": float,
    "shelfInstances.shelfInstance.contentOverview": str,
}
liste = pd.read_csv(
    "../raw_data/liste/liste.csv", usecols=cols_to_keep, dtype=datatypes
)


num_liste_records = len(liste["docID"].unique())


# Accessing the collations
folder_path = "../collations"
extension = ".qmd"

# List all files in the folder
all_files = os.listdir(folder_path)

# Filter for files with the specified extension
qmd_files = [file for file in all_files if file.endswith(extension)]

print(qmd_files)

num_transcribed_records = len(qmd_files)

head = f"""---
title: "*Liste*"
author: ""
date: ""
---

This page contains a copy of the *Kurzgefasste Liste* with links to the collations of the individual manuscripts [see @Paulson_liste for an introduction to the *Liste*] against the Byzantine majority text as edited by Maurice A. Robinson and William Pierpont [-@ntrp18]. The *Liste* and all the collated manuscripts have been obtained from the official INTF [website](https://ntvmr.uni-muenster.de/liste) and are up-to-date as of {{{{< var listeupdated >}}}} (you can download an Excel-readable copy [here](raw_data/liste/liste.csv)). The Robinson-Pierpont 2018 text (Byz^RP^) has been taken from the [official repository](https://github.com/byztxt/byzantine-majority-text) of that edition (version {{{{< var byzversion >}}}}). Note that for the collation only the *primary line* of Byz^RP^ has been used, that is, only the majority Byzantine variants are included, and all the minority Byzantine variants are ignored (they can be consulted in the upper apparatus of the [Robinson-Pierpont edition](https://web.archive.org/web/20210413060536/https://byzantinetext.com/wp-content/uploads/2021/03/robinson-pierpont-2018-gnt-edition.pdf)).

To see the manuscript attestation of a specific chapter of the New Testament, please go to [Chapters](chapters.qmd).

In order to create the collations, the XML versions of the manuscripts and of the Byz^RP^ text were parsed and {num_nomina_sacra} *nomina sacra* were spelled out (full list [here](scripts/abbreviations_equivalences.csv)). There are several dozens additional *nomina sacra* that were not included in the list because their meanings were hard to ascertain manually. Abbreviated numerals were not spelled out. In order to report an error or to propose a new *nomen sacrum*, please open a [GitHub issue](https://github.com/normansimonr/gntcollations/issues) or contact the maintainer at nsrodriguezc@unal.edu.co.

If the INTF has a transcription available, the identifier of the manuscript in the *Liste* links to its respective collation. The identifier does not contain a link otherwise. Of the {num_liste_records} identifiers in the *Liste* [see @Leggett_Paulson_2023 for a precise tally of the known Greek manuscripts of the New Testament], {num_transcribed_records} have been collated in this website. Apart from these manuscripts, which represent the totality of the available transcriptions in the INTF website, there were {num_manuscripts_errors} manuscripts that could not been processed due to errors or inconsistencies in their XML structure. You can find a list [here](scripts/manuscripts_with_xml_errors.csv). Most Byzantine manuscripts have not been transcribed as of yet.

Lacunose verses have been noted in the collations. Not all lacunae, however, are marked in the INTF transcriptions. Many collations show significant differences between the Byzantine text and a manuscript's text due to the manuscript being fragmentary, without an indication in the transcription. Such situations must be determined by manual inspection of the facsimiles. An example is [𝔓^51^](https://ntvmr.uni-muenster.de/manuscript-workspace?docID=10051), which when collated displays a lengthy omission in Galatians 1:10. The facsimile shows that the papyrus is [fragmentary](https://ntvmr.uni-muenster.de/community/modules/papyri/?zoom=33&left=6.23046875&top=53.22265625&site=INTF&image=10051/0/10/10/1) (001 recto).

### References {{.unnumbered .unlisted}}

::: {{#refs}}
:::

## The *Liste*

The collations have been created automatically and should be used only for indicative purposes. Inspecting the original facsimiles and transcriptions remains the best way to study a manuscript's text and character. Manuscripts are sorted from earliest to latest according to their latest estimated date.

"""

liste_grouped = (
    liste.groupby(["docID"])["shelfInstances.shelfInstance.contentOverview"]
    .apply(lambda x: list(set(x)))
    .reset_index()
)

liste_grouped["contents"] = [
    str(x).replace("[", "").replace("]", "").replace("'", "").replace(", nan", "")
    for x in liste_grouped["shelfInstances.shelfInstance.contentOverview"]
]
liste_grouped = liste_grouped.drop(
    columns=["shelfInstances.shelfInstance.contentOverview"]
)

liste = liste.drop_duplicates(subset=["docID"])

liste_result = pd.merge(liste, liste_grouped, on="docID")
liste_result = liste_result.drop(
    columns=["shelfInstances.shelfInstance.contentOverview"]
)

liste_result["primaryName"] = liste_result["primaryName"].apply(
    lambda x: str(x) + "^" if str(x)[0] == "P" else str(x)
)

liste_result["primaryName"] = (
    liste_result["primaryName"]
    .str.replace("^L", "*ℓ*-", regex=True)
    .str.replace("^P", "𝔓^", regex=True)
    .str.replace(".0", "", regex=False)
)

liste_result = liste_result[
    ["docID", "primaryName", "origLate", "origEarly", "contents"]
]

liste_result["origLate"] = liste_result["origLate"].replace(-1, 2999).replace(0, 2999)

liste_result["late_float"] = liste_result["origLate"].astype(float)

liste_result = liste_result.sort_values(by=["late_float"], ascending=True)

liste_result["origLate"] = (
    liste_result["origLate"]
    .astype(str)
    .str.replace("2999", "N/A")
    .str.replace(".0", "", regex=False)
    .str.replace("2599", "")
)
liste_result["origEarly"] = (
    liste_result["origEarly"]
    .astype(str)
    .str.replace("^0", "N/A", regex=True)
    .str.replace(".0", "", regex=False)
    .str.replace("-100", "N/A")
)


# Adding the links
def add_links(manuscript_id):
    manuscript_id = str(manuscript_id).replace(".0", "")
    if manuscript_id + ".qmd" in qmd_files:
        return f"[{manuscript_id}](collations/{manuscript_id}.qmd)"
    else:
        return manuscript_id


liste_result["docID"] = liste_result["docID"].apply(add_links)

# Renaming the columns
liste_result = liste_result.rename(
    columns={
        "docID": "Identifier",
        "primaryName": "Primary name",
        "contents": "Contents",
        "origLate": "Latest estimated date",
        "origEarly": "Earliest estimated date",
    }
)

# Converting to Markdown
markdown_liste = liste_result.drop(columns=["late_float"]).to_markdown(index=False)

markdown_liste = markdown_liste.replace("nan", "N/A").replace("N/A, ", "")

with open("../liste.qmd", "w") as file:
    file.write(head + markdown_liste)

# print(markdown_liste)
