#!/bin/sh
offset=00
step_dbm=5

counter=$1
echo $((counter*step_dbm+offset))
