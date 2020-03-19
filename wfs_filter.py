"""
***************************************************************************
    QGIS Server Plugin Filters: Add Output Formats to GetFeature request
    ---------------------
    Date                 : October 2015
    Copyright            : (C) 2015 by René-Luc D'Hont - 3Liz
    Email                : rldhont at 3liz dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import tempfile
import time
from xml.dom import minidom

from qgis.PyQt.QtCore import QFile
from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)
from qgis.server import QgsServerFilter

WFSFormats = {
    'shp': {
        'contentType': 'application/x-zipped-shp',
        'filenameExt': 'shp',
        'forceCRS': None,
        'ogrProvider': 'ESRI Shapefile',
        'ogrDatasourceOptions': None,
        'zip': True,
        'extToZip': ['shx', 'dbf', 'prj']
    },
    'tab': {
        'contentType': 'application/x-zipped-tab',
        'filenameExt': 'tab',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions': None,
        'zip': True,
        'extToZip': ['dat', 'map', 'id']
    },
    'mif': {
        'contentType': 'application/x-zipped-mif',
        'filenameExt': 'mif',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions': 'FORMAT=MIF',
        'zip': True,
        'extToZip': ['mid']
    },
    'kml': {
        'contentType': 'application/vnd.google-earth.kml+xml',
        'filenameExt': 'kml',
        'forceCRS': 'EPSG:4326',
        'ogrProvider': 'KML',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'gpkg': {
        'contentType': 'application/geopackage+vnd.sqlite3',
        'filenameExt': 'gpkg',
        'forceCRS': None,
        'ogrProvider': 'GPKG',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'ods': {
        'contentType': 'application/vnd.oasis.opendocument.spreadsheet',
        'filenameExt': 'ods',
        'forceCRS': None,
        'ogrProvider': 'ODS',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'xlsx': {
        'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'filenameExt': 'xlsx',
        'forceCRS': None,
        'ogrProvider': 'XLSX',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'csv': {
        'contentType': 'text/csv',
        'filenameExt': 'csv',
        'forceCRS': None,
        'ogrProvider': 'CSV',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    }
}


class WFSFilter(QgsServerFilter):

    def __init__(self, serverIface):
        QgsMessageLog.logMessage("WFSFilter.init", "wfsOutputExtension", Qgis.Info)
        super(WFSFilter, self).__init__(serverIface)

        self.format = None
        self.typename = ""
        self.filename = ""
        self.allgml = False

        self.tempdir = os.path.join(tempfile.gettempdir(), 'qgis_wfs')
        # XXX Fix race-condition if multiple serveurs are run concurrently
        os.makedirs(self.tempdir, exist_ok=True)
        QgsMessageLog.logMessage("WFSFilter.tempdir: %s" % self.tempdir, "wfsOutputExtension", Qgis.Info)

    def requestReady(self):
        QgsMessageLog.logMessage("WFSFilter.requestReady", "wfsOutputExtension", Qgis.Info)

        self.format = None
        self.allgml = False

        handler = self.serverInterface().requestHandler()
        params = handler.parameterMap()

        # only WFS
        service = params.get('SERVICE', '').upper()
        if service != 'WFS':
            return

        # only GetFeature
        request = params.get('REQUEST', '').upper()
        if request != 'GETFEATURE':
            return

        # verifying format
        formats = [k.lower() for k in WFSFormats.keys()]
        oformat = params.get('OUTPUTFORMAT', '').lower()
        if oformat in formats:
            handler.setParameter('OUTPUTFORMAT', 'GML2')
            self.format = oformat
            self.typename = params.get('TYPENAME', '')
            self.filename = 'qgis_server_wfs_features_%s' % int(time.time())
            # set headers
            formatDict = WFSFormats[self.format]
            handler.clear()
            handler.setResponseHeader('Content-type', formatDict['contentType'])
            if formatDict['zip']:
                handler.setResponseHeader('Content-Disposition', 'attachment; filename="%s.zip"' % self.typename)
            else:
                handler.setResponseHeader('Content-Disposition', 'attachment; filename="%s.%s"' % (self.typename, formatDict['filenameExt']))

    def sendResponse(self):
        # if format is null, nothing to do
        if not self.format:
            return

        handler = self.serverInterface().requestHandler()

        # write body in GML temp file
        data = handler.body().data().decode('utf8')
        with open(os.path.join(self.tempdir, '%s.gml' % self.filename), 'ab') as f:
            if data.find('xsi:schemaLocation') == -1:
                f.write(handler.body())
            else:
                # to avoid that QGIS Server/OGR loads schemas when reading GML
                import re
                data = re.sub(r'xsi:schemaLocation=\".*\"', 'xsi:schemaLocation=""', data)
                f.write(data.encode('utf8'))


        formatDict = WFSFormats[self.format]

        # change the headers
        # update content-type and content-disposition
        if not handler.headersSent():
            handler.clear()
            handler.setResponseHeader('Content-type', formatDict['contentType'])
            if formatDict['zip']:
                handler.setResponseHeader('Content-Disposition', 'attachment; filename="%s.zip"' % self.typename)
            else:
                handler.setResponseHeader('Content-Disposition', 'attachment; filename="%s.%s"' % (self.typename, formatDict['filenameExt']))
        else:
            handler.clearBody()

        if data.rstrip().endswith('</wfs:FeatureCollection>'):
            # all the gml has been intercepted
            self.allgml = True
            self.sendOutputFile(handler)

    def sendOutputFile(self, handler):
        formatDict = WFSFormats[self.format]
        # read the GML
        outputLayer = QgsVectorLayer(os.path.join(self.tempdir, '%s.gml' % self.filename), 'qgis_server_wfs_features', 'ogr')
        if outputLayer.isValid():
            try:
                # create save options
                options = QgsVectorFileWriter.SaveVectorOptions()
                # driver name
                options.driverName = formatDict['ogrProvider']
                # file encoding
                options.fileEncoding = 'utf-8'
                # coordinate transformation
                if formatDict['forceCRS']:
                    options.ct = QgsCoordinateTransform(outputLayer.crs(), QgsCoordinateReferenceSystem(formatDict['forceCRS']), QgsProject.instance())
                # datasource options
                if formatDict['ogrDatasourceOptions']:
                    options.datasourceOptions = formatDict['ogrDatasourceOptions']

                # write file
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(outputLayer, os.path.join(self.tempdir, '%s.%s' % (self.filename, formatDict['filenameExt'])), options)
                if write_result != QgsVectorFileWriter.NoError:
                    handler.appendBody(b'')
                    QgsMessageLog.logMessage(error_message, "wfsOutputExtension", Qgis.Critical)
                    return False
            except Exception as e:
                handler.appendBody(b'')
                QgsMessageLog.logMessage(str(e), "wfsOutputExtension", Qgis.Critical)
                return False

            if formatDict['zip']:
                # compress files
                import zipfile
                # noinspection PyBroadException
                try:
                    import zlib
                    compression = zipfile.ZIP_DEFLATED
                except Exception:
                    compression = zipfile.ZIP_STORED
                # create the zip file
                with zipfile.ZipFile(os.path.join(self.tempdir, '%s.zip' % self.filename), 'w') as zf:
                    # add all files
                    zf.write(os.path.join(self.tempdir, '%s.%s' % (self.filename, formatDict['filenameExt'])), compress_type=compression, arcname='%s.%s' % (self.typename, formatDict['filenameExt']))
                    for e in formatDict['extToZip']:
                        if os.path.exists(os.path.join(self.tempdir, '%s.%s' % (self.filename, e))):
                            zf.write(os.path.join(self.tempdir, '%s.%s' % (self.filename, e)), compress_type=compression, arcname='%s.%s' % (self.typename, e))
                    zf.close()
                f = QFile(os.path.join(self.tempdir, '%s.zip' % self.filename))
                if f.open(QFile.ReadOnly):
                    ba = f.readAll()
                    handler.appendBody(ba)
                    return True
            else:
                # return the file created without zip
                f = QFile(os.path.join(self.tempdir, '%s.%s' % (self.filename, formatDict['filenameExt'])))
                if f.open(QFile.ReadOnly):
                    ba = f.readAll()
                    handler.appendBody(ba)
                    return True

        handler.appendBody(b'')
        QgsMessageLog.logMessage('Error no output file', "wfsOutputExtension", Qgis.Critical)
        return False

    def responseComplete(self):
        QgsMessageLog.logMessage("WFSFilter.responseComplete", "wfsOutputExtension", Qgis.Info)

        # Update the WFS capabilities
        # by adding ResultFormat to GetFeature
        handler = self.serverInterface().requestHandler()
        params = handler.parameterMap()

        service = params.get('SERVICE', '').upper()
        if service != 'WFS':
            return

        request = params.get('REQUEST', '').upper()
        if request not in ('GETCAPABILITIES', 'GETFEATURE'):
            return

        if request == 'GETFEATURE' and self.format:
            if not self.allgml:
                # all the gml has not been intercepted in sendResponse
                handler.clearBody()
                with open(os.path.join(self.tempdir, '%s.gml' % self.filename), 'a') as f:
                    f.write('</wfs:FeatureCollection>')
                self.sendOutputFile(handler)

            self.format = None
            self.allgml = False
            return

        if request == 'GETCAPABILITIES':
            data = handler.body().data()
            dom = minidom.parseString(data)
            ver = dom.documentElement.attributes['version'].value
            if ver == '1.0.0':
                for gfNode in dom.getElementsByTagName('GetFeature'):
                    for rfNode in dom.getElementsByTagName('ResultFormat'):
                        for k in WFSFormats.keys():
                            fNode = dom.createElement(k.upper())
                            rfNode.appendChild(fNode)
            else:
                for opmNode in dom.getElementsByTagName('ows:OperationsMetadata'):
                    for opNode in opmNode.getElementsByTagName('ows:Operation'):
                        if 'name' not in opNode.attributes:
                            continue
                        if opNode.attributes['name'].value != 'GetFeature':
                            continue
                        for paramNode in opNode.getElementsByTagName('ows:Parameter'):
                            if 'name' not in paramNode.attributes:
                                continue
                            if paramNode.attributes['name'].value != 'outputFormat':
                                continue
                            for k in WFSFormats.keys():
                                vNode = dom.createElement('ows:Value')
                                vText = dom.createTextNode(k.upper())
                                vNode.appendChild(vText)
                                paramNode.appendChild(vNode)
            handler.clearBody()
            handler.appendBody(dom.toxml('utf-8'))
            return
