#!/bin/bash
. sgw_test_config.sh

outfile=test_info.txt
outfile_sar=test_info_sar.txt
sleep_time=300

free > tmp.txt
mem=`grep Mem: tmp.txt |  awk '{print $2}'`
cpu=`nproc`
echo Test start - $(date +"%Y%m%d-%H%M%S") > $outfile
echo Machine configuration: cpu:$cpu mem:$mem  >> $outfile

pid=`pgrep sync_gateway`
if [ -n "$pid" ]
then

        # Collect sar statistics
        sar -n DEV $sleep_time > $outfile_sar &

        # build the command to get socketsToDB
        cmd="egrep \""
        for ip in ${dbs_ip}; do
            cmd="${cmd}${ip}|"
        done
        cmd=${cmd%?}
        cmd="$cmd\""

        loop_count=0
        while :
        do
            cpu=`top -bn1d1 -p $pid | grep $pid | awk '{print $9}' | sed "s/m//"`
            mem=`cat /proc/${pid}/status | grep VmRSS | awk '{print $2}'`
            swap=`cat /proc/${pid}/status | grep VmSwap | awk '{print $2}'`

            netstat -lpnta > tmp_info.txt
            sockets=`cat tmp_info.txt | wc -l`
            socketsToDB=`cat tmp_info.txt | $cmd | wc -l`
            # View is using port 8091, or 8092
            socketsToDB_view=`cat tmp_info.txt | $cmd | grep :809 | wc -l`
            socketsToOthers=`expr $sockets - $socketsToDB`
            output_line="$(date +"%Y%m%d-%H%M%S"): sockets:$sockets - toDB:$socketsToDB - view:$socketsToDB_view - toOthers:$socketsToOthers  - mem:$mem - cpu:$cpu - swap:$swap"
            echo  $output_line >> $outfile

            loop_count=`expr $loop_count + 1`
            # Query p99 every 1 time in the loop - 5 minutes
            if [ $loop_count -eq 1 ]; then
                index=0
                for ip in ${gateloads_ip}; do
                    index=`expr $index + 1`
                    p99_avg=`curl "http://${seriesly_ip}:3133/gateload_${index}/_query?ptr=/gateload/ops/PushToSubscriberInteractive/p99&reducer=avg&group=100000000000"`
                    echo "PushToSubscriberInteractive/p99 average during test runs: $p99_avg"
                    echo "PushToSubscriberInteractive/p99 average during test runs: $p99_avg" >> $outfile

                    curl "http://${ip}:9876/debug/vars" > temp.json
                    if grep "cmdline" temp.json
                    then
                        total_doc_failed_to_pull="`cat temp.json | grep total_doc_failed_to_pull`"
                        if [ -z "$total_doc_failed_to_pull" ]
                        then
                            total_doc_failed_to_pull=0
                        fi
                        echo "total_doc_failed_to_pull: $total_doc_failed_to_pull"
                        echo "total_doc_failed_to_pull: $total_doc_failed_to_pull" >> $outfile

                        total_doc_failed_to_push="`cat temp.json | grep total_doc_failed_to_push`"
                        if [ -z "$total_doc_failed_to_push" ]
                        then
                            total_doc_failed_to_push=0
                        fi
                        echo "total_doc_failed_to_push: $total_doc_failed_to_push"
                        echo "total_doc_failed_to_push: $total_doc_failed_to_push" >> $outfile

                        mv temp.json gateload_expvar_$index.json
                    fi

                done
               
                maxPending=`curl "http://localhost:4985/_expvar" | grep maxPending | sed 's/\"//g' | sed 's/^.*maxPending: //' | sed -r 's/^([0-9]*).*/\1/'`
                echo "maxPending: $maxPending"
                echo "maxPending: $maxPending" >> $outfile
                loop_count=0
            fi

            sleep $sleep_time
        done
else
  echo "=== ERROR - sync_gateway process is not running"  >> $outfile
  echo "=== ERROR - sync_gateway process is not running"
fi
