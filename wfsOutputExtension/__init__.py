__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

from wfsOutputExtension.logging import Logger
from wfsOutputExtension.plausible import Plausible


# noinspection PyPep8Naming
def classFactory(iface):
    from qgis.PyQt.QtWidgets import QMessageBox

    class Nothing:

        # noinspection PyShadowingNames
        def __init__(self, iface):
            """ In QGIS Desktop.

            :param iface: The QGIS Desktop interface
            """
            self.iface = iface

        # noinspection PyPep8Naming
        def initGui(self):
            # noinspection PyArgumentList
            QMessageBox.warning(
                self.iface.mainWindow(),
                'WfsOutputExtension plugin',
                'WfsOutputExtension is plugin for QGIS Server. There is nothing in QGIS Desktop.',
            )

        def unload(self):
            pass

    return Nothing(iface)


class WfsOutputExtensionServer:
    """Plugin for QGIS server

    This plugin loads wfs filter"""

    def __init__(self, server_iface):
        self.serverIface = server_iface
        self.logger = Logger()

        # noinspection PyBroadException
        try:
            self.plausible = Plausible()
            self.plausible.request_stat_event()
        except Exception as e:
            self.logger.log_exception(e)
            self.logger.critical('Error while calling the API stats')

        from .wfs_filter import WFSFilter
        server_iface.registerFilter(WFSFilter(server_iface), 50)


# noinspection PyPep8Naming
def serverClassFactory(server_iface):
    """Load wfsOutputExtensionServer class from file wfsOutputExtension.

    :param server_iface: A QGIS Server interface instance.
    :type server_iface: QgsServerInterface
    """
    return WfsOutputExtensionServer(server_iface)
