wfsOutputExtension: QGIS3 Server Plugin to add Output Formats to WFS GetFeature request.
==========================================================================================

Description
---------------

wfsOutputExtension is a QGIS3 Server Plugin. It extends OGC Web Feature Service capabilities. It adds Output Formats to WFS GetFeature request.

It adds:
* KML
* ESRI ShapeFile as ZIP file
* MapInfo TAB as ZIP file
* MIF/MID File as ZIP file
* CSV, the datatable
* XLSX, the datatable
* ODS, the datatable

wfsOutputExtension needs QGIS Server 3.0 or higher.
 
Retrieve wfsOutputExtension 1.0.2 version or lower if you have Qgis Server 2.


Installation
------------

To install the plugin, go to the [download section](https://github.com/3liz/qgis-wfsOutputExtension/releases)
of the plugin web site, retrieve the archive of version 1.1 or higher, and 
extract the content of the archive with `unzip` or an other tool.

Then move the directory of the plugin into the plugins directory of Qgis Server
(it is `/opt/qgis/plugins` most often), rename the folder removing the version description. You need to restart Qgis Server.

For more details, read [the documention of Qgis Server](https://docs.qgis.org/3.4/en/docs/user_manual/working_with_ogc/server/plugins.html#installation).

