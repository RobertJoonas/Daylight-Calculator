from flask import Flask, render_template, request, url_for, flash, redirect
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "6d506b69907147099300d91fccac815d"

sunrise = ""
sunset = ""
daylight = ""


def show_daylight_helper(lat_str, lng_str, date):
    if date == "":
        msg = "Date undefined. Please pick a date."
        return render_template("home.html", errormsg=msg)
    try:
        # test if the given string values can be converted to float (if not -> raises ValueError)
        float(lat_str)
        float(lng_str)

        urlString = "/show_daylight/" + lat_str + "/" + lng_str + "/" + date
        return redirect(urlString)
    except ValueError:
        msg = "Could not read the input coordinates."
        return render_template("home.html", errormsg=msg)


def show_graph_helper(lat_str, lng_str, startDate, endDate):
    if startDate == "" or endDate == "":
        msg = "Both dates have to be defined for this operation"
        return render_template("home.html", errormsg=msg)

    sd = string_to_datetime(startDate)
    ed = string_to_datetime(endDate)
    if sd >= ed:
        msg = "End date has to be after start date"
        return render_template("home.html", errormsg=msg)

    try:
        # test if the given string values can be converted to float (if not -> raises ValueError)
        float(lat_str)
        float(lng_str)
        urlString = "/show_graph/" + lat_str + "/" + lng_str + "/" + startDate + "/" + endDate
        return redirect(urlString)
    except ValueError:
        msg = "Could not read the input coordinates."
        return render_template("home.html", errormsg=msg)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        print(request.form)
        lat_str = request.form["latitude"]
        lng_str = request.form["longitude"]
        action = request.form["show"]
        if action == "daylight":
            date = str(request.form["date"])
            return show_daylight_helper(lat_str, lng_str, date)
        elif action == "graph":
            startDate = str(request.form["startDate"])
            endDate = str(request.form["endDate"])
            return show_graph_helper(lat_str, lng_str, startDate, endDate)
    else:
        return render_template("home.html")


@app.route("/show_daylight/<string:lat>/<string:lng>/<string:date>")
def show_daylight(lat, lng, date):
    lat = float(lat)
    lng = float(lng)
    try:
        location = LocationInfo(latitude=lat, longitude=lng)
        s = sun(location.observer, string_to_datetime(date))
    except ValueError as e:
        return render_template("home.html", errormsg=e)

    sunrise = str(s["sunrise"]).split(" ")[1][:8] + " UTC"
    sunset = str(s["sunset"]).split(" ")[1][:8] + " UTC"
    daylight = str(s["sunset"] - s["sunrise"])[:8]
    result = {"sunrise": sunrise, "sunset": sunset, "daylight": daylight}
    params = {"lat": round(lat, 5), "lng": round(lng, 5), "date": date}
    return render_template("show_daylight.html", params=params, result=result)

@app.route("/show_graph/<string:lat>/<string:lng>/<string:startDate>/<string:endDate>")
def show_graph(lat, lng, startDate, endDate):
    lat = float(lat)
    lng = float(lng)
    params = {"lat": round(lat, 5), "lng": round(lng, 5), "startDate": startDate, "endDate": endDate}
    sd = string_to_datetime(startDate)
    ed = string_to_datetime(endDate)
    try:
        chart_data = generate_chart_data(lat, lng, sd, ed)
    except ValueError as e:
        msg = "During this time period is a day, when the s" + str(e)[1:]
        return render_template("home.html", errormsg=msg)
    return render_template("show_daylight_graph.html", params=params, result=chart_data)


def duration_in_hours(time_string):
    pieces = time_string.split(":")
    hours = int(pieces[0])
    minutes = int(pieces[1])
    seconds = int(pieces[2])
    minutes += seconds / 60
    hours += minutes / 60
    return round(hours, 5)


def generate_chart_data(lat, lng, startDate, endDate):
    dateDiff = int(str(endDate - startDate).split(" ")[0])
    if dateDiff > 1000:
        dateDiff = 1000
    loc = LocationInfo(latitude=lat, longitude=lng)
    date_range = pd.date_range(start=startDate, end=endDate, periods=dateDiff + 1).to_pydatetime().tolist()
    daylight_range = []
    for i in range(len(date_range)):
        s = sun(loc.observer, date_range[i])
        f = s["sunset"] - s["sunrise"]
        daylight_duration_str = str(f).split(".")[0]
        daylight_range.append(duration_in_hours(daylight_duration_str))
        date_range[i] = str(date_range[i]).split(" ")[0]
    return {"date_range": date_range, "daylight_range": daylight_range}

def string_to_datetime(s):
    pieces = s.split("-")
    return datetime(int(pieces[0]), int(pieces[1]), int(pieces[2]), 12, 0, 0, 0)


if __name__ == '__main__':
    app.run(debug=True)
