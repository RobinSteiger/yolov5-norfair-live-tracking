import argparse
from datetime import datetime
import threading
import time
import cv2
import numpy as np


####################################################################################################
#IO : Class controlling input and output
#Parameters :
#   args : The arguments to parse
#Attribute :
#   self.input_name : The name of the input.
#   self.output_name : The name of the output.
#   self.live : Indicate if the input is live.
#   self.cap : The video flow.
#   self.video_size : The size of the video.
#   self._local_output : The local output.
#   self._calibrate : Indicate if the camera is calibrated.
#Methods :
#   __init__(args) : 
#       Initiate the input and output objects.
#       args : The arguments passed to the function.
#   get_Frame() : 
#       Get, resize and return the last frame, and launch reconnection() if there's no frame.
#   local_output(frame) :
#       Generate a local output with the name passed in arguments.
#       frame : The last frame.
#   live_output(frame) :
#       Generate a live output.
#       frame : The last frame.
#   close() :
#       Close all input and output threads.
#   reconnection() :
#       Close the input and try to instantiate it again. Launched when get_Frame() get no frame.
#   calibrate(frame, nbr_groupe, delay) :
#       Calibrate the area of detection by getting the extreme right/left pixels position
#       of the biggest groups of the higher pixels of the frame.
#       frame : The last frame.
#       nbr_groupe : The number of groups of pixels to keep.
#       delay : The delay in minutes beetween each calibration.
#       calibration_draw : Indicate if a visual output of the calibration is needed.
####################################################################################################
class IO :
    def __init__(self, args, screen_width, screen_height) :
        #Parse arguments
        parser = argparse.ArgumentParser(description="")
        parser.add_argument("-i", type=str, required=True, default=None, dest="input_file", help="Input file")
        parser.add_argument("-o", type=str, default=None, dest="output_file", help="Output file, need to finish with a .mp4")
        list = parser.parse_args(args)
        self.input_name = list.input_file
        self.output_name = list.output_file
        if (self.output_name and self.output_name.endswith(".mp4") == False) :
            self.output_name += ".mp4"
        #Configure input
        self.live = False
        if(self.input_name.startswith("rtsp://")):
            #For live output
            if(self.input_name.endswith(":554/h264Preview_01_main") == False):
                self.input_name += ":554/h264Preview_01_main"
            self.cap = cv2.VideoCapture(self.input_name)
            self.live = True
        else:
            self.cap = cv2.VideoCapture(self.input_name)
        #Verify if video flow is valid
        if (self.cap.isOpened() == False):
            print("Error opening video stream or file")
            exit(-1)
        #Configure local output
        #Correct codec for mp4
        video_FourCC = cv2.VideoWriter_fourcc(*'avc1')
        video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        self.video_size = (screen_width, screen_height)
        self._local_output = cv2.VideoWriter(self.output_name, video_FourCC, video_fps, self.video_size)

        #If live, convert cap to a custom one
        if(self.input_name.startswith("rtsp://")):
            self.cap = CaptureLiveFrameThread(self.cap)
        #Init calibrate
        self._calibrate = False
        #Init calibration timestamp
        self.last_calibrate_time = 0
        #Calibration pixels
        self.calibration_x = [[0, 0], [0, 0]]
        self.calibration_y = [[0, 0], [0, 0]]

    def get_Frame(self) :
        if self.cap.isOpened() :
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, self.video_size)
            return ret, frame
        else :
            self.reconnection()

    def local_output(self, frame):
        self._local_output.write(frame)

    def live_output(self, frame):
        cv2.imshow('Video with Detections', frame)
        cv2.waitKey(1)
    
    def close(self):
        self.cap.release()
        self._local_output.release()

    #Reconnect camera
    def reconnection(self):
        print("\nTrying to reconnect .............")
        self.close()
        time.sleep(5)
        self.cap = cv2.VideoCapture(self.input_name, cv2.CAP_FFMPEG)
        self.cap = CaptureLiveFrameThread(self.cap)
        if self.cap.isOpened() :
            print("\nReconnected")

    # Calibration   
    def calibrate(self, frame, nbr_groupe, delay, tresh_percentage, calibration_draw):
        #Update _calibrate with the delay * 60 to get minutes
        if time.time() - self.last_calibrate_time >= delay * 60:
            self._calibrate = False  

        if not self._calibrate :
            #Return right and left pixel x coordinate for the offset of the barriers
            #Using (-1, -1) as a null value
            res = [-1, -1]
            # Format frame
            thresh1_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Sort pixels by luminosity
            sorted_pixels = np.sort(thresh1_gray, axis=None)
            # Compute index of the <tresh_percentage> % most luminous pixels
            percent_index = int((tresh_percentage/100) * len(sorted_pixels))
            # Get minimal value of the most luminous pixels
            min_brightness_value = sorted_pixels[len(sorted_pixels) - percent_index]

            #Ensure min brightness is below 255
            while min_brightness_value == 255 :
                tresh_percentage = tresh_percentage + 1
                percent = int((tresh_percentage/100) * len(sorted_pixels))
                min_brightness_value = sorted_pixels[len(sorted_pixels) - percent]
                print(f'\nCalibration used {tresh_percentage}% of the pixels.')
            #Ensure min brightness is above 230
            while min_brightness_value <= 230 :
                tresh_percentage = tresh_percentage - 1
                percent = int((tresh_percentage/100) * len(sorted_pixels))
                min_brightness_value = sorted_pixels[len(sorted_pixels) - percent]
                print(f'\nCalibration used {tresh_percentage}% of the pixels.')

            # Binary conversion, only keep 5/10% of all pixels to delete reflect
            ret,thresh1 = cv2.threshold(thresh1_gray,min_brightness_value,255,cv2.THRESH_BINARY)
            print(min_brightness_value)
            cv2.imwrite('frame.png', frame)
            cv2.imwrite('thresh.png', thresh1)
            # Get position of the most luminous pixels, positions_max[y,x]
            positions_max = np.where(thresh1 == 255)
            # Convert to format (x,y)
            positions_max = np.column_stack((positions_max[1], positions_max[0])) 
            if calibration_draw:
                # Create an image to mark adjacent's pixels
                calibration_groups = np.zeros_like(thresh1)
            # Apply "eight connectivity" for detecting contours of the regions of adjacent's pixels
            contours, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Sort contours from the biggest to the smallest
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            # Keep only the nbr_groupe biggest contours
            bigger = contours[:nbr_groupe]
            # Get the most right/left pixel of all the contours
            rightMost = (0, 0)
            leftMost = self.video_size
            topMost = self.video_size
            bottomMost = (0, 0)
            for contour in bigger:
                for pixel in contour:
                    el = pixel[0]
                    if el[0] < leftMost[0] :
                        leftMost = el
                    if el[0] > rightMost[0] :
                        rightMost = el
                    if el[1] > bottomMost[1] :
                        bottomMost = el
                    if el[1] < topMost[1] :
                        topMost = el
            
            print(f'\nTOP : {topMost}\nBOTTOM : {bottomMost}')
            print(f'\nLEFT : {leftMost}\nRIGHT : {rightMost}')

            if calibration_draw :
                for b in bigger:
                    cv2.drawContours(calibration_groups, [b], -1, 255, thickness=cv2.FILLED)
                #Calibration points
                cv2.circle(calibration_groups, leftMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
                cv2.circle(calibration_groups, rightMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
                cv2.circle(calibration_groups, topMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
                cv2.circle(calibration_groups, bottomMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
                
                cv2.imwrite('calibration_groups.png', calibration_groups)
            self._calibrate = True
            self.last_calibrate_time = time.time()
            #print("MADE CALIBRATION at "+str(self.last_calibrate_time))
            res = [leftMost[0], self.video_size[0] - rightMost[0]]
            self.calibration_x = [leftMost, rightMost]
            self.calibration_y = [topMost, bottomMost]
            return res
    
    def get_formated_calibration_x(self) :
        #As these offset are calculated FROM the right/left extreme position, before a first calibration
        #is made, the right limit (self.calibration_x[1][0]) = 0, and thus right = 1280, wich is false.
        #To ensure that this case don't reproduce, if right's value is bigger than the middle, it's 
        #too big, and will be set to 0.  
        return [self.calibration_x[0][0], self.calibration_x[1][0]]

    def get_formated_calibration_y(self) :
        return [self.calibration_y[0][1], self.calibration_y[1][1]]
    
    def set_manual_calibration(self, calibration_x, calibration_y) :
        self.calibration_x = calibration_x
        self.calibration_y = calibration_y

####################################################################################################
#CaptureLiveFrameThread : Class managing live input with a Thread to capture the latest frame/image.
#                         Usefull for MultiThreading gestion(here, ret and frame), better latency and errors gestion.
#Parameters :
#   Thread : The thread to convert.
#Attribute :
#   self.camera : The video flow/live input.
#   self.frame : The last frame/image captured.
#   self.ret : Indicate if the capture was successfull.
#   self.lock : A lock to manage the access to shared object with the other Threads.
#   self.lastTimeRet : Timestamp of the last frame/image.
#   self.isOpendval : Indicate if the camera is opened.
#Methods :
#   __init__(camera) : 
#       Initiate the thread.
#       camera : The video flow/live input.
#   run() : 
#       Running the thread, getting the last frame and closing the camera after a fixed amount of time.
#   release() :
#       Close the camera and the thread.
#       frame : The last frame.
#   read() :
#       Return the last frame.
#   isOpened() :
#       Return if the thread is working.
####################################################################################################
class CaptureLiveFrameThread(threading.Thread):

    def __init__(self, camera):
        self.camera = camera

        self.frame = None
        self.ret = False

        self.lock = threading.Lock()
        self.lastTimeRet = datetime.now()
        self.isOpenedval = True
        super().__init__()
        # Start thread
        self.daemon = True
        self.start()

    def run(self):
        while self.isOpenedval:
            ret, frame = self.camera.read()
            with self.lock:
                if ret:
                    self.ret, self.frame = ret, frame
                    self.lastTimeRet = datetime.now()
                elif (datetime.now()-self.lastTimeRet).seconds>5:
                    self.isOpenedval = False
            time.sleep(0.001)

    def release(self):
        with self.lock:
            self.camera.release()
            self.isOpenedval=False

    def read(self):
        ret = False

        while not ret:
            with self.lock:
                ret = self.ret
                frame = self.frame

                self.ret = False
            if not ret:
                time.sleep(0.001)

        return ret, frame
    
    def isOpened(self):
        with self.lock:
            return self.isOpenedval