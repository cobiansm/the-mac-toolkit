import tkinter

from PIL import Image, ImageDraw, ImageTk

import ui
from heuristic.pathfinding import HEURISTICS, dijkstra

SIZES = [5, 10, 15, 20]
DEFAULT_SIZE = 10

GRID_BOX = (40, 105, 520, 585)    
PANEL_BOX = (550, 105, 930, 585)  

# cell colors
EMPTY = "#ffffff"
GRID_LINE = "#cfc8e6"
OBSTACLE = "#4b3aa8"
START = "#3ddc84"
END = "#ff2a6a"
VISITED = "#c9b8ff"
PATH = "#ffd75a"

TEXT = "#ebfffa"
ERROR = "#ff4d4d"
FONT = ("Courier New", 11, "bold")

VISITED_MS = 15  
PATH_MS = 45

DROPDOWN_STYLE = dict(
    font=("Courier New", 12, "bold"), bg="#1e1650", fg=TEXT,
    activebackground="#ff2a6a", activeforeground="#ffffff",
    highlightthickness=3, highlightbackground="#1f2a24",
    relief="flat", bd=0, cursor="hand2",
)
MENU_STYLE = dict(
    font=("Courier New", 12, "bold"), bg="#1e1650", fg=TEXT,
    activebackground="#ff2a6a", activeforeground="#ffffff", relief="flat", bd=0,
)

photos = {}
cvs = None
size_var = None
heuristic_var = None

# grid state
n = DEFAULT_SIZE
cell_px = 0
origin = (0, 0)
cells = {}          # (row, col) -> canvas rectangle id
obstacles = set()
start = None
end = None
mode = None         # None, "start" or "end": what the next click places
drag_add = None     # True: dragging adds obstacles, False: removes them
overlay = {}        # (row, col) -> VISITED / PATH color drawn by the animation
anim_job = None


def load_photos():
    photos["bg"] = ui.load_image("bg-end.jpg", size=(ui.W, ui.H))
    photos["lbl_size"] = ui.load_image("lbl-size.png")
    photos["lbl_heuristic"] = ui.load_image("lbl-heuristic.png")
    for name, width in (("start-small", 116), ("end", 116), ("calculate", 180)):
        photos[name] = ui.load_image("btn-{}.png".format(name))
        photos[name + "_hover"] = ui.load_image("btn-{}.png".format(name),
                                                width=width + 10, pixel_art=True)
    photos["panel"] = make_panel(PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1])


def make_panel(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w - 1, h - 1), fill=(18, 12, 45, 205))
    d.rectangle((0, 0, w - 1, h - 1), outline=(31, 42, 36, 255), width=4)
    d.rectangle((4, 4, w - 5, h - 5), outline=(120, 100, 205, 255), width=2)
    return ImageTk.PhotoImage(img)


def make_dropdown(var, options, command, width):
    menu = tkinter.OptionMenu(cvs, var, *options, command=command)
    menu.config(width=width, **DROPDOWN_STYLE)
    menu["menu"].config(**MENU_STYLE)
    return menu


def show(canvas, go_back):
    global cvs, size_var, heuristic_var

    cvs = canvas
    ui.clear(cvs)
    if not photos:
        load_photos()

    cvs.create_image(ui.W / 2, ui.H / 2, image=photos["bg"])
    ui.make_back_button(cvs, lambda: (stop_animation(), go_back()))

    # size dropdown (top left)
    cvs.create_image(185, 55, image=photos["lbl_size"], anchor="w")
    size_var = tkinter.StringVar(value=size_label(DEFAULT_SIZE))
    size_menu = make_dropdown(size_var, [size_label(s) for s in SIZES], on_size_change, 7)
    cvs.create_window(272, 55, window=size_menu, anchor="w")

    # start / end (top right)
    ui.make_button(cvs, ui.W - 40 - 58 - 130, 55, photos["start-small"], photos["start-small_hover"],
                   tag="btn_start_cell", on_click=lambda: set_mode("start"))
    ui.make_button(cvs, ui.W - 40 - 58, 55, photos["end"], photos["end_hover"],
                   tag="btn_end_cell", on_click=lambda: set_mode("end"))

    # right panel: heuristic, calculate, legend, messages
    px0, py0 = PANEL_BOX[0], PANEL_BOX[1]
    cvs.create_image(px0, py0, image=photos["panel"], anchor="nw")
    cvs.create_image(px0 + 22, py0 + 35, image=photos["lbl_heuristic"], anchor="w")
    heuristic_var = tkinter.StringVar(value=HEURISTICS[0])
    heuristic_menu = make_dropdown(heuristic_var, HEURISTICS, on_heuristic_change, 22)
    cvs.create_window(px0 + 22, py0 + 80, window=heuristic_menu, anchor="w")
    ui.make_button(cvs, px0 + 22 + 90, py0 + 135, photos["calculate"], photos["calculate_hover"],
                   tag="btn_calculate", on_click=on_calculate)
    draw_legend(px0 + 22, py0 + 190)
    cvs.create_text(px0 + 22, py0 + 375, text="", fill=TEXT, font=FONT, anchor="nw",
                    width=PANEL_BOX[2] - px0 - 44, tag="status")

    build_grid(DEFAULT_SIZE)


def size_label(size):
    return "{} x {}".format(size, size)


def draw_legend(x, y):
    cvs.create_text(x, y, text="LEGEND", fill="#a99bd6", font=FONT, anchor="w")
    items = [(START, "Start"), (END, "End"), (OBSTACLE, "Obstacle"),
             (VISITED, "Explored"), (PATH, "Path")]
    for i, (color, name) in enumerate(items):
        yy = y + 28 + i * 27
        cvs.create_rectangle(x, yy - 9, x + 18, yy + 9, fill=color, outline="#1f2a24", width=2)
        cvs.create_text(x + 30, yy, text=name, fill=TEXT, font=FONT, anchor="w")


def set_status(text, color=TEXT):
    cvs.itemconfig("status", text=text, fill=color)


# ---------- Grid ----------

def build_grid(size):
    global n, cell_px, origin, obstacles, start, end, mode, overlay

    stop_animation()
    cvs.delete("grid")
    n = size
    cell_px = (GRID_BOX[2] - GRID_BOX[0]) // n
    side = cell_px * n
    x0 = GRID_BOX[0] + (GRID_BOX[2] - GRID_BOX[0] - side) // 2
    y0 = GRID_BOX[1] + (GRID_BOX[3] - GRID_BOX[1] - side) // 2
    origin = (x0, y0)
    obstacles, start, end, mode, overlay = set(), None, None, None, {}

    # frame
    cvs.create_rectangle(x0 - 5, y0 - 5, x0 + side + 4, y0 + side + 4,
                         outline="#1f2a24", width=4, tag="grid")
    cvs.create_rectangle(x0 - 2, y0 - 2, x0 + side + 1, y0 + side + 1,
                         outline="#7864cd", width=2, tag="grid")

    cells.clear()
    for r in range(n):
        for c in range(n):
            x, y = x0 + c * cell_px, y0 + r * cell_px
            cells[(r, c)] = cvs.create_rectangle(x, y, x + cell_px, y + cell_px, fill=EMPTY,
                                                 outline=GRID_LINE, tag=("grid", "cell"))

    cvs.tag_bind("cell", "<Button-1>", on_grid_press)
    cvs.tag_bind("cell", "<B1-Motion>", on_grid_drag)
    cvs.tag_bind("cell", "<Enter>", lambda e: cvs.config(cursor="crosshair"))
    cvs.tag_bind("cell", "<Leave>", lambda e: cvs.config(cursor=""))

    set_status("Click cells to add or remove obstacles. Use START and END to place them.")


def cell_at(x, y):
    c = int((x - origin[0]) // cell_px)
    r = int((y - origin[1]) // cell_px)
    if 0 <= r < n and 0 <= c < n:
        return r, c
    return None


def paint(cell):
    """ Paints a cell according to its state """
    if cell == start:
        color = START
    elif cell == end:
        color = END
    elif cell in obstacles:
        color = OBSTACLE
    else:
        color = overlay.get(cell, EMPTY)
    cvs.itemconfig(cells[cell], fill=color)

    tag = "mark_{}_{}".format(*cell)
    cvs.delete(tag)
    if cell in (start, end) and cell_px >= 20:
        x = origin[0] + cell[1] * cell_px + cell_px / 2
        y = origin[1] + cell[0] * cell_px + cell_px / 2
        cvs.create_text(x, y, text="S" if cell == start else "E", fill="#1f2a24",
                        font=("Courier New", max(8, cell_px // 2), "bold"),
                        tag=("grid", tag), state="disabled")


def on_grid_press(e):
    global start, end, mode, drag_add

    cell = cell_at(e.x, e.y)
    if cell is None:
        return
    clear_path()

    if mode in ("start", "end"):
        place_marker(cell)
        return

    if cell in (start, end):
        drag_add = None
        set_status("Use START or END to move this cell.")
        return

    # toggle obstacle
    drag_add = cell not in obstacles
    set_obstacle(cell, drag_add)


def on_grid_drag(e):
    if mode is not None or drag_add is None:
        return
    cell = cell_at(e.x, e.y)
    if cell is not None and cell not in (start, end):
        set_obstacle(cell, drag_add)


def set_obstacle(cell, add):
    if add:
        obstacles.add(cell)
    else:
        obstacles.discard(cell)
    paint(cell)


def set_mode(new_mode):
    global mode
    mode = new_mode
    set_status("Click a cell to place the {}.".format(new_mode.upper()), START if new_mode == "start" else END)


def place_marker(cell):
    global start, end, mode

    if cell in obstacles:
        set_status("That cell is an obstacle. Choose another one.", ERROR)
        return
    other = end if mode == "start" else start
    if cell == other:
        set_status("START and END can't be the same cell.", ERROR)
        return

    old = start if mode == "start" else end
    if mode == "start":
        start = cell
    else:
        end = cell
    if old is not None:
        paint(old)
    paint(cell)

    placed = mode.upper()
    mode = None
    set_status("{} placed at row {}, column {}.".format(placed, cell[0] + 1, cell[1] + 1))


# ---------- Dropdowns ----------

def on_size_change(label):
    build_grid(int(label.split(" x ")[0]))


def on_heuristic_change(name):
    clear_path()
    set_status("Heuristic: {}".format(name))


# ---------- Path ----------

def as_matrix():
    return [[(r, c) in obstacles for c in range(n)] for r in range(n)]


def on_calculate():
    if start is None or end is None:
        set_status("Place START and END first.", ERROR)
        return

    clear_path()
    try:
        visited, path = dijkstra(as_matrix(), start, end, heuristic_var.get())
    except Exception as e:
        set_status("Error calculating the path: {}".format(e), ERROR)
        return

    set_status("Calculating with {}...".format(heuristic_var.get()))
    animate(list(visited), list(path))


def animate(visited, path):
    global anim_job

    steps = [(cell, VISITED, VISITED_MS) for cell in visited if cell not in (start, end)]
    steps += [(cell, PATH, PATH_MS) for cell in path if cell not in (start, end)]

    def step(i):
        global anim_job
        if i == len(steps):
            anim_job = None
            if path:
                set_status("Path found: {} steps, {} cells explored.".format(
                    len(path) - 1, len(visited)), PATH)
            else:
                set_status("No path found ({} cells explored).".format(len(visited)), ERROR)
            return
        cell, color, ms = steps[i]
        overlay[cell] = color
        paint(cell)
        anim_job = cvs.after(ms, step, i + 1)

    step(0)


def stop_animation():
    global anim_job
    if anim_job is not None:
        cvs.after_cancel(anim_job)
        anim_job = None


def clear_path():
    stop_animation()
    old = list(overlay)
    overlay.clear()
    for cell in old:
        paint(cell)
