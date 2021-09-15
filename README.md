# wfsOutputExtension

![Icon](wfsOutputExtension/icon.png)

[![Tests 🎳](https://github.com/3liz/qgis-wfsOutputExtension/workflows/Tests%20%F0%9F%8E%B3/badge.svg)](https://github.com/3liz/qgis-wfsOutputExtension/actions?query=branch%3Amaster)

QGIS Server Plugin to add additional output formats to WFS GetFeature request.

Demo in [Lizmap Web Client](https://github.com/3liz/lizmap-web-client): 

![Demo of the plugin](demo.jpg)

## Description

wfsOutputExtension is a QGIS Server Plugin. It extends OGC Web Feature Service capabilities.
It adds output formats to WFS GetFeature request.

It adds:
* CSV
* ESRI ShapeFile as ZIP file
* Geopackage
* GPX
* KML
* MapInfo TAB as ZIP file
* MIF/MID File as ZIP file
* ODS, the datatable
* XLSX, the datatable

## Versions

* For QGIS Server 3, higher than version 1.1.0
* For QGIS Server 2, version 1.0.2 or lower

## Installation

To install the plugin :
* Go to the [download section](https://github.com/3liz/qgis-wfsOutputExtension/releases)
* Retrieve the archive version for a given QGIS version (QGIS 2 or QGIS 3)
* Extract the content of the archive with `unzip`
* Check rights
* Move the directory of the plugin into the plugin's directory of QGIS Server (it is `/opt/qgis/plugins` most
often)
* Restart QGIS Server

For more details :
* Read [the documentation of QGIS Server](https://docs.qgis.org/testing/en/docs/server_manual/plugins.html#installation).
* Read [AtlasPrint install process](https://github.com/3liz/qgis-atlasprint/blob/master/atlasprint/README.md#installation-with-qgis-server)
because it's similar.

## Debug on production

It's possible to set `DEBUG_WFSOUTPUTEXTENSION` to `TRUE` or `1`, the plugin will not remove temporary files on the disk.

## Tests

```bash
docker pull 3liz/qgis-platform:3.10
docker tag 3liz/qgis-platform:3.10 qgis-platform:3.10
make test
```
