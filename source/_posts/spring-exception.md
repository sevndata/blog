---
title: Spring MVC自定义异常解析器及异常处理过程
date: 2019-07-07 09:15:16
categories: 
- Spring MVC
tags: 
- Spring MVC
---
本文分享了Spring MVC自定义异常解析及在源码中的处理过程
<!-- more -->
## 1. HandlerExceptionResolver
`Spring MVC`定义了`HandlerExceptionResolver`接口，实现该接口的类负责解析异常。
```java
public interface HandlerExceptionResolver {
  @Nullable
  ModelAndView resolveException(HttpServletRequest request, HttpServletResponse response, 
                        @Nullable Object handler, Exception ex);
}
```
## 2. 自定义异常解析
实现`HandlerExceptionResolver`接口并启用即可自定义异常解析器。
`Spring MVC`中的`AbstractHandlerExceptionResolver`实现了该接口，所以继承此类即可自定义异常处理逻辑。
```java
@Component
public class GlobalHandlerExceptionResolver extends AbstractHandlerExceptionResolver {

  private final HandlerExceptionResolver defaultExceptionResolver;

  public GlobalHandlerExceptionResolver() {
          defaultExceptionResolver = new DefaultHandlerExceptionResolver();
  }

  @Override
  protected ModelAndView doResolveException(HttpServletRequest request,
      HttpServletResponse response, Object handler, Exception ex) {
    Exception throwable = ex;
    ModelAndView modelAndView = new ModelAndView()
    if (throwable instanceof NullPointerException) {
        //发生NullPointerException时，response写入操作失败等自定义逻辑
    }
    //其他的异常交还给spring的异常解析器解析
    else{
        modelAndView=this.defaultExceptionResolver.resolveException(request, response, handler, ex);
    }
    return modelAndView;
  }
}
```
## 3. 初始化过程

查看`AbstractHandlerExceptionResolver`的子类和`DispatcherServlet.properties`，`Spring MVC`默认配置异常解析器有：`ExceptionHandlerExceptionResolver`,`DefaultHandlerExceptionResolver`,`ResponseStatusExceptionResolver`。

在`DispatcherServlet`中初始化了异常解析器（`initHandlerExceptionResolvers`），如下：
DispatcherServlet：
```java

private boolean detectAllHandlerExceptionResolvers = true;

private void initHandlerExceptionResolvers(ApplicationContext context) {
  this.handlerExceptionResolvers = null;
  //默认
  if (this.detectAllHandlerExceptionResolvers) {
    // 寻找HandlerExceptionResolvers，包括父容器
    Map<String, HandlerExceptionResolver> matchingBeans = BeanFactoryUtils
        .beansOfTypeIncludingAncestors(context, HandlerExceptionResolver.class, true, false);
    if (!matchingBeans.isEmpty()) {
      this.handlerExceptionResolvers = new ArrayList<>(matchingBeans.values());
      // sorted order排序
      AnnotationAwareOrderComparator.sort(this.handlerExceptionResolvers);
    }
  }
  else {
    try {
      //寻找名字叫handlerExceptionResolver的类
      HandlerExceptionResolver her =
          context.getBean(HANDLER_EXCEPTION_RESOLVER_BEAN_NAME, HandlerExceptionResolver.class);
      this.handlerExceptionResolvers = Collections.singletonList(her);
    }
    catch (NoSuchBeanDefinitionException ex) {
      // Ignore, no HandlerExceptionResolver is fine too.
    }
  }

  // 如果没有则创建默认解析器，至少找到一个HandlerExceptionResolvers被注册
  if (this.handlerExceptionResolvers == null) {
    this.handlerExceptionResolvers = getDefaultStrategies(context, HandlerExceptionResolver.class);
    if (logger.isTraceEnabled()) {
      logger.trace("No HandlerExceptionResolvers declared in servlet '" + getServletName() +
          "': using default strategies from DispatcherServlet.properties");
    }
  }
}
```
默认创建过程：getDefaultStrategies(context, HandlerExceptionResolver.class)
```java
protected <T> List<T> getDefaultStrategies(ApplicationContext context, Class<T> strategyInterface) {
  String key = strategyInterface.getName();
  //从DispatcherServlet.properties读取默认配置
  //DispatcherServlet.properties中的配置为ExceptionHandlerExceptionResolver，ResponseStatusExceptionResolver，DefaultHandlerExceptionResolver
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

## 4. 处理异常

`DispatcherServlet`通过`doDispatch`处理一个请求。在`doDispatch`最后调用`processDispatchResult`进行页面渲染，返回正确结果或者异常结果。
```java
private void processDispatchResult(HttpServletRequest request, HttpServletResponse response,
			@Nullable HandlerExecutionChain mappedHandler, @Nullable ModelAndView mv,
			@Nullable Exception exception) throws Exception {

  boolean errorView = false;
  //如果有异常，如果为ModelAndViewDefiningException异常直接返回，其他异常通过processHandlerException构建view
  if (exception != null) {
    if (exception instanceof ModelAndViewDefiningException) {
      logger.debug("ModelAndViewDefiningException encountered", exception);
      mv = ((ModelAndViewDefiningException) exception).getModelAndView();
    }
    else {
      Object handler = (mappedHandler != null ? mappedHandler.getHandler() : null);
      mv = processHandlerException(request, response, handler, exception);
      errorView = (mv != null);
    }
  }
  if (mv != null && !mv.wasCleared()) {
    render(mv, request, response);
    if (errorView) {
      WebUtils.clearErrorRequestAttributes(request);
    }
  }
  else {
    if (logger.isTraceEnabled()) {
      logger.trace("No view rendering, null ModelAndView returned.");
    }
  }

  if (WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted()) {
    return;
  }
  if (mappedHandler != null) {
    mappedHandler.triggerAfterCompletion(request, response, null);
  }
}
```
processHandlerException:
```java
protected ModelAndView processHandlerException(HttpServletRequest request, HttpServletResponse response,
			@Nullable Object handler, Exception ex) throws Exception {
  //设置content types
  // Success and error responses may use different content types
  request.removeAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE);
  //找异常解析器
  //Check registered HandlerExceptionResolvers...
  //调用解析器resolveException方法
  ModelAndView exMv = null;
  if (this.handlerExceptionResolvers != null) {
    for (HandlerExceptionResolver resolver : this.handlerExceptionResolvers) {
      //异常解析器中的resolveException
      exMv = resolver.resolveException(request, response, handler, ex);
      if (exMv != null) {
        break;
      }
    }
  }
  if (exMv != null) {
    if (exMv.isEmpty()) {
      request.setAttribute(EXCEPTION_ATTRIBUTE, ex);
      return null;
    }
    // We might still need view name translation for a plain error model...
    // 有view返回，没有则设置默认view
    if (!exMv.hasView()) {
      String defaultViewName = getDefaultViewName(request);
      if (defaultViewName != null) {
        exMv.setViewName(defaultViewName);
      }
    }
    if (logger.isTraceEnabled()) {
      logger.trace("Using resolved error view: " + exMv, ex);
    }
    else if (logger.isDebugEnabled()) {
      logger.debug("Using resolved error view: " + exMv);
    }
    //设置request
    WebUtils.exposeErrorRequestAttributes(request, ex, getServletName());
    return exMv;
  }

  throw ex;
}
```
下篇文章将分享默认异常解析器的处理过程`resolveException`。
