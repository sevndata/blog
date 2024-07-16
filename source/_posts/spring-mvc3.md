---
title: 浅析Spring MVC:自定义配置
date: 2018-05-18 10:00:00
categories: 
- Spring MVC
tags: 
- Spring MVC
---

使用Spring Web MVC，开发者可以直接访问官方文档[Spring Web MVC文档Version 5.2.1.RELEASE](https://docs.spring.io/spring/docs/5.2.1.RELEASE/spring-framework-reference/web.html#mvc)，本文及Spring MVC系列文章都参考于此文档及源码。

这一节主要为Spring MVC的配置，这也是我们最常用的。
<!-- more -->
## 1. 启用
1. 可以使用`@EnableWebMvc`注解启用MVC配置
```java
@Configuration
@EnableWebMvc
public class WebConfig {
}
```
2. 可以使用`<mvc:annotation-driven>`xml配置启用MVC配置
```xml
<mvc:annotation-driven/>
```

## 2. Api
可以使用实现`WebMvcConfigurer`进行配置
```java
@Configuration
@EnableWebMvc
public class WebConfig implements WebMvcConfigurer {

    // Implement configuration methods...
}
```

## 3. 类型
Spring MVC已经包含了数字转换`@NumberFormat`，时间转换`@DateTimeFormat`。我们可以自定义类型转换:
```java
 @Override
 public void addFormatters(FormatterRegistry registry) {
     // ...
 }
```

## 4. 校验
```java
@Override
    public Validator getValidator() {
        // ...
    }
```

## 5. 拦截器
注册拦截器：
```java 
@Override
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new LocaleChangeInterceptor());
    registry.addInterceptor(new ThemeChangeInterceptor()).addPathPatterns("/**").excludePathPatterns("/admin/**");
    registry.addInterceptor(new SecurityInterceptor()).addPathPatterns("/secure/*");
}
```

## 6. 内容
```java
@Override
public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
    configurer.mediaType("json", MediaType.APPLICATION_JSON);
    configurer.mediaType("xml", MediaType.APPLICATION_XML);
}
```

## 7. 消息
可以重写`configureMessageConverters()`或`extendMessageConverters() `来自定义`HttpMessageConverter`实现数据转换
```java
@Configuration
@EnableWebMvc
public class WebConfiguration implements WebMvcConfigurer {

    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        Jackson2ObjectMapperBuilder builder = new Jackson2ObjectMapperBuilder()
                .indentOutput(true)
                .dateFormat(new SimpleDateFormat("yyyy-MM-dd"))
                .modulesToInstall(new ParameterNamesModule());
        converters.add(new MappingJackson2HttpMessageConverter(builder.build()));
        converters.add(new MappingJackson2XmlHttpMessageConverter(builder.createXmlMapper(true).build()));
    }
}
```
```xml
<mvc:annotation-driven>
    <mvc:message-converters>
        <bean class="org.springframework.http.converter.json.MappingJackson2HttpMessageConverter">
            <property name="objectMapper" ref="objectMapper"/>
        </bean>
        <bean class="org.springframework.http.converter.xml.MappingJackson2XmlHttpMessageConverter">
            <property name="objectMapper" ref="xmlMapper"/>
        </bean>
    </mvc:message-converters>
</mvc:annotation-driven>

<bean id="objectMapper" class="org.springframework.http.converter.json.Jackson2ObjectMapperFactoryBean"
      p:indentOutput="true"
      p:simpleDateFormat="yyyy-MM-dd"
      p:modulesToInstall="com.fasterxml.jackson.module.paramnames.ParameterNamesModule"/>

<bean id="xmlMapper" parent="objectMapper" p:createXmlMapper="true"/>
```

## 8. 视图
```java
@Override
public void addViewControllers(ViewControllerRegistry registry) {
    registry.addViewController("/").setViewName("home");
}
```
```xml
<mvc:view-controller path="/" view-name="home"/>
```

## 9. 解析器
```java
@Override
public void addViewControllers(ViewControllerRegistry registry) {
    registry.addViewController("/").setViewName("home");
}
```

## 10. 静态文件
```java
@Override
public void addResourceHandlers(ResourceHandlerRegistry registry) {
    registry.addResourceHandler("/resources/**")
        .addResourceLocations("/public", "classpath:/static/")
        .setCachePeriod(31556926);
}
```

## 11. 默认Servlet
```java
@Override
public void configureDefaultServletHandling(DefaultServletHandlerConfigurer configurer) {
    configurer.enable();
}
```

## 12. 路径匹配
```java
@Override
public void configurePathMatch(PathMatchConfigurer configurer) {
    configurer
        .setUseSuffixPatternMatch(true)
        .setUseTrailingSlashMatch(false)
        .setUseRegisteredSuffixPatternMatch(true)
        .setPathMatcher(antPathMatcher())
        .setUrlPathHelper(urlPathHelper())
        .addPathPrefix("/api",
                HandlerTypePredicate.forAnnotation(RestController.class));
}
```

## 13. more
`@EnableWebMvc`为程序提供配置，检测委托`WebMvcConfigurer`实现自定义配置。
去除`@EnableWebMvc`,`WebMvcConfigurer`，继承扩展`DelegatingWebMvcConfiguration`可实现更多高级配置。
```java
@Configuration
public class WebConfig extends DelegatingWebMvcConfiguration {

    // ...
}
```
xml:
```java
@Component
public class MyPostProcessor implements BeanPostProcessor {

    public Object postProcessBeforeInitialization(Object bean, String name) throws BeansException {
        // ...
    }
}
```
