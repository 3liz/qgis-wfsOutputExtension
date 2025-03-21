import configparser
import glob
import logging
import os
import sys
import tempfile
import warnings


from pathlib import Path


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    try:
        import gdal
    except ImportError:
        from osgeo import gdal

import lxml.etree
import pytest

from qgis.PyQt import Qt

LOGGER = logging.getLogger('server')
LOGGER.setLevel(logging.DEBUG)

from typing import Any, Dict, Generator

from qgis.core import Qgis, QgsApplication, QgsFontUtils, QgsProject
from qgis.server import (
    QgsBufferServerRequest,
    QgsBufferServerResponse,
    QgsServer,
    QgsServerRequest,
)

qgis_application = None


def pytest_addoption(parser):
    parser.addoption("--qgis-plugins", metavar="PATH", help="Plugin path", default=None)


plugin_path = None


def pytest_report_header(config):
    message = f'QGIS : {Qgis.QGIS_VERSION_INT}\n'
    message += f'Python GDAL : {gdal.VersionInfo("VERSION_NUM")}\n'
    message += f'Python : {sys.version}\n'
    # message += 'Python path : {}'.format(sys.path)
    message += f'QT : {Qt.QT_VERSION_STR}'
    return message


def pytest_configure(config):
    global plugin_path
    plugin_path = config.getoption('qgis_plugins')


def pytest_sessionstart(session):
    """ Start qgis application
    """
    global qgis_application
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    # Define this in global environment
    # os.environ['QGIS_DISABLE_MESSAGE_HOOKS'] = 1
    # os.environ['QGIS_NO_OVERRIDE_IMPORT'] = 1
    qgis_application = QgsApplication([], False)
    qgis_application.initQgis()

    # Install logger hook
    install_logger_hook()


def pytest_sessionfinish(session, exitstatus):
    """ End qgis session
    """
    global qgis_application
    qgis_application.exitQgis()
    del qgis_application


NAMESPACES = {
    'xlink': "http://www.w3.org/1999/xlink",
    'wms': "http://www.opengis.net/wms",
    'wfs': "http://www.opengis.net/wfs",
    'wcs': "http://www.opengis.net/wcs",
    'ows': "http://www.opengis.net/ows/1.1",
    'gml': "http://www.opengis.net/gml",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance"
}


class OWSResponse:

    def __init__(self, resp: QgsBufferServerResponse, dir: Path) -> None:
        self._resp = resp
        self._xml = None
        self._dir = dir

    @property
    def xml(self) -> 'xml':
        if self._xml is None and self._resp.headers().get('Content-Type', '').find('text/xml') == 0:
            self._xml = lxml.etree.fromstring(self.content.decode('utf-8'))
        return self._xml

    @property
    def content(self) -> bytes:
        return bytes(self._resp.body())

    def file(self, extension) -> str:
        _, path = tempfile.mkstemp(
            prefix="test-",
            suffix=f".{extension}",
            dir=str(self._dir.joinpath('tmp')),
        )
        f = open(path, 'wb')
        f.write(self.content)
        f.close()
        return path

    @property
    def status_code(self) -> int:
        return self._resp.statusCode()

    @property
    def headers(self) -> Dict[str, str]:
        return self._resp.headers()

    def xpath(self, path: str) -> lxml.etree.Element:
        assert self.xml is not None
        return self.xml.xpath(path, namespaces=NAMESPACES)

    def xpath_text(self, path: str) -> str:
        assert self.xml is not None
        return ' '.join(e.text for e in self.xpath(path))



@pytest.fixture(scope='session')
def client(request):
    """ Return a qgis server instance
    """
    class _Client:

        def __init__(self) -> None:
            # noinspection PyArgumentList
            self.fontFamily = QgsFontUtils.standardTestFontFamily()
            # noinspection PyCallByClass,PyArgumentList
            QgsFontUtils.loadStandardTestFonts(['All'])

            # Activate debug headers
            os.environ['QGIS_WMTS_CACHE_DEBUG_HEADERS'] = 'true'

            self.rootdir  = request.config.rootdir
            self.datapath = request.config.rootdir.join('data')
            self.server = QgsServer()

            # Load plugins
            load_plugins(self.server.serverInterface())

        def getplugin(self, name) -> Any:
            """ retourne l'instance du plugin
            """
            return server_plugins.get(name)

        def getprojectpath(self, name: str) -> str:
            return self.datapath.join(name)

        def get(self, query: str, project: str=None) -> OWSResponse:
            """ Return server response from query
            """
            request = QgsBufferServerRequest(query, QgsServerRequest.GetMethod, {}, None)
            response = QgsBufferServerResponse()
            if project is not None and not os.path.isabs(project):
                projectpath = self.datapath.join(project)
                qgsproject = QgsProject()
                if not qgsproject.read(projectpath.strpath):
                    raise ValueError(f"Error reading project '{projectpath.strpath}':")
            else:
                qgsproject = None
            self.server.handleRequest(request, response, project=qgsproject)
            return OWSResponse(response, dir=Path(self.rootdir.strpath))

    return _Client()


##
## Plugins
##

def checkQgisVersion(minver: str, maxver: str) -> bool:

    def to_int(ver):
        major, *ver = ver.split('.')
        major = int(major)
        minor = int(ver[0]) if len(ver) > 0 else 0
        rev = int(ver[1]) if len(ver) > 1 else 0
        if minor >= 99:
            minor = rev = 0
            major += 1
        if rev > 99:
            rev = 99
        return int(f"{major:d}{minor:02d}{rev:02d}")


    version = to_int(Qgis.QGIS_VERSION.split('-')[0])
    minver = to_int(minver) if minver else version
    maxver = to_int(maxver) if maxver else version
    return minver <= version <= maxver


def find_plugins(pluginpath: str) -> Generator[str,None,None]:
    """ Load plugins
    """
    for plugin in glob.glob(os.path.join(plugin_path + "/*")):
        if not os.path.exists(os.path.join(plugin, '__init__.py')):
            continue

        metadatafile = os.path.join(plugin, 'metadata.txt')
        if not os.path.exists(metadatafile):
            continue

        cp = configparser.ConfigParser()
        try:
            with open(metadatafile) as f:
                cp.read_file(f)
            if not cp['general'].getboolean('server'):
                logging.critical(f"{plugin} is not a server plugin")
                continue

            minver = cp['general'].get('qgisMinimumVersion')
            maxver = cp['general'].get('qgisMaximumVersion')
        except Exception as exc:
            LOGGER.critical(f"Error reading plugin metadata '{metadatafile}': {exc}", metadatafile, exc)
            continue

        if not checkQgisVersion(minver, maxver):
            LOGGER.critical(
                f"Unsupported version for {plugin}:"
                f"\n MinimumVersion: {minver}"
                f"\n MaximumVersion: {maxver}"
                f"\n Qgis version: {Qgis.QGIS_VERSION.split('-')[0]}"
                "\n Discarding"
            )
            continue

        yield os.path.basename(plugin)


server_plugins = {}


def load_plugins(serverIface: 'QgsServerInterface') -> None:
    """ Start all plugins
    """
    if not plugin_path:
        return

    LOGGER.info(f"Initializing plugins from {plugin_path}")
    sys.path.append(plugin_path)

    for plugin in find_plugins(plugin_path):
        try:
            __import__(plugin)

            package = sys.modules[plugin]

            # Initialize the plugin
            server_plugins[plugin] = package.serverClassFactory(serverIface)
            LOGGER.info(f"Loaded plugin {plugin}")
        except:
            LOGGER.error(f"Error loading plugin {plugin}")
            raise


#
# Logger hook
#

def install_logger_hook() -> None:
    """ Install message log hook
    """
    from qgis.core import Qgis, QgsApplication

    # Add a hook to qgis  message log
    def writelogmessage(message, tag, level):
        arg = f'{tag}: {message}'
        if level == Qgis.Warning:
            LOGGER.warning(arg)
        elif level == Qgis.Critical:
            LOGGER.error(arg)
        else:
            LOGGER.info(arg)

    messageLog = QgsApplication.messageLog()
    messageLog.messageReceived.connect(writelogmessage)
