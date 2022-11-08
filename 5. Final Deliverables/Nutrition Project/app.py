from flask import Flask
from pages import pages

app = Flask(__name__)
app.register_blueprint(pages, url_prefix="/pages")



if __name__ == '__main__':
    app.run(debug=True, port=8000)