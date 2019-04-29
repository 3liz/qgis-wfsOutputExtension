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

import os, time, tempfile
from xml.dom import minidom

from qgis.server import QgsServerFilter
from qgis.core import Qgis, QgsMessageLog, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QFile

WFSFormats = {
    'shp':{
        'contentType': 'application/x-zipped-shp',
        'filenameExt': 'shp',
        'forceCRS': None,
        'ogrProvider': 'ESRI Shapefile',
        'ogrDatasourceOptions':None,
        'zip': True,
        'extToZip': ['shx','dbf','prj']
    },
    'tab':{
        'contentType': 'application/x-zipped-tab',
        'filenameExt': 'tab',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions':None,
        'zip': True,
        'extToZip': ['dat','map','id']
    },
    'mif':{
        'contentType': 'application/x-zipped-mif',
        'filenameExt': 'mif',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions':'FORMAT=MIF',
        'zip': True,
        'extToZip': ['mid']
    },
    'kml':{
        'contentType': 'application/vnd.google-earth.kml+xml',
        'filenameExt': 'kml',
        'forceCRS': 'EPSG:4326',
        'ogrProvider': 'KML',
        'ogrDatasourceOptions':None,
        'zip': False,
        'extToZip': []
    },
    'ods':{
        'contentType': 'application/vnd.oasis.opendocument.spreadsheet',
        'filenameExt': 'ods',
        'forceCRS': None,
        'ogrProvider': 'ODS',
        'ogrDatasourceOptions':None,
        'zip': False,
        'extToZip': []
    },
    'xlsx':{
        'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'filenameExt': 'xlsx',
        'forceCRS': None,
        'ogrProvider': 'XLSX',
        'ogrDatasourceOptions':None,
        'zip': False,
        'extToZip': []
    },
    'csv':{
        'contentType': 'text/csv',
        'filenameExt': 'csv',
        'forceCRS': None,
        'ogrProvider': 'CSV',
        'ogrDatasourceOptions':None,
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

        self.tempdir = os.path.join( tempfile.gettempdir(), 'qgis_wfs' )
        if not os.path.exists(self.tempdir):
            os.mkdir( self.tempdir )
        QgsMessageLog.logMessage("WFSFilter.tempdir: %s" % self.tempdir,"wfsOutputExtension", Qgis.Info)

    def requestReady(self):
        QgsMessageLog.logMessage("WFSFilter.requestReady", "wfsOutputExtension", Qgis.Info)
        self.format = None
        # verifying format
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()
        if params.get('SERVICE', '').upper() == 'WFS' and params.get('REQUEST', '').upper() == 'GETFEATURE':
            oformat = params.get('OUTPUTFORMAT', '').lower()
            if oformat in WFSFormats.keys():
                request.setParameter('OUTPUTFORMAT', 'GML2')
                self.format = oformat
                self.typename = params.get('TYPENAME', '')
                self.filename = 'qgis_server_wfs_features_%s' % int(time.time())
                # set headers
                formatDict = WFSFormats[self.format]
                request.clear()
                request.setRequestHeader('Content-type', formatDict['contentType'])
                if formatDict['zip']:
                    request.setRequestHeader('Content-Disposition', 'attachment; filename="%s.zip"' % self.typename)
                else:
                    request.setRequestHeader('Content-Disposition', 'attachment; filename="%s.%s"' % (self.typename, formatDict['filenameExt']))

    def sendResponse(self):
        if not self.format:
            return

        request = self.serverInterface().requestHandler()
        data = request.body().data().decode('utf8')
        with open(os.path.join(self.tempdir,'%s.gml' % self.filename), 'ab') as f :
            f.write( request.body() )
            #f.write( data )
            #f.close()

        formatDict = WFSFormats[self.format]

        # change the headers
        # update content-type and content-disposition
        if not request.headersSent():
            request.clear()
            request.setRequestHeader('Content-type', formatDict['contentType'])
            if formatDict['zip']:
                request.setRequestHeader('Content-Disposition', 'attachment; filename="%s.zip"' % self.typename)
            else:
                request.setRequestHeader('Content-Disposition', 'attachment; filename="%s.%s"' % (self.typename, formatDict['filenameExt']))
        else:
            request.clearBody()

        if data.rstrip().endswith('</wfs:FeatureCollection>'):
            # all the gml has been intercepted
            # read the GML
            outputLayer = QgsVectorLayer(os.path.join(self.tempdir,'%s.gml' % self.filename), 'qgis_server_wfs_features', 'ogr' )
            if outputLayer.isValid():
                # transform
                crs = formatDict['forceCRS']
                if crs :
                    crs = QgsCoordinateReferenceSystem(crs)
                error = QgsVectorFileWriter.writeAsVectorFormat( outputLayer, os.path.join(self.tempdir,'%s.%s' % (self.filename, formatDict['filenameExt'])), 'utf-8', crs, formatDict['ogrProvider'], False, formatDict['ogrDatasourceOptions'] )
                if formatDict['zip']:
                    # compress files
                    import zipfile
                    try:
                        import zlib
                        compression = zipfile.ZIP_DEFLATED
                    except:
                        compression = zipfile.ZIP_STORED
                    # create the zip file
                    with zipfile.ZipFile(os.path.join(self.tempdir,'%s.zip' % self.filename), 'w') as zf:
                        # add all files
                        zf.write(os.path.join(self.tempdir,'%s.%s' % (self.filename, formatDict['filenameExt'])), compress_type=compression, arcname='%s.%s' % (self.typename, formatDict['filenameExt']))
                        for e in formatDict['extToZip']:
                            if os.path.exists(os.path.join(self.tempdir,'%s.%s' % (self.filename, e))):
                                zf.write(os.path.join(self.tempdir,'%s.%s' % (self.filename, e)), compress_type=compression, arcname='%s.%s' % (self.typename, e))
                        zf.close()
                    f = QFile(os.path.join(self.tempdir,'%s.zip' % self.filename))
                    if ( f.open( QFile.ReadOnly ) ):
                        ba = f.readAll()
                        request.appendBody(ba)
                else:
                    # return the file created without zip
                    f = QFile(os.path.join(self.tempdir,'%s.%s' % (self.filename, formatDict['filenameExt'])))
                    if ( f.open( QFile.ReadOnly ) ):
                        ba = f.readAll()
                        request.appendBody(ba)
        #else:
        #    request.appendBody('')

    def responseComplete(self):
        QgsMessageLog.logMessage("WFSFilter.responseComplete", "wfsOutputExtension", Qgis.Info)

        if self.format:
            self.format = None
            return

        # Update the WFS capabilities
        # by adding ResultFormat to GetFeature
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()

        service = params.get('SERVICE', '').upper()
        if service != 'WFS':
            return

        request = params.get('REQUEST', '').upper()
        if request not in ('GETCAPABILITIES','GETFEATURE'):
            return

        if service == 'GETCAPABILITIES':
            data = request.body().data()
            dom = minidom.parseString( data )
            for gfNode in dom.getElementsByTagName( 'GetFeature' ):
                for rfNode in dom.getElementsByTagName( 'ResultFormat' ):
                    for k in WFSFormats.keys():
                        fNode = dom.createElement( k.upper() )
                        rfNode.appendChild( fNode )
            request.clearBody()
            request.appendBody(dom.toxml('utf-8'))
