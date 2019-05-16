import time
import board
import busio
import adafruit_vl53l0x
# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from threading import Thread, Event

# Initialize I2C bus and sensor.
i2c = busio.I2C(board.SCL, board.SDA)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

# Basic Flask config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

# sensor range data fetching Thread
thread = Thread()
thread_stop_event = Event()


class SensorRangeThread(Thread):
    def __init__(self):
        self.delay = 1.0
        super(SensorRangeThread, self).__init__()

    def get_sensor_reading(self):
        """
        Fetch sensor reading every 1 second and emit to a socketio instance (broadcast)
        Ideally to be run in a separate thread?
        """
        # infinite loop of sensor readings
        print("Fetching sensor readings")
        while not thread_stop_event.isSet():
            number = vl53.range
            print(number)
            socketio.emit('newnumber', {'number': number}, namespace='/test')
            time.sleep(self.delay)

    def run(self):
        self.get_sensor_reading()


@app.route('/')
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    # Start the sensor reading thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = SensorRangeThread()
        thread.start()


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    #socketio.run(app)
    socketio.run(app, host="0.0.0.0", port="5000")
