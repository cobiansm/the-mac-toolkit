import ui

bg_photo = None
game_over_photo = None

def show(cvs, go_back):
    global bg_photo, game_over_photo

    ui.clear(cvs)

    if bg_photo is None:  
        bg_photo = ui.load_image("bg-end.jpg", size=(ui.W, ui.H))
        game_over_photo = ui.load_image("game-over.png")
    cvs.create_image(ui.W / 2, ui.H / 2, image=bg_photo)
    cvs.create_image(ui.W / 2, 110, image=game_over_photo)

    ui.make_back_button(cvs, go_back)
