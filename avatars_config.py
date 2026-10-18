from ui import W

SIZE = 220
Y = 395

AVATARS = {
    "left": {
        "images": {
            "stand": "Pose_Quieto.png",
            "walk":  "Pose_Corriendo.png",
            "hover": "Pose_ManosArriba.png",
            "click": "Pose_Flexionando.png",
            "jump":  "Pose_Saltando.png",
        },
        "x": W / 2 - 280,
        "enter_from": -120,
        "align": ["click"],
        "flip": False,
    },

    "right": {
        # right avatar
        "images": {
            "stand": "avatar-stand.PNG",
            "walk":  "avatar-walk.PNG",
            "hover": "avatar-start.PNG",
            "click": "avatar-strong.PNG",
            "jump":  "avatar-jump.PNG",
        },
        "x": W / 2 + 280,
        "enter_from": W + 120,
        "align": ["click"],
        "flip": True,
    },
}
