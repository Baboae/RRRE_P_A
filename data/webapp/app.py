from flask import Flask, render_template, request
from data.basic import downloader
from data.basic.performance_analyzer_functions import *
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        username = request.form['username_input']
        user_folder = downloader.download_career_pages(username)
        if user_folder[0]==1:
            user_details = basic_user_information(user_folder[1])
            podiums = podium_stats(user_folder[1])
            p1=podiums[0]
            p2=podiums[1]
            p3=podiums[2]
            p1_rate = str(100*(podiums[0]/user_details.race_count))[:5]
            p2_rate = str(100*(podiums[1]/user_details.race_count))[:5]
            p3_rate = str(100*(podiums[2]/user_details.race_count))[:5]
            return render_template("stat_overview.html", username = user_details.full_name, p1 = p1, p1_rate=p1_rate, p2=p2, p2_rate=p2_rate, p3=p3, p3_rate=p3_rate)
        else:
            return user_folder[1]
    else:
        return render_template("index.html")
if __name__ == '__main__':
    app.run(debug=True)