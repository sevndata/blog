---
title: shell批量修改文件名
date: 2024-07-16 09:15:16
categories: 
- shell
tags: 
- shell
---
孩子的视频，照片非常多，批量修改下文件名

<!-- more -->

如：wx_camera_1713872311407.mp4格式的修改为2024年04月23日19时38分31秒_407.mp4
```
Renaming file: wx_camera_1713872311407.mp4 -> 2024年04月23日19时38分31秒_407.mp4
```

```shell
#!/bin/bash

files=$(ls)

for file in $files
do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        extension="${filename##*.}"
        filename="${filename%.*}"

        if [[ $filename =~ ([0-9]+) ]]; then
            timestamp=${BASH_REMATCH[1]}
            seconds=$(($timestamp / 1000))
            milliseconds=$(($timestamp % 1000))
            nanoseconds=$(($timestamp % 1000 * 1000000))
            formatted_time=$(date -r $seconds "+%Y年%m月%d日%H时%M分%S秒")
            new_filename="${formatted_time}_${milliseconds}.${extension}"
            echo "Renaming file: $file -> $new_filename"
            mv "$file" "$new_filename"
        fi
    fi
done
```