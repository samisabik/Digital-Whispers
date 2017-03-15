#!/bin/bash
echo "Updating master"
ssh pi@whisper_master 'cd Digital_Whispers && git fetch origin master && git reset --hard origin/master'

for i in `seq 0 6`; do
    echo "Updating whisper_$i"
    ssh pi@whisper_$i 'cd Digital_Whispers && git fetch origin master && git reset --hard origin/master'
done