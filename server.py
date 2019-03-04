#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Thread
import uuid
import jwt
import time
import datetime
import os
import si7021
import RPi.GPIO as GPIO
import pigpio

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisissecret'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dryer.db')

pi = pigpio.pi()
sensor1 = si7021.si7021(1)
sensor2 = si7021.si7021(3)
pin = 26
pi.set_mode(pin, pigpio.OUTPUT)
global stop_run
stop_run = True
pi.write(pin, 0)

db = SQLAlchemy(app)


#  ███╗   ███╗ ██████╗ ██████╗ ███████╗██╗     ███████╗
#  ████╗ ████║██╔═══██╗██╔══██╗██╔════╝██║     ██╔════╝
#  ██╔████╔██║██║   ██║██║  ██║█████╗  ██║     ███████╗
#  ██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██║     ╚════██║
#  ██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗███████╗███████║
#  ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝
#                                                      
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


class ProcessData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    set_temp = db.Column(db.Integer)
    cook_time = db.Column(db.Integer)
    read_int = db.Column(db.Integer)
    time_stamp = db.Column(db.String(80))
    user_id = db.Column(db.Integer) # now uses string but db still set as int


class DHTData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Integer)
    hum = db.Column(db.Integer)
    time_stamp = db.Column(db.String(80))
    process_id = db.Column(db.String(50))


#  ████████╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗███████╗
#  ╚══██╔══╝██╔═══██╗██║ ██╔╝██╔════╝████╗  ██║██╔════╝
#     ██║   ██║   ██║█████╔╝ █████╗  ██╔██╗ ██║███████╗
#     ██║   ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╗██║╚════██║
#     ██║   ╚██████╔╝██║  ██╗███████╗██║ ╚████║███████║
#     ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝
#                                                      
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


#  ██╗   ██╗███████╗███████╗██████╗ ███████╗
#  ██║   ██║██╔════╝██╔════╝██╔══██╗██╔════╝
#  ██║   ██║███████╗█████╗  ██████╔╝███████╗
#  ██║   ██║╚════██║██╔══╝  ██╔══██╗╚════██║
#  ╚██████╔╝███████║███████╗██║  ██║███████║
#   ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝
#                                           
@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users': output})


@app.route('/user/<public_id>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user': user_data})


@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created'})


@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message': 'The user has been promoted!'})


@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'The user has been deleted!'})


#  ██╗      ██████╗  ██████╗ ██╗███╗   ██╗
#  ██║     ██╔═══██╗██╔════╝ ██║████╗  ██║
#  ██║     ██║   ██║██║  ███╗██║██╔██╗ ██║
#  ██║     ██║   ██║██║   ██║██║██║╚██╗██║
#  ███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║
#  ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝
#                                         
@app.route('/login')
def login():

    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})


#  ██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗
#  ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝
#  ██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗
#  ██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║
#  ██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║
#  ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝
#                                                           
@app.route('/process/admin', methods=['GET'])
@token_required
def get_all_processes(current_user): # admin only

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    processes = ProcessData.query.all()

    output = []

    for process in processes:
        process_data = {}
        process_data['process_id'] = process.process_id
        process_data['name'] = process.name
        process_data['set_temp'] = process.set_temp
        process_data['cook_time'] = process.cook_time
        process_data['read_int'] = process.read_int
        process_data['time_stamp'] = process.time_stamp
        process_data['user_id'] = process.user_id
        output.append(process_data)

    return jsonify({'processes': output})


@app.route('/process', methods=['GET'])
@token_required
def get_all_processes_by_user(current_user): # only the users processes

    if not current_user.admin:
        return jsonify({'message': 'Cannot perforn that function'})

    processes = ProcessData.query.filter_by(user_id=current_user.public_id).all()

    output = []

    for process in processes:
        process_data = {}
        process_data['process_id'] = process.process_id
        process_data['name'] = process.name
        process_data['set_temp'] = process.set_temp
        process_data['cook_time'] = process.cook_time
        process_data['read_int'] = process.read_int
        process_data['time_stamp'] = process.time_stamp
        process_data['user_id'] = process.user_id
        output.append(process_data)

    return jsonify({'processes': output})


@app.route('/process', methods=['POST'])
@token_required
def new_process(current_user):
    data = request.get_json()

    pid = str(uuid.uuid4())
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    uid = current_user.public_id

    log_process_data(pid, data['name'], data['stemp'], data['ctime'], data['rinte'], ts, uid)

    global stop_run

    run_process(pid, data['stemp'], data['ctime'], data['rinte'])

    # run_process function. Do this on a different thread so it doesnt get clogged.
    # run_process(name, set_temp, cook_time, read_int, time_stamp, user_id)

    return jsonify({'message': 'Process started!'})


#  ██████╗  █████╗ ████████╗ █████╗ 
#  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
#  ██║  ██║███████║   ██║   ███████║
#  ██║  ██║██╔══██║   ██║   ██╔══██║
#  ██████╔╝██║  ██║   ██║   ██║  ██║
#  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
#                                   
@app.route('/data/<process_id>', methods=['GET'])
@token_required
def get_process_by_id(current_user, process_id):
    print(current_user.id)

    # process = ProcessData.query.filter_by(process_id=process_id, user_id=current_user.public_id).first()
    dhtdata = DHTData.query.filter_by(process_id=process_id).all()

    output = []

    for data in dhtdata:
        dht_data = {}
        dht_data['temp'] = data.temp
        dht_data['hum'] = data.hum
        dht_data['time_stamp'] = data.time_stamp
        dht_data['process_id'] = data.process_id
        output.append(dht_data)

    return jsonify({'dht_data': output})


#  ███████╗██╗   ██╗███╗   ██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
#  ██╔════╝██║   ██║████╗  ██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
#  █████╗  ██║   ██║██╔██╗ ██║██║        ██║   ██║██║   ██║██╔██╗ ██║███████╗
#  ██╔══╝  ██║   ██║██║╚██╗██║██║        ██║   ██║██║   ██║██║╚██╗██║╚════██║
#  ██║     ╚██████╔╝██║ ╚████║╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║███████║
#  ╚═╝      ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
#                                                                            
def get_temphumi_data(pid):

    temp = (sensor1.Temperature() + sensor2.Temperature()) / 2
    hum = (sensor1.Humidity() + sensor2.Humidity()) / 2

    if hum is not None and temp is not None:
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return temp, hum, ts


def log_data(pid, temp, hum, ts):

    dht_data = DHTData(temp=temp, hum=hum, time_stamp=ts, process_id=pid)

    db.session.add(dht_data)
    db.session.commit()


def log_process_data(pid, name, set_temp, cook_time, read_interval, ts, current_user):

    process_data = ProcessData(process_id=pid, name=name, set_temp=set_temp, cook_time=cook_time, read_int=read_interval, time_stamp=ts, user_id=current_user)

    db.session.add(process_data)
    db.session.commit()


def adjust_heater_power(set_temp, current_temp):
    if set_temp <= current_temp:
        pi.write(pin, 0)
    else:
        pi.write(pin, 1)


def start_process(pid, set_temp, cook_time, read_interval):
    global stop_run
    print(stop_run)

    while not stop_run:

        current_temp, current_hum, cts = get_temphumi_data(pid)
        adjust_heater_power(set_temp, current_temp)
        log_data(pid, current_temp, current_hum, cts)

        time.sleep(read_interval)
        cook_time = cook_time - read_interval

        if cook_time <= 0:
            set_stop_run()
            break
    
    pi.write(pin, 0)
    print("yay")
    return stop_run


#  ████████╗██╗  ██╗██████╗ ███████╗ █████╗ ██████╗ ███████╗
#  ╚══██╔══╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝
#     ██║   ███████║██████╔╝█████╗  ███████║██║  ██║███████╗
#     ██║   ██╔══██║██╔══██╗██╔══╝  ██╔══██║██║  ██║╚════██║
#     ██║   ██║  ██║██║  ██║███████╗██║  ██║██████╔╝███████║
#     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝
#                                                           
def manual_run(pid, set_temp, cook_time, read_interval):
    t = Thread(target=start_process, args=(pid, set_temp, cook_time, read_interval))
    t.start()


def run_process(pid, set_temp, cook_time, read_interval):
    global stop_run
    stop_run = False
    manual_run(pid, set_temp, cook_time, read_interval)


def set_stop_run():
    global stop_run
    stop_run = True


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8023, debug="True")
