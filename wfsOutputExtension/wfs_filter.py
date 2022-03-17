__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import os
import tempfile
import time

from os import listdir, makedirs, remove
from os.path import basename, exists, join, splitext
from xml.dom import minidom

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QFile, QTemporaryFile
from qgis.server import QgsServerFilter

from wfsOutputExtension.definitions import OutputFormats
from wfsOutputExtension.logging import Logger, log_function


class ProcessingRequestException(Exception):
    """When an exception occurs during the process."""
    pass


class WFSFilter(QgsServerFilter):

    @log_function
    def __init__(self, server_iface):
        super(WFSFilter, self).__init__(server_iface)
        self.logger = Logger()

        self.format = None
        self.typename = ""
        self.filename = ""
        self.base_name_target = None
        self.all_gml = False

        self.temp_dir = join(tempfile.gettempdir(), 'QGIS_WfsOutputExtension')
        # self.temp_dir = '/src/'  # Use ONLY in debug for docker

        self.debug_mode = os.environ.get(
            'DEBUG_WFSOUTPUTEXTENSION', 'true').upper() in ('TRUE', '1')

        # Fix race-condition if multiple servers are run concurrently
        makedirs(self.temp_dir, exist_ok=True)
        self.logger.info('Temporary directory is {}'.format(self.temp_dir))

    @log_function
    def requestReady(self):
        self.format = None
        self.all_gml = False

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
        output_format = params.get('OUTPUTFORMAT', '').lower()

        format_definition = OutputFormats.find(output_format)
        if not format_definition:
            return

        handler.setParameter('OUTPUTFORMAT', 'GML2')
        self.format = output_format
        self.typename = params.get('TYPENAME', '')
        self.filename = 'gml_features_{}'.format(time.time())

        # set headers
        handler.clear()
        handler.setResponseHeader('Content-Type', format_definition.content_type)
        if format_definition.zip:
            handler.setResponseHeader(
                'Content-Disposition', 'attachment; filename="{}.zip"'.format(self.typename))
        else:
            handler.setResponseHeader(
                'Content-Disposition',
                'attachment; filename="{}.{}"'.format(self.typename, format_definition.filename_ext))

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

        format_definition = OutputFormats.find(self.format)

        # change the headers
        # update content-type and content-disposition
        if not handler.headersSent():
            handler.clear()
            handler.setResponseHeader('Content-type', format_definition.content_type)
            if format_definition.zip:
                handler.setResponseHeader(
                    'Content-Disposition', 'attachment; filename="{}.zip"'.format(self.typename))
            else:
                handler.setResponseHeader(
                    'Content-Disposition',
                    'attachment; filename="{}.{}"'.format(self.typename, format_definition.filename_ext))
        else:
            handler.clearBody()

        if data.rstrip().endswith('</wfs:FeatureCollection>'):
            # all the gml has been intercepted
            self.all_gml = True
            self.send_output_file(handler)

    @log_function
    def send_output_file(self, handler):
        """ Process the request.

        :raises ProcessingRequestException when there is an errro
        """
        format_definition = OutputFormats.find(self.format)

        # read the GML
        gml_path = join(self.temp_dir, '{}.gml'.format(self.filename))
        output_layer = QgsVectorLayer(gml_path, 'qgis_server_wfs_features', 'ogr')

        self.logger.info("Temporary GML file is {}".format(gml_path))

        if not output_layer.isValid():
            handler.appendBody(b'')
            raise ProcessingRequestException('Output layer {} is not valid.'.format(gml_path))

        # Temporary file where to write the output
        temporary = QTemporaryFile(
            join(self.temp_dir, 'to-{}-XXXXXX.{}'.format(self.format, format_definition.filename_ext)))
        temporary.open()
        output_file = temporary.fileName()
        temporary.remove()  # Fix issue #18
        self.logger.info("Temporary {} file is {}".format(format_definition.filename_ext, output_file))
        self.base_name_target = basename(splitext(output_file)[0])

        try:
            # create save options
            options = QgsVectorFileWriter.SaveVectorOptions()
            # driver name
            options.driverName = format_definition.ogr_provider
            # file encoding
            options.fileEncoding = 'utf-8'

            # coordinate transformation
            if format_definition.force_crs:
                options.ct = QgsCoordinateTransform(
                    output_layer.crs(),
                    QgsCoordinateReferenceSystem(format_definition.force_crs),
                    QgsProject.instance())

            # datasource options
            if format_definition.ogr_datasource_options:
                options.datasourceOptions = format_definition.ogr_datasource_options

            # write file
            # noinspection PyUnresolvedReferences
            if Qgis.QGIS_VERSION_INT >= 32000:
                write_result, error_message, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                    output_layer,
                    output_file,
                    QgsProject.instance().transformContext(),
                    options)
            elif Qgis.QGIS_VERSION_INT >= 31003:
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                    output_layer,
                    output_file,
                    QgsProject.instance().transformContext(),
                    options)
            else:
                # QGIS_VERSION_INT < 31003
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    output_layer,
                    output_file,
                    options)

            if write_result != QgsVectorFileWriter.NoError:
                handler.appendBody(b'')
                self.logger.critical(error_message)
                return False

        except Exception:
            handler.appendBody(b'')
            raise

        if format_definition.zip:
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
            self.logger.info("Zipping the output in {}".format(zip_file_path))
            with zipfile.ZipFile(zip_file_path, 'w') as zf:

                # Add the main file
                arc_filename = '{}.{}'.format(self.typename, format_definition.filename_ext)
                zf.write(
                    output_file,
                    compress_type=compression,
                    arcname=arc_filename)

                for extension in format_definition.ext_to_zip:
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
            self.logger.info("Sending the output file")
            # return the file created without zip
            f = QFile(output_file)
            if f.open(QFile.ReadOnly):
                ba = f.readAll()
                handler.appendBody(ba)
                return True

        handler.appendBody(b'')
        self.logger.critical('Error no output file')
        return False

    @log_function
    def responseComplete(self):
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
            if not self.all_gml:
                try:
                    # all the gml has not been intercepted in sendResponse
                    handler.clearBody()
                    with open(join(self.temp_dir, '{}.gml'.format(self.filename)), 'a') as f:
                        f.write('</wfs:FeatureCollection>')
                    self.send_output_file(handler)
                except Exception as e:
                    self.logger.critical("Critical exception when processing the request :")
                    self.logger.log_exception(e)
                finally:
                    # Find all files associated with the request and remove them
                    for file in listdir(self.temp_dir):
                        if file.startswith(self.filename):  # GML, GFS
                            file_path = join(self.temp_dir, file)
                            if self.debug_mode:
                                self.logger.info(
                                    "DEBUG_WFSOUTPUTEXTENSION is on, not removing {}".format(file_path))
                            else:
                                remove(file_path)

                        if file.startswith(self.base_name_target):  # Target extension, ZIP
                            file_path = join(self.temp_dir, file)
                            if self.debug_mode:
                                self.logger.info(
                                    "DEBUG_WFSOUTPUTEXTENSION is on, not removing {}".format(file_path))
                            else:
                                remove(file_path)

            self.format = None
            self.all_gml = False
            self.filename = None
            self.base_name_target = None
            return

        if request == 'GETCAPABILITIES':
            data = handler.body().data()
            dom = minidom.parseString(data)

            formats_added = False

            if dom.documentElement.attributes['version'].value == '1.0.0':

                for _ in dom.getElementsByTagName('GetFeature'):
                    for result_format_node in dom.getElementsByTagName('ResultFormat'):
                        formats_added = True
                        for output in OutputFormats:
                            format_node = dom.createElement(output.filename_ext.upper())
                            result_format_node.appendChild(format_node)

            else:
                for operation_metadata_node in dom.getElementsByTagName('ows:OperationsMetadata'):
                    for operation_node in operation_metadata_node.getElementsByTagName('ows:Operation'):
                        if 'name' not in operation_node.attributes:
                            continue

                        if operation_node.attributes['name'].value != 'GetFeature':
                            continue

                        for param_node in operation_node.getElementsByTagName('ows:Parameter'):
                            if 'name' not in param_node.attributes:
                                continue

                            if param_node.attributes['name'].value != 'outputFormat':
                                continue

                            formats_added = True
                            for output in OutputFormats:
                                value_node = dom.createElement('ows:Value')
                                text_node = dom.createTextNode(output.filename_ext.upper())
                                value_node.appendChild(text_node)
                                param_node.appendChild(value_node)

            if formats_added:
                self.logger.info("All formats have been added in the GetCapabilities")
            else:
                self.logger.info("No formats have been added in the GetCapabilities")

            handler.clearBody()
            handler.appendBody(dom.toxml('utf-8'))
            return
