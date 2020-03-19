"""
/***************************************************************************
    QGIS Server Plugin Filters: Add Output Formats to GetFeature request
    ---------------------
    Date                 : October 2015
    Copyright            : (C) 2015 by René-Luc D'Hont - 3Liz
    Email                : rldhont at 3liz dot com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'DHONT René-Luc'
__date__ = 'October 2015'
__copyright__ = '(C) 2015, DHONT René-Luc - 3Liz'


class WfsOutputExtensionServer:
    """Plugin for QGIS server
    this plugin loads wfs filter"""

    def __init__(self, serverIface):
        self.serverIface = serverIface

        from .wfs_filter import WFSFilter
        serverIface.registerFilter(WFSFilter(serverIface), 50)
