import os
import sys

from PIL import Image, ImageOps, ImageTk

W, H = 960, 600

FONT_TITLE = ("Arial", 32, "bold")
FONT_BUTTON = ("Arial", 14, "bold")
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

def _open(name):
    return Image.open(os.path.join(BASE_DIR, "images", name)).convert("RGBA")


def _figure(img):
    solid = img.getchannel("A").point(lambda v: 255 if v > 200 else 0)
    box = solid.getbbox()
    top = solid.crop((0, box[1], img.width, box[1] + img.height // 8)).getbbox()
    return box, top


def _align(img, ref):
    ref_box, ref_top = _figure(ref)
    box, top = _figure(img)

    # same figure height as the reference (both poses are standing)
    scale = (ref_box[3] - ref_box[1]) / (box[3] - box[1])
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.NEAREST)
    box, top = _figure(img)

    dx = (ref_top[0] + ref_top[2]) // 2 - (top[0] + top[2]) // 2
    dy = ref_box[3] - box[3]
    out = Image.new("RGBA", ref.size, (0, 0, 0, 0))
    out.paste(img, (dx, dy), img)
    return out


def load_image(name, size=None, width=None, cover=None, pixel_art=False, trim=False,
               align_to=None, flip=False):
    """
    Load an image
      size=(w, h)    
      width=w     
      cover=(w, h)
      pixel_art=True
      trim=True
      align_to=name
      flip=True
    """
    resample = Image.NEAREST if pixel_art else Image.LANCZOS
    img = Image.open(os.path.join(BASE_DIR, "images", name))
    if align_to:
        img = _align(img.convert("RGBA"), _open(align_to))
    if flip:
        img = ImageOps.mirror(img)
    if trim:
        img = img.crop(img.getbbox())
    if cover:
        w, h = cover
        scale = max(w / img.width, h / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), resample)
        left, top = (img.width - w) // 2, (img.height - h) // 2
        img = img.crop((left, top, left + w, top + h))
    elif size:
        img = img.resize(size, resample)
    elif width:
        height = int(img.height * width / img.width)
        img = img.resize((width, height), resample)
    return ImageTk.PhotoImage(img)


def make_button(cvs, x, y, photo, photo_hover, tag, on_click):
    item = cvs.create_image(x, y, image=photo, tag=tag)

    def on_enter(e):
        cvs.itemconfig(item, image=photo_hover)
        cvs.config(cursor="hand2")

    def on_leave(e):
        cvs.itemconfig(item, image=photo)
        cvs.config(cursor="")

    cvs.tag_bind(tag, "<Enter>", on_enter)
    cvs.tag_bind(tag, "<Leave>", on_leave)
    cvs.tag_bind(tag, "<Button-1>", lambda e: on_click())
    return item


_back_photo, _back_photo_hover = None, None
 

def make_back_button(cvs, on_click):
    global _back_photo, _back_photo_hover

    if _back_photo is None:
        _back_photo = load_image("btn-exit.png", width=140, pixel_art=True, trim=True)
        _back_photo_hover = load_image("btn-exit.png", width=152, pixel_art=True, trim=True)

    make_button(cvs, 20 + 140 / 2, 20 + _back_photo.height() / 2,
                _back_photo, _back_photo_hover, tag="btn_back", on_click=on_click)


def clear(cvs):
    cvs.delete("all")
    cvs.config(cursor="")
    for widget in cvs.winfo_children():
        widget.destroy()
