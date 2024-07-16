---
title: MySQL阻塞，修复损坏的innodb
date: 2021-03-09 09:50:00
categories: 
- MySQL
tags: 
- MySQL
---
记录一次生产迁移数据造成生产事故及修复过程
<!-- more -->

## 1.事件起由
该系统是运行于中东国家的分布式多节点系统，维持近十万商户交易。由于服务器硬件没有及时到位，只运行于一个节点，短时间内，业务数据库达到了接近上亿级别的数据量，应用服务器也超过了负荷。在硬件到位后，扩容了4-5个节点，面临的问题需要把运行于第一个节点的商户平均分到4个节点上，减轻压力。应用服务器比较容易处理，而数据库按照一定的规则将商户数据迁移到新数据库则比较复杂。
## 2.迁移方案
确认了俩套方案去做数据库数据的迁移：
1. 编写脚本，以时间，id等因素迁移数据。
2. 一次性将节点一数据库全量备份恢复到其他节点，并且恢复交易，然后长期计划删除不属于该节点商户业务数据。

通过评审确认了2方案为最后方案。原因为1方案涉及需要迁移的数据太多，太杂，稍有错误将会影响系统的运行，且系统每天只有4小时的可停机时间，1方案极可能迁移不完，需要二次迁移等，阻断交易风险巨大。而反向删除业务数据更加好做，且时间足够使用物理备份恢复数据库，删除数据可以分布去做，而不影响交易。

实际中使用`xtrabackup`工具迁移数据。完美的迁移了数据并且恢复了业务。而问题出现在了删除数据环节。

## 3.造成阻塞

数据恢复后，编写删除非该节点商户业务数据，准备删除脚本，并执行

```sql
delete from node_sku where op_map_id not in (xxxx,xx,xxx);
```

```shell
nohup mysql -uroot -p -Dtk_biz < exportSql/delete_sku.sql   //输入密码
nohup mysql -uroot -p -Dtk_biz < exportSql/delete_sku.sql &   //会跳过输入密码，并报没有权限
```

经过停机时间，恢复后系统后，数据库响应变的非常慢，造成大面积商户不能使用问题。登录服务器发现数据库大量报错信息。

```
Lock wait timeout exceeded; try restarting transaction
```

```sql
SELECT * FROM information_schema.INNODB_TRX;
```

通过以上脚本发现有一条涉及800万数据的回滚。准备杀掉事务，设置一些锁参数等恢复了数据库。

经过实践及大量资料的查阅，得知大量数据删除这样的操作的非常不可取的，一旦操作中断Rolling back将花费更多的时间，并造成数据库阻塞。可以通过将数据转移到临时表，使用truncate table tablename等方法，或者保证删除数据脚本的可用性，如数据量较小。

之后减小了脚本删除的数据量及关闭了mysql日志又执行了一次删除数据操作

```shell
// /etc/my.cnf
skip-log-bin
```

```
autocommit=1 默认自动提交
autocommit=0 手动提交
```
结果发生了第二次数据库阻塞，并且在业务方催的时候错误的执行了kill，reboot，断电操作，造成Mysql启动不起来。

## 4.修复损坏的innodb

查看`/var/log/mysql.log`，发现大量表innodb损坏，修复数据库：

1. 配置`my.cnf`中`innodb_force_recovery`
```
innodb_force_recovery=1
```
设置为1，重启数据库，如果不成功则修改为2重启，1-6不同含义可参考[mysql官网Forcing InnoDB Recovery](https://dev.mysql.com/doc/refman/8.0/en/forcing-innodb-recovery.html)直到启动成功。

2. mysql启动后，损坏的表是只读状态`Can't lock file (errno: 165 - Table is read only)`。

3. 将损坏的表的数据导出
```
mysqldump -u root -p tk_biz node_sku --no-create-info --where="op_map_id in ('xx','xxx','xxxx')"> /home/exportSql/sku.sql
```
4. 将损坏表drop

5. 删除`innodb_force_recovery`配置

6. 启动mysql

7. 将导出数据重新恢复到数据库中

8. 恢复是可能出现丢失数据问题
```
mysqldump: Error 2013: Lost connection to MySQL server during query when dumping table `node_payment` at row: 6060246
```

9. 恢复innodb后会有错误：
```
log sequence number is in the future
```
原因是InnoDB日志文件(重做日志)与数据文件不同步


致此数据恢复正常。分享记录了一些操作，有些其他细节也记不清了。

 
