---
title: Spring Mvc中的EnableWebMvc
date: 2021-04-07 09:15:16
categories: 
- Mybatis
tags: 
- Mybatis
---
本文分享了Mybatis-Mapper扫描及代理 
<!-- more -->



@EnableWebMvc在Spring Mvc项目负责创建”Mvc”项目中相关组件以及载入应用配置等。

@EnableWebMvc源码如下:

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@Documented
@Import(DelegatingWebMvcConfiguration.class)
public @interface EnableWebMvc {
}

@EnableWebMvc通过@Import导入DelegatingWebMvcConfiguration类。DelegatingWebMvcConfiguration继承WebMvcConfigurationSupport，调用setConfigurers方法获取应用创建的WebMvcConfigurer实例，并通过以WebMvcConfigurerComposite来代理这些实例，从而获取应用自定义配置。

@Configuration
public class DelegatingWebMvcConfiguration extends WebMvcConfigurationSupport {

    // 通过 WebMvcConfigurerComposite 管理用户自定义的 WebMvcConfigurer
    private final WebMvcConfigurerComposite configurers = new WebMvcConfigurerComposite();

    @Autowired(required = false)
    public void setConfigurers(List<WebMvcConfigurer> configurers) {
       if (!CollectionUtils.isEmpty(configurers)) {
           this.configurers.addWebMvcConfigurers(configurers);
       }
    }

    @Override
    protected void configurePathMatch(PathMatchConfigurer configurer) {
    	this.configurers.configurePathMatch(configurer);
    }

    ...
}

DelegatingWebMvcConfiguration 的父类 WebMvcConfigurationSupport 负责创建”Mvc”需要的一些组件，如ResourceUrlProvider, HandlerMapping等。

public class WebMvcConfigurationSupport implements ApplicationContextAware, ServletContextAware {

    ...

    @Bean
    public ResourceUrlProvider mvcResourceUrlProvider() {
    	ResourceUrlProvider urlProvider = new ResourceUrlProvider();
    	UrlPathHelper pathHelper = getPathMatchConfigurer().getUrlPathHelper();
    	if (pathHelper != null) {
    		urlProvider.setUrlPathHelper(pathHelper);
    	}
    	PathMatcher pathMatcher = getPathMatchConfigurer().getPathMatcher();
    	if (pathMatcher != null) {
    		urlProvider.setPathMatcher(pathMatcher);
    	}
    	return urlProvider;
    }

    @Bean
    @Nullable
    public HandlerMapping defaultServletHandlerMapping() {
    	Assert.state(this.servletContext != null, "No ServletContext set");
    	DefaultServletHandlerConfigurer configurer = new DefaultServletHandlerConfigurer(this.servletContext);
    	configureDefaultServletHandling(configurer);
    	return configurer.buildHandlerMapping();
    }

    // 由 ApplicationContextAwareProcessor 注入
    @Override
    public void setApplicationContext(@Nullable ApplicationContext applicationContext) {
    	this.applicationContext = applicationContext;
    }

    // 由 ServletContextAwareProcessor 注入
    @Override
    public void setServletContext(@Nullable ServletContext servletContext) {
        this.servletContext = servletContext;
    }

    ...

}

因此在web项目中只需使用@EnableWebMvc注解即可实现项目自动配置。

Spring Mvc 请求处理流程可参考Spring MVC 自定义接口参数解析器。
