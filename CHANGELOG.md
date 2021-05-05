# CHANGELOG

## v1.5.3 - 2021-05-05

* Upgrade the plugin as not experimental in its metadata.txt
* Upgrade PyQGIS functions which are deprecated in newer QGIS versions
* Remove some excessive logging
* Add more unit tests about trailing "0" in data

## v1.5.2 - 2021-02-26

* Remove all files associated with a request after the process
* Add more unit tests
* Switch from Travis to GitHub Actions

## v1.5.1 - 2021-01-19

* Fix error when writing and closing file with QTemporaryFile
* Review the GPX export
* Improve tests, logging, release process

## v1.5.0 - 2020-10-09

* Fix regressions about ZIP files (SHP, MIF and TAB)
* Refactoring the code and add tests for each format
* Known issue about GPX export

## v1.4.1 - 2020-09-29

* Fix a packaging issue

## v1.4.0 - 2020-09-28

* Refactor the code
* Fix issue about Excel files
* Remove the use of deprecated code

## v1.3.0 - 2020-04-28

* Enable GPX export
* Small code review

## v1.2.3 - 2020-03-19

* Add empty class for QGIS Desktop
* OGR loads schema when reading GML
* Fix race condition on multi-server platform
