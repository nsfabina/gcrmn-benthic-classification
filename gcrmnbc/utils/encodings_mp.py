"""
Note:  L4 has a collision for code "2", which represents attributes "brackish atoll lagoon" (824 instances) and
"bay exposed fringing" (462 instances). I added a code for the latter manually
"""

# Mappings for converting Millennium Project classes to a subset of visually distinct classes
# Assumptions
# Reef and non reef features should be kept separate
# Shallow and variable depth features should be kept separate
# Deep features are not always visible in the imagery and should be removed
# Features with constructions mess up the training data because they cover many different patterns with the reef
# "webbing" or constructions running through them, and they are inexact when they match up with the visual pattern; it's
# probably better to not fit over these areas and then let the model split them later based on what it's learned.
# Example:  terrace with constructions is actually two separate things, a terrace and the constructions on it; the model
# learns terraces and reef features through other classes, and should be able to divide up the terrace with
# constructions rather than group it all into one class.
# Water within land features and other water features are distinct enough to have separate classes


# The following codes are used to combine MP classes into visually distinct and useful classes for the model
# The colors are for my own use in QGIS, as a reminder of what works well
CODE_LAND = 0  # Dark brown
CODE_WATER_TERRESTRIAL = 1  # Light brown
CODE_LAND_SUPP = 2000  # Dark brown

CODE_WATER_SHALLOW = 10  # Light blue
CODE_WATER_DEEP = 11  # Dark blue
CODE_WATER_SUPP = 2001  # Dark blue

CODE_FOREREEF = 20   # Medium green
CODE_REEFFLAT_SHALLOW = 21  # Light green
CODE_REEFFLAT_VARIABLE = 22  # Light green
CODE_PINNACLES = 23  # Medium green
CODE_CONSTRUCTIONS = -9999  # Pink

CODE_NONREEF_SHALLOW = 30  # Light yellow
CODE_NONREEF_VARIABLE = 31  # Medium yellow
CODE_NONREEF_DEEP = 32  # Dark yellow

CODE_CLOUDS_SUPP = 2002  # Gray

CODE_REMOVE = -9999  # Either not many examples, not clear examples, or not in imagery (drowned classes)
CODE_UNKNOWN = -9999  # Pretty sure this class is unknown


MAPPINGS_CUSTOM = {
    999: CODE_LAND,  # 'land on reef',  ~13000
    1000: CODE_LAND,  # 'main land',  ~35000

    2: CODE_WATER_TERRESTRIAL,  # 'brackish atoll lagoon',  ~1000
    1001: CODE_WATER_TERRESTRIAL,  # 'aquatic land features',  ~7000

    4: CODE_WATER_SHALLOW,  # 'channel',
    21: CODE_WATER_SHALLOW,  # 'enclosed basin',  ~1000
    22: CODE_WATER_SHALLOW,  # 'enclosed lagoon',  ~1000
    23: CODE_WATER_SHALLOW,  # 'enclosed lagoon or basin',  ~1000
    27: CODE_WATER_SHALLOW,  # 'faro enclosed lagoon',  ~ 1000
    51: CODE_WATER_SHALLOW,  # 'shallow lagoon',

    8: CODE_WATER_DEEP,  # 'deep lagoon',  ~1000
    13: CODE_WATER_DEEP,  # 'double barrier lagoon',
    17: CODE_WATER_DEEP,  # 'drowned lagoon',
    33: CODE_WATER_DEEP,  # 'haa enclosed lagoon',
    43: CODE_WATER_DEEP,  # 'pass',  ~1000

    28: CODE_FOREREEF,  # 'faro forereef',
    30: CODE_FOREREEF,  # 'forereef',  ~20000

    5: CODE_REEFFLAT_SHALLOW,  # 'crest',
    29: CODE_REEFFLAT_SHALLOW,  # 'faro reef flat',  ~1300
    32: CODE_REEFFLAT_SHALLOW,  # 'fractal reef flat',
    39: CODE_REEFFLAT_SHALLOW,  # 'intermediate reef flat',
    41: CODE_REEFFLAT_SHALLOW,  # 'linear reef flat',
    44: CODE_REEFFLAT_SHALLOW,  # 'pass reef flat',
    48: CODE_REEFFLAT_SHALLOW,  # 'reef flat',  ~55000
    50: CODE_REEFFLAT_SHALLOW,  # 'ridge and fossil crest',
    65: CODE_REEFFLAT_SHALLOW,  # 'uplifted reef flat',
    66: CODE_REEFFLAT_SHALLOW,  # 'bay exposed fringing',  # Added manually due to collision

    # Reticulated fringing can be a bit poorly defined, e.g., Solomon Islands, where it looks much like nonreef features
    # and doesn't match the visual imagery well, removing to avoid contaminating dataset
    49: CODE_REMOVE,  # 'reticulated fringing',

    35: CODE_REEFFLAT_VARIABLE,  # 'immature reef flat',  ~20000
    63: CODE_REEFFLAT_VARIABLE,  # 'subtidal reef flat',

    1: CODE_PINNACLES,  # 'barrier reef pinnacle/patch',  ~22000
    40: CODE_PINNACLES,  # 'lagoon pinnacle',  ~3000
    47: CODE_PINNACLES,  # 'pinnacle',  ~2000

    9: CODE_CONSTRUCTIONS,  # 'deep lagoon with constructions',
    11: CODE_CONSTRUCTIONS,  # 'deep terrace with constructions',
    24: CODE_CONSTRUCTIONS,  # 'enclosed lagoon or basin with constructions',
    25: CODE_CONSTRUCTIONS,  # 'enclosed lagoon with constructions',
    52: CODE_CONSTRUCTIONS,  # 'shallow lagoon with constructions',
    54: CODE_CONSTRUCTIONS,  # 'shallow lagoonal terrace with constructions',
    57: CODE_CONSTRUCTIONS,  # 'shallow terrace with constructions',
    61: CODE_CONSTRUCTIONS,  # 'shelf terrace with constructions',

    12: CODE_NONREEF_SHALLOW,  # 'diffuse fringing',  ~3000

    6: CODE_NONREEF_VARIABLE,  # 'cross shelf',
    37: CODE_NONREEF_VARIABLE,  # 'inner slope',  ~1000
    38: CODE_NONREEF_VARIABLE,  # 'inner terrace',
    42: CODE_NONREEF_VARIABLE,  # 'outer terrace',
    53: CODE_NONREEF_VARIABLE,  # 'shallow lagoonal terrace',
    56: CODE_NONREEF_VARIABLE,  # 'shallow terrace',  ~12000
    60: CODE_NONREEF_VARIABLE,  # 'shelf terrace',  ~1000

    58: CODE_NONREEF_DEEP,  # 'shelf hardground',
    59: CODE_NONREEF_DEEP,  # 'shelf slope',  ~2000

    3: CODE_REMOVE,  # 'bridge',
    7: CODE_REMOVE,  # 'deep drowned reef flat',
    10: CODE_REMOVE,  # 'deep terrace',
    15: CODE_REMOVE,  # 'drowned bank',
    16: CODE_REMOVE,  # 'drowned inner slope',
    18: CODE_REMOVE,  # 'drowned pass',
    19: CODE_REMOVE,  # 'drowned patch',
    20: CODE_REMOVE,  # 'drowned rim',
    31: CODE_REMOVE,  # 'forereef or terrace',
    34: CODE_REMOVE,  # 'haa subtidal reef flat',

    64: CODE_UNKNOWN,  # 'undetermined envelope',
}


# The following codes are used to combine the model predictions into more general classes for better results
OUTPUT_CODE_LAND = 0
OUTPUT_CODE_WATER = 1
OUTPUT_CODE_REEF = 2
OUTPUT_CODE_NONREEF = 3
OUTPUT_CODE_CLOUDS = 4

MAPPINGS_OUTPUT = {
    CODE_LAND: OUTPUT_CODE_LAND,
    CODE_LAND_SUPP: OUTPUT_CODE_LAND,

    CODE_WATER_TERRESTRIAL: OUTPUT_CODE_WATER,
    CODE_WATER_DEEP: OUTPUT_CODE_WATER,
    CODE_WATER_SUPP: OUTPUT_CODE_WATER,

    CODE_WATER_SHALLOW: OUTPUT_CODE_REEF,  # Note:  Emma argues for including lagoon in reef, only visible in shallow
    CODE_FOREREEF: OUTPUT_CODE_REEF,
    CODE_REEFFLAT_SHALLOW: OUTPUT_CODE_REEF,
    CODE_REEFFLAT_VARIABLE: OUTPUT_CODE_REEF,
    CODE_PINNACLES: OUTPUT_CODE_REEF,

    CODE_NONREEF_SHALLOW: OUTPUT_CODE_NONREEF,
    CODE_NONREEF_VARIABLE: OUTPUT_CODE_NONREEF,
    CODE_NONREEF_DEEP: OUTPUT_CODE_NONREEF,

    CODE_CLOUDS_SUPP: OUTPUT_CODE_CLOUDS,
}
