import io
import time
import picamera
import RPi.GPIO as GPIO
from datetime import datetime
from subprocess import call #call external commands
import gps

#Boot the gpsd process
#call(["sudo killall gpsd"])
#call(["sudo gpsd -n /dev/ttyAMA0 -F /var/run/gpsd.sock"])
# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
GPIO.setmode(GPIO.BCM)
LED = 4
Btn1 = 17
Btn2 = 27
camera = picamera.PiCamera()
stream = ""
loc = '/home/pi/Desktop/video_'
recording = False

def setup():
    global camera
    global stream
    GPIO.setup(LED, GPIO.OUT)
    GPIO.setup(Btn1, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(Btn2, GPIO.IN, GPIO.PUD_UP)
    GPIO.add_event_detect(Btn1, GPIO.FALLING, callback=Btn1_callback, bouncetime=200)
    #GPIO.add_event_detect(Btn2, GPIO.FALLING, callback=Btn2_callback, bouncetime=200)
    camera.vflip = True
    camera.hflip = True
    camera.resolution = (1280, 720)
    camera.framerate = 20
    stream = picamera.PiCameraCircularIO(camera, seconds=30)
    camera.start_recording(stream, format='h264')
    camera.wait_recording(15)

def loop():
    if (recording == False):
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(LED, GPIO.LOW)
        time.sleep(0.25)
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(0.25)
        GPIO.output(LED, GPIO.LOW)
        time.sleep(1)
    else:
        GPIO.output(LED, GPIO.HIGH)

def Btn1_callback(pin):
    global stream
    global camera
    GPIO.remove_event_detect(Btn1)
    print("Button 1 Pressed")
    GPIO.output(LED, GPIO.HIGH)
    print("Waiting for video")
    camera.wait_recording(15)
    with stream.lock:
        for frame in stream.frames:
            if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                stream.seek(frame.position)
                break
        filename = loc + datetime.now().strftime("%B %d %s")
        with io.open(filename + 'h264', 'wb') as output:
            print("Writing video")
            output.write(stream.read())
    print("Writing mp4")
    call(["MP4Box -add " + filename + ".h264 " + filename + ".mp4"])
    GPIO.add_event_detect(Btn1, GPIO.FALLING, callback=Btn1_callback, bouncetime=200)
    loop()

def Btn2_callback(pin):
    global stream
    global recording
    global camera
    print("Button 2 Pressed")
##    GPIO.output(LED, GPIO.LOW)
##    camera.stop_recording()
##    for frame in stream.frames:
##        if frame.header:
##            stream.seek(frame.position)
##            break
##    filename = loc + datetime.now().strftime("%B %d $s") + '.h264'
##    with io.open(filename, 'wb') as output:
##        while True:
##            data = stream.read1()
##            if not data:
##                break
##            output.write(data)
##    recording = False
##    loop()

#Main
setup()
while True:
    loop()
