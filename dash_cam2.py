#!/usr/bin/env python

import io
import random
import picamera
import RPi.GPIO as GPIO
from datetime import datetime
from subprocess import call #call external commands
import time
import os.path
import gps
import os

GPIO.setmode(GPIO.BCM)
LED = 4
Btn1 = 17
Btn2 = 27
GPIO.setup(LED, GPIO.OUT)
GPIO.setup(Btn1, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(Btn2, GPIO.IN, GPIO.PUD_UP)
loc = '/home/pi/Desktop/video_'
overlay = "null";

#start up gpsd
command = "sudo killall gpsd"
p = os.system(command)
time.sleep(2) #give it a sec to kill old gpsd 
command = "sudo gpsd -n /dev/serial0 -F /var/run/gpsd.sock"
p = os.system(command)
#Listen to gps on gpsd
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
camera = picamera.PiCamera()
camera.resolution = (1920, 1080)
camera.framerate = 25
camera.hflip = True
camera.vflip = True
camera.annotate_background = picamera.Color('black')
stream = picamera.PiCameraCircularIO(camera, seconds=45)
camera.start_recording(stream, format='h264')

recording=False
end=False
started = False

start_time = 0
end_time = 0

def Btn1_callback(pin):
    global started
    global start_time
    start_time = time.time()
    started = True
    print('Button 1 pushed')
    #Blink the LED to show confirmation
    GPIO.output(LED, GPIO.LOW)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.LOW)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.HIGH)

def Btn2_callback(pin):
    global end
    print('Button 2 pushed')
    end = True

def write_now():
    global start_time
    global started
    time_now = time.time()
    delta = (time_now - start_time)
    #print(delta)
    if ((delta > 10) & started): 
        return True
    else:
        return False

def write_video(stream):
    global recording
    global loc
    global started
    print('Writing video!')
    filename = loc + datetime.now().strftime("%B_%d_%s")
    stream.copy_to(filename + '.h264') #Write video to file
    print('Done Writing Video')
    started = False
    #Blink LED to show confirmation
    GPIO.output(LED, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(LED, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(LED, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(LED, GPIO.HIGH)

def loop():
    GPIO.output(LED, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.LOW)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.HIGH)
    time.sleep(0.25)
    GPIO.output(LED, GPIO.LOW)
    time.sleep(1)

def get_time():
    global overlay
    report=session.next()
    #print report
    if report['class'] == 'TPV':
        if hasattr(report, 'time'):
            overlay = report.time
            if hasattr(report, 'speed'):
                overlay += (" " + str(report.speed) + "mph")
                if hasattr(report, 'lat'):
                    overlay += (" " + str(report.lat))
                    if hasattr(report, 'lon'):
                        overlay += (" " + str(report.lon))
    else:
        overlay = overlay
    #curr_time = datetime.now().strftime("%B_%d_%s")
    return overlay

GPIO.add_event_detect(Btn1, GPIO.FALLING, callback=Btn1_callback, bouncetime=500)
GPIO.add_event_detect(Btn2, GPIO.FALLING, callback=Btn2_callback, bouncetime=500)

GPIO.output(LED, GPIO.LOW)
time.sleep(30) #Give the camera & GPS some time to warm up
GPIO.output(LED, GPIO.HIGH)

while True:
    #global camera
    #global stream
    curr_time = get_time() #1Hz update rate
    camera.annotate_text = curr_time
    if write_now():
        print('Start Recording')
        write_video(stream)
    if end:
        camera.stop_recording()
        GPIO.output(LED, GPIO.LOW)
