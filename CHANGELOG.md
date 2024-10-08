# Changelog

## Unreleased

## 1.8.2 - 2024-08-12

* Minor code cleanup


## 1.8.1 - 2024-06-05

* Minor code cleanup

## 1.8.0 - 2023-07-04

* Some Python cleanup
* Raise the QGIS minimum version to QGIS 3.22 and Python 3.7
* Add FlatGeobuf support

## 1.7.1 - 2022-10-05

* Add the CPG file when a shapefile is created
* Modernize Python by using fstrings everywhere. Python 3.6 required.

## 1.7.0 - 2022-03-24

* Fix the field type detection when exporting the layer
* Fix removing files when a Python exception occurs during the request
* Removing files by default when the export is done

## 1.6.2 - 2021-09-17

* Fix error on deployment on our CI

## 1.6.1 - 2021-09-17

* Fix error in some deployments environment, regression from 1.6.0

## 1.6.0 - 2021-09-15

* Add some logs in the plugin to make it easier to debug
* Add a new environment variable `DEBUG_WFSOUTPUTEXTENSION` to not remove temporary files if needed
* Set chmod 755 on the plugin directory
* Some refactoring in the code
* Removing the `v` prefix in the version name

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
