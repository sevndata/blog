---
title: Grafana重置密码
date: 2021-05-31 11:05:56
categories: 
- Grafana
tags: 
- Grafana
---

分享`Grafana`忘记密码后如何重置密码。

<!-- more -->

## 重置密码

逻辑：修改`Grafana sqlite`中用户表密码

1. 找到`grafana.db`

```sql
find / -name "grafana.db"
-- /var/lib/grafana/grafana.db
```
2. 进入`sqlite`修改数据

```sql
--进入数据库
sqlite3 /var/lib/grafana/grafana.db
--显示所有表
.tables
--查询表user数据
select * from user;
--修改admin密码为admin
update user set password = '59acf18b94d7eb0694c61e60ce44c110c7a683ac6a8f09580d626f90f4a242000746579358d77dd9e570e83fa24faa88a8a6', salt = 'F3FAxVm33R' where login = 'admin';
--退出
.exit
```
3. 重启`Grafana`

```shell
systemctl stop grafana-server.service
systemctl start grafana-server.service
```


