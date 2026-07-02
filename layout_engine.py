import random
from ultimo_layout import ler_ultimo_layout, salvar_ultimo_layout


LAYOUTS_4 = [
    {
        "nome": "hero_direita",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 350, "h": 349, "destaque": False},
            {"i": 2, "x": 10, "y": 367, "w": 350, "h": 349, "destaque": False},
            {"i": 3, "x": 10, "y": 724, "w": 350, "h": 346, "destaque": False},
            {"i": 0, "x": 368, "y": 10, "w": 702, "h": 1060, "destaque": True},
        ],
    },
    {
        "nome": "hero_esquerda",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 702, "h": 1060, "destaque": True},
            {"i": 1, "x": 720, "y": 10, "w": 350, "h": 349, "destaque": False},
            {"i": 2, "x": 720, "y": 367, "w": 350, "h": 349, "destaque": False},
            {"i": 3, "x": 720, "y": 724, "w": 350, "h": 346, "destaque": False},
        ],
    },
    {
        "nome": "hero_topo",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 1060, "h": 560, "destaque": True},
            {"i": 1, "x": 10, "y": 578, "w": 348, "h": 492, "destaque": False},
            {"i": 2, "x": 366, "y": 578, "w": 348, "h": 492, "destaque": False},
            {"i": 3, "x": 722, "y": 578, "w": 348, "h": 492, "destaque": False},
        ],
    },
    {
        "nome": "hero_base",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 2, "x": 366, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 3, "x": 722, "y": 10, "w": 348, "h": 492, "destaque": False},
            {"i": 0, "x": 10, "y": 510, "w": 1060, "h": 560, "destaque": True},
        ],
    },
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
        "nome": "revista_01",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 650, "h": 650, "destaque": True},
            {"i": 1, "x": 668, "y": 10, "w": 402, "h": 321, "destaque": False},
            {"i": 2, "x": 668, "y": 339, "w": 402, "h": 321, "destaque": False},
            {"i": 3, "x": 10, "y": 668, "w": 1060, "h": 402, "destaque": False},
        ],
    },
    {
        "nome": "revista_02",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 402, "h": 321, "destaque": False},
            {"i": 2, "x": 10, "y": 339, "w": 402, "h": 321, "destaque": False},
            {"i": 0, "x": 420, "y": 10, "w": 650, "h": 650, "destaque": True},
            {"i": 3, "x": 10, "y": 668, "w": 1060, "h": 402, "destaque": False},
        ],
    },
    {
        "nome": "mosaico_vertical",
        "cards": [
            {"i": 0, "x": 10, "y": 10, "w": 520, "h": 740, "destaque": True},
            {"i": 1, "x": 538, "y": 10, "w": 532, "h": 366, "destaque": False},
            {"i": 2, "x": 538, "y": 384, "w": 532, "h": 366, "destaque": False},
            {"i": 3, "x": 10, "y": 758, "w": 1060, "h": 312, "destaque": False},
        ],
    },
    {
        "nome": "mosaico_horizontal",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 526, "h": 330, "destaque": False},
            {"i": 2, "x": 544, "y": 10, "w": 526, "h": 330, "destaque": False},
            {"i": 0, "x": 10, "y": 348, "w": 700, "h": 722, "destaque": True},
            {"i": 3, "x": 718, "y": 348, "w": 352, "h": 722, "destaque": False},
        ],
    },
    {
        "nome": "hero_central",
        "cards": [
            {"i": 1, "x": 10, "y": 10, "w": 526, "h": 260, "destaque": False},
            {"i": 2, "x": 544, "y": 10, "w": 526, "h": 260, "destaque": False},
            {"i": 0, "x": 10, "y": 278, "w": 1060, "h": 520, "destaque": True},
            {"i": 3, "x": 10, "y": 806, "w": 1060, "h": 264, "destaque": False},
        ],
    },
]


def escolher_layout_4():
    ultimo = ler_ultimo_layout()

    candidatos = [layout for layout in LAYOUTS_4 if layout["nome"] != ultimo]

    if not candidatos:
        candidatos = LAYOUTS_4

    layout = random.choice(candidatos)
    salvar_ultimo_layout(layout["nome"])

    print(f"Layout escolhido: {layout['nome']}")

    return layout