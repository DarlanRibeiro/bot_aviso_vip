import random
from ultimo_layout import ler_ultimo_layout, salvar_ultimo_layout


LAYOUTS_4 = [
    {
        "nome": "grade_2x2",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 526, "h": 526, "destaque": True},
            {"i": 1, "x": 544, "y": 10, "w": 526, "h": 526, "destaque": False},
            {"i": 2, "x": 10, "y": 544, "w": 526, "h": 526, "destaque": False},
            {"i": 3, "x": 544, "y": 544, "w": 526, "h": 526, "destaque": False},
        ],
    },
    {
        "nome": "hero_direita_compacto",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 360, "h": 349, "destaque": False},
            {"i": 2, "x": 10, "y": 367, "w": 360, "h": 349, "destaque": False},
            {"i": 3, "x": 10, "y": 724, "w": 360, "h": 346, "destaque": False},
            {"i": 0, "x": 378, "y": 10, "w": 692, "h": 1060, "destaque": True},
        ],
    },
    {
        "nome": "hero_esquerda_compacto",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 692, "h": 1060, "destaque": True},
            {"i": 1, "x": 710, "y": 10, "w": 360, "h": 349, "destaque": False},
            {"i": 2, "x": 710, "y": 367, "w": 360, "h": 349, "destaque": False},
            {"i": 3, "x": 710, "y": 724, "w": 360, "h": 346, "destaque": False},
        ],
    },
    {
        "nome": "hero_topo_compacto",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 1060, "h": 560, "destaque": True},
            {"i": 1, "x": 10, "y": 578, "w": 348, "h": 492, "destaque": False},
            {"i": 2, "x": 366, "y": 578, "w": 348, "h": 492, "destaque": False},
            {"i": 3, "x": 722, "y": 578, "w": 348, "h": 492, "destaque": False},
        ],
    },
    {
        "nome": "hero_base_compacto",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 2, "x": 366, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 3, "x": 722, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 0, "x": 10, "y": 510, "w": 1060, "h": 560, "destaque": True},
        ],
    },
    {
        "nome": "duplo_topo",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 526, "h": 610, "destaque": True},
            {"i": 1, "x": 544, "y": 10, "w": 526, "h": 610, "destaque": False},
            {"i": 2, "x": 10, "y": 628, "w": 526, "h": 442, "destaque": False},
            {"i": 3, "x": 544, "y": 628, "w": 526, "h": 442, "destaque": False},
        ],
    },
    {
        "nome": "duplo_base",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 526, "h": 442, "destaque": False},
            {"i": 2, "x": 544, "y": 10, "w": 526, "h": 442, "destaque": False},
            {"i": 0, "x": 10, "y": 460, "w": 526, "h": 610, "destaque": True},
            {"i": 3, "x": 544, "y": 460, "w": 526, "h": 610, "destaque": False},
        ],
    },
]


def escolher_layout_4():
    ultimo = ler_ultimo_layout()

    candidatos = [
        layout for layout in LAYOUTS_4
        if layout["nome"] != ultimo
    ]

    if not candidatos:
        candidatos = LAYOUTS_4

    layout = random.choice(candidatos)

    salvar_ultimo_layout(layout["nome"])

    print(f"Layout escolhido: {layout['nome']}")

    return layout