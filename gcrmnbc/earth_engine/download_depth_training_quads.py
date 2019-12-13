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

GCS_SUBDIR = 'gcrmn-global-map/depth/'
GEE_TASK_DESCRIPTION = 'depth_training'

FILEPATH_TASKS = 'tasks_depth.json'


def download_depth_training_quads() -> Tuple[List[ee.batch.Task], Dict[str, dict]]:
    labels_from_files = shared.get_completed_quad_labels_from_bucket(GCS_SUBDIR)
    labels_from_local_list = shared.get_completed_quad_labels_from_local_task_statuses(FILEPATH_TASKS)
    completed_labels = labels_from_files.union(labels_from_local_list)
    export_objects = _get_export_objects(completed_labels)
    tasks = list()
    for export_object in tqdm(export_objects):
        if not '0000E' in export_object.quad_label and not '2047E' in export_object.quad_label:
            continue
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
        sentinelSubset = _getSentinelQuad(quadPolygon)
        export_objects.append(shared.ExportObject(
            quad_label=quadLabel, quad_polygon=quadPolygon, image_subset=sentinelSubset, image_bands=None,
            image_scale=10, gcs_subdir=GCS_SUBDIR, gee_description=GEE_TASK_DESCRIPTION
        ))
    return sorted(export_objects, key=lambda x: x.quad_label)


def _getSentinelQuad(quadPolygon: ee.Geometry) -> ee.Image:
    # Get image subset as per usual
    subset = SENTINEL.filterBounds(quadPolygon)
    subset = subset.filterDate('2017-01-01', '2020-01-01')
    subset = subset.map(_maskSentinelImage)
    subset = subset.median()
    # Calculate depth - Rrs and rrs
    bigrrs = subset.divide(ee.Number(31415.926))
    rrsvec = bigrrs.divide((bigrrs.multiply(ee.Number(1.7))).add(ee.Number(0.52)))
    rrsvec1k = rrsvec.multiply(ee.Number(1000))
    # Calculate depth - ChlA
    chla = 0.5
    m0 = ee.Number(52.073).pow(0.957 * chla)
    m1 = ee.Number(50.156).pow(0.957 * chla)
    # Calculate depth
    lnrrsvec = rrsvec1k.log()
    depth = ((lnrrsvec.select([1]).divide(lnrrsvec.select([2]))).multiply(m0)).subtract(m1)
    # Use hard cutoffs outside of reasonable ranges / ranges we care about
    depth = depth.where(depth.lt(-5), ee.Number(-5))
    depth = depth.where(depth.gt(30), ee.Number(30))
    return depth


def _maskSentinelImage(image: ee.Image) -> ee.Image:
    bitMaskCloud = ee.Number(2).pow(10).int()
    bitMaskCirrus = ee.Number(2).pow(11).int()
    bandQA = image.select('QA60')
    mask = bandQA.bitwiseAnd(bitMaskCloud).eq(0).And(bandQA.bitwiseAnd(bitMaskCirrus).eq(0))
    return image.updateMask(mask)


if __name__ == '__main__':
    tasks, statuses = download_depth_training_quads()
