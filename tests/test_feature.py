import logging

from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import NULL

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def _test_list(list_a, list_b):
    assert len(list_a) == len(list_b)
    for item in list_a:
        assert item in list_b


def _test_vector_layer(file_path, storage, provider='ogr', count=4) -> QgsVectorLayer:
    layer = QgsVectorLayer(file_path, 'test', provider)
    assert layer.isValid()
    assert layer.featureCount() == count
    assert layer.storageType() == storage, layer.storageType()
    return layer


def test_getfeature_gml(client):
    """ Test GetFeature as GML. """
    # Default format
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'text/xml' in rv.headers.get('Content-Type'), rv.headers
    layer = _test_vector_layer(rv.file('gml'), 'GML')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])
    assert layer.uniqueValues(0) == {'lines.1', 'lines.2', 'lines.3', 'lines.4'}
    assert layer.uniqueValues(1) == {1, 2, 3, 4}
    assert layer.uniqueValues(2) == {'éù%@ > 1', '(]~€ > 2', '<![CDATA[Line < 3]]>', '05200'}


def test_getfeature_kml(client):
    """ Test GetFeature as KML. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=KML&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/vnd.google-earth.kml+xml' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer(rv.file('kml'), 'LIBKML')
    assert layer.crs().authid() == 'EPSG:4326'

    _test_list(
        layer.fields().names(),
        [
            'Name', 'description', 'timestamp', 'begin', 'end', 'altitudeMode', 'tessellate', 'extrude',
            'visibility', 'drawOrder', 'icon', 'gml_id', 'id', 'comment',
        ]
    )

    # Trailing 0
    index = layer.fields().indexFromName('Name')  # Name is capitalized for GML
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_gpkg(client):
    """ Test GetFeature as GPKG. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=GPKG&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/geopackage+vnd.sqlite3' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer(rv.file('gpkg'), 'GPKG')
    _test_list(layer.fields().names(), ['fid', 'gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_gpx(client):
    """ Test GetFeature as GPX. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=GPX&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/gpx+xml' in rv.headers.get('Content-type'), rv.headers

    # Lines is translated as routes
    layer = _test_vector_layer(rv.file('gpx') + '|layername=routes', 'GPX')
    _test_list(layer.fields().names(), [
        'name', 'cmt', 'desc', 'src', 'link1_href', 'link1_text', 'link1_type', 'link2_href', 'link2_text',
        'ogr_comment', 'link2_type', 'number', 'type', 'ogr_gml_id', 'ogr_id'])

    # GPX is a specific format with some pre-defined field names
    # Checking "name"
    assert layer.fields().indexFromName('name') == 0
    assert layer.uniqueValues(0) == {'éù%@ > 1', '(]~€ > 2', '<![CDATA[Line < 3]]>', '05200'}

    # Checking "desc"
    assert layer.fields().indexFromName('desc') == 2
    assert layer.uniqueValues(2) == {NULL}

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_ods(client):
    """ Test GetFeature as ODS. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=ODS&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/vnd.oasis.opendocument.spreadsheet' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer(rv.file('ods'), 'ODS')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_geojson(client):
    """ Test GetFeature as GeoJSON. """
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
    assert 'application/vnd.geo+json' in rv.headers.get('Content-Type'), rv.headers
    layer = _test_vector_layer(rv.file('geojson'), 'GeoJSON')
    _test_list(layer.fields().names(), ['id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_excel(client):
    """ Test GetFeature as Excel. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=XLSX&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    expected = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert expected in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer(rv.file('xlsx'), 'XLSX')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_csv(client):
    """ Test GetFeature as CSV. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=CSV&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'text/csv' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer(rv.file('csv'), 'CSV')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_shapefile(client):
    """ Test GetFeature as Shapefile. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=SHP&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/x-zipped-shp" in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer('/vsizip/' + rv.file('zip'), 'ESRI Shapefile')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_tab(client):
    """ Test GetFeature as TAB. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=TAB&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/x-zipped-tab' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer('/vsizip/' + rv.file('zip') + '/lines.tab', 'MapInfo File')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_mif(client):
    """ Test GetFeature as MIF. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=MIF&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/x-zipped-mif' in rv.headers.get('Content-type'), rv.headers
    layer = _test_vector_layer('/vsizip/' + rv.file('zip') + '/lines.mif', 'MapInfo File')
    _test_list(layer.fields().names(), ['gml_id', 'id', 'name', 'comment'])

    # Trailing 0
    index = layer.fields().indexFromName('name')
    assert '05200' in layer.uniqueValues(index)


def test_getfeature_layer_name_with_accent(client):
    """ Test a layer name with accent. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=éàIncê&"
        "OUTPUTFORMAT=CSV&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'text/csv' in rv.headers.get('Content-type'), rv.headers
    assert 'attachment; filename="éàIncê.csv"' in rv.headers.get('Content-Disposition')


def test_getfeature_geojson_with_selection(client):
    """ Test GetFeature as GeoJSON with a selection. """
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=GeoJSON&"
        "FEATUREID=lines.1,lines.2&"
        "MAP={}"
    ).format(PROJECT)
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert 'application/vnd.geo+json' in rv.headers.get('Content-Type'), rv.headers
    layer = _test_vector_layer(rv.file('geojson'), 'GeoJSON', count=2)
    _test_list(layer.fields().names(), ['id', 'name', 'comment'])
