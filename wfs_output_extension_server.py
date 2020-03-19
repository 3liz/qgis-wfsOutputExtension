__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'
__revision__ = '$Format:%H$'


class WfsOutputExtensionServer:
    """Plugin for QGIS server
    this plugin loads wfs filter"""

    def __init__(self, serverIface):
        self.serverIface = serverIface

        from .wfs_filter import WFSFilter
        serverIface.registerFilter(WFSFilter(serverIface), 50)
