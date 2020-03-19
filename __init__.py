__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'
__revision__ = '$Format:%H$'


def classFactory(iface):
    from qgis.PyQt.QtWidgets import QMessageBox

    class Nothing:

        def __init__(self, iface):
            self.iface = iface

        def initGui(self):
            QMessageBox.warning(
                self.iface.mainWindow(),
                'WfsOutputExtension plugin',
                'WfsOutputExtension is plugin for QGIS Server. There is nothing in QGIS Desktop.',
            )

        def unload(self):
            pass

    return Nothing(iface)


def serverClassFactory(serverIface):
    """Load wfsOutputExtensionServer class from file wfsOutputExtension.

    :param serverIface: A QGIS Server interface instance.
    :type serverIface: QgsServerInterface
    """
    from .wfs_output_extension_server import WfsOutputExtensionServer
    return WfsOutputExtensionServer(serverIface)
