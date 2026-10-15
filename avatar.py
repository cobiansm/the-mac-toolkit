import math
import ui

WALK_SPEED = 5      
STEP_FRAMES = 6   
STRONG_FRAMES = 20 
JUMP_FRAMES = 24    
JUMP_HEIGHT = 40    

# Avatar states:
#   "walk"   -> entering screen
#   "idle"   -> stand
#   "strong" -> click 
#   "jump"   -> START
POSES = ("stand", "walk", "hover", "click", "jump")


def load_poses(config, size):
    images = config["images"]
    photos = {}
    for pose in POSES:
        photos[pose] = ui.load_image(
            images[pose], width=size, pixel_art=True,
            align_to=images["stand"] if pose in config.get("align", ()) else None,
            flip=config.get("flip", False))
    return photos


class Avatar:

    def __init__(self, cvs, x, y, target_x, photos, tag):
        self.x = x
        self.y = y
        self.target_x = target_x 
        self.photos = photos
        self.frame = 0
        self.timer = 0
        self.hovered = False
        self.state = "walk" if x != target_x else "idle"
        self.image = cvs.create_image(x, y, image=photos["stand"], tag=tag)

        cvs.tag_bind(tag, "<Enter>", lambda e: self.on_enter(cvs))
        cvs.tag_bind(tag, "<Leave>", lambda e: self.on_leave(cvs))
        cvs.tag_bind(tag, "<Button-1>", lambda e: self.on_click(cvs))

    # ---------- Poses ----------

    def set_pose(self, cvs, name):
        cvs.itemconfig(self.image, image=self.photos[name])

    def idle_pose(self, cvs):
        self.set_pose(cvs, "hover" if self.hovered else "stand")

    # ---------- Events ----------

    def on_enter(self, cvs):
        self.hovered = True
        if self.state == "idle":
            self.set_pose(cvs, "hover")
            cvs.config(cursor="hand2")

    def on_leave(self, cvs):
        self.hovered = False
        cvs.config(cursor="")
        if self.state == "idle":
            self.set_pose(cvs, "stand")

    def on_click(self, cvs):
        if self.state in ("idle", "strong"):
            self.state = "strong"
            self.timer = STRONG_FRAMES
            self.set_pose(cvs, "click")

    def jump(self, cvs):
        self.state = "jump"
        self.timer = JUMP_FRAMES
        self.set_pose(cvs, "jump")

    # ---------- Loop ----------

    def update(self, cvs):
        dy = 0

        if self.state == "walk":
            self.frame += 1
            dist = self.target_x - self.x

            if abs(dist) <= WALK_SPEED:
                self.x = self.target_x
                self.state = "idle"
                self.idle_pose(cvs)
            else:
                self.x += WALK_SPEED if dist > 0 else -WALK_SPEED
                step = (self.frame // STEP_FRAMES) % 2
                self.set_pose(cvs, "walk" if step == 0 else "stand")

        elif self.state == "strong":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "idle"
                self.idle_pose(cvs)

        elif self.state == "jump":
            progress = 1 - self.timer / JUMP_FRAMES
            dy = -JUMP_HEIGHT * math.sin(progress * math.pi)
            if self.timer > 0:
                self.timer -= 1

        cvs.coords(self.image, self.x, self.y + dy)
