---
title: Jackson时区问题
date: 2020-03-28 09:15:16
categories: 
- Java
tags: 
- Java
---
本文分享jackson时区问题
<!-- more -->

## 1.问题

`Spring Boot`项目中发现时间差8小时问题，猜测`Jackson`序列化时间出现问题。

## 2.解决

设置`Jackson`时区：

```java
spring.jackson.locale=zh_CN
spring.jackson.time-zone=GMT+8
```

```java
@Bean
public Jackson2ObjectMapperBuilderCustomizer jacksonObjectMapperCustomization() {
  return jacksonObjectMapperBuilder ->
        jacksonObjectMapperBuilder.timeZone(TimeZone.getTimeZone("GMT+8"));
}
```

```java
@JsonFormat(timezone="GMT+8")
```

