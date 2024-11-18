import sys
import time
from tqdm import tqdm

from all_class.io import IO
from all_class.model import Model
from all_class.osc_client import OSC_Client
from all_class.tracked_points import Tracked_Points
from all_class.detection_process import Detection_Process
from all_class.moving import Moving
from all_class.draw import Draw


def main(raw_arg) :
    ########################################CONSTANTS####################################

    #Delay in frames before launching the calibration
    CALIBRATION_DELAY = 30
    #Boolean to indicate if the calibration is possible 
    CALIBRATION_READY = False

    #IO.CALIBRATE########################################################################
    #The number of groups of pixels to keep.
    NBR_GROUPE = 2
    #The delay in minutes beetween each calibration.
    DELAY = 15
    #Indicate if a visual output of the calibration is needed.
    CALIBRATION_DRAW = True
    #The percentage of the brightest pixels to set the Threshold.
    TRESH_PERCENTAGE = 5
    #Screen Width
    SCREEN_WIDTH = 1280
    #Screen Height
    SCREEN_HEIGHT = 720

    #MODEL###############################################################################
    #Indicate if the model is local or loaded from Yolo.
    LOCAL = True
    #Model confidence
    MODEL_CONFIDENCE = 0.1
    #The path to Yolo local librairie.
    YOLO_PATH = r'../local_lib/yolov5'
    #The path to the Yolo local model. 
    MODEL_PATH = r'/model/yolov5l6.pt'

    #TRACKED_POINTS######################################################################
    #Mode of tracking (bbox or centroid).
    MODE = "bbox"
    #Dstance beetween 2 detections for Norfair to accept the tracking.
    DISTANCE_THRESHOLD_BBOX = 0.7

    #DETECTION_PROCESS###################################################################
    #DETECTION_PROCESS.GET_FINAL_OBJECTS
    #The minimum number of frame for an object to be considered alive.
    MIN_AGE = 2
    #The minimum Norfair score for an object to be considered.
    MIN_SCORE_NORFAIR = 0.05
    #The special value for the person out of the detection
    OUT_ID = -137

    #OSC_CLIENT##########################################################################
    #The maximum number of people tracked simultanously (Used also for init Drawing)
    NBR_PEOPLE_MAX = 10
    #The number of informations for each tracked person.
    NBR_INFO = 3
    #The IP of the client. Default : 127.0.0.1
    IP = "10.0.0.1"
    #The port of the client. Default : 5005
    PORT = 8000
    #OSC_CLIENT.SEND_INFO
    #The number of frames until a tracked person effectively disappear to let the installation the time to adapt.
    COUNTDOWN = 36
    #Distance offset in % from the start/end of the installation to accept that a person left the detection.
    LEAVING_OFFSET = 1
    #Time difference in seconds after which we suppress a cached person definitively.
    TIME_TO_LET_GO = 3
    #Distance offset in % beetween the old and the new detection to accept that it was the same person
    #Also offset in % to accept a new detection.
    APPEAR_OFFSET = 5

    #MOVING##############################################################################
    #The difference in px which is considered as a move.
    DIFF_DIST = 3
    #The number of frame to use for the estimation of the deplacement.
    NBR_FRAME = 5

    #DRAW##############################################################################
    #Display all informations of the models.
    DRAW_DEBUG = True

    #######################################INSTANCIATION#################################
    io = IO(raw_arg, SCREEN_WIDTH, SCREEN_HEIGHT)
    model = Model(LOCAL, MODEL_CONFIDENCE, YOLO_PATH, MODEL_PATH)
    tracked_points = Tracked_Points(MODE, DISTANCE_THRESHOLD_BBOX)
    detection_process = Detection_Process(SCREEN_WIDTH, SCREEN_HEIGHT)
    osc_client = OSC_Client(NBR_PEOPLE_MAX, NBR_INFO, IP, PORT)
    moving = Moving(DIFF_DIST, NBR_FRAME)
    draw = Draw()
    
    #Display
    pbar = tqdm()
    #Init calibration
    MANUAL_CALIBRATION = True
    #From 0 on the left, from 1280 on the right
    manual_offset_calibrate_x = [[20, 400], [1260, 400]]
    #From 0
    manual_offset_calibrate_y = [[640, 440], [640, 650]]
    io.set_manual_calibration(manual_offset_calibrate_x, manual_offset_calibrate_y)
    



    #######################################MAIN LOOP#####################################
    while True:
        #Catching error made by reconnection
        try :
            ret,frame = io.get_Frame()
        except TypeError as e:
            print("Error : ")
            print(e)
            print("The program will soon restart.")
            time.sleep(10)

        pbar.update(1)
        if ret :
            cal_x = io.get_formated_calibration_x()
            cal_y = io.get_formated_calibration_y()
    
            #Get the model detection
            yolo_detections = model.getDetections(frame)
            #Convert detection to norfair format
            tracked_objects, raw = tracked_points.yolo_detections_to_tracked_points(yolo_detections)
            #Draw the frame and process informations
            detection_list = detection_process.get_final_objects(tracked_objects, MIN_AGE, MIN_SCORE_NORFAIR, moving, 
                                                          cal_x, cal_y, OUT_ID)
            #Sort the informations, send them and detect if a new person entered this frame for a calibration
            new_person = osc_client.send_info(detection_list, COUNTDOWN,LEAVING_OFFSET, TIME_TO_LET_GO, APPEAR_OFFSET)
            #Drawing all info on the frame
            frame = draw.draw_info(frame, detection_process.draw_info, osc_client.info_list,
                                    io.calibration_x, io.calibration_y, OUT_ID, raw, tracked_objects, DRAW_DEBUG)
            #Calibration is launched only when a new person enter in the detection
            if not MANUAL_CALIBRATION :
                #Loop to delay the calibration
                if new_person and not CALIBRATION_READY :
                    CALIBRATION_READY = True
                    delay = CALIBRATION_DELAY
                elif CALIBRATION_READY and delay > 0 :
                    delay = delay - 1
                    print("\nCOUNTDOWN TO CALIBRATION : "+str(delay))
                elif CALIBRATION_READY and delay == 0 :
                    print("\nCALIBRATION")
                    io.calibrate(frame, NBR_GROUPE, DELAY, TRESH_PERCENTAGE, CALIBRATION_DRAW)
                    CALIBRATION_READY = False
            io.live_output(frame)
            #io.local_output(frame)
        else :
            print("No Frame")
            if not io.live :
                break
            time.sleep(10)
            

#Entry point
if __name__ == '__main__':
    main(sys.argv[1:])
#py main.py -i rtsp://admin:heiafr@10.0.0.50:554/h264Preview_01_main  