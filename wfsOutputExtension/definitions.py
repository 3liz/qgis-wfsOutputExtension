__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

PLUGIN = 'WfsOutputExtension'


WFSFormats = {
    'shp': {
        'contentType': 'application/x-zipped-shp',
        'filenameExt': 'shp',
        'forceCRS': None,
        'ogrProvider': 'ESRI Shapefile',
        'ogrDatasourceOptions': None,
        'zip': True,
        'extToZip': ['shx', 'dbf', 'prj']
    },
    'tab': {
        'contentType': 'application/x-zipped-tab',
        'filenameExt': 'tab',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions': None,
        'zip': True,
        'extToZip': ['dat', 'map', 'id']
    },
    'mif': {
        'contentType': 'application/x-zipped-mif',
        'filenameExt': 'mif',
        'forceCRS': None,
        'ogrProvider': 'Mapinfo File',
        'ogrDatasourceOptions': ['FORMAT=MIF'],
        'zip': True,
        'extToZip': ['mid']
    },
    'kml': {
        'contentType': 'application/vnd.google-earth.kml+xml',
        'filenameExt': 'kml',
        'forceCRS': 'EPSG:4326',
        'ogrProvider': 'KML',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'gpkg': {
        'contentType': 'application/geopackage+vnd.sqlite3',
        'filenameExt': 'gpkg',
        'forceCRS': None,
        'ogrProvider': 'GPKG',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'gpx': {
        'contentType': 'application/gpx+xml',
        'filenameExt': 'gpx',
        'forceCRS': 'EPSG:4326',
        'ogrProvider': 'GPX',
        'ogrDatasourceOptions': [
            'GPX_USE_EXTENSIONS=YES',
            'GPX_EXTENSIONS_NS=ogr',
            'GPX_EXTENSION_NS_URL=http://osgeo.org/gdal',
        ],
        'zip': False,
        'extToZip': []
    },
    'ods': {
        'contentType': 'application/vnd.oasis.opendocument.spreadsheet',
        'filenameExt': 'ods',
        'forceCRS': None,
        'ogrProvider': 'ODS',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'xlsx': {
        'contentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'filenameExt': 'xlsx',
        'forceCRS': None,
        'ogrProvider': 'XLSX',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    },
    'csv': {
        'contentType': 'text/csv',
        'filenameExt': 'csv',
        'forceCRS': None,
        'ogrProvider': 'CSV',
        'ogrDatasourceOptions': None,
        'zip': False,
        'extToZip': []
    }
}
