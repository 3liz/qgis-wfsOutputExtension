import logging

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def test_getcapabilties(client):
    """ Test GetCapabilities. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetCapabilities&"
        f"MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert rv.headers.get('Content-Type', '').find('text/xml') == 0

    data = rv.content.decode('utf-8')

    # Formats
    expected = ['SHP', 'KML', 'GPKG']
    for output_format in expected:
        assert f"<ows:Value>{output_format}</ows:Value>" in data, output_format

    # Layers
    layers = ['éàIncê', 'lines']
    for layer in layers:
        assert f'<Name>{layer}</Name>' in data
