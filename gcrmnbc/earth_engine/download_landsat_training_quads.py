"""
I started by writing this with Javascript style to be consistent with EarthEngine and then realized I needed some
non-EarthEngine code to glue everything together, so I have a mix of Python and Javascript style and I'm so so sorry.
Generally, Javascript-styled code is something that is generally compatible with and could be easily ported to
EarthEngine directly, while Python-styled code would need to be more heavily rewritten for JS.
"""

from collections import namedtuple
import json
from typing import Dict, List, Set

import ee
import os
import re
import shapely.geometry
from tqdm import tqdm

from gcrmnbc.utils import reproject_geometry
from gcrmnbc.utils import command_line


ee.Initialize()

LANDSAT = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
QUADFEATURES = ee.FeatureCollection('users/nfabina/training_quad_extents')

BANDS = ['B1', 'B2', 'B3', 'B4', 'B5']
GCS_BUCKET = 'coral-atlas-data-share'
GCS_SUBDIR_LANDSAT = 'gcrmn-global-map/landsat8/'
GCS_DIR_LANDSAT = 'gs://{bucket}/{subdir}'.format(bucket=GCS_BUCKET, subdir=GCS_SUBDIR_LANDSAT)

FILEPATH_TASKS = 'tasks.json'


ExportObject = namedtuple('export_object', ('quad_label', 'quad_polygon', 'landsat_subset'))


def download_landsat_training_quads() -> List[ee.batch.Task]:
    labels_from_files = _get_completed_quad_labels()
    labels_from_local_list = _get_completed_labels_from_local_task_statuses()
    completed_labels = labels_from_files.union(labels_from_local_list)
    export_objects = _get_export_objects(completed_labels)
    tasks = list()
    for export_object in tqdm(export_objects):
        tasks.append(_export_image(export_object))
    return tasks


def read_updated_task_statuses_locally() -> Dict[str, dict]:
    with open(FILEPATH_TASKS, 'r') as file_:
        statuses: Dict[str, dict] = json.load(file_)
    task_ids = [status['id'] for status in statuses.values()]
    return get_updated_task_statuses(task_ids)


def _get_completed_quad_labels() -> Set[str]:
    command = 'gsutil ls -r {bucket}'.format(bucket=GCS_DIR_LANDSAT)
    result = command_line.run_command_line(command).stdout.decode('utf-8').split('\n')
    quad_labels = list()
    for path in result:
        quad_label = re.search(r'L15-\d{4}E-\d{4}N', path)
        if quad_label:
            quad_labels.append(quad_label.group())
    return set(quad_labels)


def _get_completed_labels_from_local_task_statuses() -> Set[str]:
    completed_labels = set()
    statuses = read_updated_task_statuses_locally()
    for quad_label, status in statuses.items():
        if status['state'] == 'COMPLETED':
            completed_labels.add(quad_label)
        elif status['state'] == 'FAILED':
            assert status['error_message'] == "Image.select: Pattern 'B1' did not match any bands.", \
                'New error message found:  {}'.format(status['error_message'])
            completed_labels.add(quad_label)
        else:
            raise AssertionError('Unknown state found:  {}'.format(status))
    return completed_labels


def _get_export_objects(completed_labels: Set[str]) -> List[ExportObject]:
    quadExtents = QUADFEATURES.getInfo()
    export_objects = list()
    for quadExtent in quadExtents['features']:
        quadLabel = quadExtent['properties']['label']
        if quadLabel in completed_labels:
            continue
        quadPolygon = _getQuadPolygon(quadExtent)
        landsatSubset = _getLandsatQuad(quadPolygon)
        export_objects.append(
            ExportObject(quad_label=quadLabel, quad_polygon=quadPolygon, landsat_subset=landsatSubset))
    return sorted(export_objects, key=lambda x: x.quad_label)


def get_updated_task_statuses(task_ids: List[str]) -> Dict[str, dict]:
    # Get raw statuses
    statuses_raw = list()
    max_task_requests = 32
    idx_start = 0
    while idx_start < len(task_ids):
        statuses_raw.extend(ee.data.getTaskStatus(task_ids[idx_start:idx_start+max_task_requests]))
        idx_start += max_task_requests
    # Parse raw statuses
    statuses = dict()
    for status in statuses_raw:
        quad_label = re.search(r'L15-\d{4}E-\d{4}N', status['description']).group()
        statuses[quad_label] = status
    return statuses


def _write_task_statuses_locally(tasks: List[ee.batch.Task]) -> None:
    # Get tasks statuses
    task_ids = [task.id for task in tasks]
    statuses_new = get_updated_task_statuses(task_ids)
    # Combine new and old statuses if necessary
    if os.path.exists(FILEPATH_TASKS):
        statuses_old = read_updated_task_statuses_locally()
        statuses_old.update(statuses_new)
        statuses_out = statuses_old
    else:
        statuses_out = statuses_new
    # Write
    with open(FILEPATH_TASKS, 'w') as file_:
        json.dump(statuses_out, file_)


def _getQuadPolygon(quadExtent: Dict) -> ee.Geometry:
    props = quadExtent['properties']
    x0 = props['llx']
    y0 = props['lly']
    x1 = props['urx']
    y1 = props['ury']
    region_3857 = shapely.geometry.Polygon([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    region_4326 = reproject_geometry(region_3857, 3857, 4326)
    return ee.Geometry.Rectangle(region_4326.bounds)


def _getLandsatQuad(quadPolygon: ee.Geometry) -> ee.Image:
    landsatSubset = LANDSAT.filterBounds(quadPolygon)
    landsatSubset = landsatSubset.filterDate('2017-01-01', '2020-01-01')
    landsatSubset = landsatSubset.map(_maskLandsatImage)
    landsatSubset = landsatSubset.median()
    return landsatSubset


def _maskLandsatImage(image: ee.Image) -> ee.Image:
    # Bits 5 and 3 are clouds and cloud shadows, respectively
    bitMaskCloudShadow = ee.Number(2).pow(3).int()
    bitMaskCloud = ee.Number(2).pow(5).int()
    bandQA = image.select('pixel_qa')
    mask = bandQA.bitwiseAnd(bitMaskCloudShadow).eq(0).And(bandQA.bitwiseAnd(bitMaskCloud).eq(0))
    return image.updateMask(mask).select(BANDS)


def _export_image(export_object: ExportObject) -> ee.batch.Task:
    task = ee.batch.Export.image.toCloudStorage(
        image=export_object.landsat_subset.select(BANDS),
        description='landsat_training_' + export_object.quad_label,
        bucket=GCS_BUCKET,
        fileNamePrefix=os.path.join(GCS_SUBDIR_LANDSAT, 'test', export_object.quad_label),
        region=export_object.quad_polygon.toGeoJSON()['coordinates'],
        scale=30,
        crs='EPSG:4326',
        maxPixels=1e13,
        fileFormat='GeoTiff',
        formatOptions={'cloudOptimized': True}
    )
    task.start()
    return task


if __name__ == '__main__':
    download_landsat_training_quads()
