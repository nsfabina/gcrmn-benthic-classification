import functools

import pyproj
import shapely.geometry
import shapely.ops


def calculate_model_performance_statistics(
        model_reef: shapely.geometry.base.BaseGeometry,
        groundtruth_reef: shapely.geometry.base.BaseGeometry
) -> dict:
    # Note that the obvious calculation for the area of true negatives, i.e., the overlap between the groundtruth and
    # model non-reef area did not work during tests of certain reefs because there are self-intersection and invalid
    # polygon issues that cannot be resolved using buffer(0). Note that the "obvious calculation" is
    # total_footprint.difference(model_reef).

    # Buffer geometries for validity and assert that areas are approximately equal
    area_old = model_reef.area
    model_reef = model_reef.buffer(0)
    assert abs(area_old - model_reef.area) <= 0.01 * area_old, 'Buffering caused significant area changes'

    # Calculate absolute and percent areas
    total_footprint = groundtruth_reef.convex_hull
    groundtruth_nonreef = total_footprint.difference(groundtruth_reef).buffer(0)
    stats = dict()
    stats['total_area'] = _calculate_area_in_square_kilometers(total_footprint)
    stats['groundtruth_reef_area'] = _calculate_area_in_square_kilometers(groundtruth_reef)
    stats['groundtruth_nonreef_area'] = _calculate_area_in_square_kilometers(groundtruth_nonreef)
    stats['model_reef_area'] = _calculate_area_in_square_kilometers(model_reef.intersection(total_footprint))
    stats['model_nonreef_area'] = stats['total_area'] - stats['model_reef_area']
    stats['groundtruth_reef_pct'] = stats['groundtruth_reef_area'] / stats['total_area']
    stats['groundtruth_nonreef_pct'] = stats['groundtruth_nonreef_area'] / stats['total_area']
    stats['model_reef_pct'] = stats['model_reef_area'] / stats['total_area']
    stats['model_nonreef_pct'] = stats['model_nonreef_area'] / stats['total_area']

    # True/false positives/negatives

    stats['area_tp'] = _calculate_area_in_square_kilometers(groundtruth_reef.intersection(model_reef))  # GT R x M R
    stats['area_fn'] = stats['groundtruth_reef_area'] - stats['area_tp']  # GT R x M NR
    stats['area_fp'] = _calculate_area_in_square_kilometers(groundtruth_nonreef.intersection(model_reef))  # GT NR x M R
    stats['area_tn'] = stats['model_nonreef_area'] - stats['area_fn']  # GT NR x M NR
    stats['pct_tp'] = stats['area_tp'] / stats['total_area']
    stats['pct_fn'] = stats['area_fn'] / stats['total_area']
    stats['pct_fp'] = stats['area_fp'] / stats['total_area']
    stats['pct_tn'] = stats['area_tn'] / stats['total_area']

    return stats


def _calculate_area_in_square_kilometers(geometry: shapely.geometry.base.BaseGeometry) -> float:
    """
    Shamelessly borrowed from:
        https://gis.stackexchange.com/questions/127607/area-in-km-from-polygon-of-coordinates
    Trusted because the answer is from sgillies
    """
    if not geometry.bounds:
        return 0.0
    transformed = shapely.ops.transform(
        functools.partial(
            pyproj.transform,
            pyproj.Proj(init='EPSG:3857'),
            pyproj.Proj(proj='aea', lat1=geometry.bounds[1], lat2=geometry.bounds[3])
        ),
        geometry
    )
    return transformed.area / 10 ** 6
