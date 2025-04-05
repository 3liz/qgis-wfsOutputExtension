import logging

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def test_describefeaturetype(client):
    """ Test DescribeFeatureType. """
    # XMLSCHEMA is used for the sub request to get the XSD
    outputs = ('XMLSCHEMA', 'GEOJSON')
    for output in outputs:
        query_string = (
            "?"
            "SERVICE=WFS&"
            "VERSION=1.0.0&"
            "REQUEST=DescribeFeatureType&"
            f"OUTPUTFORMAT={output}&"
            "TYPENAME=éàIncê&"
            f"MAP={PROJECT}"
        )
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
            assert item in data, f'The raw data for {output} is : {data}'
