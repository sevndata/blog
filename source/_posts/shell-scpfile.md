---
title: shell分布式架构下分发应用
date: 2022-07-02 14:23:07
categories: 
- shell
tags: 
- shell
---
本文分享了在`linux`下通过`shell`脚本做一些分发文件的重复操作。
<!-- more -->
### 代码

```shell
#!/bin/sh
controllist=(172.24.18.177 172.24.18.175)
backuppath=/root/ready_release/backup/
readypath=/root/ready_release/war/
webapppath=/home/webapp/apache-tomcat-9.0.40/webapps/
date=$(date "+%Y.%m.%d.%H.%M.%S")
newfilepath=/root/ready_release/

if [ ! -d $backuppath ];then
        mkdir $backuppath
fi

if [ ! -d $readypath ];then
        mkdir $readypath
fi

if [ ! -n "$1" ];
then
    echo "comand fail"
    echo "example sh run.sh control"
    exit
fi

if [ $1 != "node" ]&&[ $1 != "control" ]&&[ $1 != "batch" ];then
    echo "command fail:"$1
    echo "example: sh run.sh control"
    echo "support：control， node， batch"
    exit
fi

if [ "$1" == "control" ];then
    if [ -f $newfilepath"control.war"  ];
    then
        for control in ${controllist[*]}
        do
            scp root@$control:$webapppath"control.war" $backuppath"control.war".bak.$date
            scp $newfilepath"control.war" root@$control:$webapppath"control.war"
            echo "SUCCESS->"$newfilepath"control.war"
            sleep 240
        done
        mv $newfilepath"control.war" $readypath"control.war".bak.$date
    else
        echo "NOSUCH FILE->"$newfilepath"control.war"
    fi
fi

if [ "$1" == "batch" ];then
    if [ -f $newfilepath"batch.war"  ];
    then
        mv $webapppath"batch.war" $backuppath"batch.war".bak.$date
        cp $newfilepath"batch.war" $webapppath"batch.war"
        mv $newfilepath"batch.war" $readypath"batch.war".bak.$date
        echo "SUCCESS->"$newfilepath"node.war"
    else
        echo "NOSUCH FILE->"$newfilepath"batch.war"
    fi
fi
```