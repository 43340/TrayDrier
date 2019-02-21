from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import time
import Adafruit_DHT
import sqlite3
import json
import datetime as dt
import RPi.GPIO as GPIO
import pigpio
import datetime

dbname = 'sensorData.db'
pi = pigpio.pi()
pin = 19
pi.set_mode(pin, pigpio.OUTPUT)
global processing
processing = False


app = Flask("__name__")
api = Api(app)


def getDHTData(pid):
    DHT22Sensor = Adafruit_DHT.DHT22
    DHTPin = 4
    hum, temp = Adafruit_DHT.read_retry(DHT22Sensor, DHTPin)
    # adjustHeaterPower(hum, temp)

    if hum is not None and temp is not None:
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hum = round(hum)
        temp = round(temp)
    return temp, hum, ts


def logData(pid, temp, hum, ts):
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    curs.execute("INSERT INTO dht_data VALUES((?), (?), (?), (?))",
                 (pid, temp, hum, ts))
    conn.commit()
    conn.close()


def logProcessData(pid, name, set_temp, cook_time, read_interval):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(dbname)
    curs = conn.cursor()
    curs.execute("INSERT INTO process_data VALUES((?), (?), (?), (?), (?), (?))",
                 (pid, name, set_temp, cook_time, read_interval, ts))
    conn.commit()
    conn.close()

    return ts


def adjustHeaterPower(set_temp, current_temp):
    if set_temp <= current_temp:
        pi.write(pin, 0)
    else:
        pi.write(pin, 1)


def startProcess(pid, set_temp, cook_time, read_interval, param):
    start = param

    while start:
        start = processing
        current_temp, current_hum, cts = getDHTData(pid)
        adjustHeaterPower(set_temp, current_hum) # changed current_temp to current_hum for testing purposes
        logData(pid, current_temp, current_hum, cts)

        time.sleep(read_interval)
        cook_time = cook_time - read_interval
        print(start)

        if cook_time <= 0:
            pi.write(pin, 0)
            start = False
            
            return start
    
    pi.write(pin, 0)
    start = False
    return start


# This function will hold some parameter one day. Now it does
def getData(pid=""):
    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()

    if pid == "":
        rows = curs.execute("SELECT * FROM dht_data").fetchall()
    else:
        rows = curs.execute("SELECT * FROM dht_data WHERE process_id=" + pid)

    # print (json.dumps([dict(ix) for ix in rows]))
    return [dict(ix) for ix in rows]


def deleteData(pid="", db_table=""):
    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()

    curs.execute("DELETE FROM " + db_table)
    conn.commit()
    conn.close()


def countDownTimer(cook_time):
    x=datetime.today()
    y=x.replace(day=x.day+1, hour=0, minute=cook_time, second=0, microsecond=0)
    delta_t=y-x
    secs=delta_t.seconds+1

    second = (secs % 60)
    minute = (secs / 60) % 60
    hour = (secs / 3600)
    print ("Seconds: %s " % (second))
    print ("Minute: %s " % (minute))
    print ("Hour: %s" % (hour))

    print ("Time is %s:%s:%s" % (hour, minute, second))


class Data(Resource):
    def get(self):

        temp, hum, ts = getDHTData(pid="")

        return {
            'time': ts,
            'temperature': temp,
            'humidity': hum
        }


class History(Resource):
    def get(self):

        history = getData()
        jsonify(history)

        return {
            'history': history
        }
    

    def delete(self):
        deleteData("", "dht_data")


class History_By_Id(Resource):
    def get(self, id):
        history = getData(id)
        jsonify(history)

        return {
            'history': history
        }


class Start_Process(Resource):
    def post(self, param):
        pid = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        content = request.get_json()
        name = content['name']
        set_temp = content['stemp']
        cook_time = content['ctime']
        read_interval = content['rinte']

        if(param==1):
            logProcessData(pid, name, set_temp, cook_time, read_interval)
        
        isProcessing = startProcess(pid, set_temp, cook_time, read_interval, param)

        return {
                'processing': isProcessing
                }


api.add_resource(Data, '/data')
api.add_resource(History, '/history')
api.add_resource(History_By_Id, '/history/<id>')
api.add_resource(Start_Process, '/start/<param>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8023, debug="True")
