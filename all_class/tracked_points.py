from norfair import Detection, Tracker
import torch
from typing import List
import numpy as np


class Tracked_Points :
    def __init__(self, mode, distance_threshold_bbox) :
        #Constants
        DISTANCE_THRESHOLD_BBOX: float = distance_threshold_bbox
        #On the test session, tried with 0.8
        DISTANCE_THRESHOLD_CENTROID: int = 30

        self.track_points = mode
        distance_function = "iou" if self.track_points == "bbox" else "euclidean"
        distance_threshold = (
            DISTANCE_THRESHOLD_BBOX
            if self.track_points == "bbox"
            else DISTANCE_THRESHOLD_CENTROID
        )
        self.tracker = Tracker(
            distance_function=distance_function,
            distance_threshold=distance_threshold,
            hit_counter_max=30
        )

    def yolo_detections_to_tracked_points(self, yolo_detections: torch.tensor) -> List[Detection]:
        """convert detections_as_xywh to norfair detections"""
        norfair_detections: List[Detection] = []

        if self.track_points == "centroid":
            detections_as_xywh = yolo_detections.xywh[0]
            for detection_as_xywh in detections_as_xywh:
                centroid = np.array(
                    [detection_as_xywh[0].item(), detection_as_xywh[1].item()]
                )
                scores = np.array([detection_as_xywh[4].item()])
                norfair_detections.append(
                    Detection(
                        points=centroid,
                        scores=scores,
                        label=int(detection_as_xywh[-1].item()),
                    )
                )
        elif self.track_points == "bbox":
            detections_as_xyxy = yolo_detections.xyxy[0]
            for detection_as_xyxy in detections_as_xyxy:
                bbox = np.array(
                    [
                        [detection_as_xyxy[0].item(), detection_as_xyxy[1].item()],
                        [detection_as_xyxy[2].item(), detection_as_xyxy[3].item()],
                    ]
                )
                scores = np.array(
                    [detection_as_xyxy[4].item(), detection_as_xyxy[4].item()]
                )
                norfair_detections.append(
                    Detection(
                        points=bbox, scores=scores, label=int(detection_as_xyxy[-1].item())
                    )
                )

        return self.tracker.update(norfair_detections), norfair_detections