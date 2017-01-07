import io
import random
import picamera
import RPi.GPIO as GPIO
from datetime import datetime
from subprocess import call #call external commands
import time
import os.path
import gps

GPIO.setmode(GPIO.BCM)
LED = 4
Btn1 = 17
Btn2 = 27
GPIO.setup(LED, GPIO.OUT)
GPIO.setup(Btn1, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(Btn2, GPIO.IN, GPIO.PUD_UP)
loc = '/home/pi/Desktop/video_'
overlay = "null";

#Listen to gps on gpsd
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

def Btn1_callback(pin):
    global started
    started = not started
    print('Button 1 pushed')
    print(started)

def Btn2_callback(pin):
    global recording
    recording = not recording
    print('Button 2 pushed')
    print(recording)
    if (recording):
        GPIO.output(LED, GPIO.HIGH)
    else:
        GPIO.output(LED, GPIO.LOW)
    

def write_now():
    global recording
    if recording:
        return True
    else:
        return False

def write_video(stream):
    global recording
    print('Writing video!')
    with stream.lock:
        # Find the first header frame in the video
        for frame in stream.frames:
            if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                stream.seek(frame.position)
                break
        # Write the rest of the stream to disk
        filename = loc + datetime.now().strftime("%B_%d_%s")
        with io.open(filename + '.h264', 'wb') as output:
            output.write(stream.read())
        print('Done writing video')
        recording = False
        GPIO.output(LED, GPIO.LOW)
        while (not os.path.isfile(filename + ".h264")):
            time.sleep(0.5)
            #Loop until file is made
        try:
            cmd="ffmpeg -r 25 -i " + filename + ".h264 -vcodec copy " + filename + ".mp4"
            call([cmd])
            print('Made .mp4')
        except:
            print('MP4 failed to create')

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
                overlay += (" " + str(report.speed * 1.6))
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
recording=False
started=False

while True:
    with picamera.PiCamera() as camera:
        camera.resolution = (1280, 720)
        camera.framerate = 25
        camera.hflip = True
        camera.vflip = True
        stream = picamera.PiCameraCircularIO(camera, seconds=60)
        camera.start_recording(stream, format='h264')
        try:
            while started:
                curr_time = get_time()
                camera.annotate_text = curr_time
                camera.wait_recording(1)
                if write_now():
                    # Keep recording for 10 seconds and only then write the
                    # stream to disk
                    print('Start Recording')
                    camera.wait_recording(5)
                    write_video(stream)
        finally:
            camera.stop_recording()
            loop()
