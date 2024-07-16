---
title: ShardingSphere-JDBC进行数据分片
date: 2020-05-28 09:15:16
categories: 
- Java
- MySQL
- Spring
tags: 
- MySQL
- Spring
---

分享在实战中分表分库的策略。

<!-- more -->

## 1. 数据量评估与策略

数据量评估和并发评估是项目的至关重要的环节，数据量的多少决定项目的架构，技术的选取。

很多同学往往会进入误区，认为某个技术就是比另一个技术好，微服务就是比单系统好。而事实上技术最终都可归结为资源问题，技术大多数是业务演变而形成。

选取合适的技术非常重要，盲目的追求技术将会加大人力，财力等资源消耗。

应对不同的数据量并发性简单分享下关于数据库几种应对策略：

1. 读写分离
2. 垂直分库，垂直分表
3. 水平分库，水平分表
4. 其他方式：跑批数据转移等策略

## 2. ShardingSphere-JDBC

简单分享使用`ShardingSphere-JDBC`做数据分片，`ShardingSphere-JDBC`是`Apache ShardingSphere`中的一个模块，更加详细的内容请参阅(Apache ShardingSphere文档)[https://shardingsphere.apache.org/document/legacy/4.x/document/en/overview/],以下为在`Spring Boot`中使用：

```xml
<dependency>
    <groupId>org.apache.shardingsphere</groupId>
    <artifactId>sharding-jdbc-spring-boot-starter</artifactId>
    <version>{last.version}</version>
</dependency>
```

```java
spring.jpa.database=mysql
spring.datasource.url=jdbc:mysql://jdbc:mysql://xxx.xxx.xxx.xxx:3306/xxx
spring.datasource.username=username
spring.datasource.password=password
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

spring.shardingsphere.datasource.name=master
spring.shardingsphere.datasource.master.type=com.zaxxer.hikari.HikariDataSource
spring.shardingsphere.datasource.master.drive-class-name=com.mysql.cj.jdbc.Driver
spring.shardingsphere.datasource.master.jdbc-url=jdbc:mysql://jdbc:mysql://xxx.xxx.xxx.xxx:3306/xxx
spring.shardingsphere.datasource.master.username=username
spring.shardingsphere.datasource.master.password=password

spring.shardingsphere.sharding.default-data-source-name=master
spring.shardingsphere.sharding.tables.vip_user.actual-data-nodes=master.vip_user${0..19}
spring.shardingsphere.sharding.tables.vip_user.table-strategy.inline.sharding-column=id
spring.shardingsphere.sharding.tables.vip_user.table-strategy.inline.algorithm-expression=vip_user${id % 20}
spring.shardingsphere.sharding.tables.vip_user.key-generator.column=id
spring.shardingsphere.sharding.tables.vip_user.key-generator.type=SNOWFLAKE

spring.shardingsphere.sharding.tables.vip_addr.actual-data-nodes=master.vip_addr${0..19}
spring.shardingsphere.sharding.tables.vip_addr.table-strategy.inline.algorithm-expression=vip_addr${id % 20}
spring.shardingsphere.sharding.tables.vip_addr.table-strategy.inline.sharding-column=id
spring.shardingsphere.sharding.tables.vip_addr.key-generator.type=SNOWFLAKE
spring.shardingsphere.sharding.tables.vip_addr.key-generator.column=id
```

```java
@Table(name ="vip_addr")
@Entity
@Getter
@Setter
@NoArgsConstructor
@ToString
public class Addr  implements Serializable {
    private static final long serialVersionUID =  2200950815215875003L;

    /**
     * id
     */
    @Column(name = "id")
    @GeneratedValue(strategy=GenerationType.IDENTITY)
    @Id
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private Long id;

    /**
     * 
     */
    @Column(name = "user_map_id", updatable = false)
    private Integer userMapId;
}
```

在数据库中创建`vip_user0`,`vip_user1`...`vip_user19`20个表。这样就将数据水平分割到20个表中。
