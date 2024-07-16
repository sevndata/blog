---
title: 在Ubuntu下开启ssh
date: 2018-05-10 11:05:56
categories: 
- Ubuntu
tags: 
- Ubuntu
---
本文分享了在Ubuntu下开启ssh。
<!-- more -->
安装启动
```shell
apt-get install openssh-server
```
修改配置文件`/etc/ssh/sshd_config`
将注释的`Port 22`放开
重启`ssh`服务



