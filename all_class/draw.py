import cv2


class Draw:
    def __init__(self) :
        #Position
        self.x_start = 20
        self.y_start = 50 
        
        # Text settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_thickness = 2
        #Space between each line
        self.line_spacing = 20
        
    #detection_info : [id, tl, br, center] only for tracked person
    #client_info : [id, inside/outside, moving, position in %] for all slots
    def draw_info(self, frame, detection_info, client_info, calibration_x, calibration_y, out_id, raw, objects, debug = False) :
        
        #Drawing calibration rectangle
        leftMost = calibration_x[0]
        rightMost = calibration_x[1]
        topMost = calibration_y[0]
        bottomMost = calibration_y[1]

        calibration_topLeft = [leftMost[0], topMost[1]]
        calibration_bottomRight = [rightMost[0], bottomMost[1]]

        cv2.circle(frame, leftMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
        cv2.circle(frame, rightMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
        cv2.circle(frame, topMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
        cv2.circle(frame, bottomMost, radius=10, color=(255, 0, 0), thickness=cv2.FILLED)
        cv2.rectangle(frame, calibration_topLeft, calibration_bottomRight, (255, 0, 0), self.font_thickness)
        y = self.y_start
        #print("\nDRAW*******************************\n")
        #print(f'DETECTION INFO : {detection_info}')
        #print(f'\nCLIENT INFO : {client_info}')
        #Drawing for all slots
        #Drawing the raw YOLO detection
        if debug:
            for raw_object in raw:
                cv2.rectangle(frame, (int(raw_object.points[0][0]), int(raw_object.points[0][1])),
                              (int(raw_object.points[1][0]), int(raw_object.points[1][1])),
                              (255, 255, 0),
                              self.font_thickness)

            for raw_object in objects:
                tl = (int(raw_object.estimate[0][0]), int(raw_object.estimate[0][1]))
                br = (int(raw_object.estimate[1][0]), int(raw_object.estimate[1][1]))

                cv2.rectangle(frame, tl, br, (26, 128, 255), self.font_thickness)

            
        for i in range(len(detection_info)):
            detect_person = detection_info[i]
            person_id = detect_person[0]
            #Drawing the detection's rectangle if exist
            if detect_person != None :
                #Special value for exclueded person
                if person_id == out_id :
                    person_id = 'OUT'
                    cv2.rectangle(frame, detect_person[1], detect_person[2], (255, 0, 0), self.font_thickness)
                    cv2.putText(frame, str(person_id), (int(detect_person[3][0]), int(detect_person[3][1])), self.font, 1, (255, 255, 255), self.font_thickness)
        #Drawing info
        for i in range(len(client_info)) :
            person = client_info[i]
            id_client = person[0]
            moving = person[2]
            for detect_person in detection_info:
                if detect_person[0] == id_client :
                    if moving :
                        # Moving
                        cv2.rectangle(frame, detect_person[1], detect_person[2], (0, 0, 255), self.font_thickness)
                    else :
                        # Not moving
                        cv2.rectangle(frame, detect_person[1], detect_person[2], (0, 255, 0), self.font_thickness)
                    cv2.putText(frame, str(id_client), (int(detect_person[3][0]), int(detect_person[3][1])), self.font, 2, (255, 255, 255), self.font_thickness)

            text = "Slot "+str(i)+" : Inside : "+str(person[1])+", Moving : "+str(person[2])+", Position : "+str(person[3])+"."
            cv2.putText(frame, text, (self.x_start, y), self.font, self.font_scale, (255, 255, 255), self.font_thickness)
            y += self.line_spacing
        return frame