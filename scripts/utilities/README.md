# README

The `utilities` folder contains scripts that can be used to detect *nomina sacra* and spelling variants in the corpus. As for spelling variants, these are quite difficult to standardise, as even the spelling of the RP Byzantine text is not standardised.

* `nomina_sacra_extractor.py` takes the existing *nomina sacra* list and updates it with other *nomina sacra* present in the corpus but not present in the list.
* `variant_spellings_extractor.py` does something similar, but with potential spelling variants. Contrary to *nomina sacra*, spelling variants are much harder to standardise.
* `variants_finder_in_html.py` is similar to the previous script, but instead of analysing the manuscripts directly, it tries to detect other spelling variants that made it to the final Htmls. In order to take the results of the script and incorporate them in the spelling variants list, you need to copy and paste the results manually using Excel or LibreOffice.
* `depurate_spelling_equivalences.py` this script is meant to take the spelling variants detected by the previous two scripts and clean them so that duplicates are removed, as well as any variants that are considered both nonstandard and standard.
