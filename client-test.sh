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

node_type=sta
wifi_iface=wlan0
protocol=udp
#ap_mac=64:d1:54:3f:d0:36
ap_mac=cc:2d:e0:0f:8b:e2

sta_ip=`ifconfig $wifi_iface | grep 'inet addr' | awk '{print $2}'`
sta_ip=${sta_ip#*:} #extract substring
#ap_ip=192.168.1.1
ap_ip=192.168.1.2
max_iperf_bandwidth=14M
duration=60
dump_pcap=n


echo ============TEST BEGIN $suite_number/$test_number ============
echo device name: $device_name
echo date: `date`
echo suite number: $suite_number
echo test number: $test_number
echo iperf bandwidth: $max_iperf_bandwidth
echo attenuator dBm: $attenuator_dbm
suite_dir_name=/tmp/$suite_number-${device_name}-$node_type-$protocol
echo wifi_iface: $wifi_iface
echo protocol: $protocol
echo target ap_mac: $ap_mac
echo sta_ip: $sta_ip
echo ap_ip: $ap_ip
echo duration seconds: $duration
#echo
#echo Print enter to begin test...

#read

#trap "echo SIGINT catched; kill -9 $IPERF_PID $TCPDUMP_PID; exit 0;" INT

iw dev $wifi_iface station get $ap_mac  >/tmp/before
rssi=`grep 'signal' /tmp/before | awk '{print $2}'`
echo rssi: $rssi
test_dir_name=$suite_dir_name/$test_number-${device_name}-${node_type}${attenuator_dbm}dBm
plot_filename=$suite_dir_name.plot

usleep 100
mkdir -p $test_dir_name

rx_packets_before=`grep 'rx packets' /tmp/before | awk '{print $3}'`
rx_bytes_before=`grep 'rx bytes' /tmp/before | awk '{print $3}'`
tx_packets_before=`grep 'tx packets' /tmp/before | awk '{print $3}'`
tx_bytes_before=`grep 'tx bytes' /tmp/before | awk '{print $3}'`
tx_retries_before=`grep 'tx retries' /tmp/before | awk '{print $3}'`
tx_failed_before=`grep 'tx failed' /tmp/before | awk '{print $3}'`

if [[ $protocol == 'tcp' ]]; then
    #iperf --len 1400 --bandwidth $max_iperf_bandwidth  -c $ap_ip -t $duration
    iperf --len 1400 --bandwidth $max_iperf_bandwidth  -c iperf.ring.com -t $duration
else
    if [[ $dump_pcap = 'y' ]]; then
        tcpdump -i $wifi_iface -n -s 0 port 5002 -vvv -w $test_dir_name/$test_number-${node_type}.pcap&
        TCPDUMP_PID=$!
#        ((tcpdump -i $wifi_iface -n -s 0 port 5001 -vvv -w - & echo $! >tcpdump_pid) | \
#            gzip -c >$test_dir_name/${test_number}-${node_type}.pcap.gz; echo pcap.gz is ready!)&
#        GZIP_PID=$!
        usleep 300
        iperf --len 1400 --bandwidth $max_iperf_bandwidth --bind $sta_ip:5002 \
            -u -c $ap_ip -t $duration
        sleep 3
        kill -2 $TCPDUMP_PID
#        kill -2 `cat tcpdump_pid`;
#        rm tcpdump_pid
    else
        iperf --len 1400 --bandwidth $max_iperf_bandwidth --bind $sta_ip:5002 \
            -u -c $ap_ip -t $duration
    fi
fi

iw dev $wifi_iface station get $ap_mac >/tmp/after

rx_packets_after=`grep 'rx packets' /tmp/after | awk '{print $3}'`
rx_bytes_after=`grep 'rx bytes' /tmp/after | awk '{print $3}'`
tx_packets_after=`grep 'tx packets' /tmp/after | awk '{print $3}'`
tx_bytes_after=`grep 'tx bytes' /tmp/after | awk '{print $3}'`
tx_retries_after=`grep 'tx retries' /tmp/after | awk '{print $3}'`
tx_failed_after=`grep 'tx failed' /tmp/after | awk '{print $3}'`

rx_packets=$((rx_packets_after-rx_packets_before))
rx_bytes=$((rx_bytes_after-rx_bytes_before))
rx_throughput=`awk "BEGIN{printf \"%.3f\", $rx_bytes*8/60/1000000}"`
tx_packets=$((tx_packets_after-tx_packets_before))
tx_bytes=$((tx_bytes_after-tx_bytes_before))
tx_throughput=`awk "BEGIN{printf \"%.3f\", $tx_bytes*8/60/1000000}"` #mbps
tx_retries=$((tx_retries_after-tx_retries_before))
tx_failed=$((tx_failed_after-tx_failed_before))

echo signal $rssi
echo tx_packets $tx_packets
echo tx_bytes $tx_bytes
echo tx_throughput $tx_throughput Mbps
echo rx_packets $rx_packets
echo rx_throughput $rx_throughput Mbps
echo tx_retries $tx_retries
echo tx_failed $tx_failed

out_filename=$test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-result
mv /tmp/before $test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-before-detailed
mv /tmp/after $test_dir_name/${test_number}-$device_name-${node_type}${attenuator_dbm}dBm-after-detailed

echo -e "$attenuator_dbm    $rssi    $tx_packets  $tx_throughput    $rx_packets    $rx_throughput    $tx_retries    $tx_failed" >>$plot_filename

echo signal $rssi >>$out_filename
echo rx_packets $rx_packets >>$out_filename
echo tx_packets $tx_packets >>$out_filename
echo tx_bytes $tx_bytes >>$out_filename
echo tx_throughput $tx_throughput >>$out_filename
echo tx_retries $tx_retries >>$out_filename
echo tx_failed $tx_failed >>$out_filename

archive_name=${test_dir_name}.tar.gz

#if [[ $dump_pcap = y ]]; then
#    wait $GZIP_PID
#fi
tar cfz ${archive_name} -C ${test_dir_name} `ls $test_dir_name`
rm -rf ${test_dir_name}
echo -e "Copy link:\nscp root@$sta_ip:$archive_name ."
echo ============TEST END, switch RSSI!!!!============

