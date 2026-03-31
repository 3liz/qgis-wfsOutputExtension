from pathlib import Path

from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import NULL, QDate, QDateTime, QVariant

from .core.client import Client

PROJECT = "lines.qgs"


def assert_list_equal(list_a: list, list_b: list):
    list_a.sort()
    list_b.sort()
    assert list_a == list_b


def get_test_vector_layer(
    file_path: Path | str,
    storage: str,
    provider="ogr",
    count=4,
) -> QgsVectorLayer:
    layer = QgsVectorLayer(str(file_path), "test", provider)
    assert layer.isValid()
    assert layer.featureCount() == count
    assert layer.storageType() == storage, layer.storageType()
    return layer


def test_getfeature_gml(client: Client):
    """Test GetFeature as GML."""
    # Default format
    query_string = f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&MAP={PROJECT}"
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "text/xml" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("gml"), "GML")
    expected_fields = ["gml_id"]
    expected_fields.extend(["lowerCorner", "upperCorner"])
    expected_fields.extend(["id", "trailing_zero", "name", "comment", "date_time", "date"])
    assert layer.fields().names() == expected_fields

    index = layer.fields().indexFromName("gml_id")
    assert layer.uniqueValues(index) == {"lines.1", "lines.2", "lines.3", "lines.4"}

    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    index = layer.fields().indexFromName("name")
    assert layer.uniqueValues(index) == {"éù%@ > 1", "(]~€ > 2", "Line < 3", "Line name"}


    index = layer.fields().indexFromName("trailing_zero")
    match layer.fields().at(index).type():
        case QVariant.Int:
            # field detected as integer, so losing the trailing zero
            assert layer.uniqueValues(index) == {5200}
        case QVariant.String:
            # In QGIS 4/Gdal 3.10 this is no more interpreted
            # as integer
            assert layer.uniqueValues(index) == {"05200"}
        case unexpected:
            assert False, f"Unexpected field type: {unexpected}"

    # Date time
    index = layer.fields().indexFromName("date_time")
    assert "2023-08-01T12:00:00.000" in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.String

    # Date
    index = layer.fields().indexFromName("date")
    assert "2023-08-01" in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.String


def test_getfeature_kml(client: Client):
    """Test GetFeature as KML."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=KML&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/vnd.google-earth.kml+xml" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("kml"), "LIBKML")
    assert layer.crs().authid() == "EPSG:4326"

    assert_list_equal(
        layer.fields().names(),
        [
            "Name",
            "description",
            "timestamp",
            "begin",
            "end",
            "altitudeMode",
            "tessellate",
            "extrude",
            "visibility",
            "drawOrder",
            "icon",
            "gml_id",
            "id",
            "trailing_zero",
            "comment",
            "date_time",
            "date",
        ],
    )

    # ID
    index = layer.fields().indexFromName("id")
    match layer.fields().at(index).type():
        case QVariant.Int:
            assert layer.uniqueValues(index) == {1, 2, 3, 4}
        case QVariant.String:
            # In QGIS 4/Gdal 3.10 the OGR (LIB)KML driver interpret this as string
            assert layer.uniqueValues(index) == {"1", "2", "3", "4"}
        case unexpected:
            assert False, f"Unexpected field type: {unexpected}"

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_gpkg(client: Client):
    """Test GetFeature as GPKG."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=GPKG&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/geopackage+vnd.sqlite3" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("gpkg"), "GPKG")
    assert_list_equal(
        layer.fields().names(),
        ["fid", "gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_gpx(client: Client):
    """Test GetFeature as GPX."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=GPX&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/gpx+xml" in rv.headers.get("Content-Type", ""), rv.headers

    # Lines is translated as routes
    layer = get_test_vector_layer(f"{rv.file('gpx')}|layername=routes", "GPX")
    assert_list_equal(
        layer.fields().names(),
        [
            "name",
            "cmt",
            "desc",
            "src",
            "link1_href",
            "link1_text",
            "link1_type",
            "link2_href",
            "link2_text",
            "link2_type",
            "number",
            "type",
            "ogr_gml_id",
            "ogr_id",
            "ogr_trailing_zero",
            "ogr_comment",
            "ogr_date_time",
            "ogr_date",
        ],
    )

    # GPX is a specific format with some pre-defined field names
    # ID
    index = layer.fields().indexFromName("ogr_id")
    assert layer.uniqueValues(index) == {1, 2, 3, 4}
    assert layer.fields().at(index).type() == QVariant.Int

    # Checking "name"
    assert layer.fields().indexFromName("name") == 0
    # QGIS 3.24.1 and 3.22.6
    assert layer.uniqueValues(0) == {"éù%@ > 1", "(]~€ > 2", "Line < 3", "Line name"}

    # Checking "desc"
    assert layer.fields().indexFromName("desc") == 2
    assert layer.uniqueValues(2) == {NULL}

    # Trailing 0 not working in GPX
    index = layer.fields().indexFromName("ogr_trailing_zero")
    assert 5200 in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.Int


def test_getfeature_ods(client: Client):
    """Test GetFeature as ODS."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=ODS&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/vnd.oasis.opendocument.spreadsheet" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("ods"), "ODS")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)

    # Date time
    index = layer.fields().indexFromName("date_time")
    assert layer.fields().at(index).type() == QVariant.DateTime
    assert QDateTime(2023, 8, 1, 12, 0) in layer.uniqueValues(index)

    # Date
    index = layer.fields().indexFromName("date")
    assert QDate(2023, 8, 1) in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.Date


def test_getfeature_geojson(client: Client):
    """Test GetFeature as GeoJSON."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=GeoJSON&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/vnd.geo+json" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("geojson"), "GeoJSON")
    assert_list_equal(
        layer.fields().names(),
        ["id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_excel(client: Client):
    """Test GetFeature as Excel."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=XLSX&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    expected = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert expected in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("xlsx"), "XLSX")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)

    # Date time
    index = layer.fields().indexFromName("date_time")
    assert QDateTime(2023, 8, 1, 12, 0) in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.DateTime

    # Date
    index = layer.fields().indexFromName("date")
    assert QDate(2023, 8, 1) in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.Date


def test_getfeature_csv(client: Client):
    """Test GetFeature as CSV."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=CSV&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "text/csv" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("csv"), "CSV")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    # All fields are loaded as string
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.String
    assert layer.uniqueValues(index) == {"1", "2", "3", "4"}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)

    # Date time
    index = layer.fields().indexFromName("date_time")
    assert layer.fields().at(index).type() == QVariant.String
    assert "2023/08/01 12:00:00" in layer.uniqueValues(index)

    # Date
    index = layer.fields().indexFromName("date")
    assert "2023/08/01" in layer.uniqueValues(index)
    assert layer.fields().at(index).type() == QVariant.String


def test_getfeature_shapefile(client: Client):
    """Test GetFeature as Shapefile."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=SHP&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/x-zipped-shp" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(f"/vsizip/{rv.file('zip')}", "ESRI Shapefile")
    # shapefile is splitting trailing_zero to trailing_z
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_z", "name", "comment", "date_time", "date"],
    )
    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.LongLong  # Int to LongLong compare to others
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_z")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_tab(client: Client):
    """Test GetFeature as TAB."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=TAB&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/x-zipped-tab" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(f"/vsizip/{rv.file('zip')}/lines.tab", "MapInfo File")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_mif(client: Client):
    """Test GetFeature as MIF."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=MIF&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/x-zipped-mif" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(f"/vsizip/{rv.file('zip')}/lines.mif", "MapInfo File")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_layer_name_with_accent(client: Client):
    """Test a layer name with accent."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=éàIncê&OUTPUTFORMAT=CSV&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "text/csv" in rv.headers.get("Content-Type", ""), rv.headers
    assert 'attachment; filename="éàIncê.csv"' in rv.headers.get("Content-Disposition", "")


def test_getfeature_geojson_with_selection(client: Client):
    """Test GetFeature as GeoJSON with a selection."""
    query_string = (
        "?"
        "SERVICE=WFS&"
        "VERSION=1.1.0&"
        "REQUEST=GetFeature&"
        "TYPENAME=lines&"
        "OUTPUTFORMAT=GeoJSON&"
        "FEATUREID=lines.1,lines.2&"
        f"MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/vnd.geo+json" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("geojson"), "GeoJSON", count=2)
    assert_list_equal(
        layer.fields().names(),
        ["id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)


def test_getfeature_fgb(client: Client):
    """Test GetFeature as FlatGeobuf."""
    query_string = (
        f"?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=lines&OUTPUTFORMAT=FGB&MAP={PROJECT}"
    )
    rv = client.get(query_string, PROJECT)
    assert rv.status_code == 200
    assert "application/x-fgb" in rv.headers.get("Content-Type", ""), rv.headers
    layer = get_test_vector_layer(rv.file("fgb"), storage="FlatGeobuf")
    assert_list_equal(
        layer.fields().names(),
        ["gml_id", "id", "trailing_zero", "name", "comment", "date_time", "date"],
    )

    # ID
    index = layer.fields().indexFromName("id")
    assert layer.fields().at(index).type() == QVariant.Int
    assert layer.uniqueValues(index) == {1, 2, 3, 4}

    # Trailing 0
    index = layer.fields().indexFromName("trailing_zero")
    assert layer.fields().at(index).type() == QVariant.String
    assert "05200" in layer.uniqueValues(index)

    # Date time
    index = layer.fields().indexFromName("date_time")
    assert layer.fields().at(index).type() == QVariant.DateTime
    assert QDateTime(2023, 8, 1, 12, 0) in layer.uniqueValues(index)

    # Date
    index = layer.fields().indexFromName("date")
    assert layer.fields().at(index).type() == QVariant.DateTime
    assert QDateTime(2023, 8, 1, 0, 0) in layer.uniqueValues(index)
