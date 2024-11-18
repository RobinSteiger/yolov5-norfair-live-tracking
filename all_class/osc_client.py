import time
from pythonosc import udp_client


####################################################################################################
#OSC_Client : Class to communicate in .osc format and format the output.
#Parameters :
#   int nbr_people_max: The maximum number of people tracked simultanously
#   String ip : The IP of the client. Default : 127.0.0.1
#   int port : The port of the client. Default : 5005
#Attributes :
#   self.client : The udp (and osc) client.
#   self.info_list : The list of all tracked people's informations. Format : [id, inside/outside, moving, position in %].
#   self.crossing_cache : The list to store tracked people when they disapear in the middle of the detection's zone,
#                         meaning they're hidden by another person.
#   self.crossing_age : The age of each person stored in the crossing_cache.
#Methods :
#   __init__(nbr_people_max, ip, port) :
#       Initiate the osc client.
#       nbr_people_max: The maximum number of people tracked simultanously
#       nbr_info : The number of informations for each tracked person.
#       ip : The IP of the client. Default : 127.0.0.1
#       port : The port of the client. Default : 5005
#   send(header, msg) :
#       Send a message with a header.
#       header : The header to use.
#       msg : The message to send.
#   send_info(new_info, countdown, leaving_offset, time_to_let_go, reappear_offset) :
#       Sort the informations, send them and detect if a new person entered this frame for a calibration.
#       new_info : The new informations of the detection.
#       countdown : The number of frames until a tracked person effectively disappear to let the installation the time to adapt.
#       leaving_offset : Distance offset in % from the start/end of the installation to accept that a person left the detection.
#       time_to_let_go : Time difference in seconds after which we suppress a cached person definitively.
#       reappear_offset : Distance offset in % beetween the old and the new detection to accept that it was the same person.
####################################################################################################

class OSC_Client:

    def __init__(self, nbr_people_max, nbr_info, ip = "192.168.10.201", port = 5005) :
        self.client = udp_client.SimpleUDPClient(ip, port)
        # 4 is an id plus the number of informations to send, here 3
        self.info_list = [[0 for _ in range(nbr_info + 1)] for _ in range(nbr_people_max)]
        # Ensure move is always True unless someone stop moving
        for el in self.info_list :
            el[2] = True
        
        self.crossing = []
        self.age_inside = []
    
    def send(self, header, msg) :
        self.client.send_message(header, msg)

    def init_leaving(self,person) : 
        # Negative id for the countdown   
        person[0] = -1
        # Set parameter in to 0
        person[1] = 0
        # Resetting move to true
        person[2] = True

    def send_info(self, detection_list, countdown, leaving_offset, time_to_let_go, appear_offset) :
        print(f'\n\nOLD : {self.info_list}\n\nNEW : {detection_list}\n\nCACHED : {self.crossing}\n\n')
        # DEPARTURE GESTION
        countdown = - abs(countdown)
        for i in range(len(self.info_list)) :
            info = self.info_list[i]
            id = info[0]
            #Negative id are used for countdown
            if not id <= 0 :
                if not (any(row[0] == id for row in detection_list)):
                    #If the id was in the ancient info, but not in the new one
                    #Crossing gestion
                    if (info[3] > leaving_offset and info[3] < 100-leaving_offset) :
                        #If disparition inside the zone of detection, add the tracking to the cache and keep it in all_info.
                        if not (any(row[0] == info for row in self.crossing)) :
                            #Always keeping move to true unless it's detected
                            info[2] = True
                            self.crossing.append([info, time.time()])
                    else :
                        #Real leaving
                        self.init_leaving(info)
            elif id < 0 :
                #Countdown gestion
                if id > countdown : 
                    #Count frame age until countdown
                    info[0] = id - 1
                else :
                    #If we achieved the countdown
                    self.info_list[i] = [0, 0, True, 0]

        #Crossing gestion
        #Reapparition of a cached person detected by the models           
        for cached in self.crossing :
            if (any(row[0] == cached[0][0] for row in detection_list)):
                self.crossing.remove(cached)
                print(f'\n\nREAPPEARED (detected by the models) : {cached}\n')
            else :
                #Adding the cached person to the detection_list, to keep it in the detection
                detection_list.append(cached[0])  

        #Leaving because the time has passed 
        for cached in self.crossing :
            age = cached[1]
            if (time.time() - age >= time_to_let_go) :
                print(f'\n\nTIME PASSED : {cached}\n')
                person = self.info_list[self.info_list.index(cached[0])]
                self.init_leaving(person)
                detection_list.remove(person)
                self.crossing.remove(cached)

        #Update gestion : Update self.info_list with new_info
        #Needed to launch the calibration only when a new person enter in the detection
        new_person = False
        for info in detection_list:
            #UPDATE ALREADY PRESENT DETECTION
            #Getting the position of the concerned id if exists, else =-1
            try :
                pos = list(zip(*self.info_list))[0].index(info[0])
            except ValueError :
                pos = -1
            #If the id already in the list, replace by new value
            if not pos==-1 :
                self.info_list[pos] = info
            #DETECTION IS NOT IN THE OLD INFO
            else :    
                #Replace represent the fact that the new person was an old one and don't need to be added.
                replace = False
                #Reapparition of and old person with a new id
                for cached in self.crossing :
                    id = cached[0][0]
                    print(f'\nCached info to compare : {cached}')
                    if (abs(info[3] - cached[0][3]) <= appear_offset): #and (info[0] == id)
                        print(f'\n\nREAPPEARED (not detected) : {cached}\n')
                        pos = list(zip(*self.info_list))[0].index(id)
                        self.info_list[pos] = info
                        self.crossing.remove(cached)
                        detection_list.remove(cached[0])
                        replace = True
                #Else, we store it in the first empty slot, and we send the signal for the calibration
                if not replace :
                    for i in range(len(self.info_list)) :
                        if self.info_list[i][0] == 0 and not new_person:
                            self.info_list[i] = info
                            new_person = True

        for i in range(len(self.info_list)) :
            element = self.info_list[i]
            header = "/detect/"+str(i)+"/"
            self.send(header+"in", element[1])
            self.send(header+"move", element[2])
            self.send(header+"pos", element[3])

        return new_person
