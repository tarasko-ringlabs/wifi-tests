#!/bin/sh

current_counter=`grep __counter /root/client-test.sh | awk '{print $2}'`
/root/client-test.sh $current_counter lpdv2_1.15
new_counter=$((current_counter+1))
sed -i "s/__counter $current_counter/__counter $new_counter/" /root/client-test.sh
