from flask import Flask, render_template, request
from data.basic import downloader
from data.basic.performance_analyzer_functions import *
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATES_DIR)
print(BASE_DIR)
print(TEMPLATES_DIR)
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/src.html')
def src():
    return render_template("src.html")

if __name__ == '__main__':
    app.run(debug=True)