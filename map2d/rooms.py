"""Starting rooms. Legend: W=wall, .=floor, D=door."""

ROOMS = {
    "hospital_lobby": {
        "map": [
            "WWWWWWWWWWWWWWW",
            "W.............W",
            "W..WWW........W",
            "W..W.W........W",
            "W..W.W........D",
            "W..W..........W",
            "W..WWW........W",
            "W.............W",
            "W.............W",
            "WWWWWWWWWWWWWWW",
        ],
        "player_spawn": (7, 5),
        "depth": 1,
        "label": "Hospital Lobby",
        "doors": {
            (14, 4): {
                "target": "street",
                "spawn_at": (2, 4),
                "label": "Hospital Exit",
            },
        },
        "objects": [
            {"pos": (5, 2), "color": (100, 150, 200)},
            {"pos": (5, 4), "color": (140, 90, 60)},
            {"pos": (7, 4), "color": (120, 120, 130)},
        ],
    },
    "street": {
        "map": [
            "WWWWWWWWWWWWWWW",
            "W.............W",
            "W.............W",
            "W.............W",
            "D.............W",
            "W.............W",
            "W.............W",
            "W.............W",
            "W.............W",
            "WWWWWWWWWWWWWWW",
        ],
        "player_spawn": (7, 4),
        "depth": 0,
        "label": "Street",
        "doors": {
            (0, 4): {
                "target": "hospital_lobby",
                "spawn_at": (12, 4),
                "label": "Hospital Entrance",
            },
        },
        "objects": [
            {"pos": (5, 2), "color": (80, 140, 80)},
            {"pos": (9, 6), "color": (80, 140, 80)},
            {"pos": (12, 2), "color": (160, 160, 100)},
        ],
    },
}