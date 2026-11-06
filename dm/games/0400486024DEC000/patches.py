# Ocarina v131072. The engine owns allocation sizes, effect constants and command rectangles.
# These gates override its resolution parameters before their consumers, never NVN descriptors.
OBS = {
    'e0f3ccfaf50065ae4ea01eb5aeb13b1a': [
        (0x31ac7e0, 27, 'a9484ff4', 'resolution parameter loaded: x20 owns BaseResolution (+0x38), FinalImageResolution (+0x40), presence flags (+0x4c/0x4d)'),
        (0x31915ec, 28, 'a9474ff4', 'dynamic level loaded: x20 owns ResolutionReduceScale (+0x3c), presence flag (+0x40)'),
        (0xe83050, 29, '1e2202a0', 'final resolution selected: x19 +0xe54/+0xe58, height cap w21; override the framework clamp and fixed 1080p fallback together'),
    ],
}

BINDING = [
    {'what': 'opt-in internal render resolution', 'now': 'build', 'goal': 'game', 'purpose': 'rendering',
     'why': 'the game selects scene and final dimensions and a dynamic palette before the NVN calls',
     'blocked': 'parameter layouts and the final-size selection have not been matched across builds',
     'checked': 'v131072 main disassembly and shipped ModelSceneExtensionParam; gameplay acceptance open'},
]
