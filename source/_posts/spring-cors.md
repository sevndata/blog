---
title: Spring CORS原理解析
date: 2021-01-25 16:39:11
categories: 
- Spring
- CORS
tags: 
- Spring
- CORS
---
本文分享了跨域，CORS原理解析等内容。阐述了CORS在Spring MVC和Spring Security中实现原理。
<!-- more -->

## 1. 同源策略
同源策略是一种约定，缺少同源策略浏览器容易受到XSS，CSFR等攻击，为了安全，浏览器会限制非同源的请求。同源为协议，域名，端口三者相同，任意一者不同则为非同源。
## 2. 跨域方案
1. 通过`nginx`代理转发。避开跨域请求，使浏览器访问同源，`nginx`转发到不同源。
2. JSONP，利用`Ajax`请求会受到同源策略限制，而`script`标签请求不会，绕过同源策略。但只支持`GET`，同时是不安全的。
3. CORS是跨域资源共享，对于简单请求只要服务器返回正确的响应头即可，非简单请求需要先进行预检请求，要求首先使用`Fetch`发起`OPTIONS`预检请求到服务器，通过`Access-Control-Allow-Origin`以获知服务器是否允许该请求。
4. websocket，document.domain等其他方案。

## 3. CORS简介

跨域资源共享(CORS) 是一种机制，它使用额外的 HTTP 头来告诉浏览器 让运行在一个 origin (domain) 上的Web应用被准许访问来自不同源服务器上的指定的资源。当一个资源从与该资源本身所在的服务器不同的域、协议或端口请求一个资源时，资源会发起一个跨域 HTTP 请求。 跨域资源共享（ CORS ）机制允许 Web 应用服务器进行跨域访问控制，从而使跨域数据传输得以安全进行。现代浏览器支持在 API 容器中（例如 XMLHttpRequest 或 Fetch ）使用 CORS，以降低跨域 HTTP 请求所带来的风险。

通常配置`CorsConfigurationSource`即可实现CORS设置。

```java
@Bean
public CorsConfigurationSource corsConfigurationSource() {
  CorsConfiguration configuration = new CorsConfiguration();
  configuration.applyPermitDefaultValues();
  configuration.addAllowedHeader("Authentication-Info");
  configuration.addExposedHeader("Authentication-Info");
  configuration.setAllowCredentials(true);
  UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
  source.registerCorsConfiguration("/**", configuration);
  return source;
}
```

## 4. Spring MVC

当`OPTIONS`预检请求发生时，`HandlerMapping.getHandler`会得到`PreFlightHandler`作为请求`handler`。更多详细内容可先理解`Spring MVC`如何处理一个请求。

`Spring MVC`是如何获取的该`handler`:
```java
public final HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception {
	Object handler = getHandlerInternal(request);
	if (handler == null) {
		handler = getDefaultHandler();
	}
	if (handler == null) {
		return null;
	}
	// Bean name or resolved handler?
	if (handler instanceof String) {
		String handlerName = (String) handler;
		handler = obtainApplicationContext().getBean(handlerName);
	}

	HandlerExecutionChain executionChain = getHandlerExecutionChain(handler, request);

	if (logger.isTraceEnabled()) {
		logger.trace("Mapped to " + handler);
	}
	else if (logger.isDebugEnabled() && !request.getDispatcherType().equals(DispatcherType.ASYNC)) {
		logger.debug("Mapped to " + executionChain.getHandler());
	}
	//如果是预检请求则获取HandlerExecutionChain
	if (hasCorsConfigurationSource(handler)) {
		//从配置的corsConfigurationSource中获取CorsConfiguration
		CorsConfiguration config = (this.corsConfigurationSource != null ? this.corsConfigurationSource.getCorsConfiguration(request) : null);
		//从注解中获取CorsConfiguration
		CorsConfiguration handlerConfig = getCorsConfiguration(handler, request);
		//CorsConfiguration选取，优先获取corsConfigurationSource中CorsConfiguration
		config = (config != null ? config.combine(handlerConfig) : handlerConfig);
		//配置获取CorsHandlerExecutionChain,详细查看下一块代码
		executionChain = getCorsHandlerExecutionChain(request, executionChain, config);
	}

	return executionChain;
}
```

```java
protected HandlerExecutionChain getCorsHandlerExecutionChain(HttpServletRequest request,
															 HandlerExecutionChain chain, @Nullable CorsConfiguration config) {
	//是否是预检请求
	//return (HttpMethod.OPTIONS.matches(request.getMethod()) &&
	//		request.getHeader(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD) != null);   
	//public static final String ACCESS_CONTROL_REQUEST_METHOD = "Access-Control-Request-Method";         
	if (CorsUtils.isPreFlightRequest(request)) {
		//创建HandlerExecutionChain
		HandlerInterceptor[] interceptors = chain.getInterceptors();
		chain = new HandlerExecutionChain(new PreFlightHandler(config), interceptors);
	}
	else {
		//添加CorsInterceptor
		chain.addInterceptor(0, new CorsInterceptor(config));
	}
	//PreFlightHandler和CorsInterceprtor都是调用corsProcessor.processRequest
	return chain;
}
```

`CorsProcessor`是一个`interface`，他的默认实现是`DefaultCorsProcessor`，来看`DefaultCorsProcessor`:

```java
public boolean processRequest(@Nullable CorsConfiguration config, HttpServletRequest request,
							  HttpServletResponse response) throws IOException {
	//Origin
	response.addHeader(HttpHeaders.VARY, HttpHeaders.ORIGIN);
	//Access-Control-Request-Method
	response.addHeader(HttpHeaders.VARY, HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD);
	//AAccess-Control-Request-Headers
	response.addHeader(HttpHeaders.VARY, HttpHeaders.ACCESS_CONTROL_REQUEST_HEADERS);

	//非Cors请求通过
	if (!CorsUtils.isCorsRequest(request)) {
		return true;
	}
	//已经包含了Access-Control-Allow-Origin通过
	if (response.getHeader(HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN) != null) {
		logger.trace("Skip: response already contains \"Access-Control-Allow-Origin\"");
		return true;
	}

	boolean preFlightRequest = CorsUtils.isPreFlightRequest(request);
	if (config == null) {
		if (preFlightRequest) {
			//没有配置CorsConfiguration的预请求返回403
			//response.setStatusCode(HttpStatus.FORBIDDEN);  FORBIDDEN(403, "Forbidden")
			//response.getBody().write("Invalid CORS request".getBytes(StandardCharsets.UTF_8));
			//response.flush();
			rejectRequest(new ServletServerHttpResponse(response));
			return false;
		}
		//否则通过
		else {
			return true;
		}
	}
	//执行具体处理，详细如下
	return handleInternal(new ServletServerHttpRequest(request), new ServletServerHttpResponse(response), config, preFlightRequest);
}
```
```java
protected boolean handleInternal(ServerHttpRequest request, ServerHttpResponse response,
								 CorsConfiguration config, boolean preFlightRequest) throws IOException {
	//该方法主要为检查请求是否允许，并作出了不同动作如：
	//rejectRequest 403 Reject:origin is not allowed
	//通过请求设置AccessControlAllowMethods等
	//在下方代码中详细描述checkOrigin，如何确认请求通过
	String requestOrigin = request.getHeaders().getOrigin();
	String allowOrigin = checkOrigin(config, requestOrigin);
	HttpHeaders responseHeaders = response.getHeaders();

	if (allowOrigin == null) {
		logger.debug("Reject: '" + requestOrigin + "' origin is not allowed");
		rejectRequest(response);
		return false;
	}

	HttpMethod requestMethod = getMethodToUse(request, preFlightRequest);
	List<HttpMethod> allowMethods = checkMethods(config, requestMethod);
	if (allowMethods == null) {
		logger.debug("Reject: HTTP '" + requestMethod + "' is not allowed");
		rejectRequest(response);
		return false;
	}

	List<String> requestHeaders = getHeadersToUse(request, preFlightRequest);
	List<String> allowHeaders = checkHeaders(config, requestHeaders);
	if (preFlightRequest && allowHeaders == null) {
		logger.debug("Reject: headers '" + requestHeaders + "' are not allowed");
		rejectRequest(response);
		return false;
	}

	responseHeaders.setAccessControlAllowOrigin(allowOrigin);

	if (preFlightRequest) {
		responseHeaders.setAccessControlAllowMethods(allowMethods);
	}

	if (preFlightRequest && !allowHeaders.isEmpty()) {
		responseHeaders.setAccessControlAllowHeaders(allowHeaders);
	}

	if (!CollectionUtils.isEmpty(config.getExposedHeaders())) {
		responseHeaders.setAccessControlExposeHeaders(config.getExposedHeaders());
	}

	if (Boolean.TRUE.equals(config.getAllowCredentials())) {
		responseHeaders.setAccessControlAllowCredentials(true);
	}

	if (preFlightRequest && config.getMaxAge() != null) {
		responseHeaders.setAccessControlMaxAge(config.getMaxAge());
	}

	response.flush();
	return true;
}
```

检查请求Origin:
```java
public String checkOrigin(@Nullable String requestOrigin) {
	//检查请求Origin，不存在则不通过
	if (!StringUtils.hasText(requestOrigin)) {
		return null;
	}
	//allowedOrigins为空不通过
	if (ObjectUtils.isEmpty(this.allowedOrigins)) {
		return null;
	}
	//如果allowedOrigins包含*
	//发出请求时，如果前端携带了cookie, 而服务器配置为*, 浏览器则会拒绝请求
	if (this.allowedOrigins.contains(ALL)) {
		//Access-Control-Allow-Credentials
		//如果allowCredentials配置为true，表示可携带验证信息如：cookie则返回*
		if (this.allowCredentials != Boolean.TRUE) {
			return ALL;
		}
		//返回来源地址
		else {
			return requestOrigin;
		}
	}
	//遍历允许地址，包含改地址则返回
	for (String allowedOrigin : this.allowedOrigins) {
		if (requestOrigin.equalsIgnoreCase(allowedOrigin)) {
			return requestOrigin;
		}
	}
	//该地址不允许
	return null;
}
```
## 5. Spring Security

在`Spring Security`中通常配置`HttpSecurity`。

```java
protected void configure(HttpSecurity http) throws Exception {
	http
		.authorizeRequests()
		.permitAll()
		.and()
		.cors();
}
```

只需调用`.cors()`就配置了允许跨域：
```java
public CorsConfigurer<HttpSecurity> cors() throws Exception {
	return getOrApply(new CorsConfigurer<>());
}
```

```java
private <C extends SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity>> C getOrApply(
			C configurer) throws Exception {
	C existingConfig = (C) getConfigurer(configurer.getClass());
	if (existingConfig != null) {
		return existingConfig;
	}
	return apply(configurer);
}
```

在`HttpSecurity`中获取了`CorsConfigurer`，`configure()`在`SecurityBuilder`build调用，详看`configure()`如何创建`CorsConfigurer`：

```java
public void configure(H http) {
	ApplicationContext context = http.getSharedObject(ApplicationContext.class);
	//获取CorsFilter
	CorsFilter corsFilter = getCorsFilter(context);
	if (corsFilter == null) {
		throw new IllegalStateException(
				"Please configure either a " + CORS_FILTER_BEAN_NAME + " bean or a "
						+ CORS_CONFIGURATION_SOURCE_BEAN_NAME + "bean.");
	}
	//添加CorsFilter到filter调用链
	http.addFilter(corsFilter);
}
```

获取`CorsFilter`,`CorsFilter`是`Spring MVC`中实现跨域一种方式。

```java
private CorsFilter getCorsFilter(ApplicationContext context) {
	//如果配置了configurationSource，从configurationSource中获取corsFilter
	if (this.configurationSource != null) {
		return new CorsFilter(this.configurationSource);
	}
	//从容器查corsFilter获取corsFilter
	boolean containsCorsFilter = context
			.containsBeanDefinition(CORS_FILTER_BEAN_NAME);
	if (containsCorsFilter) {
		return context.getBean(CORS_FILTER_BEAN_NAME, CorsFilter.class);
	}
	//从容器中查corsConfigurationSource创建corsFilter
	boolean containsCorsSource = context
			.containsBean(CORS_CONFIGURATION_SOURCE_BEAN_NAME);
	if (containsCorsSource) {
		CorsConfigurationSource configurationSource = context.getBean(
				CORS_CONFIGURATION_SOURCE_BEAN_NAME, CorsConfigurationSource.class);
		return new CorsFilter(configurationSource);
	}
	//从HandlerMappingIntrospector获取corsFilter
	boolean mvcPresent = ClassUtils.isPresent(HANDLER_MAPPING_INTROSPECTOR,
			context.getClassLoader());
	if (mvcPresent) {
		return MvcCorsFilter.getMvcCorsFilter(context);
	}
	return null;
}
```
`Spring Security`通过以上四种方式获取`corsFilter`,同样我们可以通过这四种方式进行跨域配置。
`Spring MVC`中`CorsFilter`同样是调用`DefaultCorsProcessor`中`processRequest`，和`PreFlightHandler`中一样。详细流程参考上方内容。

```java
public void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
			FilterChain filterChain) throws ServletException, IOException {
	CorsConfiguration corsConfiguration = this.configSource.getCorsConfiguration(request);
	boolean isValid = this.processor.processRequest(corsConfiguration, request, response);
	if (!isValid || CorsUtils.isPreFlightRequest(request)) {
		return;
	}
	filterChain.doFilter(request, response);
}
```  

