---
title: CentOS7 ssh免密登录及失效问题
date: 2020-09-30 16:15:26
categories: 
- CentOS
tags: 
- CentOS
---
分享ssh免密登录及失效问题
<!-- more -->

## 1. ssh免密登录

通过配置本机公钥到目标服务器认证文件方式实现免密登录，常用于免密登录服务器，免密git等。

如:A服务器登录到B服务器，A生成公私钥，将A的公钥配置到B认证文件中，实现了A免密登录到B服务器。

### 1. 配置ssh免密登录

1. 生成秘钥
```shell
ssh-keygen -t rsa
```

2. 免密设置
将在用户目录下`.ssh`中生成`id_rsa`,`id_rsa.pub`公私钥，将`id_rsa.pub`公钥设置在目标服务器用户目录`.ssh`中认证文件`authorized_keys`尾部（可设置多个）。这样就实现了服务器间免密登录。

## 2. 免密失效

### 1. 修改密码IP

因修改密码或IP等导致免密失效可删除`known_hosts`中对应`IP`信息。

### 2. 权限问题

用户目录，`.ssh`目录，`authorized_keys`文件等文件权限会引起认证失效，可重新设置权限为`700`

```shell
chmod 700 authorized_keys
```

### 3. ssh配置文件

在`/etc/ssh/sshd_config`中检查`StrictModes`,`AuthorizedKeysFile`等配置是否正确。

### 4. 防火墙等问题

检查是否端口禁止访问等导致免密失效。

### 5. ssh重启

```shell
service sshd restart
```







