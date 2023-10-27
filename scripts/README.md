# README

These scripts process the manuscript data to generate the website pages.

* `liste_downloader.py` downloads the *Liste* from the INTF website. It normally takes a few *minutes* as the INTF API can be a bit slow sometimes.
* `manuscript_downloader.py` downloads the transcripts of the manuscripts present in the *Liste*, including those manuscripts for which there is no transcription (their transcriptions are XML files that have `error` tags to indicate that there is no transcription available).
* `collate.py` collates the manuscripts with the Byzantine text and produces the `.qmd` files of the `collations` folder.
* `liste_quarto_creator.py` creates the `liste.qmd` page, which contains a table that lists all the manuscripts in the *Liste*, linking to their collations.
* `chapter_list_creator.py` creates the `chapters.qmd` page, which contains lists of the manuscripts that attest to each chapter of the New Testament.

There are some auxiliary files as well:

* `manuscripts_with_xml_errors.csv` has a list of manuscripts that we were not able to parse because their XML structure had errors. These errors come from the source directly (the INTF).
* `abbreviations_equivalences.csv` contains the *nomina sacra* standardisation.
* `spelling_equivalences.csv` contains a list of spelling equivalences. This file is currently not being used (there is a parameter in one of the functions of the `collate.py` file that deactivates is use) because after many tests we detected that the Byzantine spellings (which we were using as the standard) were not standardised themselves. Additionally, having the possibility to inspect spelling variants can be of interest to some textual scholars. We are leaving the functionality code in the script, however, in case we find it useful in the future (it was not removed, only inactivated).

Should you want to regenerate the `.qmd` files of the website yourself from scratch, make sure to run the scripts in this order:

1. `liste_downloader.py`
1. `manuscript_downloader.py`
1. `collate.py`
1. `liste_quarto_creator.py`
1. `chapter_list_creator.py`

You would then have to render the website by opening a terminal in the root folder and running `quarto render .`.
