import os
import tkinter

import avatars_config
import ui
from avatar import Avatar, JUMP_FRAMES, load_poses
from ui import W, H
from pages import folder1, folder2, folder3

F_RATE = 30
F_INTERVAL = int(1000 / F_RATE)

bg_photo = None
title_photo = None
bg_folders_photo = None
btn_photo, btn_photo_hover = None, None
project_photos = []
avatar_photos = {}  

PROJECTS = [
    ("bayesian", folder1),
    ("graphs", folder2),
    ("semaphores", folder3),
]

avatars = []
first_home = True
leaving_home = False

def init():
    global bg_photo, title_photo, bg_folders_photo, btn_photo, btn_photo_hover

    bg_photo = ui.load_image("bg-forest.jpg", cover=(W, H))
    title_photo = ui.load_image("title.png")
    bg_folders_photo = ui.load_image("bg-projects.jpg", size=(W, H))
    btn_photo = ui.load_image("start-btn-pink.png", width=260, pixel_art=True)
    btn_photo_hover = ui.load_image("start-btn-pink.png", width=280, pixel_art=True)  

    for key, page in PROJECTS:
        project_photos.append({
            "slot": ui.load_image("slot-{}.png".format(key)),
            "slot_hover": ui.load_image("slot-{}-hover.png".format(key)),
            "btn": ui.load_image("btn-{}.png".format(key)),
            "btn_hover": ui.load_image("btn-{}.png".format(key), width=270, pixel_art=True),
        })

    for name, config in avatars_config.AVATARS.items():
        avatar_photos[name] = load_poses(config, avatars_config.SIZE)

    show_home()


def update():
    for avatar in avatars:
        avatar.update(cvs)

    root.after(F_INTERVAL, update)


def show_home():
    global first_home, leaving_home

    ui.clear(cvs)
    avatars.clear()
    leaving_home = False

    cvs.create_image(W / 2, H / 2, image=bg_photo)
    cvs.create_image(W / 2, 110, image=title_photo)

    ui.make_button(cvs, W / 2, H / 2, btn_photo, btn_photo_hover,
                   tag="btn_start", on_click=on_start_clicked)

    for name, config in avatars_config.AVATARS.items():
        start_x = config["enter_from"] if first_home else config["x"]
        avatars.append(Avatar(cvs, start_x, avatars_config.Y, config["x"],
                              avatar_photos[name], tag="avatar_" + name))
    first_home = False


def on_start_clicked():
    global leaving_home
    if leaving_home:
        return
    leaving_home = True
    for avatar in avatars:
        avatar.jump(cvs)
    root.after(JUMP_FRAMES * F_INTERVAL, show_folders)


def show_folders():
    ui.clear(cvs)
    avatars.clear()
    cvs.create_image(W / 2, H / 2, image=bg_folders_photo)

    for i, ((key, page), photos) in enumerate(zip(PROJECTS, project_photos)):
        x = W / 2 + (i - 1) * 300
        open_page = lambda page=page: page.show(cvs, go_back=show_folders)

        ui.make_button(cvs, x, 230, photos["slot"], photos["slot_hover"],
                       tag="slot_" + key, on_click=open_page)
        ui.make_button(cvs, x, 345, photos["btn"], photos["btn_hover"],
                       tag="btn_" + key, on_click=open_page)

    ui.make_back_button(cvs, show_home)


root = tkinter.Tk()
root.title("The Mac Toolkit")
root.iconbitmap(os.path.join(ui.BASE_DIR, "images", "icon.ico"))
root.resizable(False, False)

cvs = tkinter.Canvas(root, width=W, height=H, bg="black", highlightthickness=0)
cvs.pack()

init()
update()
root.mainloop()
