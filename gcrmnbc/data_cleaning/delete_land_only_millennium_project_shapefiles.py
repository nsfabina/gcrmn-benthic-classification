import os

import fiona
from tqdm import tqdm

from gcrmnbc.utils import logs, paths


_logger = logs.get_logger(__file__)


def delete_land_only_millennium_project_shapefiles() -> None:
    _logger.info('Delete land-only quad shapefiles')
    filepaths_polys = [
        os.path.join(paths.DIR_DATA_TRAIN_RAW_MP, filename) for filename in paths.DIR_DATA_TRAIN_RAW_MP
        if filename.startswith('L15-') and filename.endswith('.shp')
    ]
    num_deleted = 0
    for filepath_poly in tqdm(filepaths_polys, desc='Delete land-only Millennium Project quad shapefiles'):
        is_land_only = _check_is_land_only(filepath_poly)
        if not is_land_only:
            continue
        _logger.debug('Deleting land-only quad shapefile:  {}'.format(filepath_poly))
        basename = os.path.splitext(filepath_poly)[0]
        for extension in ('.cpg', '.dbf', '.prf', '.shp', '.shx'):
            os.remove(basename + extension)
        num_deleted += 1
    _logger.info('Deleted {} land-only quad shapefiles'.format(num_deleted))


def _check_is_land_only(filepath_poly: str) -> bool:
    features = fiona.open(filepath_poly)
    num_found = 0
    num_needed = 10
    for feature in features:
        if feature['properties']['DEPTHLEVEL'] != 'land':
            num_found += 1
        is_not_land_only = num_found == num_needed
        if is_not_land_only:
            return False
    return True


if __name__ == '__main__':
    delete_land_only_millennium_project_shapefiles()
