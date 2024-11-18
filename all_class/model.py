import os
import torch


####################################################################################################
#Model : Class for loading and configurate a model.
#Parameters :
#   bool local : Indicate if the model is local or loaded from Yolo.
#   String yolo_path : The path to Yolo local librairie.
#   String model_path : The path to the Yolo local model.
#Attribute :
#   self.model : The model.
#Methods :
#   __init__(local, yolo_path, model_path) : 
#       Load and initiate the Model.
#       local : Indicate if the model is local or loaded from Yolo.
#       yolo_path : The path to Yolo local librairie.
#       model_path : The path to the Yolo local model.
####################################################################################################
class Model :
    def __init__(self, local, model_confidence, yolo_path = "", model_path= ""):
        #Model Config
        #Normalise the model path.
        yolo_path = os.path.normpath(yolo_path)
        if local :
            self.model = torch.hub.load(yolo_path, 'custom', path=model_path, source='local')
        else :
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5l6', pretrained=True)
        self.model.eval()
        self.model.conf = model_confidence  # NMS confidence threshold
        self.model.iou = 0.45  # NMS IoU threshold
        self.model.agnostic = False  # NMS class-agnostic
        self.model.multi_label = False  # NMS multiple labels per box
        self.model.max_det = 100  # maximum number of detections per image
        self.model.classes = [0] 

    def getDetections(self,frame):
        return self.model(frame)