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

from gcrmnbc.utils import reproject_geometry
from gcrmnbc.utils import command_line


GCS_BUCKET = 'coral-atlas-data-share'
GCS_DIR_LANDSAT = 'gs://{bucket}/{subdir}'


def read_updated_task_statuses_locally(filepath_statuses: str) -> Dict[str, dict]:
    if not os.path.exists(filepath_statuses):
        return dict()
    with open(filepath_statuses, 'r') as file_:
        statuses: Dict[str, dict] = json.load(file_)
    task_ids = [status['id'] for status in statuses.values()]
    return get_updated_task_statuses(task_ids)


def write_task_statuses_locally(tasks: List[ee.batch.Task], filepath_statuses: str) -> Dict[str, dict]:
    # Get tasks statuses
    task_ids = [task.id for task in tasks]
    statuses_new = get_updated_task_statuses(task_ids)
    # Combine new and old statuses if necessary
    if os.path.exists(filepath_statuses):
        statuses_old = read_updated_task_statuses_locally(filepath_statuses)
        statuses_old.update(statuses_new)
        statuses_out = statuses_old
    else:
        statuses_out = statuses_new
    # Write
    with open(filepath_statuses, 'w') as file_:
        json.dump(statuses_out, file_)
    return statuses_out


def get_updated_task_statuses(task_ids: List[str]) -> Dict[str, dict]:
    # Get raw statuses
    statuses_raw = list()
    max_task_requests = 32  # Set by GEE
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


def get_completed_quad_labels_from_bucket(subdir_bucket: str) -> Set[str]:
    command = 'gsutil ls -r {bucket}'.format(bucket=GCS_DIR_LANDSAT.format(bucket=GCS_BUCKET, subdir=subdir_bucket))
    result = command_line.run_command_line(command, assert_success=False).stdout.decode('utf-8').split('\n')
    quad_labels = list()
    for path in result:
        quad_label = re.search(r'L15-\d{4}E-\d{4}N', path)
        if quad_label:
            quad_labels.append(quad_label.group())
    return set(quad_labels)


def get_completed_quad_labels_from_local_task_statuses(filepath_statuses: str) -> Set[str]:
    completed_labels = set()
    statuses = read_updated_task_statuses_locally(filepath_statuses)
    for quad_label, status in statuses.items():
        if status['state'] == 'COMPLETED':
            completed_labels.add(quad_label)
        elif status['state'] == 'FAILED':
            error = status['error_message']
            if error == 'Internal error.':
                continue
            elif error == "Image.select: Pattern 'B1' did not match any bands.":
                completed_labels.add(quad_label)
            else:
                raise AssertionError('New error message found:  {}'.format(status['error_message']))
        else:
            raise AssertionError('Unknown state found:  {}'.format(status))
    return completed_labels


def getQuadPolygon(quadExtent: Dict) -> ee.Geometry:
    props = quadExtent['properties']
    x0 = props['llx']
    y0 = props['lly']
    x1 = props['urx']
    y1 = props['ury']
    region_3857 = shapely.geometry.Polygon([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    region_4326 = reproject_geometry(region_3857, 3857, 4326)
    return ee.Geometry.Rectangle(region_4326.bounds)


ExportObject = namedtuple(
    'export_object',
    ('quad_label', 'quad_polygon', 'image_subset', 'image_bands', 'image_scale', 'gcs_subdir', 'gee_description')
)


def export_image(export_object: ExportObject) -> ee.batch.Task:
    image = export_object.image_subset
    if export_object.image_bands is not None:
        image = image.select(export_object.image_bands)
    task = ee.batch.Export.image.toCloudStorage(
        image=image,
        description=export_object.gee_description + '_' + export_object.quad_label,
        bucket=GCS_BUCKET,
        fileNamePrefix=os.path.join(export_object.gcs_subdir, export_object.quad_label),
        region=export_object.quad_polygon.toGeoJSON()['coordinates'],
        scale=export_object.image_scale,
        crs='EPSG:4326',
        maxPixels=1e13,
        fileFormat='GeoTiff',
        formatOptions={'cloudOptimized': True}
    )
    task.start()
    return task
