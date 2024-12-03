import time
import RPi.GPIO as GPIO
from gpiozero import Servo

# Setup GPIO pins
TRIG = 15  # Trigger pin of HC-SR04
ECHO = 14  # Echo pin of HC-SR04
SERVO_PIN = 17  # Servo control pin

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Initialize the servo
servo = Servo(SERVO_PIN)

# Function to calculate the distance using the HC-SR04 sensor
def get_distance():
    # Send pulse to trigger pin
    GPIO.output(TRIG, GPIO.LOW)  # Ensure it's off
    time.sleep(0.5)
    GPIO.output(TRIG, GPIO.HIGH)  # Send a pulse
    time.sleep(0.00001)  # 10ms pulse
    GPIO.output(TRIG, GPIO.LOW)  # Stop the pulse

    # Wait for the echo pin to go HIGH
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()

    # Wait for the echo pin to go LOW
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()

    # Calculate the time difference
    pulse_duration = pulse_end - pulse_start

    # Calculate the distance (speed of sound = 34300 cm/s)
    distance = (pulse_duration * 34300) / 2  # in centimeters

    return distance

# Function to adjust the servo speed based on distance
def adjust_servo_speed(distance):
    # Set the speed of the servo based on distance
    # Closer distance -> faster servo movement
    # Farther distance -> slower servo movement

    # Define a minimum and maximum speed threshold (in seconds)
    min_speed = 0.05  # fastest (servo responds quickly)
    max_speed = 0.5  # slowest (servo responds slowly)

    # Invert the speed relationship (closer = faster)
    if distance < 10:  # If person is very close (less than 10 cm)
        speed = max_speed
    elif distance > 100:  # If person is far (greater than 100 cm)
        speed = min_speed+0.05
    else:
        # Linear interpolation between min_speed and max_speed
        speed = max_speed - ((distance - 10) / 90) * (max_speed - min_speed)

    # Print out the current speed and distance for debugging
    print(f"Distance: {distance:.2f} cm, Speed: {speed:.2f}")

    # Move the servo based on the calculated speed
    servo.min()  # Move to one end
    time.sleep(speed)
    servo.max()  # Move to the other end
    time.sleep(speed)

# Main loop
def main():
    try:
        while True:
            # Get the distance
            try:
                distance = None
                distance = get_distance()
                print(f"Distance: {distance:.2f} cm")

                # Adjust the servo motor speed based on distance
                if not distance:
                    continue
                adjust_servo_speed(distance)

                # Delay between readings
                time.sleep(0.1)
            except:
                print("err")

    except KeyboardInterrupt:
        print("Measurement stopped by user")
        GPIO.cleanup()  # Clean up GPIO settings
if __name__ == "__main__":
    main()
