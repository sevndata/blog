---
title: GitLab的安装使用及迁移
date: 2020-09-21 06:15:16
categories: 
- GitLab
tags: 
- Git
---

记录一次GitLab的迁移过程。

<!-- more -->

由于原有的GitLab部署在内网环境中，对于出差的同事只能通过路由器映射端口才能使用GitLab，如此背景下进行GitLab从内网迁移到云。系统环境为Ubuntu迁移到CentOS下。在安装迁移过程中遇到很多问题，本文将以事件过程分享。

### 1.安装文档

查看[GitLab官方安装文档](https://about.gitlab.com/install/#centos-7)，得到如下内容：

```shell
sudo yum install -y curl policycoreutils-python openssh-server
sudo systemctl enable sshd
sudo systemctl start sshd
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo systemctl reload firewalld
```

```shell
sudo yum install postfix
sudo systemctl enable postfix
sudo systemctl start postfix
```

```shell
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ee/script.rpm.sh | sudo bash
```

```shell
sudo EXTERNAL_URL="https://gitlab.example.com" yum install -y gitlab-ee
```

### 2.社区版安装 

尝试修改为社区版脚本安装，结果为可使用，如下：

```shell
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash
```

```shell
sudo EXTERNAL_URL="https://gitlab.example.com" yum install -y gitlab-ce
```

目录:

```
主目录：/opt/gitlab
配置文件地址：/etc/gitlab/gitlab.rb
各个组件地址：/var/opt/gitlab
日志地址：/var/log/gitlab
```

常用命令:

```shell
#启动状态
gitlab-ctl status
#重新加载配置
sudo gitlab-ctl reconfigure
#重新启动
gitlab-ctl restart
#启动
gitlab-ctl start
#停止
gitlab-ctl stop
#停止某个组件
gitlab-ctl stop unicorn
#各组件日志查看
gitlab-ctl tail nginx
```

### 3.备份被迁移的GitLab

备份原来的GitLab:

```shell
sudo gitlab-rake gitlab:backup:create
```

将备份文件(几十个G，有点大)上传到目标服务器上:

```shell
scp 1599804179_2020_09_11_12.6.2_gitlab_backup.tar root@xxx:/var/opt/gitlab/backups/
```

### 4.恢复备份

在目标服务恢复备份：

```shell
gitlab-ctl stop unicorn
gitlab-ctl stop sidekiq
```

```shell
chmod 777 1599804179_2020_09_11_12.6.2_gitlab_backup.tar
gitlab-rake gitlab:backup:restore BACKUP=1599804179_2020_09_11_12.6.2
```

在恢复过程中报错，版本不兼容。

### 5.版本兼容问题

查看原来GitLab版本为12.6.2，新安装版本为13.3.5，尝试升级原有GitLab:

```shell
cat /opt/gitlab/embedded/service/gitlab-rails/VERSION
sudo apt-get update
sudo apt-get install gitlab-ce
sudo apt install gitlab-ce=13.3.5-ce
```

发现GitLab不能跨版本升级，升级到了12.9.2，考虑到升级需要时间，备份文件过大传输过慢，决定将新安装的13.3.5版本GitLab降版本到12.6.2

### 6.卸载重装

卸载并删除GitLab:

```shell
sudo yum install -y gitlab-ee
```

```
find / -name gitlab | xargs rm -rf
```

尝试直接修改脚本安装：

```shell
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce-12.6.2/script.rpm.sh | sudo bash
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce.12.6.2/script.rpm.sh | sudo bash
```

未能成功。查看连接是否正确。浏览器中打开显示`The page you were looking for doesn't exist`，`wget`显示`404`。官网中寻找到[下载地址](https://packages.gitlab.com/gitlab/gitlab-ce/)（直接改地址，官网查找，找了好久没找到，最后在搜索引擎中找到了地址），搜索`12.6.2`查找包，根据系统版本选择版本，这里选择`el/7`:

```shell
curl -s https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash
sudo yum install gitlab-ce-12.6.2-ce.0.el7.x8，6_64
```

安装成功后，启动服务。浏览器中访问为502。查看各组件启动情况，并配置修改。

### 7.配置

挨个查询各个组件运行情况并解决（比较庞大，繁琐。只能遇到什么问题解决什么问题），修改配置后需要重新加载配置并启动

各组件进程不能通过kill杀掉，gitlab-ctl守护进程会启动子进程。

```shell
sudo gitlab-ctl reconfigure
sudo gitlab-ctl restart
```

以下为本次迁移遇到的问题以及解决方案：

1. `gitlab-ctl reconfigure`出现`No such file or directory`错误

```shell
/opt/gitlab/embedded/bin/gitlab-logrotate-wrapper: No such file or directory
/opt/gitlab/embedded/service/gitlab-rails/bin/sidekiq-cluster: No such file or directory
```
可以从其他机器拷贝一份，也可以通过来回修改`unicorn`端口号自动生成文件

2. nginx端口号冲突导致启动异常

本台服务器通过`nginx`代理很多其他服务。决定禁用`GitLab`自带`nginx`使用原有`nginx`。修改`GitLab`配置：
```shell
external_url 'xxx'
gitlab_workhorse['listen_network'] = "tcp"
gitlab_workhorse['listen_addr'] = "127.0.0.1:18181"
nginx['enable'] = false
```
修改原有`nginx`代理到该服务。启动后出现异常，手动关闭`GitLab`中`nginx`服务恢复正常。猜测与`external_url`有关系。可尝试注释掉`external_url`。

```shell
gitlab-ctl stop nginx
```

同时可能没有写日志权限，要赋予权限

```shell
chmod -R o+x /var/opt/gitlab/gitlab-rails
```

3. unicorn端口号冲突导致启动异常

```shell
unicorn['port'] = 18080
```

4. prometheus端口冲突导致启动异常

直接修改了原来的prometheus端口

5. unicorn写日志权限不足

```shell
chmod -R 777 /var/log/gitlab

```

6. 其他类似问题

```shell
{"address":"/var/opt/gitlab/redis/redis.socket","level":"info","msg":"redis: dialing","network":"unix","time":"2020-09-11T18:01:41+08:00"}
{"error":"keywatcher: dial unix /var/opt/gitlab/redis/redis.socket: connect: connection refused","level":"error","msg":"unknown error","time":"2020-09-11T18:01:41+08:00"}

ind() to 0.0.0.0:80 failed (98: Address already in use)

The data directory was initialized by PostgreSQL version 11, which is not compatible with this version 10.9

```

经过各种问题的解决终于服务正常，并在浏览器中可以访问到。

### 8.再次恢复

```shell
chmod 777 1599804179_2020_09_11_12.6.2_gitlab_backup.tar
gitlab-rake gitlab:backup:restore BACKUP=1599804179_2020_09_11_12.6.2
```

过程中有一个项目恢复失败

```shell
sxf ... [DONE]
        * tangKu8/misapp ... Error: 13:CreateRepositoryFromBundle: cmd wait failed: exit status 128
        [Failed] restoring tangKu8/misapp repository
Warning: Your gitlab.rb and gitlab-secrets.json files contain sensitive data
and are not included in this backup. You will need to restore these files manually.
```
### 9.邮件配置
### 10.验证

验证各个用户和项目迁移是否成功。
    

