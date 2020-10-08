__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'
__revision__ = '$Format:%H$'

import tempfile
import time
import traceback

from os import makedirs
from os.path import join, exists, splitext
from sys import exc_info
from xml.dom import minidom

from qgis.PyQt.QtCore import QFile, QTemporaryFile
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
        'ogrDatasourceOptions': ['FORMAT=MIF'],
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
    'gpx': {
        'contentType': 'application/gpx+xml',
        'filenameExt': 'gpx',
        'forceCRS': 'EPSG:4326',
        'ogrProvider': 'GPX',
        'ogrDatasourceOptions': ['GPX_USE_EXTENSIONS=YES'],
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


class Logger:

    PLUGIN = 'wfsOutputExtension'

    def info(self, message):
        QgsMessageLog.logMessage(message, self.PLUGIN, Qgis.Info)

    def critical(self, message):
        QgsMessageLog.logMessage(message, self.PLUGIN, Qgis.Critical)


class WFSFilter(QgsServerFilter):

    def __init__(self, server_iface):
        super(WFSFilter, self).__init__(server_iface)
        self.logger = Logger()
        self.logger.info('WFSFilter.init')

        self.format = None
        self.typename = ""
        self.filename = ""
        self.allgml = False

        self.temp_dir = join(tempfile.gettempdir(), 'QGIS_WfsOutputExtension')
        # self.temp_dir = '/src/'  # Use ONLY in debug for docker

        # XXX Fix race-condition if multiple servers are run concurrently
        makedirs(self.temp_dir, exist_ok=True)
        self.logger.info('WFSFilter.tempdir: {}'.format(self.temp_dir))

    def requestReady(self):
        self.logger.info('WFSFilter.requestReady')

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
            self.filename = 'gml_features_{}'.format(time.time())

            # set headers
            format_dict = WFSFormats[self.format]
            handler.clear()
            handler.setResponseHeader('Content-Type', format_dict['contentType'])
            if format_dict['zip']:
                handler.setResponseHeader(
                    'Content-Disposition', 'attachment; filename="{}.zip"'.format(self.typename))
            else:
                handler.setResponseHeader(
                    'Content-Disposition',
                    'attachment; filename="{}.{}"'.format(self.typename, format_dict['filenameExt']))

    def sendResponse(self):
        # if format is null, nothing to do
        if not self.format:
            return

        handler = self.serverInterface().requestHandler()

        # write body in GML temp file
        data = handler.body().data().decode('utf8')
        output_file = join(self.temp_dir, '{}.gml'.format(self.filename))
        with open(output_file, 'ab') as f:
            if data.find('xsi:schemaLocation') == -1:
                # noinspection PyTypeChecker
                f.write(handler.body())
            else:
                # to avoid that QGIS Server/OGR loads schemas when reading GML
                import re
                data = re.sub(r'xsi:schemaLocation=\".*\"', 'xsi:schemaLocation=""', data)
                f.write(data.encode('utf8'))

        format_dict = WFSFormats[self.format]

        # change the headers
        # update content-type and content-disposition
        if not handler.headersSent():
            handler.clear()
            handler.setResponseHeader('Content-type', format_dict['contentType'])
            if format_dict['zip']:
                handler.setResponseHeader(
                    'Content-Disposition', 'attachment; filename="{}.zip"'.format(self.typename))
            else:
                handler.setResponseHeader(
                    'Content-Disposition',
                    'attachment; filename="{}.{}"'.format(self.typename, format_dict['filenameExt']))
        else:
            handler.clearBody()

        if data.rstrip().endswith('</wfs:FeatureCollection>'):
            # all the gml has been intercepted
            self.allgml = True
            self.send_output_file(handler)

    def send_output_file(self, handler):
        format_dict = WFSFormats[self.format]

        # read the GML
        gml_path = join(self.temp_dir, '{}.gml'.format(self.filename))
        output_layer = QgsVectorLayer(gml_path, 'qgis_server_wfs_features', 'ogr')

        if not output_layer.isValid():
            handler.appendBody(b'')
            self.logger.critical('Output layer {} is not valid.'.format(gml_path))
            return False

        # Temporary file where to write the output
        temporary = QTemporaryFile(
            join(self.temp_dir, 'to-{}-XXXXXX.{}'.format(self.format, format_dict['filenameExt'])))
        temporary.open()
        output_file = temporary.fileName()
        temporary.close()

        try:
            # create save options
            options = QgsVectorFileWriter.SaveVectorOptions()
            # driver name
            options.driverName = format_dict['ogrProvider']
            # file encoding
            options.fileEncoding = 'utf-8'

            # coordinate transformation
            if format_dict['forceCRS']:
                options.ct = QgsCoordinateTransform(
                    output_layer.crs(),
                    QgsCoordinateReferenceSystem(format_dict['forceCRS']),
                    QgsProject.instance())

            # datasource options
            if format_dict['ogrDatasourceOptions']:
                options.datasourceOptions = format_dict['ogrDatasourceOptions']

            # write file
            # noinspection PyUnresolvedReferences
            if Qgis.QGIS_VERSION_INT >= 31003:
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                    output_layer,
                    output_file,
                    QgsProject.instance().transformContext(),
                    options)
            else:
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    output_layer,
                    output_file,
                    options)

            if write_result != QgsVectorFileWriter.NoError:
                handler.appendBody(b'')
                self.logger.critical(error_message)
                return False

        except Exception as e:
            handler.appendBody(b'')
            exc_type, _, exc_tb = exc_info()
            self.logger.critical(str(e))
            self.logger.critical(exc_type)
            self.logger.critical('\n'.join(traceback.format_tb(exc_tb)))
            return False

        if format_dict['zip']:
            # compress files
            import zipfile
            try:
                import zlib  # NOQA
                compression = zipfile.ZIP_DEFLATED
            except ImportError:
                compression = zipfile.ZIP_STORED

            # create the zip file
            base_filename = splitext(output_file)[0]
            zip_file_path = join(self.temp_dir, '{}.zip'.format(base_filename))
            with zipfile.ZipFile(zip_file_path, 'w') as zf:

                # Add the main file
                arc_filename = '{}.{}'.format(self.typename, format_dict['filenameExt'])
                zf.write(
                    output_file,
                    compress_type=compression,
                    arcname=arc_filename)

                for extension in format_dict['extToZip']:
                    file_path = join(self.temp_dir, '{}.{}'.format(base_filename, extension))
                    if exists(file_path):
                        arc_filename = '{}.{}'.format(self.typename, extension)
                        zf.write(
                            file_path,
                            compress_type=compression,
                            arcname=arc_filename)

                zf.close()

            f = QFile(zip_file_path)
            if f.open(QFile.ReadOnly):
                ba = f.readAll()
                handler.appendBody(ba)
                return True

        else:
            # return the file created without zip
            f = QFile(output_file)
            if f.open(QFile.ReadOnly):
                ba = f.readAll()
                handler.appendBody(ba)
                return True

        handler.appendBody(b'')
        self.logger.critical('Error no output file')
        return False

    def responseComplete(self):
        self.logger.info('WFSFilter.responseComplete')

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
                with open(join(self.temp_dir, '{}.gml'.format(self.filename)), 'a') as f:
                    f.write('</wfs:FeatureCollection>')
                self.send_output_file(handler)

            self.format = None
            self.allgml = False
            return

        if request == 'GETCAPABILITIES':
            data = handler.body().data()
            dom = minidom.parseString(data)
            ver = dom.documentElement.attributes['version'].value
            if ver == '1.0.0':
                for gfNode in dom.getElementsByTagName('GetFeature'):
                    _ = gfNode
                    for rfNode in dom.getElementsByTagName('ResultFormat'):
                        for k in WFSFormats.keys():
                            f_node = dom.createElement(k.upper())
                            rfNode.appendChild(f_node)
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
                                v_node = dom.createElement('ows:Value')
                                v_text = dom.createTextNode(k.upper())
                                v_node.appendChild(v_text)
                                paramNode.appendChild(v_node)
            handler.clearBody()
            handler.appendBody(dom.toxml('utf-8'))
            return
