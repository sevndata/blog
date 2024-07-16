---
title: Redis单机，哨兵，集群模式安装及其配置
date: 2022-03-10 18:15:16
categories: 
- Java
- Redis
tags: 
- Java
- Redis
---
本文分享了`Redis`单机，哨兵，集群模式原理，以及安装配置，`Java`应用连接`Redis`。
<!-- more -->
更多内容请查看[Redis官网](https://redis.io/)
## 1.Redis安装
`Redis`官方提供了多种下载安装方式，请查看[Redis官方下载页](https://redis.io/download/)选择适合的安装方式，本文使用源码方式安装。

### 1.1 下载
```shell
wget https://download.redis.io/releases/redis-6.2.6.tar.gz
```
### 1.2 解压
```shell
tar -zxvf redis-6.2.6.tar.gz
```
### 1.3 编译
```shell
#编译需使用gcc，查询gcc是否安装
gcc -v
#gcc若未安装，安装gcc
yum install gcc
#在redis目录中编译
make
```
### 1.4 常用配置
`Redis`配置是redis目录下redis.conf`。
```shell
#保护模式,白名单
protected-mode yes
bind 127.0.0.1
#密码
requirepass newpassword
#后台模式运行
daemonize yes
#redis的进程文件
pidfile /var/run/redis/redis-server.pid 
#端口
port 6379
#数据文件目录
dir /data
#日志文件目录
logfile /var/log/redis/redis-server.log 

# 持久化策略RDB，Redis还提供了AOF策略，详情查看Redis官网
# redis是基于内存的数据库，可以通过设置该值定期写入磁盘，注释掉“save”这一行配置项就可以让保存数据库功能失效 
# 60秒（1分钟）内至少10000个key值改变（则进行数据库保存--持久化） 
save 60 10000 

#淘汰机制，内存容量超过maxmemory后的处理策略。 
#volatile-lru：利用LRU算法移除设置过过期时间的key。 
#volatile-random：随机移除设置过过期时间的key。 
#volatile-ttl：移除即将过期的key，根据最近过期时间来删除（辅以TTL） 
#allkeys-lru：利用LRU算法移除任何key。 
#allkeys-random：随机移除任何key。 
#noeviction：不移除任何key，只是返回一个写错误。 
#上面的这些驱逐策略，如果redis没有合适的key驱逐，对于写命令，还是会返回错误。redis将不再接收写请求，只接收get请求。
maxmemory-policy volatile-lru 
```
### 1.5 常用操作
```shell
#启动
./src/redis-server redis.conf
#客户端redis-cli连接redis
src/redis-cli -a newpassword -h 127.0.0.1 -p 6379
#redis数据库中一些操作，更多详见[Redis官网文档](https://redis.io/docs/)
keys *
dbsize
set name foo
get name
del name
flushall
```
### 1.6应用连接

1.6.1 `spring-data-redis`
```shell
#spring-data-redis配置
spring.redis.host=host
spring.redis.port=6379
spring.redis.password=password
spring.data.redis.repositories.enabled=false
#session
spring.session.store-type=redis
server.servlet.session.timeout=PT8H
#spring cache使用redis
spring.cache.type=redis
spring.cache.redis.time-to-live=PT8H
spring.cache.redis.cache-null-values=false

#使用spring cacheManager做redis操作
cacheManager.getCache("CACHE-KEY").get("KEY",Object.class);
#使用redisTemplate，批量操作，匹配pre
redisTemplate..opsForValue().multiGet("KEY"+"*");

```
1.6.2 `jedis`
```java
/**
 * jedis连接Factory
 */
@Bean
public JedisConnectionFactory jedisConnectionFactory() {
    return new JedisConnectionFactory(redisStandaloneConfiguration(), jedisClientConfiguration());
}
/**
 * jedis configuration
 */
@Bean
public RedisStandaloneConfiguration redisStandaloneConfiguration() {
    RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
    configuration.setHostName(redisHostName);
    configuration.setPassword(RedisPassword.of(redisPassWd));
    configuration.setPort(redisPort);
    return configuration;
}
/**
 * jedis Pool Client Configuration
 */
@Bean
public JedisClientConfiguration jedisClientConfiguration() {
    JedisPoolConfig poolConfig = new JedisPoolConfig();
    poolConfig.setMinEvictableIdleTimeMillis(43200000);
    poolConfig.setSoftMinEvictableIdleTimeMillis(43200000);
    return JedisClientConfiguration.builder()
            .usePooling()
            .poolConfig(poolConfig)
            .build();
}
/**
 * 集成到spring CacheManager
 */
@Bean
public CacheManager cacheManager() {
    RedisCacheConfiguration redisCacheConfiguration=RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofDays(30L));
    return RedisCacheManager.builder(jedisConnectionFactory()).cacheDefaults(redisCacheConfiguration).build();
}
```
**3.配置多哨兵**

- 表 1 机器分配

| 服务类型 | 是否主服务器 | IP地址                   | 端口  |
| -------- | ------------ | ------------------------ | :---: |
| Redis    | 是           | 10.0.3.16(217.30.160.78) | 6379  |
| Redis    | 否           | 10.0.3.14(217.30.160.79) | 6379  |
| Redis    | 否           | 10.0.3.15(217.30.160.80) | 6379  |
| Sentinel | ——           | 10.0.3.16(217.30.160.78) | 26379 |
| Sentinel | ——           | 10.0.3.14(217.30.160.79) | 26379 |
| Sentinel | ——           | 10.0.3.15(217.30.160.80) | 26379 |

- 配置服务器  进到redis目录:

```
vim redis.conf 修改以下内容:

#使得Redis服务器可以跨网络访问
bind 0.0.0.0
#设置密码
requirepass uzxingdata
# 指定主服务器，注意：有关slaveof的配置只是配置从服务器，主服务器不需要配置
slaveof 217.30.160.78 6379
# 主服务器密码，注意：有关slaveof的配置只是配置从服务器，主服务器不需要配置
masterauth uzxingdata
# 守护线程 yes 后台启动
daemonize yes



replica-read-only no
--------------
vim sentinel.conf 修改以下内容:
# 守护线程 yes 后台启动
daemonize yes
#禁止保护模式
protected-mode no
#配置监听的主服务器，这里 sentinel monitor 代表监控
#master代表服务器名称，可以自定义
#10.0.3.16代表监控的主服务器
#6379代表端口
#2代表只有两个或者两个以上的烧饼认为主服务器不可用的时候，才会做故障切换操作
sentinel monitor master 217.30.160.78 6379 2
#sentinel auth-pass 定义服务的密码
#master服务名称
#Redis服务器密码
sentinel auth-pass master uzxingdata

```

```
日志文件配置 logfile "/var/log/sentinel_log.log"
```

```
配置哨兵sentinel.conf

sentinel down-after-milliseconds mymaster 5000 //哨兵监听redis主服务器没有响应超过5秒，就认为是SDOWN了。
sentinel parallel-syncs mymaster 1 //新master启动之后，只允许同一时刻一台从服务器更新同步数据
sentinel failover-timeout mymaster 15000 //哨兵监听redis主服务器没有响应超过15秒，就开始进行failover，进行选举新的master。
```



**4.启动**  

```
# 启动Redis服务器进程
./redis-server ../redis.conf
# 启动哨兵进程
./redis-sentinel ../sentinel.conf
```

注意启动的顺序。**首先是主机（10.0.3.16）的Redis服务进程，然后启动从机的服务进程，最后启动3个哨兵的服务进程。**

```
进到 redis/src/redis.cli  info replication 查redis连接信息
lsof -i:26379 查端口号开放
```



**淘汰策略优化**



```
maxmemory-policy noeviction

1.volatile-lru: 在所有带有过期时间的 key 中使用 LRU 算法淘汰数据；
2.alkeys-lru: 在所有的 key 中使用最近最少被使用 LRU 算法淘汰数据，保证新加入的数据正常；
3.volatile-random: 在所有带有过期时间的 key 中随机淘汰数据；
4.allkeys-random: 在所有的 key 中随机淘汰数据；
5.volatile-ttl: 在所有带有过期时间的 key 中，淘汰最早会过期的数据；
6.noeviction: 不回收，当达到最大内存的时候，在增加新数据的时候会返回 error，不会清除旧数据，这是 Redis 的默认策略；
```



**连接哨兵模式注意事项**

```
服务器在同一网段可以使用内网ip地址进行连接, 若redis服务器 与应用服务器不在同一网段使用公网ip访问
```









