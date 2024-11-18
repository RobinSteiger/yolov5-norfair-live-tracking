import numpy as np


#######################################################
#Moving : Class for storing old position information and decide whether they are moving or not
#Detection_Process(object, frame, 2, 0.35)
#Parameters :
#   diff_dist : The difference in px which is considered as a move.
#Attribute :
#   self.all_moves : All the ancient movements.
#   diff_dist : The difference in px which is considered as a move.
#   self.nbr_frame : The number of frame to use for the estimation of the deplacement. 
class Moving:
    def __init__(self, diff_dist, nbr_frame) :
        self.all_moves = []
        self.diff_dist = diff_dist
        self.nbr_frame = nbr_frame

    def get_moving(self, id, age, center) -> bool :
        # Register new move
        self.all_moves.append([id, age, center])
        res = True
        # List of all last center of the current object
        last_moves = []
        # Getting all last moves
        for move in self.all_moves:
            move_age = move[1]
            move_x = move[2][0]
            #move_y = move[2][1]
            # Last frame
            if (move[0] == id and move[1] >= age - self.nbr_frame):
                # TODO : PARAMETER TO GET THE OUTPUT ABOUT X OR X AND Y OR Y
                # Diff with X and Y
                # diff = math.sqrt((abs(move[2][0] - center[0]) ** 2 +  abs(move[2][1] - center[1]) ** 2))
                # Diff with only X
                last_moves.append([move_age, move_x]) 
        # Sort list by age
        last_moves.sort(key=lambda x:x[0])
        all_diff = []
        # Differences for all last moves with the next one
        for i in range(len(last_moves) - 1):
            diff = abs(last_moves[i][1] - last_moves[i+1][1])
            all_diff.append(diff)
        # Mean of all last moves
        # No calculation and considered as moving if all_diff is empty
        mean = self.diff_dist + 1
        if len(all_diff) > 0 :
            mean = np.mean(all_diff)
        # Result
        if (mean <= self.diff_dist):
            res = False

        # Clearing older moves
        # Another loop to prevent alterate self.all_moves while calculation diff.
        for move in self.all_moves:
            if(move[0] == id and move[1] < age - self.nbr_frame):
                self.all_moves.remove(move)
        return res