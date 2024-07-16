---
title: shell获取CPU使用率信息并重启应用
date: 2022-01-02 14:23:07
categories: 
- shell
tags: 
- shell
---
本文分享了在`linux`下通过`shell`脚本获取`CPU`使用率，超过预警值后重新启动异常应用。
<!-- more -->
### 代码

```shell
#!bin/bash

#监控程序
process="java"

#输出文件
output_file="mn_info.log"

#一分钟探测一次
TIME_INTERVAL=10
TIME_SLEEP=50

#记录连续超过告警值的次数
init_count=0
count_step=1

#告警值
cpu_top=80

#连续超过多少次执行操作
top_count=5

#持续监控
while true;do
    time=$(date "+%Y-%m-%d %H:%M:%S")
    LAST_CPU_INFO=$(cat /proc/stat | grep -w cpu | awk '{print $2,$3,$4,$5,$6,$7,$8}')
    LAST_SYS_IDLE=$(echo $LAST_CPU_INFO | awk '{print $4}')
    LAST_TOTAL_CPU_T=$(echo $LAST_CPU_INFO | awk '{print $1+$2+$3+$4+$5+$6+$7}')
    sleep ${TIME_INTERVAL}
    NEXT_CPU_INFO=$(cat /proc/stat | grep -w cpu | awk '{print $2,$3,$4,$5,$6,$7,$8}')
    NEXT_SYS_IDLE=$(echo $NEXT_CPU_INFO | awk '{print $4}')
    NEXT_TOTAL_CPU_T=$(echo $NEXT_CPU_INFO | awk '{print $1+$2+$3+$4+$5+$6+$7}')

    SYSTEM_IDLE=`echo ${NEXT_SYS_IDLE} ${LAST_SYS_IDLE} | awk '{print $1-$2}'`
    TOTAL_TIME=`echo ${NEXT_TOTAL_CPU_T} ${LAST_TOTAL_CPU_T} | awk '{print $1-$2}'`
    CPU_USAGE=`echo ${SYSTEM_IDLE} ${TOTAL_TIME} | awk '{printf "%.2f", 100-$1/$2*100}'`
    cpu=`echo "$CPU_USAGE" | cut -d "." -f 1`

    #记录CPU过高
    if [ "${cpu}" -gt "${cpu_top}" ];then
        init_count=$(($init_count+1))
        echo "${time}连续第${init_count}次发生cpu使用率过高${cpu}%" >> $output_file
    else
        init_count=0
    fi
    #超过次数触发重启
    if [ "${top_count}" -le "${init_count}"  ];then
        echo "触发重启行为：${time}连续第${init_count}次发生cpu使用率过高${cpu}%" >> $output_file
        init_count=0
        pid=$(pgrep $process)
        kill -9 ${pid}
        sh startup.sh
        sleep 120
    fi
    sleep "${TIME_SLEEP}"
done
```