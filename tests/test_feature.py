import logging

from qgis.core import QgsVectorLayer

LOGGER = logging.getLogger('server')

__copyright__ = 'Copyright 2020, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PROJECT = 'lines.qgs'


def _test_vector_layer(file_path, storage, provider='ogr') -> QgsVectorLayer:
    layer = QgsVectorLayer(file_path, 'test', provider)
    assert layer.isValid()
    assert layer.featureCount() == 4
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
    assert layer.fields().names() == ['gml_id', 'id', 'name']
    assert layer.uniqueValues(0) == {'lines.1', 'lines.2', 'lines.3', 'lines.4'}
    assert layer.uniqueValues(1) == {1, 2, 3, 4}
    assert layer.uniqueValues(2) == {'éù%@ > 1', '(]~€ > 2', '<![CDATA[Line < 3]]>', '<![CDATA[Line < 4]]>'}


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
    assert layer.fields().names() == ['fid', 'gml_id', 'id', 'name']


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
    assert layer.fields().names() == [
        'name', 'cmt', 'desc', 'src', 'link1_href', 'link1_text', 'link1_type', 'link2_href', 'link2_text',
        'link2_type', 'number', 'type', 'ogr_gml_id', 'ogr_id']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
    assert layer.fields().names() == ['id', 'name']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
    assert layer.fields().names() == ['gml_id', 'id', 'name']


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
