import os
import tkinter

import ui
from bayesian.classifier import BayesClassifier
from bayesian.evaluator import Evaluator
from bayesian.preprocessing import Preprocessor
from chart import Chart

DATA_PATH = os.path.join(ui.BASE_DIR, "bayesian", "data", "dataset_walk_drive_publicado.csv")

# point colors
TRAIN_COLOR = "#ebfffa"
TEST_COLOR = "#ffd75a"
MANUAL_COLOR = "#8fd8ff"
OK_COLOR = "#3ddc84"
ERROR_COLOR = "#ff4d4d"

# ranges and bins
AGE_RANGE = (10, 80)
INCOME_RANGE = (0, 60000)
AGE_EDGES = [17, 29, 59, 75]
INCOME_EDGES = [9999, 19999, 29999, 39999, 49999, 60000]

ENTRY_STYLE = dict(
    font=("Courier New", 14, "bold"), width=9,
    bg="#1e1650", fg="#ebfffa", insertbackground="#ebfffa",
    relief="flat", highlightthickness=3,
    highlightbackground="#1f2a24", highlightcolor="#ff2a6a",
)

photos = {}
chart = None
age_entry = None
income_entry = None
prep = None
clf = None
y_pred = []      
test_points = []  


def load_photos():
    photos["bg"] = ui.load_image("bg-end.jpg", size=(ui.W, ui.H))
    photos["lbl_edad"] = ui.load_image("lbl-edad.png")
    photos["lbl_ingreso"] = ui.load_image("lbl-ingreso.png")
    for name, width in (("classify", 156), ("load-data", 172), ("predict", 172), ("evaluate", 172)):
        photos[name] = ui.load_image("btn-{}.png".format(name))
        photos[name + "_hover"] = ui.load_image("btn-{}.png".format(name),
                                                width=width + 10, pixel_art=True)


def show(cvs, go_back):
    global chart, age_entry, income_entry, prep, clf, y_pred, test_points

    ui.clear(cvs)
    if not photos:
        load_photos()

    prep, clf, y_pred, test_points = None, None, [], []

    cvs.create_image(ui.W / 2, ui.H / 2, image=photos["bg"])
    ui.make_back_button(cvs, go_back)

    # inputs
    cvs.create_image(40, 125, image=photos["lbl_edad"], anchor="w")
    cvs.create_image(40, 168, image=photos["lbl_ingreso"], anchor="w")
    age_entry = tkinter.Entry(cvs, **ENTRY_STYLE)
    income_entry = tkinter.Entry(cvs, **ENTRY_STYLE)
    cvs.create_window(185, 125, window=age_entry, anchor="w")
    cvs.create_window(185, 168, window=income_entry, anchor="w")

    ui.make_button(cvs, 40 + 156 / 2, 212, photos["classify"], photos["classify_hover"],
                   tag="btn_classify", on_click=on_classify)
    cvs.create_text(40 + 156 + 15, 212, text="", fill="#ebfffa",
                    font=("Courier New", 13, "bold"), anchor="w", tag="classify_result")

    # buttons
    right_x = ui.W - 40 - 172 / 2
    for i, (name, action) in enumerate((("load-data", on_load_data),
                                        ("predict", on_predict),
                                        ("evaluate", on_evaluate))):
        ui.make_button(cvs, right_x, 70 + i * 55, photos[name], photos[name + "_hover"],
                       tag="btn_" + name, on_click=action)

    # messages
    cvs.create_text(ui.W - 40, 212, text="", fill="#ebfffa",
                    font=("Courier New", 12, "bold"), anchor="e", tag="status")
    cvs.create_text(ui.W / 2 + 40, 140, text="", fill="#ebfffa",
                    font=("Courier New", 11, "bold"), tag="matrix")

    # empty chart with axes and bins
    chart = Chart(cvs, (40, 240, ui.W - 40, ui.H - 15), AGE_RANGE, INCOME_RANGE,
                  AGE_EDGES, INCOME_EDGES)
    chart.draw()


def set_status(text, color=TRAIN_COLOR):
    chart.cvs.itemconfig("status", text=text, fill=color)


def to_bin(value, edges):
    if value == edges[0]:
        return 0
    for i in range(len(edges) - 1):
        if edges[i] < value <= edges[i + 1]:
            return i
    return None


def read_number(entry, name):
    try:
        return float(entry.get().replace(",", ""))
    except ValueError:
        raise ValueError("{} must be a number".format(name))


def on_classify():
    # classify data given by the user
    if clf is None:
        set_status("First click on LOAD DATA", ERROR_COLOR)
        return

    chart.cvs.itemconfig("classify_result", text="")
    try:
        age = read_number(age_entry, "Age")
        income = read_number(income_entry, "Income")
    except ValueError as e:
        set_status(str(e), ERROR_COLOR)
        return

    age_bin = to_bin(age, AGE_EDGES)
    income_bin = to_bin(income, INCOME_EDGES)
    if age_bin is None or income_bin is None:
        set_status("Out of range: age {}-{}, income {:,}-{:,}".format(
            AGE_EDGES[0], AGE_EDGES[-1], INCOME_EDGES[0], INCOME_EDGES[-1]), ERROR_COLOR)
        return

    label = clf.predict(age_bin, income_bin)
    proba = clf.predict_proba(age_bin, income_bin)[label]

    chart.add_point(age, income, label, MANUAL_COLOR, tag=("point", "manual"))
    chart.cvs.itemconfig("classify_result", text="{} ({:.0%})".format(label, proba))
    set_status("Bins -> age: {}, income: {}".format(age_bin, income_bin))


def on_load_data():
    # runs the preprocessing, trains the classifier and draws the train data 
    global prep, clf, y_pred, test_points

    prep = Preprocessor()
    try:
        train, test = prep.run(DATA_PATH)
    except Exception as e:
        set_status("Error loading the data: {}".format(e), ERROR_COLOR)
        return

    clf = BayesClassifier()
    clf.fit(train)
    y_pred, test_points = [], []

    chart.clear_points()
    chart.cvs.itemconfig("matrix", text="")
    chart.cvs.itemconfig("classify_result", text="")
    for age, income, label in zip(train["Edad"], train["Ingreso"], train["Clase"]):
        chart.add_point(age, income, label, TRAIN_COLOR, tag=("point", "train"))

    set_status("Train: {} registers | Test: {} registers".format(len(train), len(test)))


def on_predict():
    # predicts the test data and draws it 
    global y_pred, test_points

    if clf is None:
        set_status("First click on LOAD DATA", ERROR_COLOR)
        return

    test = prep.test
    chart.clear_points("test")
    chart.cvs.itemconfig("matrix", text="")
    y_pred, test_points = [], []

    for age, income, age_bin, income_bin in zip(test["Edad"], test["Ingreso"],
                                                 test["age-bin"], test["income-bin"]):
        proba = clf.predict_proba(age_bin, income_bin)
        label = max(proba, key=proba.get)  # class with the highest probability
        y_pred.append(label)
        test_points.append(chart.add_point(age, income, label, TEST_COLOR, tag=("point", "test")))

    set_status("Prediction of {} registers from test df".format(len(y_pred)), TEST_COLOR)


def on_evaluate():
    # compares predictions with the real classes
    if not y_pred:
        set_status("First click on PREDICT", ERROR_COLOR)
        return

    y_true = list(prep.test["Clase"])
    evaluator = Evaluator(y_true, y_pred)
    matrix = evaluator.get_confusion_matrix()
    accuracy = evaluator.accuracy()

    for ids, real, pred in zip(test_points, y_true, y_pred):
        chart.recolor(ids, OK_COLOR if real == pred else ERROR_COLOR)

    hits = sum(real == pred for real, pred in zip(y_true, y_pred))
    set_status("Accuracy: {:.2%}  ({} out of {} correct ones)".format(accuracy, hits, len(y_pred)), OK_COLOR)
