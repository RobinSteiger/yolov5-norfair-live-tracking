import numpy as np


#######################################################
#Detection_Process : Class for drawing the tracked points and returning usefull information.
#Detection_Process(object, frame, 2, 0.35)
#Parameters :
#   all_object : The norfair detection.
#   frame : The frame to draw.
#   min_age : The minimum age of a valid object in frame.
#   min_score : The minimum norfair confidence of a valid object.
#   moving : The moving detection object.
#   draw : Indicate if the informations needs to be drawn on the frame.
#   calibration : The (right limit, left limit) defined by the calibration.
#Attribute :
#   self.informations : Informations of the object.
#   self.final_frame : The final drawn frame.

class Detection_Process:
    #Documentation of the objects
    #https://tryolabs.github.io/norfair/2.2/reference/tracker/#norfair.tracker.TrackedObject
    def __init__(self, screen_width, screen_height) :
        #Not counted because of the calibration
        self.unused = []
        #Store Dimensions of the screen
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    #Convert the pixel center's position into percentage relative to the calibration
    def convertCenter(self, center) :
        percent = (self.right_limit - self.left_limit) /100
        return (center[0] - self.left_limit) / percent
                      
    #Here to process informations
    def get_final_objects(self, all_object, min_age, min_score, moving ,calibration_x, calibration_y, out_id):
        #To store informations
        self.informations = []
        #Drawing informations
        self.draw_info = []
        #Init the calibration's limit
        self.left_limit = calibration_x[0]
        self.right_limit = calibration_x[1]
        self.top_limit = calibration_y[0]
        self.down_limit = calibration_y[1]

        for object in all_object : 
            detected = True
            #Reject detection if one of the points doesn't exists
            live_counter = 0
            for live in object.live_points:
                if not live:
                    live_counter += 1

            if live_counter > 0:
                    detected = False

            if detected:
                tl = (int(object.estimate[0][0]), int(object.estimate[0][1]))
                br = (int(object.estimate[1][0]), int(object.estimate[1][1]))
                id = object.global_id
                if id == None:
                    id = -1
                #Norfair Confidence
                tmp_score = []
                for detection in object.past_detections:
                    tmp_score.append(np.median(detection.scores))
                score = np.median(tmp_score)
                center = tl[0] + abs((br[0] - tl[0])/2), tl[1] + abs((br[1] - tl[1])/2)

                #Call to Moving
                move = moving.get_moving(id, object.age, center)
                pos = self.convertCenter(center)
                
                if object.age >= min_age and score >= min_score :
                    #Calibration Gestion
                    #Offset is 25% of the height
                    offset = (br[1] - center[1]) / 2
                    if (br[1] > self.down_limit or br[1] - offset < self.top_limit) and (self.down_limit != 0 or self.top_limit != 0):
                        #Out on Y axis
                        self.draw_info.append([out_id, tl, br, center])
                    elif (center[0] < self.left_limit or center[0] > self.right_limit):
                        #Out on X axis
                        self.draw_info.append([out_id, tl, br, center])
                    else :
                        self.informations.append([id, 1, move, pos])
                        self.draw_info.append([id, tl, br, center])
                    
        to_send = []
        for id, in_, move, pos in self.informations:
            to_send.append([id, in_, move, pos])
        
        return to_send