import os
import re

import fiona
import gdal
import shapely.geometry
import shapely.ops
from tqdm import tqdm


# Total number of quads
filenames = os.listdir('global_data/resolution_50')
print(len(filenames))


# Get total raster extent and save out
extents = list()

for filename in tqdm(filenames):
    raster = gdal.Open(filename)
    cols = raster.RasterXSize
    rows = raster.RasterYSize
    llx, xres, _, y0, _, yres = raster.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])
    extent = shapely.geometry.Polygon([(llx, lly), (llx, ury), (urx, ury), (urx, lly), (llx, lly)])
    extents.append(extent)


total_extent = shapely.ops.unary_union(extents)
del extents


schema = {
    'geometry': 'MultiPolygon',
    'properties': {'id': 'int'},
}

with fiona.open('quad_extent.shp', 'w', 'ESRI Shapefile', schema) as file_:
    file_.write({
        'geometry': shapely.geometry.mapping(total_extent),
        'properties': {'id': 0},
    })


# Number of quads with MP training data
filenames = os.listdir('training_data/responses_mp/raw')
quads = set()
for filename in filenames:
    quad = re.search('L15-\d{4}E-\d{4}N', filename)
    if not quad:
        continue
    quads.add(quad.group())

print(len(quads))


# Number of quads with interesting MP training data
filenames = os.listdir('training_data/responses_mp/clean')
quads = set()
for filename in filenames:
    quad = re.search('L15-\d{4}E-\d{4}N', filename)
    if not quad:
        continue
    quads.add(quad.group())

print(len(quads))


# Get total MP data raster extent and save out
dir_ = 'global_data/resolution_50'
filepaths = [os.path.join(dir_, fn) for fn in os.listdir(dir_)]
extents = list()

for filepath in tqdm(filepaths):
    quad = re.search('L15-\d{4}E-\d{4}N', filepath).group()
    if not quad in quads:
        continue
    raster = gdal.Open(filepath)
    cols = raster.RasterXSize
    rows = raster.RasterYSize
    llx, xres, _, y0, _, yres = raster.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])
    extent = shapely.geometry.Polygon([(llx, lly), (llx, ury), (urx, ury), (urx, lly), (llx, lly)])
    extents.append(extent)


print(len(extents))
total_extent = shapely.ops.unary_union(extents)
del extents


schema = {
    'geometry': 'MultiPolygon',
    'properties': {'id': 'int'},
}

with fiona.open('mp_extent.shp', 'w', 'ESRI Shapefile', schema) as file_:
    file_.write({
        'geometry': shapely.geometry.mapping(total_extent),
        'properties': {'id': 0},
    })




