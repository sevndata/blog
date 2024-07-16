---
title: 基于Spring Boot Actuator制作炫酷可视化系统监控
date: 2020-08-31 11:05:56
categories: 
- Spring Boot
tags: 
- Actuator
- Prometheus
- Grafana
---

分享基于`Spring Boot Actuator`制作炫酷可视化系统监控，其中使用到了`Prometheus`，`Grafana`。

<!-- more -->

## 1. 概述

1. `Spring Boot Actuator`是一个采集应用内部信息并暴露给外部的模块,它可以帮助我们监控和管理`Spring Boot`应用。

2. `Prometheus`是由`SoundCloud`开发的开源监控报警系统和时序列数据库，我们还可以选用其他工具如：`AppOptics`,`Atlas`,`JMX`等，更多支持可查阅[Spring Boot Actuator文档](https://docs.spring.io/spring-boot/docs/current/reference/html/production-ready-features.html#production-ready)。

3. `Grafana`是一个跨平台的开源的度量分析和可视化工具,可以通过将采集的数据查询然后可视化的展示,并及时通知。

在下文中，我们将利用这三个工具制作炫酷可视化系统监控，查阅文档分别为：[Spring Boot Actuator文档](https://docs.spring.io/spring-boot/docs/current/reference/html/production-ready-features.html#production-ready)，[Spring Boot Actuator数据文档](https://docs.spring.io/spring-boot/docs/2.3.4.RELEASE/actuator-api/html/)，[Prometheus引入文档](https://micrometer.io/docs/registry/prometheus)，[Prometheus安装文档](https://prometheus.io/docs/prometheus/latest/getting_started/?__cf_chl_captcha_tk__=b792618af602f67bdd94ccaf08839dd5cfac2068-1603764581-0-AdDJqe86JGdz12O1xVpzo_FLocxdk0a9FkNcW53_n0CKyLnbAOsF8bsTNgbS0bdqrKEc4ie8JowlO6Ds4GvnXmAkuKcMyPSPD51Wg2rZ0oALUFUA5WeNStAd-VOmA3TeIJf7rKVaWaYCKB0TbiOIIxCfo7W2evTCePxIRk4ZqcJaZIr-C9LcDH62LncGb0KMdlcUwnU20a1wVq9qwB3Yc05l_viKqv72qj90eGXdz_5TbR6mo86tREGL9F05Hg15JWp86y8xGURSA-ackFt8Y9nDZjFEDrMQ6qZw-dowGPSypLl5EHT9azR6qFP23VKJrpEAQXh3SXd8UoJTfSSAq-HFXMsINhKUO-g_a5-l1e9neQLGA9URT4pqYaSJSP7fWiLcdmSDwg-imyDp6DpYYQef4N5-u1tIA6jjbAL6wO1Ds61nqX_1zFXzvZ4rejZFS_tZ2EG26-rkvX_ul0KWXXdr4hPczboSJLUTPQfS7y9BknxMTQhFH9HW6Es8sKYwyovscHUYXDqRDM4-ZtaEhWqxS4nNvNKv3T2PEu0g5RVC)，[Grafana安装文档](https://grafana.com/docs/grafana/latest/installation/rpm/)

## 2. Spring Boot Actuator

### 1. 引入
```xml
<!-- for maven -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
</dependencies>
```
```java
//for gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
}
```
### 2. 配置
```java
//启用禁止
management.endpoint.shutdown.enabled=true
management.endpoints.enabled-by-default=false
//暴露接口
management.endpoint.info.enabled=true
management.endpoints.jmx.exposure.include=health,info
management.endpoints.web.exposure.include=*
management.endpoints.web.exposure.exclude=env,beans
//缓存时间
management.endpoint.beans.cache.time-to-live=10s
//CORS支持
management.endpoints.web.cors.allowed-origins=https://example.com
management.endpoints.web.cors.allowed-methods=GET,POST
```
设置数据接口权限
```java
@Configuration(proxyBeanMethods = false)
public class ActuatorSecurity extends WebSecurityConfigurerAdapter {

  @Override
  protected void configure(HttpSecurity http) throws Exception {
      http.requestMatcher(EndpointRequest.toAnyEndpoint()).authorizeRequests((requests) ->
          requests.anyRequest().permitAll());
  }
}
```
自定义数据接口
```java

@ReadOperation
public CustomData getCustomData() {
    return new CustomData("test", 5);
}
```
### 3. 通过`HTTP`获取数据
`Spring Boot Actuator`会自动配置所有启用的接口并通过`HTTP`公开。默认使用id前缀为的端点的`/Actuator`作为URL路径。例如，`health`暴露为`/Actuator/health`。他会使用`Spring MVC`,`Jackson`。
### 4. 指标数据内容
从`HTTP`接口获取到为`json`格式的数据。具体详细含义可查阅[Spring Boot Actuator数据文档](https://docs.spring.io/spring-boot/docs/2.3.4.RELEASE/actuator-api/html/)。
例如获取`health`：
```shell
curl 'http://localhost:8080/Actuator/health' -i -X GET -H 'Accept: application/json'
```
```json
{
  "status" : "UP",
  "components" : {
    "broker" : {
      "status" : "UP",
      "components" : {
        "us1" : {
          "status" : "UP",
          "details" : {
            "version" : "1.0.2"
          }
        },
        "us2" : {
          "status" : "UP",
          "details" : {
            "version" : "1.0.4"
          }
        }
      }
    },
    "db" : {
      "status" : "UP",
      "details" : {
        "database" : "H2",
        "validationQuery" : "isValid()"
      }
    },
    "diskSpace" : {
      "status" : "UP",
      "details" : {
        "total" : 194687758336,
        "free" : 92457164800,
        "threshold" : 10485760,
        "exists" : true
      }
    }
  }
}
```
## 3. Prometheus

### 1. 引入

1. `maven`引入
```xml
<!--for maven-->
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-prometheus</artifactId>
  <version>${micrometer.version}</version>
</dependency>
```

2. 暴露数据接口
```java
management.endpoints.web.exposure.include=*
management.metrics.tags.application=${spring.application.name}
```


### 2. 配置

在Spring Boot环境中下自动配置Prometheus接口。否则，可以使用任何基于JVM的HTTP服务器实现来将数据公开给Prometheus。

在Spring Boot中使用`MeterRegistryCustomizer`自动注册配置：
```java
@Bean
MeterRegistryCustomizer<MeterRegistry> metricsCommonTags() {
  return registry -> registry.config().commonTags("application", "MYAPPNAME");
}
```
其他环境可参考下面示例：
```java
//com.sun.net.httpserver.HttpServer
PrometheusMeterRegistry prometheusRegistry = new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);

try {
    HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
    server.createContext("/prometheus", httpExchange -> {
        String response = prometheusRegistry.scrape(); (1)
        httpExchange.sendResponseHeaders(200, response.getBytes().length);
        try (OutputStream os = httpExchange.getResponseBody()) {
            os.write(response.getBytes());
        }
    });

    new Thread(server::start).start();
} catch (IOException e) {
    throw new RuntimeException(e);
}
```
更加详细的内容查阅[Prometheus引入文档](https://micrometer.io/docs/registry/prometheus)
### 3. 安装

1. 下载最新的安装包。并安装
```shell
wget https://github.com/prometheus/prometheus/releases/download/v2.22.0/prometheus-2.22.0.linux-amd64.tar.gz
tar xvfz prometheus-2.22.tar.gz
cd prometheus-2.22
```

2. 配置文件`prometheus.yml`。
注意`GitLab`或者其他软件也使用到了`Prometheus`，修改端口号解决问题。
```shell
global:
  scrape_interval:     15s # By default, scrape targets every 15 seconds.

  # Attach these labels to any time series or alerts when communicating with
  # external systems (federation, remote storage, Alertmanager).
  external_labels:
    monitor: 'codelab-monitor'

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # Override the global default and scrape targets from this job every 5 seconds.
    scrape_interval: 5s

    static_configs:
      - targets: ['localhost:9090']
```
```shell
-job_name: 'Prometheus' #应用部署机器上的应用名
-targets: ['127.0.0.1:9090'] #应用运行机器上的本机端口号本机ip

-job_name: 'SpringBoot_Prometheus' #SpringBoot的应用名
metrics_path: '/actuator/prometheus' #能获取节点信息的路径
-targets: ['192.168.159.1:8080'] #SpringBoot应用运行的机器的ip端口号
```

3. 启动
```shell
# Start Prometheus.
# By default, Prometheus stores its database in ./data (flag --storage.tsdb.path).
./prometheus --config.file=prometheus.yml
```

更加详细的内容查阅[Prometheus安装文档](https://prometheus.io/docs/prometheus/latest/getting_started/?__cf_chl_captcha_tk__=b792618af602f67bdd94ccaf08839dd5cfac2068-1603764581-0-AdDJqe86JGdz12O1xVpzo_FLocxdk0a9FkNcW53_n0CKyLnbAOsF8bsTNgbS0bdqrKEc4ie8JowlO6Ds4GvnXmAkuKcMyPSPD51Wg2rZ0oALUFUA5WeNStAd-VOmA3TeIJf7rKVaWaYCKB0TbiOIIxCfo7W2evTCePxIRk4ZqcJaZIr-C9LcDH62LncGb0KMdlcUwnU20a1wVq9qwB3Yc05l_viKqv72qj90eGXdz_5TbR6mo86tREGL9F05Hg15JWp86y8xGURSA-ackFt8Y9nDZjFEDrMQ6qZw-dowGPSypLl5EHT9azR6qFP23VKJrpEAQXh3SXd8UoJTfSSAq-HFXMsINhKUO-g_a5-l1e9neQLGA9URT4pqYaSJSP7fWiLcdmSDwg-imyDp6DpYYQef4N5-u1tIA6jjbAL6wO1Ds61nqX_1zFXzvZ4rejZFS_tZ2EG26-rkvX_ul0KWXXdr4hPczboSJLUTPQfS7y9BknxMTQhFH9HW6Es8sKYwyovscHUYXDqRDM4-ZtaEhWqxS4nNvNKv3T2PEu0g5RVC)

## 4. Grafana

### 1. 添加源`/etc/yum.repos.d/grafana.repo`
```shell
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
```
### 2. 安装
```shell
sudo yum install grafana
```
更多版本和安装方法查阅[Grafana安装文档](https://grafana.com/docs/grafana/latest/installation/rpm/)
### 3. 启动
```shell
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```
### 4. 自启动
```shell
sudo systemctl enable grafana-server
```
### 5. 登录
访问`http//xxx:3000/`，输入用户名`admin`和密码登录，第一次成功会提示更改密码。`3000`为`Grafana`的默认监听端口。

### 6. 绘制监控图
可以在`Grafana`上设置数据源，自定义模板，导入模板等。这样就可以制作炫酷可视化系统监控了。

