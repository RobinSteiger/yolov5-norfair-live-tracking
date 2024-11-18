# INTERACTIVE ART INSTALLATION USING CAMERA AND OBJECT DETECTION



A project using Yolo and Norfair to achieve tracking of individuals (in real time and on video) and informations extraction.

The informations extracted are, realtively to a calibrated zone :

- Inside/Outside of the calibrated zone
- Position in % relative to the calibrated zone
- Moving/Immobile

This project was realized in the context of the 5 semester's project at [HEIA-FR](https://www.heia-fr.ch/) and 
used in an interactive art installation at [Murten Licht Festival 2024](https://fr.murtenlichtfestival.ch/).

The project was realized under the supervision of **Beat Wolf**, **Damien Goetschi** and **Jean Hennebert**.



## Setup

  

Install necesaries librairies : `pip install -r requirements.txt`

  

Execution of the project on a local MP4 file : `py main.py -i <RELATIVE_PATH_OF_THE_FILE> -o <OUTPUT_NAME>`

  

Execution of the project on a live input :

- Into main.py, comment `io.local_output(frame)` et uncomment `#io.live_output(frame)`

- `py main.py -i <CAMERA_IP>:<CAMERA_PORT>/h264Preview_01_main`

  
## Manual Calibration



The calibration is made automatically, based on the most luminous area of the input, but you can do it manually.



Into constants of the lines 17 to 27 :

- Modify the value MANUAL_CALIBRATION from False to True

	- >Example : `MANUAL_CALIBRATION = True`

- Modify the value of manual_offset_calibrate_x [offset_left, offset_right].

	- >Example : `manual_offset_calibrate_x = [[20, 400], [1260, 400]]`

- Do the same with the value of manual_offset_calibrate_y [offset_top, offset_down].

	- >Example : `manual_offset_calibrate_y = [640, 440], [640, 650]`
