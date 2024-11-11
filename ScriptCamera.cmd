::https://www.windowscentral.com/how-create-automated-tasks-windows-11 for planning the automatic execution

::NEED TO ADAPT PATH TO WHERE IT'LL BE LAUNCHED AND PATH OF THE MODEL

@echo off
:run
echo Démarrage du programme...
py main.py -i rtsp://admin:heiafr@192.168.1.10:554/h264Preview_01_main 

echo Le programme s'est terminé avec une erreur. Redémarrage en cours...
timeout /t 5 /nobreak >nul 2>&1
goto run