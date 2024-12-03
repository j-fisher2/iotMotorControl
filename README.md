# **IoT motor (Fan) Control**

This project allows you to control a motor (fan) based on temperature and distance readings from sensors. It also provides an interface to monitor and configure the system remotely via Flask web routes.

### **Features**
- **Temperature Monitoring**: Uses a SensorTag to read temperature and log it to ThingSpeak.
- **Fan Control**: Manages a fan through a GPIO pin based on temperature or manual control.
- **Distance Measurement**: Uses an HC-SR04 ultrasonic sensor to measure distance.
- **Auto Mode**: The fan can be automatically controlled based on a temperature threshold.
- **Web Interface**: A Flask web app that provides endpoints to control the fan and monitor system status.

---

## **Prerequisites**
Make sure you have the following installed and configured:
- **Python 3** (version 3.10 or higher recommended)
- **Flask**: A Python web framework
- **RPi.GPIO**: For Raspberry Pi GPIO pin control
- **gpiozero**: To control GPIO pins like a servo
- **bluepy**: To interact with Bluetooth Low Energy (BLE) devices (SensorTag)
- **ThingSpeak Account**: To log temperature and security status (get API keys)

Start webserver `python3 webserver.py` available at http://localhost:5000

