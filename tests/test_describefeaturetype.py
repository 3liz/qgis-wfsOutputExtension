import logging

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def test_describefeaturetype(client):
    """ Test DescribeFeatureType. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=DescribeFeatureType&"
        "OUTPUTFORMAT=GEOJSON&"  # Does not have an effet, it's still XML below ?
        "TYPENAME=éàIncê&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert rv.headers.get('Content-Type', '').find('text/xml') == 0

    data = rv.content.decode('utf-8')

    expected = [
        'name="geometry"',
        'name="id"',
        'name="name"',
    ]
    for item in expected:
        assert item in data
