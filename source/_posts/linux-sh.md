---
title: CentOS7开机自启动
date: 2020-04-29 11:14:26
categories: 
- Linux
tags: 
- Linux
---
记录分享一些关于Linux操作。
<!-- more -->

## CentOS7开机自启动

设置开机自启动程序有很多种方法。这里记录一种比较实用的方法。逻辑为：创建一个脚本，并在脚本中添加执行的命令，如redis,nginx,tomcat等启动命令，把该脚本设置为开机执行。

1. 创建脚本`server-start.sh`

如下等一些服务启动：

```shell
#!/bin/bash
/home/redis/src/redis-server /home/redis/redis.conf
service nginx start
```

2. 赋予执行权限

```shell
chmod +x /home/server-start.sh
```

3. `/etc/rc.d/rc.local`赋予执行权限

```shell
chmod +x /etc/rc.d/rc.local
```

4. 在`/etc/rc.d/rc.local`添加`server-start.sh`

```shell
/home/server-start.sh
``` 


