---
title: 浅析Spring MVC:DispatcherServlet
date: 2018-04-01 10:00:00
categories: 
- Spring MVC
tags: 
- Spring MVC
---

使用Spring Web MVC，开发者可以直接访问官方文档[Spring Web MVC文档Version 5.2.1.RELEASE](https://docs.spring.io/spring/docs/5.2.1.RELEASE/spring-framework-reference/web.html#mvc)，本文及Spring MVC系列文章都参考于此文档及源码。

<!-- more -->

先看文档是如何介绍Spring MVC的：

`Spring Web MVC` is the original web framework built on the `Servlet API` and has been included in the Spring Framework from the very beginning. The formal name, “Spring Web MVC,” comes from the name of its source module (spring-webmvc), but it is more commonly known as “Spring MVC”

同时也提到到了`Spring WebFlux`。

## 1. Spring MVC引入

这里使用maven：
```xml
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-webmvc</artifactId>
    <version>${spring.version}</version>
</dependency>
```
## 2. DispatcherServlet
### 1. 声明
The `DispatcherServlet`, as any `Servlet`, needs to be declared and mapped according to the Servlet specification by using `Java configuration` or in `web.xml`

可以看到需要通过`Java configuration`或者`web.xml`来申明配置`DispatcherServlet`，也就是Web容器寻找的入口。

1. Java configuration
```java
public class MyWebApplicationInitializer implements WebApplicationInitializer {

@Override
public void onStartup(ServletContext servletCxt) {

	// Load Spring web application configuration
	AnnotationConfigWebApplicationContext ac = new AnnotationConfigWebApplicationContext();
	ac.register(AppConfig.class);
	ac.refresh();

	// Create and register the DispatcherServlet
	DispatcherServlet servlet = new DispatcherServlet(ac);
	ServletRegistration.Dynamic registration = servletCxt.addServlet("app", servlet);
	registration.setLoadOnStartup(1);
	registration.addMapping("/app/*");
}
}
```
2. web.xml
```xml
<web-app>

    <listener>
        <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
    </listener>

    <context-param>
        <param-name>contextConfigLocation</param-name>
        <param-value>/WEB-INF/app-context.xml</param-value>
    </context-param>

    <servlet>
        <servlet-name>app</servlet-name>
        <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
        <init-param>
            <param-name>contextConfigLocation</param-name>
            <param-value></param-value>
        </init-param>
        <load-on-startup>1</load-on-startup>
    </servlet>

    <servlet-mapping>
        <servlet-name>app</servlet-name>
        <url-pattern>/app/*</url-pattern>
    </servlet-mapping>

</web-app>
```

### 2. 上下文

`DispatcherServlet` expects a `WebApplicationContext` (an extension of a plain ApplicationContext) for its own configuration。

`WebApplicationContext`和`ServletContext`通过监听器实现共存亡的关系。可以从源码中看到：

`ContextLoaderListener`,`ContextCleanupListener`等实现了`Servlet`中的`ServletContextListener`。

例如：`ContextLoaderListener`中：

```java
public class ContextLoaderListener extends ContextLoader implements ServletContextListener {

	public ContextLoaderListener() {
	}

	public ContextLoaderListener(WebApplicationContext context) {
		super(context);
	}

	/**
	 * 项目启动，创建ServletContext时初始化WebApplicationContext
	 */
	@Override
	public void contextInitialized(ServletContextEvent event) {
		initWebApplicationContext(event.getServletContext());
	}

	/**
	 * 项目关闭，销毁ServletContext时调用ContextCleanupListener销毁清理WebApplicationContext
	 */
	@Override
	public void contextDestroyed(ServletContextEvent event) {
		closeWebApplicationContext(event.getServletContext());
		ContextCleanupListener.cleanupAttributes(event.getServletContext());
	}

}
```

### 2. 实例

可以在源码中看到初始化`DispatcherServlet`时使用`onRefresh`方法，`onRefresh`又调用了`initStrategies`，在`initStrategies`中初始化了这9个实例:

```java
initMultipartResolver(context);
initLocaleResolver(context);
initThemeResolver(context);
initHandlerMappings(context);
initHandlerAdapters(context);
initHandlerExceptionResolvers(context);
initRequestToViewNameTranslator(context);
initViewResolvers(context);
initFlashMapManager(context);

```

可以自定义扩张或者替换这些组件。当没有配置时，会调用默认的配置。

例如在`initHandlerAdapters`中，没有找到自定义配置的`handlerAdapters`则会调用`getDefaultStrategies`获取默认配置：

```java
if (this.handlerAdapters == null) {
	this.handlerAdapters = getDefaultStrategies(context, HandlerAdapter.class);
	if (logger.isTraceEnabled()) {
		logger.trace("No HandlerAdapters declared for servlet '" + getServletName() +
				"': using default strategies from DispatcherServlet.properties");
	}
}
```

再看一下如何获取的默认配置：
```java

//获取默认配置属性
//Create a List of default strategy objects for the given strategy interface.
protected <T> List<T> getDefaultStrategies(ApplicationContext context, Class<T> strategyInterface) {
	String key = strategyInterface.getName();
	String value = defaultStrategies.getProperty(key);
	if (value != null) {
		String[] classNames = StringUtils.commaDelimitedListToStringArray(value);
		List<T> strategies = new ArrayList<>(classNames.length);
		for (String className : classNames) {
			try {
				Class<?> clazz = ClassUtils.forName(className, DispatcherServlet.class.getClassLoader());
				Object strategy = createDefaultStrategy(context, clazz);
				strategies.add((T) strategy);
			}
			catch (ClassNotFoundException ex) {
				throw new BeanInitializationException(
						"Could not find DispatcherServlet's default strategy class [" + className +
						"] for interface [" + key + "]", ex);
			}
			catch (LinkageError err) {
				throw new BeanInitializationException(
						"Unresolvable class definition for DispatcherServlet's default strategy class [" +
						className + "] for interface [" + key + "]", err);
			}
		}
		return strategies;
	}
	else {
		return new LinkedList<>();
	}
}
```

可以看到`defaultStrategies`作为配置：

```java
private static final Properties defaultStrategies;

static {
	// Load default strategy implementations from properties file.
	// This is currently strictly internal and not meant to be customized
	// by application developers.
	try {
		ClassPathResource resource = new ClassPathResource(DEFAULT_STRATEGIES_PATH, DispatcherServlet.class);
		defaultStrategies = PropertiesLoaderUtils.loadProperties(resource);
	}
	catch (IOException ex) {
		throw new IllegalStateException("Could not load '" + DEFAULT_STRATEGIES_PATH + "': " + ex.getMessage());
	}
}
```
而这里加载的`DEFAULT_STRATEGIES_PATH`可以在申明中找到：

```java
private static final String DEFAULT_STRATEGIES_PATH = "DispatcherServlet.properties";
```

也就是说会通过默认`DispatcherServlet.properties`配置文件来初始化默认实例。


### 3. 配置

上面说到需要通过`WebApplicationInitializer`或者`web.xml`配置容器。

An abstract base class implementation of `WebApplicationInitializer` named `AbstractDispatcherServletInitializer` makes it even easier to register the DispatcherServlet by overriding methods to specify the servlet mapping and the location of the DispatcherServlet configuration.

可以继承`AbstractDispatcherServletInitializer`注册一个Servlet。


```java
public class MyWebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {

	@Override
	protected Class<?>[] getRootConfigClasses() {
		return null;
	}

	@Override
	protected Class<?>[] getServletConfigClasses() {
		return new Class<?>[] { MyWebConfig.class };
	}

	@Override
	protected String[] getServletMappings() {
		return new String[] { "/" };
	}

	//添加Filter 实例并将其自动映射快捷方法
	@Override
	protected Filter[] getServletFilters() {
		return new Filter[] {
			new HiddenHttpMethodFilter(), new CharacterEncodingFilter() };
	}
}
```

如果使用xml配置，也可以使用`AbstractDispatcherServletInitializer`。


如果需要进一步的自定义`DispatcherServlet`，可以重写`createDispatcherServlet`方法。

### 4. 处理一个请求

可以在源码中看到如何处理一个请求的。在`DispatcherServlet`中`doService`方法：

```java
protected void doService(HttpServletRequest request, HttpServletResponse response) throws Exception {
		logRequest(request);
        
	//把request中数据备份到attributesSnapshot中，以便还原
	Map<String, Object> attributesSnapshot = null;
	if (WebUtils.isIncludeRequest(request)) {
		attributesSnapshot = new HashMap<>();
		Enumeration<?> attrNames = request.getAttributeNames();
		while (attrNames.hasMoreElements()) {
			String attrName = (String) attrNames.nextElement();
			if (this.cleanupAfterInclude || attrName.startsWith(DEFAULT_STRATEGIES_PREFIX)) {
				attributesSnapshot.put(attrName, request.getAttribute(attrName));
			}
		}
	}

	// request设置WebApplicationContext属性
	request.setAttribute(WEB_APPLICATION_CONTEXT_ATTRIBUTE, getWebApplicationContext());
	// 绑定解析器
	request.setAttribute(LOCALE_RESOLVER_ATTRIBUTE, this.localeResolver);
	request.setAttribute(THEME_RESOLVER_ATTRIBUTE, this.themeResolver);
	request.setAttribute(THEME_SOURCE_ATTRIBUTE, getThemeSource());

	if (this.flashMapManager != null) {
		FlashMap inputFlashMap = this.flashMapManager.retrieveAndUpdate(request, response);
		if (inputFlashMap != null) {
			request.setAttribute(INPUT_FLASH_MAP_ATTRIBUTE, Collections.unmodifiableMap(inputFlashMap));
		}
		request.setAttribute(OUTPUT_FLASH_MAP_ATTRIBUTE, new FlashMap());
		request.setAttribute(FLASH_MAP_MANAGER_ATTRIBUTE, this.flashMapManager);
	}

	try {
		//交由doDispatch处理请求
		doDispatch(request, response);
	}
	finally {
		//还原request
		if (!WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted()) {
			// Restore the original attribute snapshot, in case of an include.
			if (attributesSnapshot != null) {
				restoreAttributesAfterInclude(request, attributesSnapshot);
			}
		}
	}
}
```

### 5. 拦截

通过实现`HandlerMapping`，并且使用`setter`注册可以实现处理程序的拦截器。

1. preHandle(..)：执行实际的处理程序之前

2. postHandle(..)：处理程序执行后

3. afterCompletion(..)：完整请求完成后

### 6. 异常

if an exception occurs during request mapping or is thrown from a request handler (such as a @Controller), the DispatcherServlet delegates to a chain of HandlerExceptionResolver beans to resolve the exception and provide alternative handling, which is typically an error response.

如果异常在请求映射或者期间发生，`DispatcherServlet`会委托`HandlerExceptionResolver`来处理。

`HandlerExceptionResolver`的实现有：

1. SimpleMappingExceptionResolver: 异常类名称和错误视图名称之间的映射。

2. DefaultHandlerExceptionResolver: 解决了Spring MVC引发的异常，并将它们映射到HTTP状态代码。

3. ResponseStatusExceptionResolver: 使用@ResponseStatus注释解决异常，并根据注释中的值将它们映射到HTTP状态代码。

4. ExceptionHandlerExceptionResolver: 通过调用@ExceptionHandlera @Controller或 @ControllerAdviceclass中的方法来解决异常。

可以在Spring configuration设置`HandlerExceptionResolver beans`,并且能够设置`order`优先级来处理异常。也可以使用`@ResponseStatus`,`@ExceptionHandler`

可以在定义它的错误页面`<location>/error</location>`

我们可以看到Spring MVC提供了一个抽象方法`AbstractHandlerExceptionResolver`，他实现了`HandlerExceptionResolver`,当然就可以通过`AbstractHandlerExceptionResolver`来自定义异常的解析。从来做到项目异常的统一管理。

### 7. 视图

在处理请求`doService`中，可以看到`request`绑定了一个视图解析器`ViewResolver`。

在源码包`view`中，可以看到`freemarker`,`groovy`,`json`,`script`,`xml`。

可以申明多个解析器，并通过设置`order`链接。

可以`redirect`,`forward`

### 5. 国际化

Spirng MVC通过`LocaleResolver`对象完成国际化。我们也在`doService`看到`request`绑定了一个解析器`LocaleResolver`。可以使用`RequestContext.getLocale()`

可以从`i18n`包中如下解析器：

1. Time Zone: 获取请求语言时区环境
2. Header Resolver: 检查请求头信息，如`accept-language`
3. Cookie Resolver: 请求Cookie解析，可以通过`CookieLocaleResolver`设置属性

```xml

<bean id="localeResolver" class="org.springframework.web.servlet.i18n.CookieLocaleResolver">

    <property name="cookieName" value="clientlanguage"/>

    <!-- in seconds. If set to -1, the cookie is not persisted (deleted when browser shuts down) -->
    <property name="cookieMaxAge" value="100000"/>
    <property name="cookiePath" value="">

</bean>

```
4. Session Resolver: Session解析
5. Locale Interceptor: 拦截器，可以自定义添加`LocaleChangeInterceptor`来改变语言区域环境

```xml
<bean id="localeChangeInterceptor"
        class="org.springframework.web.servlet.i18n.LocaleChangeInterceptor">
    <property name="paramName" value="siteLanguage"/>
</bean>

<bean id="localeResolver"
        class="org.springframework.web.servlet.i18n.CookieLocaleResolver"/>

<bean id="urlMapping"
        class="org.springframework.web.servlet.handler.SimpleUrlHandlerMapping">
    <property name="interceptors">
        <list>
            <ref bean="localeChangeInterceptor"/>
        </list>
    </property>
    <property name="mappings">
        <value>/**/*.view=someController</value>
    </property>
</bean>
```


### 6. 主题

需要实现`ThemeSource`接口，当然他提供了一个抽象类`AbstractThemeResolver`便于我们实现。

Spring还提供了`ThemeChangeInterceptor`进行更改。

### 7. Multipart Resolver

`multipart/form-data`

### 8. 日志

`enableLoggingRequestDetails`

