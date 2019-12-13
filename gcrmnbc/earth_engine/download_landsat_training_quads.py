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

LANDSAT = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
QUADFEATURES = ee.FeatureCollection('users/nfabina/training_quad_extents')

BANDS = ['B1', 'B2', 'B3', 'B4', 'B5']
GCS_SUBDIR_LANDSAT = 'gcrmn-global-map/landsat8/'

FILEPATH_TASKS = 'tasks_landsat.json'


def download_landsat_training_quads() -> Tuple[List[ee.batch.Task], Dict[str, dict]]:
    labels_from_files = shared.get_completed_quad_labels_from_bucket(GCS_SUBDIR_LANDSAT)
    labels_from_local_list = shared.get_completed_quad_labels_from_local_task_statuses(FILEPATH_TASKS)
    completed_labels = labels_from_files.union(labels_from_local_list)
    export_objects = _get_export_objects(completed_labels)
    tasks = list()
    for export_object in tqdm(export_objects):
        tasks.append(shared.export_image(export_object))
    statuses = shared.write_task_statuses_locally(tasks, FILEPATH_TASKS)
    return tasks, statuses


def _get_export_objects(completed_labels: Set[str]) -> List[shared.ExportObject]:
    quadExtents = QUADFEATURES.getInfo()
    export_objects = list()
    for quadExtent in quadExtents['features']:
        quadLabel = quadExtent['properties']['label']
        if quadLabel in completed_labels:
            continue
        quadPolygon = shared.getQuadPolygon(quadExtent)
        landsatSubset = _getLandsatQuad(quadPolygon)
        export_objects.append(shared.ExportObject(
            quad_label=quadLabel, quad_polygon=quadPolygon, image_subset=landsatSubset, image_bands=BANDS,
            gcs_subdir=GCS_SUBDIR_LANDSAT, gcs_description='landsat_training'
        ))
    return sorted(export_objects, key=lambda x: x.quad_label)


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


if __name__ == '__main__':
    tasks, statuses = download_landsat_training_quads()
