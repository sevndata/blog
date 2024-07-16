---
title: MySQL8搭建，调优及数据迁移(xtrabackup)
date: 2020-10-26 11:21:43
categories: 
- MySQL
- xtrabackup
tags: 
- MySQL
- xtrabackup
---

记一次国外项目MySQL生产环境搭建，并使用xtrabackup8对大数量数据进行迁移过程。

<!-- more -->

本文使用的操作系统为`CentOS7`。更多详细的内容请查看[MySQL官网](https://www.mysql.com)，[MySQL下载](https://dev.mysql.com/downloads/mysql)，[xtrabackup官网](https://www.percona.com/doc/percona-xtrabackup/8.0/index.html)。

mysql升级到8可能出现一些连不上的问题，可升级连接驱动解决。如：`com.mysql.jdbc.Driver`版本升级。

生产环境数据库应隐藏到内网中，外网不可连接。

## 1. MySQL8安装及使用
### 1. 卸载

```shell
yum list mysql*

yum remove mysql*
```

### 2. 安装

```shell
wget https://repo.mysql.com//mysql80-community-release-el7-6.noarch.rpm

yum install mysql80-community-release-el7-6.noarch.rpm

yum install mysql-community-server

# 失败可添加参数 --nogpgcheck
# 可能缺少glib等依赖 安装及可
# 过期访问https://dev.mysql.com/downloads/repo/yum/
```
### 3. 配置，调优

配置文件在`/etc/my.cnf`目录下。

```shell
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
# sql_mode 模式，sql语法，数据校验，可能出现有的项目中sql报错等
sql_mode=NO_ENGINE_SUBSTITUTION
# updateTime自动更新必要参数
explicit_defaults_for_timestamp=false

# mysql调优参数
# 缓存数据内容大小
innodb_buffer_pool_chunk_size=1073741824
# 缓存池大小，应为上方参数的倍数
innodb_buffer_pool_size=10737418240
# 默认设置为1024，数据量大达到1024后会报错Too many open files
open_files_limit=10000
# innoDB 存储引擎使用一个指定大小的Redo log空间,Redo log越大会导致在断电，数据崩溃下需要越长的时间恢复
# 1G预估恢复速度为5分钟
# 参数影响写入速度，测试产生文件大小调整此参数大小
innodb_log_file_size=1G
# 缓存池数量
innodb_buffer_pool_instances=10
```

### 4. 启动

```shell
# 启动
systemctl start mysqld.service
# 停止
systemctl stop mysqld.service
# 查看运行状态
systemctl status mysqld.service
```

### 5. 初次连接

```shell
# 尝试登陆，登陆不成功
mysql -u root -p

# 获取初始密码
# A temporary password is generated for root@localhost: ;y*(uKZQ,4rq
# ;y*(uKZQ,4rq则为初始密码
grep ‘temporary password’ /var/log/mysqld.log

# 再次尝试用新密码登陆
mysql -u root -p

# 强制修改初始密码，mysql8中密码都必须至少有三种字符，可大小写符号三种拼接
alter user user() identified by ‘dD_d’
```

### 6. 创建应用使用账号

```sql
-- 创建修改用户，注意mysql8引进新的加密方式caching_sha2_password，这种加密方式客户端不支持，需要制定mysql_native_password加密方式
-- 在生产环境中，每个应用服务器需单独设置可连数据库账号
CREATE USER 'tk_node'@'10.0.10.70' IDENTIFIED WITH mysql_native_password BY 'dD_d';

ALTER USER 'tk_node'@'10.0.10.70' IDENTIFIED WITH mysql_native_password BY 'dD_d';
```

### 7. 赋予权限

```sql
-- 一般我们赋予应用服务器SELECT, INSERT,UPDATE,DELETE这些权限。可依据实际情况赋予权限
-- *.*是为目标库
GRANT SELECT, INSERT,UPDATE,DELETE ON *.* TO 'tk_node'@'10.0.10.70';
```

### 8. 数据库操作

```sql
CREATE DATABASE tk_control default charset utf8 COLLATE utf8_general_ci;
USE tk_control;
```

## 2. 使用xtrabackup8数据迁移

### 1. 数据迁移方案

1. 使用`mysqldump`进行数据迁移，逻辑备份，~~此方案在数据量小时比较实用~~。实战效果在千万级别数据下，`mysqldump`有非常好的性能。
```shell
mysqldump -u root -p xxx tk_xx tk_xx2 tk_xx3 > /home/tk_node.sql
```
2. 使用`datadir`进行数据迁移。需停机，有风险。
3. 使用`navicat`等工具进行数据迁移。同样为逻辑备份恢复。
4. 使用`xtrabackup`进行数据迁移，物理备份恢复，速度快，不需要停机，不锁表，不影响正常业务，热更新，可增量备份，适用于大数据量迁移备份。
  
所以，~~在生产环境少量数据时推荐使用`mysqldump`~~，`mysqldump`比较推荐，~~大数据量时使用`xtrabackup`~~,优选`mysqldump`次选`xtrabackup`。

### 2. xtrabackup安装

注意`xtrabackup`的版本。`xtrabackup`不同版本对应不同`MySQL`版本。在官方文档查找合适的版本。下文的版本为`xtrabackup8`对应`MySQL8`。

```shell
yum install https://repo.percona.com/yum/percona-release-latest.noarch.rpm

percona-release enable-only tools release

yum install percona-xtrabackup-80

# 压缩备份工具
yum install qpress
```

### 3. xtrabackup所需要的权限

```sql
CREATE USER 'bkpuser'@'localhost' IDENTIFIED BY 'xxx';

GRANT BACKUP_ADMIN, PROCESS, RELOAD, LOCK TABLES, REPLICATION CLIENT ON *.* TO 'bkpuser'@'localhost';

GRANT SELECT ON performance_schema.log_status TO 'bkpuser'@'localhost';

FLUSH PRIVILEGES;
```

### 4. xtrabackup全量备份

压缩备份：
```shell
# defaults-file:mysql配置文件， compress-threads：线程数
xtrabackup --defaults-file=/etc/my.cnf --host=localhost --user=bkpuser --password=xxx --port=3306 --backup --compress --compress-threads=10 --target-dir=/home/compressed/

```
### 5. 可能出现的报错

```
问题1：
Please upgrade PXB, if a new version is available. To continue with risk, use the option --no-server-version-check.
解决：添加参数 --no-server-version-check
xtrabackup --defaults-file=/etc/my.cnf --host=localhost --user=bkpuser --password=xxx --port=3306 --backup --compress --compress-threads=10 --target-dir=/home/compressed/ --no-server-version-check
```

```
问题2：
Error: failed to execute query 'SELECT lower(STATUS_KEY), STATUS_VALUE FROM performance_schema.keyring_component_status': 1142 (42000) SELECT command denied to user 'bkpuserxz'@'localhost' for table 'keyring_component_status'
解决：添加权限
GRANT SELECT ON performance_schema.keyring_component_status TO bkpuserxz@'localhost';
FLUSH PRIVILEGES;
```

### 6. xtrabackup还原

1. 把全量备份文件上传到目标服务器，进行备份恢复。
2. 目标MySQL服务停止
```shell
systemctl stop mysqld.service
```
3. 解压备份文件
```shell
xtrabackup --decompress --target-dir=/home/compressed/
```
4. 备份还原
```shell
xtrabackup --copy-back --target-dir=/home/compressed/
```
还原过程中出现错误`/var/lib/mysql is not empty!`，可删除`/var/lib/mysql`下所有文件。
```shell
rm -rf /var/lib/mysql/*
```
5. 赋于权限
```shell
chown -R mysql:mysql /var/lib/mysql
```
6. 启动MySQL服务
```shell
systemctl start mysqld.service
```
7. 启动不成功
```shell
若启动不成功，查看 /var/log/mysql.log文件具体查看启动不成功原因。
若文件损坏，innodb损坏等问题。需使用innodb_force_recovery=1进行详细纠错，可见本网MySQL阻塞，修复损坏的innodb一文
```
8. 检查恢复是否正常

### 7. xtrabackup增量备份

```shell
xtrabackup --backup --target-dir = /data/backups/base
xtrabackup --backup --target-dir = /data/backups/inc1 --incremental-basedir = /data/backups/base
xtrabackup --backup --target-dir = /data/backups/inc2 --incremental-basedir = /data/backups/inc1

xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base
xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base --incremental-dir=/data/backups/inc1
xtrabackup --prepare --target-dir=/data/backups/base --incremental-dir=/data/backups/inc2
xtrabackup --prepare --apply-log-only --target-dir = /data/backups/base -incremental-dir = /data/backups/inc1
```

更多xtrabackup功能详见[xtrabackup官方文档](https://www.percona.com/doc/percona-xtrabackup/8.0/index.html)