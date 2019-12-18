"""
I started by writing this with Javascript style to be consistent with EarthEngine and then realized I needed some
non-EarthEngine code to glue everything together, so I have a mix of Python and Javascript style and I'm so so sorry.
Generally, Javascript-styled code is something that is generally compatible with and could be easily ported to
EarthEngine directly, while Python-styled code would need to be more heavily rewritten for JS.
"""

from typing import Dict, List, Set, Tuple

import ee
from tqdm import tqdm

from gcrmnbc.earth_engine import shared


ee.Initialize()

SENTINEL = ee.ImageCollection('COPERNICUS/S2_SR')
QUADFEATURES = ee.FeatureCollection('users/nfabina/training_quad_extents')

GCS_SUBDIR_SENTINEL = 'gcrmn-global-map/sentinel2/{image_scale}m/'
GEE_IMAGE_BANDS = {'10': ['B2', 'B3', 'B4', 'B8'], '20': ['B5', 'B6', 'B7', 'B8A', 'B11', 'B12']}
GEE_TASK_DESCRIPTION = 'sentinel_training_{image_scale}m'

FILEPATH_TASKS = 'tasks_sentinel_{image_scale}m.json'


def download_sentinel_training_quads(image_scale: int) -> Tuple[List[ee.batch.Task], Dict[str, dict]]:
    # Get parameters/variales for image scale
    gcs_subdir = GCS_SUBDIR_SENTINEL.format(image_scale=image_scale)
    gee_description = GEE_TASK_DESCRIPTION.format(image_scale=image_scale)
    image_bands = GEE_IMAGE_BANDS[str(image_scale)]
    image_scale = int(image_scale)
    filepath_tasks = FILEPATH_TASKS.format(image_scale=image_scale)
    # Download data
    labels_from_files = shared.get_completed_quad_labels_from_bucket(gcs_subdir)
    labels_from_local_list = shared.get_completed_quad_labels_from_local_task_statuses(filepath_tasks)
    completed_labels = labels_from_files.union(labels_from_local_list)
    export_objects = _get_export_objects(completed_labels, image_bands, image_scale, gcs_subdir, gee_description)
    tasks = list()
    for export_object in tqdm(export_objects):
        tasks.append(shared.export_image(export_object))
    statuses = shared.write_task_statuses_locally(tasks, filepath_tasks)
    return tasks, statuses


def _get_export_objects(
        completed_labels: Set[str],
        image_bands: List[str],
        image_scale: int,
        gcs_subdir: str,
        gee_description: str
) -> List[shared.ExportObject]:
    quadExtents = QUADFEATURES.getInfo()
    export_objects = list()
    for quadExtent in quadExtents['features']:
        quadLabel = quadExtent['properties']['label']
        if quadLabel in completed_labels:
            continue
        quadPolygon = shared.getQuadPolygon(quadExtent)
        sentinelSubset = _getSentinelQuad(quadPolygon, image_bands)
        export_objects.append(shared.ExportObject(
            quad_label=quadLabel, quad_polygon=quadPolygon, image_subset=sentinelSubset, image_bands=image_bands,
            image_scale=image_scale, gcs_subdir=gcs_subdir, gee_description=gee_description
        ))
    return sorted(export_objects, key=lambda x: x.quad_label)


def _getSentinelQuad(quadPolygon: ee.Geometry, image_bands: List[str]) -> ee.Image:
    subset = SENTINEL.filterBounds(quadPolygon)
    subset = subset.filterDate('2017-01-01', '2020-01-01')
    subset = subset.map(_maskSentinelImage).select(image_bands)
    return subset.median()


def _maskSentinelImage(image: ee.Image) -> ee.Image:
    bitMaskCloud = ee.Number(2).pow(10).int()
    bitMaskCirrus = ee.Number(2).pow(11).int()
    bandQA = image.select('QA60')
    mask = bandQA.bitwiseAnd(bitMaskCloud).eq(0).And(bandQA.bitwiseAnd(bitMaskCirrus).eq(0))
    return image.updateMask(mask)


if __name__ == '__main__':
    tasks, statuses = download_sentinel_training_quads(10)
    tasks, statuses = download_sentinel_training_quads(20)
