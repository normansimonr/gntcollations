# Greek New Testament Collations

This is the repository of the *Greek New Testament Collations* [website](www.gntcollations.com). It contains:

* The source XML files for all the manuscripts in the INTF's [*Liste*]([Liste (Greek) - INTF](https://ntvmr.uni-muenster.de/liste)). The XML files can be found in `raw_data/manuscripts`. INTF stands for *Institut für Neutestamentliche Textforschung*.

* The source files of the Robinson-Pierpont 2018 Byzantine textform (taken from the [official repository](https://github.com/byztxt/byzantine-majority-text)). An XML file of the entire New Testament can be found as `raw_data/manuscripts/BYZ.xml` and CSVs of the individual books are included in `byz_csv`.

* The *The case for Byzantine priority* essay by Maurice A. Robinson, in both English and Spanish. The texts were taken from the [official repository](https://github.com/byztxt/byzantine-majority-text).

* The Python code that pre-processes and collates the manuscripts (`scripts` folder).

* The [Quarto Markdown](https://quarto.org/) files that, once rendered, produce the Html files of the website.

## Licence

The Byzantine majority text is in the Public Domain. The transcriptions of the individual manuscripts have been created by the *Institut für Neutestamentliche Textforschung* and are under the Creative Commons Attribution 4.0 Unported Licence.

The code to create the collations has been released to the Public Domain.
