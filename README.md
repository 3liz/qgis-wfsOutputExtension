wfsOutputExtension: QGIS2 Server Plugin to add Output Formats to WFS GetFeature request.
==========================================================================================

Description
---------------

wfsOutputExtension is a QGIS2 Server Plugin. It extends OGC Web Feature Service capabilities. It adds Output Formats to WFS GetFeature request.

It adds:
* KML
* ESRI ShapeFile as ZIP file
* MapInfo TAB as ZIP file
* MIF/MID File as ZIP file
* CSV, the datatable
* XLSX, the datatable
* ODS, the datatable

CSV, XLSX and ODS needs QGIS Server 2.14 or 2.18.


Installation
------------

To install the plugin, go to the [download section](https://github.com/3liz/qgis-wfsOutputExtension/releases)
of the plugin web site, retrieve the archive of 1.0.x (1.1. and higher are compatible
only with QGIS3), and extract the content of the archive with `unzip` or an other
tools.

Then move the directory of the plugin into the plugins directory of Qgis Server
(it is `/opt/qgis/plugins` most often). You need to restart Qgis Server.

For more details, read [the documention of Qgis Server](https://docs.qgis.org/2.18/en/docs/user_manual/working_with_ogc/server/plugins.html#installation).

