import logging

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def test_getfeature(client):
    """Test Get Feature."""
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=GeoJSON&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert rv.headers.get('Content-Type', '').find('application/json') == 0
