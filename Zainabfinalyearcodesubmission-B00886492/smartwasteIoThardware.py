import time
import RPi.GPIO as GPIO
import BlynkLib
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import serial
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

# Set GPIO Pins
GPIO_TRIGGER = 18 #the pin for the ultrasonic trig sensor
GPIO_ECHO = 24 #the pin for the ultrasonic  echo sensor
RED_LED = 26 #the pin for the red led light sensor
GREEN_LED = 19 #the pin for the green led light sensor
BLUE_LED = 13 #the pin for the blue led light sensor
PIR_SENSOR = 4 #the pin for the pir sensor
SERVO_PIN = 21 #the pin for the servo sensor
BUZZER_PIN = 17  # GPIO 17 for the buzzer
AIR_QUALITY_SENSOR = 20  # the pin for the air quality sensor

# Set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
GPIO.setup(RED_LED, GPIO.OUT)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(BLUE_LED, GPIO.OUT)
GPIO.setup(PIR_SENSOR, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(AIR_QUALITY_SENSOR, GPIO.IN)  # Set the air quality sensor pin as input

# Blynk setup
BLYNK_TEMPLATE_ID = "TMPL5L_8iWxRT"
BLYNK_TEMPLATE_NAME = "project"
BLYNK_AUTH = "nhwFbjB_SAqcHh1SWAdCJTUyvZKeo1v5"
blynk = BlynkLib.Blynk(BLYNK_AUTH, server='blynk.cloud', port=8080)

# Servo setup
servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM frequency
servo.start(0)  # Initialization

# Setup OLED display
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)

# Clear display
oled.fill(0)
oled.show()

# Create blank image for drawing
width = oled.width
height = oled.height
image = Image.new("1", (width, height))

# Initialize drawing object
draw = ImageDraw.Draw(image)

# Load default font
font = ImageFont.load_default()

# Initialize serial connection for GPS
GPS_SERIAL_PORT = '/dev/serial0'
GPS_BAUD_RATE = 9600

# Open CSV file for writing
csv_file = open('bin_data.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['timestamp', 'bin_level', 'gps_lat', 'gps_lon', 'air_quality', 'bin_distance', 'led_lights'])

# Email setup
SMTP_SERVER = "smtp.gmail.com"  # Example for Gmail SMTP server
SMTP_PORT = 587
EMAIL_ADDRESS = "zolayiwola623@gmail.com"
EMAIL_PASSWORD = "hnjyttqqzlcagpst" 
TO_EMAIL = "zlayiwola@gmail.com"

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, TO_EMAIL, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def read_gps_data():
    """
    Read data from the GT-U7 GPS module and parse the current location.
    """
    try:
        with serial.Serial(GPS_SERIAL_PORT, GPS_BAUD_RATE, timeout=1) as ser:
            time.sleep(2)  # Allow module to initialize

            while True:
                line = ser.readline().decode('ascii', errors='ignore')
                if "$GPGGA" in line:
                    lat, lon = parse_GPGGA(line)
                    if lat and lon:
                        return lat, lon
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def parse_GPGGA(data):
    """
    Parse the GPGGA NMEA sentence to extract latitude and longitude.
    """
    parts = data.split(',')
    if parts[0] == "$GPGGA" and parts[2] and parts[4]:
        # Latitude
        lat = float(parts[2])
        lat_dir = parts[3]
        lat_deg = int(lat / 100)
        lat_min = lat - lat_deg * 100
        latitude = lat_deg + lat_min / 60
        if lat_dir == 'S':
            latitude = -latitude
        
        # Longitude
        lon = float(parts[4])
        lon_dir = parts[5]
        lon_deg = int(lon / 100)
        lon_min = lon - lon_deg * 100
        longitude = lon_deg + lon_min / 60
        if lon_dir == 'W':
            longitude = -longitude
        
        return latitude, longitude
    return None, None

# Ultrasonic sensor
def distance():
    # Set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
    # Set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # Save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # Save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # Time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # Multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because the signal travels to the object and back to the sensor
    distance = (TimeElapsed * 34300) / 2

    return distance

# LED setup
def update_leds(bin_level):
    if bin_level >= 80:
        GPIO.output(RED_LED, GPIO.HIGH)
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(BLUE_LED, GPIO.LOW)
        print("Bin is full")
    elif bin_level >= 40:
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(GREEN_LED, GPIO.LOW)
        GPIO.output(BLUE_LED, GPIO.HIGH)
        print("Bin is at the middle")
    else:
        GPIO.output(RED_LED, GPIO.LOW)
        GPIO.output(GREEN_LED, GPIO.HIGH)
        GPIO.output(BLUE_LED, GPIO.LOW)
        print("Bin level is low")

def calculate_bin_level(distance_cm, bin_height_cm):
    if distance_cm >= bin_height_cm:
        return 0  # Empty
    elif distance_cm <= 0:
        return 100  # Full
    else:
        return (1 - (distance_cm / bin_height_cm)) * 100

def open_bin():
    servo.ChangeDutyCycle(7.5)  #this value to open the bin
    time.sleep(0.3)
    servo.ChangeDutyCycle(0)  # Stop sending signal to prevent jitter

def close_bin():
    servo.ChangeDutyCycle(2.5)  # this value to close the bin
    time.sleep(0.3)
    servo.ChangeDutyCycle(0)  # Stop sending signal to prevent jitter

def sound_buzzer():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def read_air_quality():
    """
    Read the air quality sensor.
    Returns True if air quality is poor, False if good.
    """
    return GPIO.input(AIR_QUALITY_SENSOR) == GPIO.HIGH

def update_display(bin_level, is_full, air_quality_poor, lat=None, lon=None):
    # Clear previous content
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Write text
    draw.text((0, 0), "Bin Level: {:.1f}%".format(bin_level), font=font, fill=255)
    draw.text((0, 10), "Bin Status: {}".format("Full" if is_full else "Not Full"), font=font, fill=255)
    draw.text((0, 20), "Air Quality: {}".format("Poor" if air_quality_poor else "Good"), font=font, fill=255)
    
    # Display image
    oled.image(image)
    oled.show()
    time.sleep(0.1)  


BIN_HEIGHT_CM = 30
FULL_BIN_THRESHOLD = 80  

# Variables to track the previous state
previous_bin_level = None
previous_bin_full_status = None
alert_sent = False  # Track whether an alert has been sent

try:
    while True:
        start_time = time.time()
        
        blynk.run()
        
        dist = distance()
        bin_level = calculate_bin_level(dist, BIN_HEIGHT_CM)
        print("Measured Distance = %.1f cm" % dist)
        print("Bin Level = %.1f%%" % bin_level)

        # Update LEDs based on bin level
        update_leds(bin_level)

        # Send bin level data to Blynk
        blynk.virtual_write(0, bin_level)
        blynk.virtual_write(1, dist)

        # Read air quality
        air_quality_poor = read_air_quality()
        print("Air Quality is {}".format("Poor" if air_quality_poor else "Good"))
        blynk.virtual_write(4, "Poor" if air_quality_poor else "Good")

        # Check PIR sensor for human detection and bin level
        if GPIO.input(PIR_SENSOR):
            if bin_level < FULL_BIN_THRESHOLD:
                print("Human detected and bin is not full")
                open_bin()
                time.sleep(10)  # Wait for 10 seconds before closing the bin
                close_bin()
            else:
                print("Human detected and bin is full")
                close_bin()
                sound_buzzer()
        else:
            close_bin()

        # Update OLED display only if there's a change in the bin level or status
        is_full = bin_level >= FULL_BIN_THRESHOLD
        lat, lon = None, None
        if is_full:
            lat, lon = read_gps_data()
            if lat and lon:
                print(f"Current location: Latitude: {lat}, Longitude: {lon}")
                map_link = f"https://www.google.com/maps?q={lat}%2C{lon}"
                print(f"Map Link: {map_link}")
                blynk.virtual_write(2, lat)
                blynk.virtual_write(3, lon)
          
                # Send email when bin is full
                map_link = f"https://www.google.com/maps?q={lat},{lon}"
                subject = "Bin Full Alert!"
                body = f"The bin is full.\nLocation: Latitude: {lat}, Longitude: {lon}\nMap: {map_link}"
                send_email(subject, body)
                alert_sent = True  # Set the flag to prevent multiple alerts

        # Reset the alert flag if the bin is not full
        if not is_full:
            alert_sent = False

        # Collect data to save in CSV
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        led_lights = "Red" if bin_level >= FULL_BIN_THRESHOLD else ("Blue" if bin_level >= 40 else "Green")
        csv_writer.writerow([timestamp, bin_level, lat if lat else '', lon if lon else '', "Poor" if air_quality_poor else "Good", dist, led_lights])

        # Update display only if there's a change in the bin level or status
        if bin_level != previous_bin_level or is_full != previous_bin_full_status:
            update_display(bin_level, is_full, air_quality_poor, lat, lon)
            previous_bin_level = bin_level
            previous_bin_full_status = is_full

        # Ensure the loop runs quickly
        elapsed_time = time.time() - start_time
        delay = max(0, 15 - elapsed_time)
        time.sleep(delay)

except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()
    servo.stop()
    csv_file.close()  # Ensure CSV file is closed properly
