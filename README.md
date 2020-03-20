# wfsOutputExtension

QGIS Server Plugin to add additional output formats to WFS GetFeature request.

Demo in [Lizmap Web Client](https://github.com/3liz/lizmap-web-client): 

![Demo of the plugin](demo.jpg)

## Description

wfsOutputExtension is a QGIS Server Plugin. It extends OGC Web Feature Service capabilities.
It adds Output Formats to WFS GetFeature request.

It adds:
* CSV, the datatable
* ESRI ShapeFile as ZIP file
* Geopackage
* KML
* MapInfo TAB as ZIP file
* MIF/MID File as ZIP file
* ODS, the datatable
* XLSX, the datatable

## Versions

* For QGIS Server 3, higher than version 1.1.0
* For QGIS Server 2, version 1.0.2 or lower

## Installation

To install the plugin, go to the [download section](https://github.com/3liz/qgis-wfsOutputExtension/releases)
of the plugin web site, retrieve the correct archive version and 
extract the content of the archive with `unzip` or an other tool.

Then move the directory of the plugin into the plugins directory of QGIS Server
(it is `/opt/qgis/plugins` most often), rename the folder to `wfsOutputExtension`. You need to restart QGIS Server.

For more details, read [the documention of Qgis Server](https://docs.qgis.org/3.4/en/docs/user_manual/working_with_ogc/server/plugins.html#installation).
