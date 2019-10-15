from collections import Counter
import os

import fiona
from tqdm import tqdm

"""
Note:  L4 has a collision for code "2", which represents attributes "brackish atoll lagoon" (824 instances) and
"bay exposed fringing" (462 instances). I added a code for the latter manually
"""


MAPPINGS_L1 = {
    0: 'oceanic',
    1: 'continental',
    2: 'main land',
}

MAPPINGS_L2 = {
    1: 'Oceanic atoll',
    2: 'Oceanic uplifted/filled atoll',
    3: 'Oceanic Bank',
    4: 'Oceanic island',
    5: 'Continental atoll',
    7: 'Continental bank',
    8: 'Continental island',
    9: 'Continental Patch complex',
    10: 'Continental intra-shelf barrier',
    11: 'Continental outer shelf barrier',
    12: 'Continental Fringing',
    13: 'Shelf marginal structures',
    14: 'cross shelf',
    1000: 'main land',
    1001: 'aquatic land features',
}

MAPPINGS_L3 = {
    1: 'Drowned atoll',
    2: 'Atoll rim',
    3: 'Atoll rim land',
    4: 'Atoll lagoon',
    5: 'Atoll patch',
    6: 'Atoll patch land',
    7: 'Uplifted atoll',
    8: 'Drowned bank',
    9: 'Bank barrier',
    10: 'Bank barrier land',
    11: 'Bank lagoon',
    12: 'Bank patch',
    13: 'Bank patch land',
    14: 'Island lagoon',
    15: 'Barrier land',
    16: 'Outer Barrier Reef Complex',
    17: 'Multiple Barrier Complex',
    18: 'Imbricated Barrier Reef Complex',
    19: 'Coastal Barrier Reef Complex',
    20: 'Barrier-Fringing Reef Complex',
    21: 'Faro Barrier Reef Complex',
    22: 'Coastal/fringing patch',
    23: 'Patch land',
    24: 'Intra-lagoon patch-reef complex',
    25: 'Intra-seas patch-reef complex',
    26: 'Shelf patch-reef complex',
    27: 'Ocean exposed fringing',
    28: 'Intra-seas exposed fringing',
    29: 'Lagoon exposed fringing',
    30: 'Bay exposed fringing',
    31: 'Diffuse fringing',
    32: 'Fringing of coastal barrier complex',
    33: 'Fringing of  barrier-fringing complex',
    34: 'Exposed shelf reef',
    35: 'Sheltered margin reef',
    36: 'Shelf terrace',
    37: 'Shelf structure',
    38: 'Shelf slope',
    40: 'Cross Shelf',
    1000: 'Main Land',
    1001: 'Aquatic Land Features',
}

MAPPINGS_L4 = {
    1: 'barrier reef pinnacle/patch',
    2: 'brackish atoll lagoon',
    3: 'bridge',
    4: 'channel',
    5: 'crest',
    6: 'cross shelf',
    7: 'deep drowned reef flat',
    8: 'deep lagoon',
    9: 'deep lagoon with constructions',
    10: 'deep terrace',
    11: 'deep terrace with constructions',
    12: 'diffuse fringing',
    13: 'double barrier lagoon',
    15: 'drowned bank',
    16: 'drowned inner slope',
    17: 'drowned lagoon',
    18: 'drowned pass',
    19: 'drowned patch',
    20: 'drowned rim',
    21: 'enclosed basin',
    22: 'enclosed lagoon',
    23: 'enclosed lagoon or basin',
    24: 'enclosed lagoon or basin with constructions',
    25: 'enclosed lagoon with constructions',
    27: 'faro enclosed lagoon',
    28: 'faro forereef',
    29: 'faro reef flat',
    30: 'forereef',
    31: 'forereef or terrace',
    32: 'fractal reef flat',
    33: 'haa enclosed lagoon',
    34: 'haa subtidal reef flat',
    35: 'immature reef flat',
    37: 'inner slope',
    38: 'inner terrace',
    39: 'intermediate reef flat',
    40: 'lagoon pinnacle',
    41: 'linear reef flat',
    42: 'outer terrace',
    43: 'pass',
    44: 'pass reef flat',
    47: 'pinnacle',
    48: 'reef flat',
    49: 'reticulated fringing',
    50: 'ridge and fossil crest',
    51: 'shallow lagoon',
    52: 'shallow lagoon with constructions',
    53: 'shallow lagoonal terrace',
    54: 'shallow lagoonal terrace with constructions',
    56: 'shallow terrace',
    57: 'shallow terrace with constructions',
    58: 'shelf hardground',
    59: 'shelf slope',
    60: 'shelf terrace',
    61: 'shelf terrace with constructions',
    63: 'subtidal reef flat',
    64: 'undetermined envelope',
    65: 'uplifted reef flat',
    66: 'bay exposed fringing',  # Added manually
    999: 'land on reef',
    1000: 'main land',
    1001: 'aquatic land features',
}

MAPPINGS_RB = {
    0: 'non-reef',
    1: 'land',
    2: 'barrier island',
    3: 'barrier continental',
    4: 'barrier atoll-bank',
    5: 'fringing island',
    6: 'fringing continental',
    7: 'patch island',
    8: 'patch continental',
    9: 'patch atoll-bank',
    10: 'shelf island',
    11: 'shelf continental',
}

MAPPINGS_DEPTH = {
    0: 'shallow',
    1: 'variable',
    2: 'deep',
    3: 'land',
}


def _parse_all_codes():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future
    """
    all_codes = dict()
    filenames = [fn for fn in os.listdir('.') if fn.endswith('.shp')]
    for fn in tqdm(filenames):
        features = fiona.open(fn)
        for feature in features:
            properties = feature['properties']
            for meta in ('L1', 'L2', 'L3', 'L4', 'L5', 'RB'):
                code = properties.get(meta + '_CODE')
                attr = properties.get(meta + '_ATTRIB')
                all_codes.setdefault(meta, dict()).setdefault(code, Counter()).update([attr])
            code = properties.get('DEPTH_CODE')
            attr = properties.get('DEPTHLABEL')
            all_codes.setdefault('DEPTH', dict()).setdefault(code, Counter()).update([attr])
            all_codes.setdefault('VALIDATED', set()).update([properties.get('Validated')])


def _get_duplicated_codes():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future
    """
    for k, v in all_codes.items():
        for kk, vv in v.items():
            if len(vv) > 1:
                print(k, kk, vv)


def _print_encodings_in_dictionary_format():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future, meant to use
    the parsed dictionary from the above function

    Exclude L5 because there are no attributes names

    There's a duplicate in L4
    """
    for meta in ('L1', 'L2', 'L3', 'L4', 'RB', 'DEPTH'):
        mappings = sorted([(code, counter.most_common()[0][0]) for code, counter in all_codes[meta].items()],
                          key=lambda x: x[0])
        print(meta)
        for m in mappings:
            print('    {}: \'{}\','.format(m[0], m[1]))
        for _ in range(3):
            print()
