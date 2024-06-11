# Greek New Testament Collations

This is the repository of the *Greek New Testament Collations* website: www.gntcollations.com

It contains:

* The source XML files for all the manuscripts in the INTF's [*Liste*](https://ntvmr.uni-muenster.de/liste). The XML files can be found in `raw_data/manuscripts`. INTF stands for *Institut für Neutestamentliche Textforschung*.

* The source files of the Robinson-Pierpont 2018 Byzantine textform (taken from the [official repository](https://github.com/byztxt/byzantine-majority-text)). An XML file of the entire New Testament can be found as `raw_data/manuscripts/BYZ.xml` and CSVs of the individual books are included in `byz_csv`.

* The *The case for Byzantine priority* essay by Maurice A. Robinson, in both English and Spanish. The texts were taken from the [official repository](https://github.com/byztxt/byzantine-majority-text).

* The Python code that pre-processes and collates the manuscripts (`scripts` folder).

* The [Quarto Markdown](https://quarto.org/) files that, once rendered, produce the Html files of the website.

## Building the website

In order to build the website you need to:

1. Clone the repository and install the requirements. The scripts are in the `scripts` folder.
2. Run the `liste_downloader.py` script to download the XML files from the INTF website or, alternatively, skip this step and simply use the XML transcriptions that are already in the `raw_data` folder.
3. Run the `liste_quarto_creator.py` script. It creates the "Liste" page on the website.
4. Run the `collate.py` script. It creates the collations of each individual witness against Robinson-Pierpont. It also creates a number of logs in the `scripts/manuscript_verses_logs/` subfolder. Those logs are important because they contain the witness to chapter and verse mapping that will later be used by the apparatus creator.
5. Execute the `chapter_list_creator.py` script. It creates the "Chapters" page on the website and also a `.json` file that contains the witness-to-chapter-and-verse mapping.
6. Execute `apparatus_creator.py`. It creates the apparatuses. It creates one apparatus file for each chapter in the New Testament (there are 260 chapters in the New Testament). Those apparatus files have the `.qmd` extension. They are not included in this repository because they are too large, so you will necessarily have to generate them yourself using the script. These files are added to the `apparatus` folder.
7. You can render each apparatus file with the command `quarto render filename.qmd`. For instance, to render Acts 1 you can run `quarto render acts_1.qmd`. You can also render them in bulk using a foor loop. In Unix that could be something like `for file in *.qmd; do quarto render "$file"; done`.

Please note that each of the above tasks can take a long time to run. Re-creating the entire website may take a few hours depending on your hardware.

## Note about the apparatuses

We only include the transcriptions published by the Institute for New Testament Textual Research at the University of Münster, [INTF](https://ntvmr.uni-muenster.de/). This means that for some books, most notably the Gospel of John, the number of available witnesses is very low. We *may* add the transcriptions of the International Greek New Testament Project, [IGNTP](https://itseeweb.cal.bham.ac.uk/igntp/transcriptions.html), in future (the IGNTP have published a number of transcriptions of Johannine manuscripts and of the Pauline corpus). We cannot commit to a timeline, however, so if you happen to know how to program in Python and would like to contribute the code to include those transcriptions in this website, feel free to fork the [repo](https://github.com/normansimonr/gntcollations) and open a pull request. Your contributions are more than welcome.

## Licence

The Byzantine majority text is in the Public Domain. The transcriptions of the individual manuscripts have been created by the *Institut für Neutestamentliche Textforschung* and are under the Creative Commons Attribution 4.0 Unported Licence.

The code to create the collations has been released to the Public Domain.
