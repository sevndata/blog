---
title: 在Ubuntu中编译OpenJDK11
date: 2021-03-20 11:05:56
categories: 
- JDK
tags: 
- JDK
---
本文分享了在Ubuntu中编译OpenJDK11
<!-- more -->

## 1. 下载
1. 下载源码
```shell
#下载源码
wget http://hg.openjdk.java.net/jdk/jdk11/archive/tip.tar.gz
#解压源码包
tar -xzf tip.tar.gz
```
2. 从`github`克隆
```shell
git clone git@github.com:openjdk/jdk.git
```

## 2. 依赖
查看`doc/building.html (html version)`或者`doc/building.md (markdown version)`获取编译步骤。

安装编译基础工具：
```shell
sudo apt-get install build-essential
```

在配置或编译过程中缺少一些依赖，会有如下类似报错：
```
error: Could not find all X11 headers (shape.h Xrender.h XTest.h Intrinsic.h).
 You might be able to fix this by running 
 'sudo apt-get install libx11-dev libxext-dev libxrender-dev libxtst-dev libxt-dev'.
```
根据提示信息安装依赖，本人至少安装以下依赖：
```shell
apt-get install zip
apt-get install libx11-dev
apt-get install libxext-dev
apt-get install libxrender-dev
apt-get install libxtst-dev
apt-get install libxt-dev
apt-get install libcups2-dev
apt-get install libfontconfig1-dev
apt-get install libasound2-dev
```
## 3. 配置
在源码根目录下执行：
```
bash configure --enable-debug --with-jvm-variants=server 
    --enable-dtrace --disable-ccache --disable-warnings-as-errors
```
一些参数说明：
```
--enable-debug：启用debug模式
--with-jvm-variants=server：server模式
--enable-dtrace：开启性能工具
--disable-warnings-as-errors：跳过警告
--with-boot-jdk：指定boot jdk路径

```

成功结果：
```
Configuration summary:
* Debug level:    release
* HS debug level: product
* JVM variants:   server
* JVM features:   server: 'aot cds cmsgc compiler1 compiler2 epsilongc g1gc graal jfr jni-check jvmci jvmti management nmt parallelgc serialgc services vm-structs'
* OpenJDK target: OS: linux, CPU architecture: x86, address length: 64
* Version string: 11-internal+0-adhoc.root.jdk11-1ddf9a99e4ad (11-internal)

Tools summary:
* Boot JDK:       openjdk version "11.0.10" 2021-01-19 OpenJDK Runtime Environment (build 11.0.10+9-Ubuntu-0ubuntu1.18.04) OpenJDK 64-Bit Server VM (build 11.0.10+9-Ubuntu-0ubuntu1.18.04, mixed mode, sharing)  (at /usr/lib/jvm/java-11-openjdk-amd64)
* Toolchain:      gcc (GNU Compiler Collection)
* C Compiler:     Version 7.5.0 (at /usr/bin/gcc)
* C++ Compiler:   Version 7.5.0 (at /usr/bin/g++)

Build performance summary:
* Cores to use:   3
* Memory limit:   3921 MB
```
## 4. 编译
配置后执行编译命令：
```shell
make images
```
成功结果：
```
Creating jdk image
Stopping sjavac server
Finished building target 'images' in configuration 'linux-x86_64-normal-server-fastdebug'
```
## 5. 验证
找到编译好的jdk目录并验证：
```shell
#编译日志路径
build/linux-x86_64-normal-server-fastdebug/configure.log
#jdk路径
cd build/linux-x86_64-normal-server-fastdebug/jdk
#验证命令
./build/linux-x86_64-normal-server-fastdebug/jdk/bin/java -version
```
成功结果：
```
openjdk version "11-internal" 2018-09-25
OpenJDK Runtime Environment (fastdebug build 11-internal+0-adhoc.root.jdk11-1ddf9a99e4ad)
OpenJDK 64-Bit Server VM (fastdebug build 11-internal+0-adhoc.root.jdk11-1ddf9a99e4ad, mixed mode)
```
## 6. 问题

1. 配置编译过程中，大部分都是缺少依赖问题，提示缺少什么依赖安装什么依赖即可
2. `Boot JDK`未找到，如下错误
```
Could not find a valid Boot JDK. You might be able to fix this by running 'sudo apt-get install openjdk-8-jdk'.
configure: This might be fixed by explicitly setting --with-boot-jdk
configure: error: Cannot continue
configure exiting with result code 1
```
安装`openjdk-8-jdk`依赖：
```shell
apt-get install openjdk-8-jdk
```
仍然报错：
```
configure: Potential Boot JDK found at /usr/lib/jvm/java-1.8.0-openjdk-amd64 is incorrect JDK version (openjdk version "1.8.0_282"); ignoring
configure: (Your Boot JDK version must be one of: 10 11)
```
卸载`openjdk-8-jdk`并安装`openjdk-11-jdk`：
```
apt-get remove openjdk-8-jdk
apt-get install openjdk-11-jdk
apt autoremove
```

至此，在Ubuntu中编译了OpenJDK11。