#!/bin/sh
dir=`dirname $(readlink $0)`

pushd $dir
aplay ./beep-02.wav
current_counter=`grep __counter ./jfwusb/set-dbm.py | awk '{print $2}'`
./jfwusb/set-dbm.py `./get-dbm.sh $current_counter`
new_counter=$((current_counter+1))
sleep 50
sed -i "s/__counter $current_counter/__counter $new_counter/" ./jfwusb/set-dbm.py
