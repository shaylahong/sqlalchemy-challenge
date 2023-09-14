# Dependencies 
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# Setup Database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Existing database into new model
Base = automap_base()

# Reflect tables 
Base.prepare(autoload_with=engine)

# Save ref to table 
Measurement = Base.classes.measurement 
Station = Base.classes.station

# Setup Flask 
app = Flask(__name__)

def recent():
    session = Session(engine)
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
     
    session.close()
    return(recent_date)

# Define oldest data 
def oldest():
    session = Session(engine)
    oldest_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first().date
     
    session.close()
    return(oldest_date)

# Define last 12 months
def date_last_year():
    session = Session(engine)
    
    last_12_months = dt.datetime.strptime(recent(), '%Y-%m-%d') - dt.timedelta(days=365) 
    session.close()
    return(last_12_months) 

# Routes 
@app.route("/")
def welcome():
    #list all the available routes on home page
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/><br/>"
        f"Precipitation data for the last 12 months:<br/>/api/v1.0/precipitation<br/><br/>"
        f"List of Stations:<br/>/api/v1.0/stations<br/><br/>"
        f"Temperature observations for most active station for last 12 months:<br/>/api/v1.0/tobs<br/><br/>"
        f"Temperature observations from start date(yyyy-mm-dd):<br/>Oldest Date = {oldest()}<br/>/api/v1.0/yyyy-mm-dd<br/><br/>"
        f"Temperature observations from start date(yyyy-mm-dd) to end date(yyyy-mm-dd):<br/>Oldest Date = {oldest()}, Most Recent Date = {recent()}<br/>/api/v1.0/yyyy-mm-dd/yyyy-mm-dd"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    
    #Only returns the jsonified precipitation data for the last year in the database
    precip_scores = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= date_last_year()).all()
    session.close()
    
    #Convert the query results to a dictionary by using date as the key and prcp as the value
    prcp_lst = []
    for date, prcp in precip_scores:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        prcp_lst.append(prcp_dict)
        
    #Return the JSON representation of your dictionary
    return jsonify(prcp_lst)


@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    station_list = session.query(Station.station).all()
    session.close()

    stn_lst = list(map(list, station_list))
        
    #Return a JSON list of stations from the dataset
    return jsonify(stn_lst)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # List the stations and their counts in descending order.
    active_stations = session.query(Measurement.station, func.count(Measurement.prcp)).\
        group_by(Measurement.station).order_by(func.count(Measurement.prcp).desc()).all()
    
    # Most active station id based on list of active_stations
    most_active_station = active_stations[0][0]

    #Query the dates and temperature observations of the most-active station for the previous year of data
    sel = [Measurement.date, Measurement.tobs]
    station_temps = session.query(*sel).\
        filter(func.strftime(Measurement.date) >= date_last_year(), Measurement.station == most_active_station).\
        group_by(Measurement.date).\
        order_by(Measurement.date).all()

    session.close()

    stn_tmp = list(map(list, station_temps))
    #Return a JSON list of temperature observations for the previous year
    return jsonify(stn_tmp)


@app.route('/api/v1.0/<start>')
# Accepts the start date as a parameter from the URL
def get_start(start):
    session = Session(engine)
    # Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset
    start_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).all()
    session.close()

    start_tobs = []
    for min,avg,max in start_result:
        start_tobs_dict = {}
        start_tobs_dict["Min"] = min
        start_tobs_dict["Average"] = avg
        start_tobs_dict["Max"] = max
        start_tobs.append(start_tobs_dict)

    return jsonify(start_tobs)


@app.route('/api/v1.0/<start>/<end>')
# Accepts the start and end dates as parameters from the URL 
def get_start_end(start, end):
    session = Session(engine)
    # Returns the min, max, and average temperatures calculated from the given start date to the given end date
    start_end_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start, Measurement.date <= end).all()
    session.close()

    start_end_tobs = []
    for min,avg,max in start_end_result:
        start_end_dict = {}
        start_end_dict["Min"] = min
        start_end_dict["Average"] = avg
        start_end_dict["Max"] = max
        start_end_tobs.append(start_end_dict)

    return jsonify(start_end_tobs)

if __name__ == '__main__':
    app.run(debug=True)