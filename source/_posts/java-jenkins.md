---
title: 使用jenkins实现自动部署
date: 2018-10-11 11:05:56
categories: 
- Java
tags: 
- jenkins
---
Jenkins是一款开源 CI&CD 软件，用于自动化各种任务，包括构建、测试和部署软件。
Jenkins 支持各种运行方式，可通过系统包、Docker 或者通过一个独立的 Java 程序。

<!-- more -->

在实际开发中，特别是在开发测试环境中，频繁的修改部署是一件特别烦的事情。同样生产环境中数量过多的服务器部署，手动操作非常容易出现错误，所以可以使用`jenkins`实现自动部署。当然使用`jenkins`可以实现更多的功能。

可以查看[jenkins官方文档](https://jenkins.io/doc/)

## 1. 安装

可以使用`Docker`,`WAR`等各种方式安装`jenkins`，这里使用最简单的`WAR`方式：
1. 安装Java
2. [下载Jenkins.war](http://mirrors.jenkins.io/war-stable/latest/jenkins.war)
3. 使用`java -jar`或者web容器启动
4. 客户端浏览器输入地址访问
5. 初次访问需要解锁`jenkins`,需要从日志中找到生成的秘钥输入到浏览器中并激活`jenkins`
6. 创建用户正式使用`jenkins`

## 2. 使用

1. 创建一个新的`item`,选择`Freestyle project`(还有别的选项,该选项自由)
2. 设置名称描述等信息
3. 设置代码库。填写`Repository URL`,`Credentials`,`Branch Specifier`等信息
4. 设置构建触发器。设置`Poll SCM`的`Schedule`为`* * * * *`(设置一分钟检查一次代码是否更新并开始构建,开发环境中检测到更新就会开始构建)
5. 设置环境，可以不设置
6. 设置构建方式。使用`Execute shell`,加入`shell`命令,下面为示例，可以自由变化。
```bash
#进入工作目录下
cd /root/.jenkins/jobs/demo/workspace
#maven打包（服务器需要安装maven），也可以使用npm等
mvn clean install -Pdev
#执行远程命令（需要设置服务器间免密登录）
ssh root@ip " sh /bin/shutdown.sh"
#上传文件等
scp -r /root/.jenkins/jobs/demo/workspace/demo/target/demo.war root@ip:/home/webapp/demo/webapps/demo.war
```
7. 添加构建后流程。这里添加`Delete workspace when build is done`（删除构建后的文件）
8. 保存后可看到新的`item`,可以看到构建过程，次数，日志，状态，可手动执行等，详见web。

