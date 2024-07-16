---
title: Tomcat9安装使用
date: 2020-05-22 22:13:26
categories: 
- Tomcat
tags: 
- Tomcat
---

记录分享Tomcat9安装使用过程

<!-- more -->

### 1. java环境安装

使用`openjdk`,注意`openjdk`与`jdk`是有区别的。如使用到`sun.misc.BASE64Decoder`等`jdk`中有而`openjdk`中没有的则不能使用`openjdk`。

```shell

yum search java

yum install java-1.8.0-openjdk.x86_64

java -version
```

### 2. tomcat使用

#### 1. 下载解压

```shell

wget https://mirror.bit.edu.cn/apache/tomcat/tomcat-9/v9.0.38/bin/apache-tomcat-9.0.38.tar.gz

tar zxvf apache-tomcat-9.0.38.tar.gz

```

#### 2. 配置文件

配置文件在conf下，列举俩个常用的配置，其他配置如`web.xml`,`logging.properties`,`catalina.properties`详见配置文件中内容。

1. 修改端口，修改server.xml

```shell
<Connector port="80" protocol="HTTP/1.1"
               connectionTimeout="20000"
               redirectPort="8443" />
```

2. https配置，修改server.xml

```shell
<Connector port="443" protocol="HTTP/1.1"
maxThreads="150" SSLEnabled="true" scheme="https" secure="true"
keystoreFile="/home/webapp/xxxx.pfx"
keystoreType="PKCS12"
keystorePass="xxxxxxx"
clientAuth="false" sslProtocol="TLS" />
```

#### 3. 设置tomcat不产生大量日志

生产环境中因会有大量业务日志生成，tomcat也会产生大量日志，通常我们会有日志系统或者应用日志，不需要tomcat产生日志，可以设置tomcat不产生大量日志。修改`bin/catalina.sh`中：

```shell
if [ -z "$CATALINA_OUT" ] ; then
  CATALINA_OUT=/dev/null
fi
```

#### 4. 启动与停止

```shell

./startup.sh

./shutdown.sh

```