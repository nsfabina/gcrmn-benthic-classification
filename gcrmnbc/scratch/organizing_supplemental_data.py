import os
import re
import shutil

import gdal
import numpy as np
from tqdm import tqdm

from gcrmnbc.utils import gdal_command_line


def get_unique_codes_from_raster(filepath_raster: str):
    raster = gdal.Open(filepath_raster)
    band = raster.GetRasterBand(1)
    arr = band.ReadAsArray()
    unique = np.unique(arr, return_counts=True)
    return unique


filenames = os.listdir()

unique_codes = dict()

for filename in tqdm(filenames, desc='Parse rasters'):
    unique_codes[filename] = get_unique_codes_from_raster(filename)


contents = dict()

for filename, codes in unique_codes.items():
    parsed_codes = set(codes[0])
    if -9999 in parsed_codes:
        parsed_codes.remove(-9999)
    if np.any([x in parsed_codes for x in (3, 12, 14, 21, 24)]):
        continue
    label = '_'.join([str(x) for x in sorted(parsed_codes)])
    contents.setdefault(label, list()).append(filename)


"""
Water Clouds
['L15-1548E-1084N_model_class.tif', 'L15-1969E-0931N_model_class.tif', 'L15-2046E-0962N_model_class.tif', 'L15-1548E-1092N_model_class.tif', 'L15-0825E-0973N_model_class.tif', 'L15-0010E-0916N_model_class.tif', 'L15-0823E-0970N_model_class.tif', 'L15-2024E-0957N_model_class.tif', 'L15-1965E-0967N_model_class.tif', 'L15-0822E-0968N_model_class.tif', 'L15-2046E-0961N_model_class.tif', 'L15-0826E-0973N_model_class.tif', 'L15-1547E-1093N_model_class.tif', 'L15-2025E-0956N_model_class.tif', 'L15-0825E-0974N_model_class.tif', 'L15-2046E-0963N_model_class.tif', 'L15-1549E-1094N_model_class.tif', 'L15-2043E-0974N_model_class.tif', 'L15-0822E-0967N_model_class.tif', 'L15-1548E-1083N_model_class.tif', 'L15-2023E-0958N_model_class.tif', 'L15-1547E-1084N_model_class.tif', 'L15-2023E-0959N_model_class.tif', 'L15-2046E-0964N_model_class.tif', 'L15-2026E-0956N_model_class.tif', 'L15-1548E-1082N_model_class.tif', 'L15-0824E-0970N_model_class.tif', 'L15-2024E-0958N_model_class.tif', 'L15-0824E-0971N_model_class.tif', 'L15-2026E-0950N_model_class.tif', 'L15-2046E-0969N_model_class.tif', 'L15-0000E-0932N_model_class.tif', 'L15-0823E-0969N_model_class.tif', 'L15-2044E-0963N_model_class.tif', 'L15-1548E-1094N_model_class.tif', 'L15-2043E-0976N_model_class.tif', 'L15-1549E-1083N_model_class.tif', 'L15-0825E-0971N_model_class.tif', 'L15-0825E-0970N_model_class.tif', 'L15-0823E-0968N_model_class.tif']

Water
['L15-1752E-1038N_model_class.tif', 'L15-1551E-1089N_model_class.tif', 'L15-0822E-0969N_model_class.tif', 'L15-1969E-0899N_model_class.tif', 'L15-0821E-0968N_model_class.tif', 'L15-2045E-0921N_model_class.tif']

Water Land Clouds
['L15-1747E-1021N_model_class.tif', 'L15-1747E-1019N_model_class.tif']

Clouds
['L15-0839E-1002N_model_class.tif']

Water Land
['L15-1748E-1031N_model_class.tif', 'L15-1753E-1014N_model_class.tif']

Land Clouds
['L15-2046E-0928N_model_class.tif', 'L15-1752E-1027N_model_class.tif']

"""

"""
Land only to keep
L15-2039E-0921N
L15-2039E-0914N
L15-2034E-0922N
L15-2033E-0921N
L15-2033E-0919N
L15-0137E-1140N
L15-0137E-1139N
L15-0137E-1136N
L15-0137E-1135N
L15-0136E-1138N
L15-0004E-0923N
"""

quads = [
    'L15-2039E-0921N', 'L15-2039E-0914N', 'L15-2034E-0922N', 'L15-2033E-0921N', 'L15-2033E-0919N', 'L15-0137E-1140N',
    'L15-0137E-1139N', 'L15-0137E-1136N', 'L15-0137E-1135N', 'L15-0136E-1138N', 'L15-0004E-0923N'
]

for quad in quads:
    fn = quad + '_land.tif'
    if not os.path.exists(fn):
        continue
    shutil.copy(fn, os.path.join('../../responses_mp_supp', fn))

"""

Water only to keep
L15-2038E-0923N
L15-1854E-0930N
L15-1853E-0928N
L15-1852E-0931N
L15-1652E-0991N
L15-0526E-1124N
L15-0002E-0924N
L15-0001E-0929N
L15-0001E-0913N

"""

quads = [
    'L15-2038E-0923N', 'L15-1854E-0930N', 'L15-1853E-0928N', 'L15-1852E-0931N', 'L15-1652E-0991N', 'L15-0526E-1124N',
    'L15-0002E-0924N', 'L15-0001E-0929N', 'L15-0001E-0913N',
]

for quad in quads:
    fn = quad + '_water.tif'
    if not os.path.exists(fn):
        continue
    shutil.copy(fn, os.path.join('../../responses_mp_supp', fn))


"""
Water only to keep from model
['L15-1752E-1038N_model_class.tif', 'L15-1551E-1089N_model_class.tif', 'L15-0822E-0969N_model_class.tif', 'L15-1969E-0899N_model_class.tif', 'L15-0821E-0968N_model_class.tif', 'L15-2045E-0921N_model_class.tif']
"""

fns = [
    'L15-1752E-1038N_model_class.tif', 'L15-1551E-1089N_model_class.tif', 'L15-0822E-0969N_model_class.tif',
    'L15-1969E-0899N_model_class.tif', 'L15-0821E-0968N_model_class.tif', 'L15-2045E-0921N_model_class.tif'
]

for fn in fns:
    quad = re.search('L15-\d{4}E-\d{4}N', fn).group()
    dest = os.path.join('../../responses_mp_supp', quad + '_water.tif')
    if not os.path.exists(fn):
        continue
    shutil.copy(fn, dest)

"""
Water clouds to keep from model
L15-0000E-0932N_model_class.tif
L15-0010E-0916N_model_class.tif
L15-0822E-0967N_model_class.tif
L15-0823E-0969N_model_class.tif
L15-0824E-0970N_model_class.tif
L15-0825E-0971N_model_class.tif
L15-0826E-0973N_model_class.tif
L15-1547E-1093N_model_class.tif
L15-1548E-1094N_model_class.tif
L15-1549E-1083N_model_class.tif
L15-1965E-0967N_model_class.tif
L15-2023E-0959N_model_class.tif
L15-2025E-0956N_model_class.tif
L15-2026E-0950N_model_class.tif
L15-2043E-0976N_model_class.tif
L15-2046E-0962N_model_class.tif
L15-2046E-0969N_model_class.tif


"""

fns = [
    'L15-0000E-0932N_model_class.tif',
    'L15-0010E-0916N_model_class.tif',
    'L15-0822E-0967N_model_class.tif',
    'L15-0823E-0969N_model_class.tif',
    'L15-0824E-0970N_model_class.tif',
    'L15-0825E-0971N_model_class.tif',
    'L15-0826E-0973N_model_class.tif',
    'L15-1547E-1093N_model_class.tif',
    'L15-1548E-1094N_model_class.tif',
    'L15-1549E-1083N_model_class.tif',
    'L15-1965E-0967N_model_class.tif',
    'L15-2023E-0959N_model_class.tif',
    'L15-2025E-0956N_model_class.tif',
    'L15-2026E-0950N_model_class.tif',
    'L15-2043E-0976N_model_class.tif',
    'L15-2046E-0962N_model_class.tif',
    'L15-2046E-0969N_model_class.tif',
]

for fn in fns:
    quad = re.search('L15-\d{4}E-\d{4}N', fn).group()
    dest = os.path.join('../../responses_mp_supp', quad + '_water_cloud.tif')
    if not os.path.exists(fn):
        continue
    shutil.copy(fn, dest)


# Convert land to 2000
fns = [fn for fn in os.listdir() if fn.endswith('_land.tif')]
for fn in fns:
    dest = os.path.join('../clean', os.path.basename(fn))
    command = 'gdal_calc.py -A {fn} --outfile={dest} --calc="2000*(A==1)+-9999*(A!=1)" --NoDataValue=-9999 --co=TILED=YES --co=COMPRESS=DEFLATE'.format(fn=fn, dest=dest)
    gdal_command_line.run_gdal_command(command)

# Convert water to 2001
fns = [fn for fn in os.listdir() if fn.endswith('_water.tif')]
for fn in fns:
    dest = os.path.join('../clean', os.path.basename(fn))
    command = 'gdal_calc.py -A {fn} --outfile={dest} --calc="2001*(A==2)+-9999*(A!=2)" --NoDataValue=-9999 --co=TILED=YES --co=COMPRESS=DEFLATE'.format(fn=fn, dest=dest)
    gdal_command_line.run_gdal_command(command)

# Convert clouds to 2002
fns = [fn for fn in os.listdir() if fn.endswith('_water_cloud.tif')]
for fn in fns:
    dest = os.path.join('../clean', os.path.basename(fn))
    command = 'gdal_calc.py -A {fn} --outfile={dest} --calc="2001*(A==2)+2002*(A==23)+-9999*numpy.logical_and(A!=2, A!=23)" --NoDataValue=-9999 --co=TILED=YES --co=COMPRESS=DEFLATE'.format(fn=fn, dest=dest)
    gdal_command_line.run_gdal_command(command)


all_codes = dict()

for fn in os.listdir('../clean'):
    raster = gdal.Open(os.path.join('../clean', fn))
    band = raster.GetRasterBand(1)
    arr = band.ReadAsArray()
    all_codes[fn] = np.unique(arr, return_counts=True)

for fn, codes in all_codes.items():
    print(fn)
    print(codes[0])
    print(codes[1])
    print()
    print()
