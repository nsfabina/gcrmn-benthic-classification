import csv
import os
import re

import gdal
from tqdm import tqdm


fps = sorted(os.listdir('.'))

quad_extents = list()


for fp in tqdm(fps):
    raster_quad = gdal.Open(fp)
    cols = raster_quad.RasterXSize
    rows = raster_quad.RasterYSize
    llx, xres, _, y0, _, yres = raster_quad.GetGeoTransform()
    urx = llx + cols * xres
    y1 = y0 + rows * yres
    lly = min([y0, y1])
    ury = max([y0, y1])
    label = re.search(r'L15-\d{4}E-\d{4}N', fp).group()
    quad_extents.append({'label': label, 'llx': llx, 'lly': lly, 'urx': urx, 'ury': ury})


with open('quad_extents.csv', 'w') as file_:
    writer = csv.DictWriter(file_, fieldnames=sorted(quad_extents[0].keys()))
    writer.writeheader()
    for quad_extent in quad_extents:
        writer.writerow(quad_extent)
