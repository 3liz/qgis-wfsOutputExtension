import logging
import pytest

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
    _test_vector_layer(rv.file('gml'), 'GML')


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
    _test_vector_layer(rv.file('gpkg'), 'GPKG')


@pytest.mark.xfail
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
    _test_vector_layer(rv.file('gpx'), 'GPX')


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
    _test_vector_layer(rv.file('ods'), 'ODS')


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
    _test_vector_layer(rv.file('geojson'), 'GeoJSON')


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
    _test_vector_layer(rv.file('xlsx'), 'XLSX')


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
    _test_vector_layer(rv.file('csv'), 'CSV')


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
    _test_vector_layer('/vsizip/' + rv.file('zip'), 'ESRI Shapefile')


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
    _test_vector_layer('/vsizip/' + rv.file('zip') + '/lines.tab', 'MapInfo File')


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
    _test_vector_layer('/vsizip/' + rv.file('zip') + '/lines.mif', 'MapInfo File')
