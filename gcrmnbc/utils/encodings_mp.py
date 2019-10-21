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
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
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
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
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
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
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
    66: 'bay exposed fringing',  # Added manually due to collision
    999: 'land on reef',
    1000: 'main land',
    1001: 'aquatic land features',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
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
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}


# Mappings for converting Millennium Project classes to a subset of visually distinct classes
# Assumptions
# Water within land features and other water features are distinct enough to have separate classes
# Shallow and deep features have enough variability to warrant different classes, may help the model differentiate
# between classes when due to less variability within classes
# Channels and passes look like deep lagoons, basins look like lagoons
# Flats and terraces and shelves seem to have enough visual variability and spatial occurrences to keep separate, but
# this may not be completely necessary
# Inner slopes look like shelves or reef flats, but I saw them nearby reef flats more often, so choosing that
# Crests are found with forereefs but have very little area, just label them forereefs
# Constructions and pinnacles have distinct visual patterns from one another, but also from the classes they are lumped
# in with often (e.g., lagoon with constructions), so we separate them out into their own classes

_CODE_LAND = 0  # Any land features
_CODE_WATER_TERRESTRIAL = 1  # Any water within land features
_CODE_WATER = 2  # Any water features not on land, probably will be mostly my own data
_CODE_CLOUDS = 3  # Any clouds, will need to add myself
_CODE_REEF = 10  # Reef features
_CODE_REEFFLAT_SHALLOW = 11
_CODE_REEFFLAT_DEEP = 12
_CODE_SHELF = 13
_CODE_TERRACE_SHALLOW = 14
_CODE_TERRACE_DEEP = 15
_CODE_CONSTRUCTIONS = 16
_CODE_PINNACLES = 17
_CODE_LAGOON_SHALLOW = 3
_CODE_LAGOON_DEEP = 4
_CODE_NONREEF_NEARSHORE = 18  # Nearshore, often appear muddy or turbid
_CODE_REMOVE = -9999  # Either not many examples, not clear examples, or not in imagery (drowned classes)
_CODE_UNKNOWN = -9999  # Pretty sure this class is unknown


MAPPINGS_CUSTOM = {
    1: _CODE_PINNACLES,  # 'barrier reef pinnacle/patch',
    2: _CODE_WATER_TERRESTRIAL,  # 'brackish atoll lagoon',
    3: _CODE_REMOVE,  # 'bridge',
    4: _CODE_LAGOON_DEEP,  # 'channel',
    5: _CODE_REEF,  # 'crest',
    6: _CODE_SHELF,  # 'cross shelf',
    7: _CODE_REEFFLAT_DEEP,  # 'deep drowned reef flat',
    8: _CODE_LAGOON_DEEP,  # 'deep lagoon',
    9: _CODE_CONSTRUCTIONS,  # 'deep lagoon with constructions',
    10: _CODE_TERRACE_DEEP,  # 'deep terrace',
    11: _CODE_CONSTRUCTIONS,  # 'deep terrace with constructions',
    12: _CODE_NONREEF_NEARSHORE,  # 'diffuse fringing',
    13: _CODE_LAGOON_SHALLOW,  # 'double barrier lagoon',
    15: _CODE_REEFFLAT_DEEP,  # 'drowned bank',
    16: _CODE_SHELF,  # 'drowned inner slope',
    17: _CODE_LAGOON_DEEP,  # 'drowned lagoon',
    18: _CODE_REMOVE,  # 'drowned pass',
    19: _CODE_REMOVE,  # 'drowned patch',
    20: _CODE_REMOVE,  # 'drowned rim',
    21: _CODE_LAGOON_SHALLOW,  # 'enclosed basin',
    22: _CODE_LAGOON_SHALLOW,  # 'enclosed lagoon',
    23: _CODE_LAGOON_SHALLOW,  # 'enclosed lagoon or basin',
    24: _CODE_CONSTRUCTIONS,  # 'enclosed lagoon or basin with constructions',
    25: _CODE_CONSTRUCTIONS,  # 'enclosed lagoon with constructions',
    27: _CODE_LAGOON_SHALLOW,  # 'faro enclosed lagoon',
    28: _CODE_REEF,  # 'faro forereef',
    29: _CODE_REEFFLAT_SHALLOW,  # 'faro reef flat',
    30: _CODE_REEF,  # 'forereef',
    31: _CODE_REEF,  # 'forereef or terrace',
    32: _CODE_NONREEF_NEARSHORE,  # 'fractal reef flat',
    33: _CODE_LAGOON_SHALLOW,  # 'haa enclosed lagoon',
    34: _CODE_REEFFLAT_SHALLOW,  # 'haa subtidal reef flat',
    35: _CODE_REEFFLAT_SHALLOW,  # 'immature reef flat',
    37: _CODE_REEFFLAT_SHALLOW,  # 'inner slope',
    38: _CODE_TERRACE_SHALLOW,  # 'inner terrace',
    39: _CODE_REEFFLAT_SHALLOW,  # 'intermediate reef flat',
    40: _CODE_PINNACLES,  # 'lagoon pinnacle',
    41: _CODE_REEFFLAT_SHALLOW,  # 'linear reef flat',
    42: _CODE_TERRACE_SHALLOW,  # 'outer terrace',
    43: _CODE_LAGOON_DEEP,  # 'pass',
    44: _CODE_REEFFLAT_SHALLOW,  # 'pass reef flat',
    47: _CODE_PINNACLES,  # 'pinnacle',
    48: _CODE_REEFFLAT_SHALLOW,  # 'reef flat',
    49: _CODE_NONREEF_NEARSHORE,  # 'reticulated fringing',
    50: _CODE_REMOVE,  # 'ridge and fossil crest',
    51: _CODE_LAGOON_SHALLOW,  # 'shallow lagoon',
    52: _CODE_CONSTRUCTIONS,  # 'shallow lagoon with constructions',
    53: _CODE_TERRACE_SHALLOW,  # 'shallow lagoonal terrace',
    54: _CODE_CONSTRUCTIONS,  # 'shallow lagoonal terrace with constructions',
    56: _CODE_TERRACE_SHALLOW,  # 'shallow terrace',
    57: _CODE_CONSTRUCTIONS,  # 'shallow terrace with constructions',
    58: _CODE_SHELF,  # 'shelf hardground',
    59: _CODE_SHELF,  # 'shelf slope',
    60: _CODE_SHELF,  # 'shelf terrace',
    61: _CODE_CONSTRUCTIONS,  # 'shelf terrace with constructions',
    63: _CODE_REEFFLAT_DEEP,  # 'subtidal reef flat',
    64: _CODE_UNKNOWN,  # 'undetermined envelope',
    65: _CODE_REEFFLAT_SHALLOW,  # 'uplifted reef flat',
    66: _CODE_NONREEF_NEARSHORE,  # 'bay exposed fringing',  # Added manually due to collision
    999: _CODE_LAND,  # 'land on reef',
    1000: _CODE_LAND,  # 'main land',
    1001: _CODE_WATER_TERRESTRIAL,  # 'aquatic land features',
    2000: _CODE_WATER,  # 'deep water', added manually to account for deep water
    2001: _CODE_CLOUDS,  # 'clouds', added manually to account for clouds
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
