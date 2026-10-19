from PIL import Image, ImageDraw, ImageTk

TEXT = "#ebfffa"
MUTED = "#a99bd6"
BIN_LINE = "#ff2a6a"
FONT = ("Courier New", 10, "bold")
FONT_SMALL = ("Courier New", 9, "bold")


class Chart:

    def __init__(self, cvs, box, x_range, y_range, x_edges, y_edges,
                 x_step=10, y_step=10000):
        """
        box:      (x0, y0, x1, y1)
        x_range:  (min, max) of the x axis (edad)
        y_range:  (min, max) of the y axis (ingreso)
        x_edges:  bin edges for x (vertical lines)
        y_edges:  bin edges for y (horizontal lines)
        """
        self.cvs = cvs
        self.box = box
        self.x_range, self.y_range = x_range, y_range
        self.x_edges, self.y_edges = x_edges, y_edges
        self.x_step, self.y_step = x_step, y_step

        x0, y0, x1, y1 = box
        self.px0, self.py0 = x0 + 102, y0 + 34
        self.px1, self.py1 = x1 - 46, y1 - 50

        self.panel_photo = None

    def to_px(self, x, y):
        (xmin, xmax), (ymin, ymax) = self.x_range, self.y_range
        px = self.px0 + (x - xmin) / (xmax - xmin) * (self.px1 - self.px0)
        py = self.py1 - (y - ymin) / (ymax - ymin) * (self.py1 - self.py0)
        return px, py

    # ---------- Drawing ----------

    def draw(self):
        self._draw_panel()
        self._draw_bins()
        self._draw_axes()
        self._draw_legend()

    def _draw_panel(self):
        x0, y0, x1, y1 = self.box
        w, h = x1 - x0, y1 - y0
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, w - 1, h - 1), fill=(18, 12, 45, 205))
        d.rectangle((0, 0, w - 1, h - 1), outline=(31, 42, 36, 255), width=4)
        d.rectangle((4, 4, w - 5, h - 5), outline=(120, 100, 205, 255), width=2)
        self.panel_photo = ImageTk.PhotoImage(img)
        self.cvs.create_image(x0, y0, image=self.panel_photo, anchor="nw", tag="chart")

    def _draw_bins(self):
        # age bins (no line on the first edge: bin 0 starts at the y axis)
        for x in self.x_edges[1:]:
            px, _ = self.to_px(x, 0)
            self.cvs.create_line(px, self.py0, px, self.py1, fill=BIN_LINE, dash=(4, 4), tag="chart")
        # income bins
        for y in self.y_edges:
            _, py = self.to_px(0, y)
            self.cvs.create_line(self.px0, py, self.px1, py, fill=BIN_LINE, dash=(4, 4), tag="chart")

        x_starts = [self.x_range[0]] + self.x_edges[1:-1]  # bin 0 starts at the axis
        for i in range(len(self.x_edges) - 1):
            px, _ = self.to_px((x_starts[i] + self.x_edges[i + 1]) / 2, 0)
            self.cvs.create_text(px, self.py0 - 8, text=str(i), fill=BIN_LINE, font=FONT_SMALL, tag="chart")
        for i in range(len(self.y_edges) - 1):
            _, py = self.to_px(0, (self.y_edges[i] + self.y_edges[i + 1]) / 2)
            self.cvs.create_text(self.px1 + 12, py, text=str(i), fill=BIN_LINE, font=FONT_SMALL, tag="chart")

    def _draw_axes(self):
        (xmin, xmax), (ymin, ymax) = self.x_range, self.y_range
        self.cvs.create_line(self.px0, self.py1, self.px1, self.py1, fill=TEXT, width=2, tag="chart")
        self.cvs.create_line(self.px0, self.py0, self.px0, self.py1, fill=TEXT, width=2, tag="chart")

        # x axis
        for x in range(xmin, xmax + 1, self.x_step):
            px, _ = self.to_px(x, ymin)
            self.cvs.create_line(px, self.py1, px, self.py1 + 5, fill=TEXT, tag="chart")
            self.cvs.create_text(px, self.py1 + 15, text=str(x), fill=TEXT, font=FONT, tag="chart")

        # y axis
        for y in range(ymin, ymax + 1, self.y_step):
            _, py = self.to_px(xmin, y)
            self.cvs.create_line(self.px0 - 5, py, self.px0, py, fill=TEXT, tag="chart")
            self.cvs.create_text(self.px0 - 9, py, text="{:,}".format(y), fill=TEXT,
                                 font=FONT, anchor="e", tag="chart")

        # axis titles
        self.cvs.create_text((self.px0 + self.px1) / 2, self.py1 + 32, text="EDAD (AÑOS)",
                             fill=MUTED, font=FONT, tag="chart")
        self.cvs.create_text(self.box[0] + 18, (self.py0 + self.py1) / 2, text="INGRESO (MXN)",
                             fill=MUTED, font=FONT, angle=90, tag="chart")

    def _draw_legend(self):
        x, y = self.px1 - 190, self.py0 - 18
        self._circle(x, y, TEXT, "chart")
        self.cvs.create_text(x + 10, y, text="CAMINA", fill=TEXT, font=FONT, anchor="w", tag="chart")
        self._cross(x + 95, y, TEXT, "chart")
        self.cvs.create_text(x + 105, y, text="CONDUCE", fill=TEXT, font=FONT, anchor="w", tag="chart")

    # ---------- Points ----------

    def _circle(self, px, py, color, tag, r=4):
        return [self.cvs.create_oval(px - r, py - r, px + r, py + r, outline=color, width=2, tag=tag)]

    def _cross(self, px, py, color, tag, r=4):
        return [self.cvs.create_line(px - r, py - r, px + r, py + r, fill=color, width=2, tag=tag),
                self.cvs.create_line(px - r, py + r, px + r, py - r, fill=color, width=2, tag=tag)]

    def add_point(self, x, y, label, color, tag="point", r=4):
        px, py = self.to_px(x, y)
        if label == "Camina":
            return self._circle(px, py, color, tag, r)
        return self._cross(px, py, color, tag, r)

    def recolor(self, ids, color):
        for item in ids:
            if self.cvs.type(item) == "oval":
                self.cvs.itemconfig(item, outline=color)
            else:
                self.cvs.itemconfig(item, fill=color)

    def clear_points(self, tag="point"):
        self.cvs.delete(tag)
