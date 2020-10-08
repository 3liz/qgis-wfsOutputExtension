import logging

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'france_parts.qgs'


def test_getcapabilties(client):
    """Test Get Capabilities for WFS."""
    query_string = (
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetCapabilities&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200

    assert rv.headers.get('Content-Type', '').find('text/xml') == 0
    # To be continued, this is not a valid GetCapabilities request, it's a QGIS Server error
