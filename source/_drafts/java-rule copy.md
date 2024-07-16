---
title: Java代码规格建议
date: 2020-03-28 09:15:16
categories: 
- Java
tags: 
- Java
---
本文分享了Java代码规格建议，包括注释等规范
<!-- more -->

/etc/yum.repos.d/mongodb-org-4.2.repo

[mongodb-org-4.2]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.2/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc

sudo yum install -y mongodb-org

sudo systemctl start mongod

sudo systemctl status mongod

sudo systemctl enable mongod
sudo systemctl restart mongod


/var/lib/mongo /var/log/mongodb


use logdb

show dbs

show tables


> use logdb
switched to db logdb
> db.createCollection("payerrdb")
{ "ok" : 1 }
> db.createCollection("servererrdb")
{ "ok" : 1 }
> db.createCollection("syserrdb")
{ "ok" : 1 }


db.createUser(
    {
        user: "root",
        pwd: "sxxc.co.mongodb",
        roles: [
           {
            role: "userAdminAnyDatabase",
            db: "admin"
           },
           {
            role: "dbAdminAnyDatabase",
            db: "admin"
           }
        ]
    }
)

show users  // 查看当前库下的用户

db.dropUser('testadmin')  // 删除用户

db.updateUser('admin', {pwd: '654321'})  // 修改用户密码

db.auth('admin', '654321')


db.createUser(
    {
        user: "sxxc.co",
        pwd: "sxxc.co.mongodb",
        roles: [
           {
            role: "readWrite",
            db: "logdb"
           },{
            role: "dbAdmin",
            db: "logdb"
           }
        ]

    }
)


[mongodb-org]
name=MongoDB Repository
baseurl=https://mirrors.tuna.tsinghua.edu.cn/mongodb/yum/el$releasever/
gpgcheck=0
enabled=1


sudo yum makecache
sudo yum install mongodb-org