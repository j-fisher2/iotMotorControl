from flask import Flask,render_template,jsonify,request, make_response
import subprocess
import time
import RPi.GPIO as GPIO
import threading
from gpiozero import Servo
from bluepy import btle
import struct
import requests

TRIG = 15  # Trigger pin of HC-SR04
ECHO = 14  # Echo pin of HC-SR04
SERVO_PIN = 17  # Servo control pin

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Initialize global variable to store the distance
current_distance = None
auto_mode = False  # Whether the fan should be auto-controlled based on distance
fan_process = None
current_temp = None

# Replace with your SensorTag's BLE address
BLE_ADDRESS = "0C:61:CF:4F:DE:07"

# UUIDs for the Temperature Service and Characteristic on the SensorTag
TEMP_CHARACTERISTIC_UUID = "f000aa21-0451-4000-b000-000000000000"
TEMP_ENABLE_UUID = "f000aa22-0451-4000-b000-000000000000"

fan_process_lock = threading.Lock()
auto_mode_lock = threading.Lock()

FAN_ACT_TEMP = 25
ADMIN_PASSCODE = "00000"

AUTO_MODE_EVENT = threading.Event()  # Event for auto mode control
AUTO_MODE_EVENT.clear()
AUTO_MODE = False
SECURITY_LOG_ENDPOINT = "https://api.thingspeak.com/update?api_key=0WHNH25IGLEMVSR&field1=1"
TEMP_LOG_ENDPOINT = " https://api.thingspeak.com/update?api_key=INP1SFW1ZWB8BMD&field1="

# Function to get temperature from SensorTag
def get_temperature_from_sensortag():
    tag = None

    try:
        # Connect to SensorTag
        tag = btle.Peripheral(BLE_ADDRESS,btle.ADDR_TYPE_PUBLIC)

        # Enable temperature measurement
        tag.getCharacteristics(uuid=TEMP_ENABLE_UUID)[0].write(struct.pack("B", 0x01))
        time.sleep(1) # wait for the sensor to activate

        # Get the temperature service and characteristic
        temp_characteristic = tag.getCharacteristics(uuid=TEMP_CHARACTERISTIC_UUID)[0]
        temp_data = temp_characteristic.read()

        # Read temperature data
        temp_celsius = int.from_bytes(temp_data[2:4], byteorder='little') / 1280
        return temp_celsius
    finally:
        if tag:
            tag.disconnect()

def read_temperature_continuous():
    global current_temp
    while True:
        temp = get_temperature_from_sensortag()
        print(temp)
        with open('temperature.txt','w') as f:
            f.write(str(temp))
            try:
                response = requests.get(TEMP_LOG_ENDPOINT+str(temp))
            except:
                print("error")
        time.sleep(1)

def create_fan_process():
    response = requests.get("http://localhost:5000/start-fan")
    

def get_distance_continuous():
    global current_distance
    while True:
        try:
            GPIO.output(TRIG, GPIO.LOW)  # Ensure it's off
            time.sleep(0.5)
            GPIO.output(TRIG, GPIO.HIGH)  # Send a pulse
            time.sleep(0.00001)  # 10ms pulse
            GPIO.output(TRIG, GPIO.LOW)  # Stop the pulse
        
            pulse_start = None
            pulse_end = None
            # Wait for the echo pin to go HIGH
            while GPIO.input(ECHO) == GPIO.LOW:
                pulse_start = time.time()

            # Wait for the echo pin to go LOW
            while GPIO.input(ECHO) == GPIO.HIGH:
                pulse_end = time.time()


            if not pulse_end or not pulse_start:
                continue

            # Calculate the time difference
            pulse_duration = pulse_end - pulse_start

            # Calculate the distance (speed of sound = 34300 cm/s)
            distance = (pulse_duration * 34300) / 2  # in centimeters

            # Update the global variable with the latest distance
            current_distance = distance
            time.sleep(1)
        except:
            time.sleep(1)

def get_current_temp():
    with open('temperature.txt','r') as f:
        temp = float(f.read().strip())
        return temp


app = Flask(__name__)

@app.route('/start-fan')
def start_fan():
    global fan_process
    with fan_process_lock:
        if fan_process is None or fan_process.poll() is not None:
        
            fan_process = subprocess.Popen(['python3', 'fan.py'])
            return jsonify({"message":"Fan script started!"})
        return jsonify({"message":"Fan is already running."})

@app.route('/stop-fan')
def stop_fan():
    global fan_process
    with fan_process_lock:
        if fan_process and fan_process.poll() is None:
            fan_process.terminate()
            fan_process = None
            return jsonify({"message":"Fan script stopped!"})
        return jsonify({"message":"Fan is not running."})

@app.route('/enable-auto-mode')
def auto_mode_on():
    print(FAN_ACT_TEMP)
    global AUTO_MODE
    AUTO_MODE = True
    current_temp = None
    current_temp = get_current_temp()
    if current_temp >= FAN_ACT_TEMP:
        create_fan_process()
    return jsonify({"message":"success"})

@app.route('/disable-auto-mode')
def auto_mode_off():
    global AUTO_MODE
    AUTO_MODE = False
    response = requests.get("http://localhost:5000/stop-fan")
    return jsonify({"message":"success"})

@app.route('/check-auto')
def check_auto_mode():
    global AUTO_MODE
    if AUTO_MODE:
        current_temp = get_current_temp()
        if current_temp < FAN_ACT_TEMP:
            response = requests.get("http://localhost:5000/stop-fan")
        elif current_temp >= FAN_ACT_TEMP:
            response = requests.get("http://localhost:5000/start-fan")

    return jsonify({"message":"success"})

@app.route('/get-current-temperature')
def get_current_temperature():
    current_temp = get_current_temp()
    return jsonify({"temperature":str(current_temp)})

@app.route('/set-auto-temperature',methods=["POST"])
def update_temp():
    temp,passcode = request.json.get('temperature'),request.json.get('passcode')
    print(passcode)
    print(temp)
    if passcode != ADMIN_PASSCODE:
        response = requests.get(SECURITY_LOG_ENDPOINT)
        return make_response(jsonify({"message":"Unauthorized"}),401)
    global FAN_ACT_TEMP
    FAN_ACT_TEMP = int(temp)
    return "Success", 200

@app.route('/settings')
def render_settings():
    return render_template("settings.html")

@app.route('/')
def home():
    return render_template("index2.html",auto_temp=FAN_ACT_TEMP)

if __name__ == '__main__':
    # Start the background thread to measure distance continuously
    distance_thread, temp_thread = threading.Thread(target=get_distance_continuous), threading.Thread(target=read_temperature_continuous)
    temp_thread.daemon = True
    distance_thread.daemon = True  # This allows the thread to exit when the main program exits
    distance_thread.start()
    temp_thread.start()
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0')
