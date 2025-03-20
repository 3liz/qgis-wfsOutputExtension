__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.dom import minidom

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.server import (
    QgsBufferServerRequest,
    QgsBufferServerResponse,
    QgsRequestHandler,
    QgsServerFilter,
    QgsServerInterface,
    QgsServerRequest,
)

from wfsOutputExtension.definitions import Format, OutputFormats
from wfsOutputExtension.logging import Logger, log_function


class ProcessingRequestException(Exception):
    """When an exception occurs during the process."""
    pass


# Execution context, created for each request
@dataclass
class Context:
    output_format: str
    typename: str
    filename: str
    base_name_target: str
    temp_dir: Path
    format_definition: Format
    # Optional for debugging and keep the intermediate files
    lock_dir: Optional[tempfile.TemporaryDirectory] = None
    all_gml: bool = False


TRUESTR = ('yes', 'true', '1')
TMPDIR_PREFIX = "QGIS_WfsOutputExtension-"


class WFSFilter(QgsServerFilter):
    @log_function
    def __init__(self, server_iface: QgsServerInterface) -> None:
        super().__init__(server_iface)
        self.server_iface = server_iface
        self.logger = Logger()
        self.debug_mode = os.getenv("DEBUG_WFSOUTPUTEXTENSION", "").lower() in TRUESTR
        # XXX: we need to hold a reference to the context
        # because of the QgsServerFilter implementation
        self.context: Optional[Context] = None

    @log_function
    def requestReady(self):
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

        # Create temporary directory
        if self.debug_mode:
            lock_dir = None
            temp_dir = Path(tempfile.mkdtemp(prefix=TMPDIR_PREFIX))
        else:
            # Removed when deleted
            lock_dir = tempfile.TemporaryDirectory(prefix=TMPDIR_PREFIX)
            temp_dir = Path(lock_dir.name)

        base_name_target = f"to-{output_format}"

        # Create the request context
        self.context = Context(
            output_format=output_format,
            format_definition=format_definition,
            typename=params.get('TYPENAME', ''),
            filename='gml_features',
            base_name_target=base_name_target,
            lock_dir=lock_dir,
            temp_dir=temp_dir,
        )

        # set headers
        handler.clear()
        handler.setResponseHeader('Content-Type', format_definition.content_type)
        if format_definition.zip:
            handler.setResponseHeader(
                'Content-Disposition', f'attachment; filename="{self.context.typename}.zip"')
        else:
            handler.setResponseHeader(
                'Content-Disposition',
                f'attachment; filename="{self.context.typename}.{format_definition.filename_ext}"')

    def sendResponse(self) -> None:
        # if the context is null, nothing to do
        if not self.context:
            return

        context = self.context

        handler = self.serverInterface().requestHandler()

        # write body in GML temp file
        data = handler.body().data().decode('utf8')
        output_file = self.context.temp_dir.joinpath(f'{context.filename}.gml')

        with output_file.open('ab') as f:
            if data.find('xsi:schemaLocation') == -1:
                # noinspection PyTypeChecker
                f.write(handler.body())
            else:
                # to avoid that QGIS Server/OGR loads schemas when reading GML
                import re
                data = re.sub(r'xsi:schemaLocation=\".*\"', 'xsi:schemaLocation=""', data)
                f.write(data.encode('utf8'))

        format_definition = context.format_definition

        # change the headers
        # update content-type and content-disposition
        if not handler.headersSent():
            handler.clear()
            handler.setResponseHeader('Content-Type', format_definition.content_type)
            if format_definition.zip:
                handler.setResponseHeader(
                    'Content-Disposition', f'attachment; filename="{context.typename}.zip"')
            else:
                handler.setResponseHeader(
                    'Content-Disposition',
                    f'attachment; filename="{context.typename}.{format_definition.filename_ext}"')
        else:
            handler.clearBody()

        if data.rstrip().endswith('</wfs:FeatureCollection>'):
            # all the gml has been intercepted
            context.all_gml = True
            self.send_output_file(handler, context)

    @log_function
    def send_output_file(self, handler: QgsRequestHandler, context: Context) -> None:
        """ Process the request.

        :raise ProcessingRequestException when there is an error
        """
        format_definition = context.format_definition
        self.logger.info(f"WFS request to get format {format_definition.ogr_provider}")

        # Fetch the XSD
        type_name = context.typename
        headers = handler.requestHeaders()
        result = self.xsd_for_layer(type_name, headers, context)

        # read the GML
        gml_path = context.temp_dir.joinpath(f'{context.filename}.gml')
        gml_url = f"{gml_path}|option:FORCE_SRS_DETECTION=YES" if result else f"{gml_path}"
        output_layer = QgsVectorLayer(gml_url, 'qgis_server_wfs_features', 'ogr')

        self.logger.info(f"Temporary GML file is {gml_url}")

        if not output_layer.isValid():
            handler.appendBody(b'')
            raise ProcessingRequestException(f'Output layer {gml_url} is not valid.')

        # Temporary file where to write the output
        output_file = context.temp_dir.joinpath(
            f"{context.base_name_target}.{format_definition.filename_ext}",
        )

        self.logger.info(f"Temporary {format_definition.filename_ext} file is {output_file}")

        try:
            # create save options
            options = QgsVectorFileWriter.SaveVectorOptions()
            # driver name
            options.driverName = format_definition.ogr_provider
            # file encoding
            options.fileEncoding = 'utf-8'

            # coordinate transformation
            if format_definition.force_crs:
                # noinspection PyArgumentList
                options.ct = QgsCoordinateTransform(
                    output_layer.crs(),
                    QgsCoordinateReferenceSystem(format_definition.force_crs),
                    QgsProject.instance())

            # datasource options
            if format_definition.ogr_datasource_options:
                options.datasourceOptions = format_definition.ogr_datasource_options

            # write file
            # noinspection PyArgumentList
            write_result, error_message, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                output_layer,
                str(output_file),
                QgsProject.instance().transformContext(),
                options)

            # noinspection PyUnresolvedReferences
            if write_result != QgsVectorFileWriter.NoError:
                handler.appendBody(b'')
                self.logger.critical(error_message)
                return False

        except Exception:
            handler.appendBody(b'')
            raise

        if format_definition == OutputFormats.Shp:
            # For SHP, we add the CPG, #55
            cpg_file = context.temp_dir.joinpath(f"{context.base_name_target}.cpg")
            with cpg_file.open('w', encoding='utf8') as f:
                f.write(f"{options.fileEncoding}\n")

        if format_definition.zip:
            # compress files
            import zipfile
            try:
                import zlib  # noqa
                compression = zipfile.ZIP_DEFLATED
            except ImportError:
                compression = zipfile.ZIP_STORED

            # create the zip file
            zip_file_path = context.temp_dir.joinpath(f"{context.base_name_target}.zip")
            self.logger.info(f"Zipping the output in {zip_file_path}")
            with zipfile.ZipFile(zip_file_path, 'w') as zf:

                # Add the main file
                arc_filename = f'{context.typename}.{format_definition.filename_ext}'
                zf.write(
                    output_file,
                    compress_type=compression,
                    arcname=arc_filename,
                )

                for extension in format_definition.ext_to_zip:
                    file_path = context.temp_dir.joinpath(f'{context.base_name_target}.{extension}')
                    if file_path.exists():
                        arc_filename = f'{context.typename}.{extension}'
                        zf.write(
                            file_path,
                            compress_type=compression,
                            arcname=arc_filename,
                        )

                zf.close()

            with zip_file_path.open("rb") as f:
                handler.appendBody(f.read())
                return True

        else:
            self.logger.info("Sending the output file")
            # return the file created without zip
            with output_file.open("rb") as f:
                handler.appendBody(f.read())
                return True

        handler.appendBody(b'')
        self.logger.critical('Error no output file')
        return False

    @log_function
    def xsd_for_layer(self, type_name: str, headers: dict, context: Context) -> bool:

        """ Get the XSD describing the layer. """
        # noinspection PyArgumentList
        project = QgsProject.instance()
        parameters = {
            "MAP": project.fileName(),
            "SERVICE": "WFS",
            "VERSION": "1.0.0",
            "REQUEST": "DescribeFeatureType",
            "TYPENAME": type_name,
            "OUTPUT": "XMLSCHEMA",
        }

        query_string = "?" + "&".join(f"{key}={value}" for key, value in parameters.items())
        # noinspection PyUnresolvedReferences
        request = QgsBufferServerRequest(
            query_string,
            QgsServerRequest.GetMethod,
            headers,
            None,
        )
        service = self.server_iface.serviceRegistry().getService('WFS', '1.0.0')
        response = QgsBufferServerResponse()
        service.executeRequest(request, response, project)
        # Flush otherwise the body is empty
        response.flush()
        self.logger.info(f"Fetching XSD : HTTP code {response.statusCode()}, request {query_string}")
        # noinspection PyTypeChecker
        content = bytes(response.body()).decode('utf8')
        if content == "":
            self.logger.critical("Content for the XSD request is empty.")
            return False

        if response.statusCode() != 200:
            self.logger.critical(f"HTTP error when requesting the XSD : return {response.statusCode()}")
            return False

        with context.temp_dir.joinpath(f'{context.filename}.xsd').open('w') as f:
            f.write(content)

        return True

    @log_function
    def responseComplete(self) -> None:

        context = self.context

        # Remove current context
        self.context = None

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

        if request == 'GETFEATURE' and context:
            if not context.all_gml:
                try:
                    # all the gml has not been intercepted in sendResponse
                    handler.clearBody()
                    with context.temp_dir.joinpath(f'{context.filename}.gml').open('a') as f:
                        f.write('</wfs:FeatureCollection>')
                    self.send_output_file(handler, context)
                except Exception as e:
                    self.logger.critical("Critical exception when processing the request :")
                    self.logger.log_exception(e)
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
