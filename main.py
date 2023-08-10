import numpy as np
import cv2
import time
from pyfirmata import Arduino, SERVO, util
import imutils
import requests
from google.cloud import vision
import os
from google.cloud.vision_v1 import types
from google.cloud.vision_v1.services.image_annotator import client

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'savvy-bit-394301-ad7f811cd35d.json'

# State
object = False

# Arduino Info
port = '/dev/cu.usbmodem1201'
pin = 9
board = Arduino(port)

board.digital[pin].mode = SERVO

def rotate_servo(pin, angle):
    board.digital[pin].write(angle)
    time.sleep(0.015)

def rotate_servo2(pin,angle):
    board.digital[pin].write(angle)
    time.sleep(0.015)

def open_servo(num):
    for i in range(0,num):
        rotate_servo(9,i)
        rotate_servo2(8,abs(num-i))

def text_detection(uri):
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = uri

    response_text = client.text_detection(image=image)

    for r in response_text.text_annotations:
        d = r.description
        print(d)
        # if d == "Seizure":
        #     return True
        # elif d == "Boo":
        #     return True
        # else: return False
        if d:
            return True
        else: return False

def upload_image_to_imgur(image_path, client_id):
    url = "https://api.imgur.com/3/image"

    headers = {
        "Authorization": f"Client-ID {client_id}"
    }

    with open(image_path, "rb") as image_file:
        files = {"image": image_file}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        data = response.json()
        image_url = data["data"]["link"]
        return image_url
    else:
        print(f"Failed to upload the image. Status code: {response.status_code}")
        return None

haar_upper_body_cascade = cv2.CascadeClassifier("haarcascade_upperbody.xml")

video_capture = cv2.VideoCapture(0)

strength = 0

open_servo(35)

while 1:
    ret, frame = video_capture.read(1)

    frame = imutils.resize(frame, width=1000) 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 

    upper_body = haar_upper_body_cascade.detectMultiScale(
        gray,
        # scaleFactor = 5,
        #minNeighbors = 5,
        minSize = (5, 10), # Min size for valid detection, changes according to video size or body size in the video.
        # flags = cv2.CASCADE_SCALE_IMAGE
    )

    # Draw a rectangle around the upper bodies
    for (x, y, w, h) in upper_body:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.putText(frame, "AHHH SCARY MONSTER", (x + 5, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        strength += 1

    cv2.imshow('Video', frame)

    if strength > 25:
        image = cv2.imwrite('output.jpg', frame)
        video_capture.release()
        cv2.destroyAllWindows()
        print("working")

        imgur_client_id = "4c2675b31036b06"
        image = cv2.imread('output.jpg')
        flipped_image = cv2.flip(image, 1)
        cv2.imwrite('output.jpg', flipped_image)

        image_url = upload_image_to_imgur('output.jpg', imgur_client_id)
        if image_url:
            print("printing image url")
            print(f"Image URL: {image_url}")
            print("-------------------------")
            if text_detection(image_url) == True:      
                open_servo(90)
                break
            else:
                break
        else:
            print("Image upload failed.")
            break
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break 