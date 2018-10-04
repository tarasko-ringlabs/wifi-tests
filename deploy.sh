#!/bin/sh
client_ip=${1:-10.0.8.197}
server_ip=192.168.1.1
scp get-dbm.sh client-test.sh client.crontab run-client.sh root@$client_ip:/root/
scp get-dbm.sh server.crontab server-test.sh run-server.sh root@$server_ip:/root/
