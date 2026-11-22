import csv
import math
import tkinter
from tkinter import filedialog

from PIL import Image, ImageDraw, ImageTk

import ui
from coloring.algorithms import ALGORITHMS, MODES, color_graph
from coloring.chromatic import chromatic_number, chromatic_polynomial, evaluate
from coloring.graph import load_graph, parse_graph

BOARD_BOX = (40, 105, 520, 585)
PANEL_BOX = (550, 105, 930, 585)
TABS = ["graph", "coloring", "results"]

PALETTE = [("Blue", "#3d8bff"), ("Red", "#ff2a6a"), ("Green", "#3ddc84"), ("Yellow", "#ffd75a"),
           ("Purple", "#b06cff"), ("Orange", "#ff9a3d"), ("Cyan", "#3de0e0"), ("Pink", "#ff7ad9"),
           ("Lime", "#a8e05a"), ("Lilac", "#c9b8ff")]
ALIASES = {"azul": "blue", "rojo": "red", "verde": "green", "amarillo": "yellow", "morado": "purple",
           "naranja": "orange", "cian": "cyan", "rosa": "pink", "lima": "lime", "lila": "lilac"}
NODE = "#ffffff"
EDGE = "#4b3aa8"
TEXT = "#ebfffa"
MUTED = "#a99bd6"
ERROR = "#ff4d4d"
OK = "#ffd75a"
DARK = "#1f2a24"
FONT = ("Courier New", 11, "bold")
SMALL = ("Courier New", 10, "bold")

STEP_MS = 400
DEFAULT_TEXT = "4 4\nA B C D\nA B\nA C\nB C\nB D\n"
DEFAULT_COLORS = "Blue Red Green Yellow"

DROPDOWN_STYLE = dict(
    font=("Courier New", 12, "bold"), bg="#1e1650", fg=TEXT,
    activebackground="#ff2a6a", activeforeground="#ffffff",
    highlightthickness=3, highlightbackground=DARK,
    relief="flat", bd=0, cursor="hand2",
)
MENU_STYLE = dict(
    font=("Courier New", 12, "bold"), bg="#1e1650", fg=TEXT,
    activebackground="#ff2a6a", activeforeground="#ffffff", relief="flat", bd=0,
)
ENTRY_STYLE = dict(
    font=("Courier New", 11, "bold"), bg="#1e1650", fg=TEXT, insertbackground=TEXT,
    highlightthickness=3, highlightbackground=DARK, highlightcolor="#ff2a6a",
    relief="flat", bd=4,
)

photos = {}
cvs = None
go_back_fn = None
tab = "graph"

# data shared by the three tabs
graph = None
graph_text = DEFAULT_TEXT
color_text = DEFAULT_COLORS
k = 3
algorithm = ALGORITHMS[0]
mode = MODES[0]
assigned = {}       # vertex -> color index
fail_vertex = None
positions = {}      # vertex -> (x, y)
node_r = 20
result = None
step_index = 0
anim_job = None
results = []        # rows of the comparison table
poly = None

# widgets of the current tab
graph_box = None
colors_entry = None
algorithm_var = None
mode_var = None


def load_photos():
    photos["bg"] = ui.load_image("bg-end.jpg", size=(ui.W, ui.H))
    for name in TABS:
        photos["tab_" + name] = ui.load_image("tab-{}.png".format(name))
        photos["tab_" + name + "_on"] = ui.load_image("tab-{}-on.png".format(name))
        width = photos["tab_" + name].width()
        photos["tab_" + name + "_hover"] = ui.load_image("tab-{}.png".format(name),
                                                         width=width + 10, pixel_art=True)
    for name in ("load", "file", "color", "step", "reset", "run-all", "export",
                 "calculate", "plus", "minus"):
        photos[name] = ui.load_image("btn-{}.png".format(name))
        photos[name + "_hover"] = ui.load_image("btn-{}.png".format(name),
                                                width=photos[name].width() + 10, pixel_art=True)
    for name in ("graph", "colors", "algorithm", "mode", "polynomial"):
        photos["lbl_" + name] = ui.load_image("lbl-{}.png".format(name))
    photos["panel"] = make_panel(PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1])
    photos["board"] = make_panel(BOARD_BOX[2] - BOARD_BOX[0], BOARD_BOX[3] - BOARD_BOX[1])


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


def button(x, y, name, on_click, anchor_left=True):
    photo = photos[name]
    if anchor_left:
        x += photo.width() / 2
    item = ui.make_button(cvs, x, y, photo, photos[name + "_hover"],
                          tag="btn_" + name, on_click=on_click)
    cvs.addtag_withtag("view", item)


def show(canvas, go_back):
    global cvs, go_back_fn

    cvs = canvas
    go_back_fn = go_back
    ui.clear(cvs)
    if not photos:
        load_photos()

    cvs.create_image(ui.W / 2, ui.H / 2, image=photos["bg"])
    ui.make_back_button(cvs, on_exit)
    show_tab(tab)


def on_exit():
    save_inputs()
    stop_animation()
    go_back_fn()


def show_tab(name):
    global tab

    save_inputs()
    stop_animation()
    tab = name
    cvs.delete("view")
    cvs.delete("tabs")
    for widget in cvs.winfo_children():
        widget.destroy()

    x = 440
    for t in TABS:
        key = "tab_" + t
        w = photos[key].width()
        on = photos[key + "_on"] if t == name else photos[key]
        hover = on if t == name else photos[key + "_hover"]
        item = ui.make_button(cvs, x + w / 2, 55, on, hover, tag="tab_" + t,
                              on_click=lambda t=t: show_tab(t))
        cvs.addtag_withtag("tabs", item)
        x += w + 10

    cvs.create_image(PANEL_BOX[0], PANEL_BOX[1], image=photos["panel"], anchor="nw", tag="view")
    {"graph": build_graph_tab, "coloring": build_coloring_tab, "results": build_results_tab}[name]()


def status_text(y):
    cvs.create_text(PANEL_BOX[0] + 22, y, text="", fill=TEXT, font=FONT, anchor="nw",
                    width=PANEL_BOX[2] - PANEL_BOX[0] - 44, tag=("view", "status"))


def set_status(text, color=TEXT):
    cvs.itemconfig("status", text=text, fill=color)


def save_inputs():
    global graph_text, color_text
    try:
        if graph_box is not None and graph_box.winfo_exists():
            graph_text = graph_box.get("1.0", "end-1c")
        if colors_entry is not None and colors_entry.winfo_exists():
            color_text = colors_entry.get()
    except tkinter.TclError:
        pass


def palette():
    # k (name, hex) pairs: typed names first (priority order), then the rest of PALETTE
    hex_by_name = {name.lower(): color for name, color in PALETTE}
    chosen, used = [], set()
    for name in color_text.split():
        key = ALIASES.get(name.lower(), name.lower())
        if key in hex_by_name and key not in used:
            chosen.append((name, hex_by_name[key]))
            used.add(key)
    for name, color in PALETTE:
        if name.lower() not in used:
            chosen.append((name, color))
    return chosen[:k]


def color_names():
    return [name for name, _ in palette()]


def color_hex(index):
    return palette()[index][1]


# ---------- Graph tab ----------

def build_graph_tab():
    global graph_box, colors_entry

    px0, py0 = PANEL_BOX[0], PANEL_BOX[1]
    cvs.create_image(px0 + 22, py0 + 30, image=photos["lbl_graph"], anchor="w", tag="view")

    graph_box = tkinter.Text(cvs, width=34, height=7, **ENTRY_STYLE)
    graph_box.insert("1.0", graph_text)
    cvs.create_window(px0 + 22, py0 + 52, window=graph_box, anchor="nw", width=336, height=140, tag="view")

    button(px0 + 22, py0 + 222, "load", on_load_text)
    button(px0 + 22 + 126, py0 + 222, "file", on_load_file)

    cvs.create_image(px0 + 22, py0 + 275, image=photos["lbl_colors"], anchor="w", tag="view")
    button(px0 + 22 + 125, py0 + 275, "minus", lambda: change_k(-1))
    cvs.create_text(px0 + 22 + 213, py0 + 275, text="", fill=TEXT, font=FONT, tag=("view", "k_text"))
    button(px0 + 22 + 246, py0 + 275, "plus", lambda: change_k(1))

    colors_entry = tkinter.Entry(cvs, width=34, **ENTRY_STYLE)
    colors_entry.insert(0, color_text)
    colors_entry.bind("<KeyRelease>", lambda e: (save_inputs(), draw_color_chips(), reset_coloring()))
    cvs.create_window(px0 + 22, py0 + 302, window=colors_entry, anchor="nw", width=336, tag="view")

    status_text(py0 + 400)
    update_k_text()
    draw_color_chips()
    draw_graph()
    if graph is None:
        set_status("Write the graph or load a .txt file, then press LOAD.")
    else:
        set_status(graph_summary())


def change_k(delta):
    global k
    save_inputs()
    k = min(len(PALETTE), max(1, k + delta))
    update_k_text()
    draw_color_chips()
    reset_coloring()


def update_k_text():
    cvs.itemconfig("k_text", text="k={}".format(k))


def draw_color_chips():
    cvs.delete("chips")
    x0, y0 = PANEL_BOX[0] + 22, PANEL_BOX[1] + 350
    for i, (name, color) in enumerate(palette()):
        x, y = x0 + (i % 4) * 85, y0 + (i // 4) * 20
        cvs.create_rectangle(x, y, x + 12, y + 12, fill=color, outline=DARK, width=2,
                             tag=("view", "chips"))
        cvs.create_text(x + 18, y + 6, text=name[:8], fill=TEXT, font=SMALL, anchor="w",
                        tag=("view", "chips"))


def on_load_text():
    save_inputs()
    set_graph(lambda: parse_graph(graph_text))


def on_load_file():
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not path:
        return
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        set_status("Can't read the file: {}".format(e), ERROR)
        return
    graph_box.delete("1.0", "end")
    graph_box.insert("1.0", text)
    save_inputs()
    set_graph(lambda: load_graph(path))


def set_graph(loader):
    global graph, poly, results
    try:
        new_graph = loader()
    except NotImplementedError:
        set_status("Graph reader not implemented yet.", ERROR)
        return
    except ValueError as e:
        set_status(str(e), ERROR)
        return
    graph, poly, results = new_graph, None, []
    reset_coloring()
    layout()
    draw_graph()
    set_status(graph_summary(), OK)


def graph_summary():
    degrees = [len(graph.adj[v]) for v in graph.vertices]
    if not degrees:
        return "Empty graph."
    return "Graph loaded: {} vertices, {} edges. Max degree {}, min degree {}.".format(
        len(graph.vertices), len(graph.edges), max(degrees), min(degrees))


# ---------- Drawing ----------

def layout():
    global node_r
    positions.clear()
    n = len(graph.vertices)
    cx = (BOARD_BOX[0] + BOARD_BOX[2]) / 2
    cy = (BOARD_BOX[1] + BOARD_BOX[3]) / 2
    node_r = 24 if n <= 10 else 18 if n <= 18 else 13
    radius = (BOARD_BOX[2] - BOARD_BOX[0]) / 2 - node_r - 30
    for i, v in enumerate(graph.vertices):
        if n == 1:
            positions[v] = (cx, cy)
            continue
        angle = -math.pi / 2 + 2 * math.pi * i / n
        positions[v] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))


def draw_graph():
    cvs.delete("board")
    x0, y0, x1, y1 = BOARD_BOX
    cvs.create_rectangle(x0 - 5, y0 - 5, x1 + 4, y1 + 4, outline=DARK, width=4, tag=("view", "board"))
    cvs.create_rectangle(x0 - 2, y0 - 2, x1 + 1, y1 + 1, fill="#ffffff", outline="#7864cd",
                         width=2, tag=("view", "board"))
    if graph is None:
        cvs.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="No graph loaded", fill=MUTED,
                        font=FONT, tag=("view", "board"))
        return

    for a, b in graph.edges:
        cvs.create_line(*positions[a], *positions[b], fill=EDGE, width=3, tag=("view", "board"))
    size = 12 if node_r >= 18 else 9
    for v in graph.vertices:
        x, y = positions[v]
        cvs.create_oval(x - node_r, y - node_r, x + node_r, y + node_r, fill=NODE,
                        outline=DARK, width=3, tag=("view", "board", "node_" + v))
        cvs.create_text(x, y, text=v[:4], fill=DARK, font=("Courier New", size, "bold"),
                        tag=("view", "board"))
    paint_nodes()


def paint_nodes():
    if graph is None:
        return
    for v in graph.vertices:
        color = color_hex(assigned[v]) if v in assigned else NODE
        failed = v == fail_vertex
        cvs.itemconfig("node_" + v, fill=color, outline=ERROR if failed else DARK,
                       width=6 if failed else 3)


# ---------- Coloring tab ----------

def build_coloring_tab():
    global algorithm_var, mode_var

    px0, py0 = PANEL_BOX[0], PANEL_BOX[1]
    cvs.create_image(px0 + 22, py0 + 30, image=photos["lbl_algorithm"], anchor="w", tag="view")
    algorithm_var = tkinter.StringVar(value=algorithm)
    menu = make_dropdown(algorithm_var, ALGORITHMS, on_algorithm_change, 22)
    cvs.create_window(px0 + 22, py0 + 70, window=menu, anchor="w", tag="view")

    cvs.create_image(px0 + 22, py0 + 115, image=photos["lbl_mode"], anchor="w", tag="view")
    mode_var = tkinter.StringVar(value=mode)
    menu = make_dropdown(mode_var, MODES, on_mode_change, 22)
    cvs.create_window(px0 + 22, py0 + 155, window=menu, anchor="w", tag="view")

    button(px0 + 18, py0 + 210, "color", on_color)
    button(px0 + 18 + 120, py0 + 210, "step", on_step)
    button(px0 + 18 + 224, py0 + 210, "reset", on_reset)

    draw_legend(px0 + 22, py0 + 255)
    cvs.create_text(px0 + 22, py0 + 292, text="", fill=MUTED, font=SMALL, anchor="nw",
                    width=PANEL_BOX[2] - px0 - 44, tag=("view", "log"))
    status_text(py0 + 395)

    draw_graph()
    if graph is None:
        set_status("Load a graph in the GRAPH tab first.", ERROR)
    elif result is not None:
        show_log()
        if step_index == len(result["steps"]):
            show_outcome()
    else:
        set_status("Choose an algorithm and a mode, then press COLOR or STEP.")


def draw_legend(x, y):
    for i, (name, color) in enumerate(palette()):
        xx, yy = x + (i % 4) * 85, y + (i // 4) * 20
        cvs.create_rectangle(xx, yy, xx + 12, yy + 12, fill=color, outline=DARK, width=2, tag="view")
        cvs.create_text(xx + 18, yy + 6, text=name[:8], fill=TEXT, font=SMALL, anchor="w", tag="view")


def on_algorithm_change(name):
    global algorithm
    algorithm = name
    reset_coloring()


def on_mode_change(name):
    global mode
    mode = name
    reset_coloring()


def run_coloring():
    # returns True when a result is ready to be shown
    global result, step_index
    if graph is None:
        set_status("Load a graph in the GRAPH tab first.", ERROR)
        return False
    names = color_names()
    try:
        result = color_graph(graph, algorithm, mode, names)
    except NotImplementedError:
        set_status("{} is not implemented yet.".format(algorithm), ERROR)
        return False
    except Exception as e:
        set_status("Error while coloring: {}".format(e), ERROR)
        return False
    step_index = 0
    return True


def on_color():
    reset_coloring()
    if run_coloring():
        set_status("Coloring with {} ({})...".format(algorithm, mode))
        animate()


def on_step():
    stop_animation()
    if result is None or step_index == len(result["steps"]):
        reset_coloring()
        if not run_coloring():
            return
    next_step()
    if step_index == len(result["steps"]):
        show_outcome()


def on_reset():
    reset_coloring()
    if graph is not None:
        set_status("Same graph and k restored. Ready to run again.")


def reset_coloring():
    global result, step_index, fail_vertex
    stop_animation()
    result, step_index, fail_vertex = None, 0, None
    assigned.clear()
    cvs.itemconfig("log", text="")
    paint_nodes()


def next_step():
    global step_index, fail_vertex
    vertex, color, note = result["steps"][step_index]
    step_index += 1
    if color is None:
        fail_vertex = vertex
    else:
        assigned[vertex] = color
    paint_nodes()
    show_log()


def show_log():
    names = color_names()
    lines = []
    for i, (vertex, color, note) in enumerate(result["steps"][:step_index]):
        target = names[color] if color is not None else "no legal color"
        lines.append("{}. {} -> {}{}".format(i + 1, vertex, target, "  " + note if note else ""))
    cvs.itemconfig("log", text="\n".join(lines[-4:]))


def animate():
    global anim_job
    if step_index == len(result["steps"]):
        anim_job = None
        show_outcome()
        return
    next_step()
    anim_job = cvs.after(STEP_MS, animate)


def show_outcome():
    names = color_names()
    if result["success"]:
        used = len(set(result["colors"].values()))
        set_status("Found a {}-coloring using {} colors. Checks: {}, time: {:.3f} ms.".format(
            k, used, result["verifications"], result["time_ms"]), OK)
    else:
        neighbors = ", ".join("{} ({})".format(v, names[c]) for v, c in result["fail_neighbors"])
        set_status("No {}-coloring found with this strategy. Failed at {}; colored neighbors: {}.".format(
            k, result["fail_vertex"], neighbors or "none"), ERROR)


def stop_animation():
    global anim_job
    if anim_job is not None:
        cvs.after_cancel(anim_job)
        anim_job = None


# ---------- Results tab ----------

COLUMNS = [("Algorithm", 6), ("Mode", 138), ("OK", 216), ("Colors", 250),
           ("Checks", 324), ("ms", 398)]


def build_results_tab():
    x0, y0 = BOARD_BOX[0], BOARD_BOX[1]
    cvs.create_image(x0, y0, image=photos["board"], anchor="nw", tag="view")
    draw_table()
    button(x0 + 40, y0 + 445, "run-all", on_run_all)
    button(x0 + 40 + 160, y0 + 445, "export", on_export)

    px0, py0 = PANEL_BOX[0], PANEL_BOX[1]
    cvs.create_image(px0 + 22, py0 + 30, image=photos["lbl_polynomial"], anchor="w", tag="view")
    button(px0 + 22, py0 + 80, "calculate", on_calculate)
    cvs.create_text(px0 + 22, py0 + 115, text="", fill=TEXT, font=FONT, anchor="nw",
                    width=PANEL_BOX[2] - px0 - 44, tag=("view", "poly"))
    status_text(py0 + 420)
    show_polynomial()
    if graph is None:
        set_status("Load a graph in the GRAPH tab first.", ERROR)
    else:
        set_status("Graph: {} vertices, {} edges, k = {}.".format(len(graph.vertices), len(graph.edges), k))


def draw_table():
    cvs.delete("table")
    x0, y0 = BOARD_BOX[0] + 10, BOARD_BOX[1] + 22
    for name, dx in COLUMNS:
        cvs.create_text(x0 + dx, y0, text=name, fill=MUTED, font=FONT, anchor="w", tag=("view", "table"))
    cvs.create_line(x0, y0 + 16, BOARD_BOX[2] - 10, y0 + 16, fill="#7864cd", width=2, tag=("view", "table"))
    if not results:
        cvs.create_text((BOARD_BOX[0] + BOARD_BOX[2]) / 2, y0 + 190, text="Press RUN ALL", fill=MUTED,
                        font=FONT, tag=("view", "table"))
    for i, row in enumerate(results):
        y = y0 + 40 + i * 30
        values = [row["algorithm"], row["mode"], "yes" if row["success"] else "no",
                  row["colors"], row["verifications"], "{:.3f}".format(row["time_ms"])]
        color = TEXT if row["success"] else ERROR
        for (name, dx), value in zip(COLUMNS, values):
            cvs.create_text(x0 + dx, y, text=str(value), fill=color, font=SMALL, anchor="w",
                            tag=("view", "table"))


def on_run_all():
    global results
    if graph is None:
        set_status("Load a graph in the GRAPH tab first.", ERROR)
        return
    names = color_names()
    rows = []
    for alg in ALGORITHMS:
        for m in MODES:
            try:
                r = color_graph(graph, alg, m, names)
            except NotImplementedError:
                set_status("{} is not implemented yet.".format(alg), ERROR)
                return
            except Exception as e:
                set_status("Error in {} ({}): {}".format(alg, m, e), ERROR)
                return
            used = {c for c in r["colors"].values() if c is not None}
            rows.append(dict(algorithm=alg, mode=m, k=k, success=r["success"], colors=len(used),
                             verifications=r["verifications"], time_ms=r["time_ms"],
                             fail_vertex=r["fail_vertex"] or ""))
    results = rows
    draw_table()
    set_status("{} runs done with k = {}.".format(len(rows), k), OK)


def on_export():
    if not results:
        set_status("Press RUN ALL first.", ERROR)
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
    except OSError as e:
        set_status("Can't save the file: {}".format(e), ERROR)
        return
    set_status("Results saved.", OK)


def on_calculate():
    global poly
    if graph is None:
        set_status("Load a graph in the GRAPH tab first.", ERROR)
        return
    set_status("Calculating...")
    cvs.update_idletasks()
    try:
        data = chromatic_polynomial(graph)
        chi = chromatic_number(data["coeffs"])
    except NotImplementedError:
        set_status("Chromatic polynomial not implemented yet.", ERROR)
        return
    except Exception as e:
        set_status("Error calculating the polynomial: {}".format(e), ERROR)
        return
    poly = dict(data, chi=chi)
    show_polynomial()
    set_status("Done.", OK)


def show_polynomial():
    if poly is None:
        cvs.itemconfig("poly", text="")
        return
    chi = poly["chi"]
    lines = ["P(q) = " + format_polynomial(poly["coeffs"]), "", "χ(G) = {}".format(chi)]
    qs = sorted({q for q in (chi - 1, chi, chi + 1, k) if q >= 1})
    for q in qs:
        lines.append("P({}) = {}{}".format(q, evaluate(poly["coeffs"], q), "   <- k" if q == k else ""))
    lines += ["", "Subproblems: {}".format(poly["subproblems"]),
              "Time: {:.3f} ms".format(poly["time_ms"])]
    cvs.itemconfig("poly", text="\n".join(lines))


SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def format_polynomial(coeffs):
    degree = len(coeffs) - 1
    terms = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        p = degree - i
        number = "" if abs(c) == 1 and p > 0 else str(abs(c))
        var = "" if p == 0 else "q" if p == 1 else "q" + str(p).translate(SUPERSCRIPT)
        sign = "-" if c < 0 else "+"
        terms.append((sign, number + var))
    if not terms:
        return "0"
    text = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for sign, term in terms[1:]:
        text += " {} {}".format(sign, term)
    return text
