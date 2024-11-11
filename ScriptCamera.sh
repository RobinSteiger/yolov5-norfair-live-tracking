#!/bin/bash

while true
do
    echo "Démarrage du programme..."
    python main.py -i rtsp://admin:heiafr@192.168.1.10:554/h264Preview_01_main -o output

    echo "Le programme s'est terminé avec une erreur. Redémarrage en cours..."
    sleep 5
done