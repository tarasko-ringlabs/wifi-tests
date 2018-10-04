#!/bin/sh
#__counter 0
test_number=${1:-0}
device_name=${2:-lpdv1}

attenuator_map='0 -10 -20 -30 -40 -50 -60 -63 -66 -69'
idx=0
attenuator_idx=$((test_number%10))
attenuator_dbm=10 # invalid value

# busybox shell doesn't support arrays
# so find dbm with this stupid way
for dbm in $attenuator_map
do
    if [[ $idx == $attenuator_idx ]]; then
        attenuator_dbm=$dbm
        break;
    fi
    idx=$((idx+1))
done

attenuator_dbm=`./get-dbm.sh $test_number`
attenuator_dbm=$((attenuator_dbm*-1))

suite_number=$((test_number/10))
suite_number=0

node_type=ap
wifi_iface=wlan0
ap_ip=192.168.1.1
protocol=udp
#sta_mac=9c:1d:58:fb:03:9b
#sta_mac=38:d2:69:d2:ad:d8
#sta_mac=44:39:c4:df:ab:e4
#sta_mac=d4:36:39:88:1b:a0
#sta_mac=e0:4f:43:10:b4:95
sta_mac=e0:4f:43:13:74:c2
duration=60
dump_pcap=n

echo ============TEST BEGIN $suite_number/$test_number ============
echo device: $device_name
echo date: `date`
echo suite number: $suite_number
echo test number: $test_number
echo attenuator dBm: $attenuator_dbm
suite_dir_name=/tmp/$suite_number-${device_name}-$node_type-$protocol
echo wifi_iface: $wifi_iface
echo protocol: $protocol
echo target sta_mac: $sta_mac
echo duration seconds: $duration
#echo
#echo Print enter to begin test...

#read

#trap "kill -9 ; exit 0;" INT

iw dev $wifi_iface station get $sta_mac  >/tmp/before
rssi=`grep 'signal avg' /tmp/before | awk '{print $3}'`
echo rssi: $rssi
test_dir_name=$suite_dir_name/$test_number-${device_name}-${node_type}${attenuator_dbm}dBm
plot_filename=$suite_dir_name.plot

rx_packets_before=`grep 'rx packets' /tmp/before | awk '{print $3}'`
rx_bytes_before=`grep 'rx bytes' /tmp/before | awk '{print $3}'`
tx_packets_before=`grep 'tx packets' /tmp/before | awk '{print $3}'`
tx_bytes_before=`grep 'tx bytes' /tmp/before | awk '{print $3}'`
tx_retries_before=`grep 'tx retries' /tmp/before | awk '{print $3}'`
tx_failed_before=`grep 'tx failed' /tmp/before | awk '{print $3}'`
rx_drop_before=`grep 'rx drop' /tmp/before | awk '{print $4}'`

mkdir -p $test_dir_name
if [[ $protocol = 'tcp' ]]; then
	iperf -s -t $duration
else
    if [[ $dump_pcap = y ]]; then
        tcpdump -i $wifi_iface -n -s 0 port 5002 -vvv -w $test_dir_name/$test_number-${node_type}.pcap&
        TCPDUMP_PID=$!
#        ((tcpdump -i $wifi_iface -n -s 0 port 5001 -vvv -w - & echo $! >tcpdump_pid) | \
#            gzip -c >$test_dir_name/${test_number}-${node_type}.pcap.gz; echo pcap.gz is ready!)&
#        GZIP_PID=$!
        sleep 1
        iperf -s -u -t $duration
        sleep 3
        kill -2 $TCPDUMP_PID
    #    kill -2 `cat tcpdump_pid`;
    #    rm tcpdump_pid;
    else
        iperf -s -u -t $duration
    fi
fi

iw dev $wifi_iface station get $sta_mac >/tmp/after

rx_packets_after=`grep 'rx packets' /tmp/after | awk '{print $3}'`
rx_bytes_after=`grep 'rx bytes' /tmp/after | awk '{print $3}'`
tx_packets_after=`grep 'tx packets' /tmp/after | awk '{print $3}'`
tx_bytes_after=`grep 'tx bytes' /tmp/after | awk '{print $3}'`
tx_retries_after=`grep 'tx retries' /tmp/after | awk '{print $3}'`
tx_failed_after=`grep 'tx failed' /tmp/after | awk '{print $3}'`
rx_drop_after=`grep 'rx drop' /tmp/after | awk '{print $4}'`

rx_packets=$((rx_packets_after-rx_packets_before))
rx_bytes=$((rx_bytes_after-rx_bytes_before))
rx_throughput=`awk "BEGIN{printf \"%.3f\", $rx_bytes*8/60/1000000}"`
tx_packets=$((tx_packets_after-tx_packets_before))
tx_bytes=$((tx_bytes_after-tx_bytes_before))
tx_throughput=`awk "BEGIN{printf \"%.3f\", $tx_bytes*8/60/1000000}"`
tx_retries=$((tx_retries_after-tx_retries_before))
tx_failed=$((tx_failed_after-tx_failed_before))
rx_drop=$((rx_drop_after-rx_drop_before))

echo rssi $rssi
echo rx_packets $rx_packets
echo rx_throughput $rx_throughput Mbps
echo tx_packets $tx_packets
echo tx_bytes $tx_bytes
echo tx_throughput $tx_throughput Mbps
echo tx_retries $tx_retries
echo tx_failed $tx_failed
echo rx_drop $rx_drop

out_filename=$test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-result
mv /tmp/before $test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-before-detailed
mv /tmp/after $test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-after-detailed


echo -e "$attenuator_dbm    $rssi    $tx_packets    $tx_throughput   $rx_packets  $rx_throughput   $tx_retries    $tx_failed    $rx_drop" >>$plot_filename

echo signal $rssi >>$out_filename
echo rx_packets $rx_packets >>$out_filename
echo rx_throughput $tx_throughput >>$out_filename
echo tx_packets $tx_packets >>$out_filename
echo tx_bytes $tx_bytes >>$out_filename
echo tx_throughput $tx_throughput >>$out_filename
echo tx_retries $tx_retries >>$out_filename
echo tx_failed $tx_failed >>$out_filename
echo rx_drop $rx_drop >>$out_filename

archive_name=${test_dir_name}.tar.gz

#if [[ $dump_pcap = y ]]; then
#    wait $GZIP_PID
#fi
tar cfz ${archive_name} -C ${test_dir_name} `ls $test_dir_name`
rm -rf ${test_dir_name}
echo Copy link:
echo scp root@$ap_ip:$archive_name .

echo ============TEST END, switch RSSI!!!! ============
