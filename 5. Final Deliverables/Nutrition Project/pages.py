from flask import Blueprint, render_template

pages = Blueprint(__name__,"pages")

@pages.route("/login")
def home():
    return render_template("index.html")