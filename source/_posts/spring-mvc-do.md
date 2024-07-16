---
title: 剖析Spring MVC:处理一个请求
date: 2018-11-27 11:05:56
categories: 
- Spring MVC
tags: 
- Spring MVC
---

剖析Spring MVC,介绍Spring MVC是如何处理请求的。

<!-- more -->

上一篇文章中，介绍了Spirng MVC的结构与创建过程，然后我们来看Spring MVC是如何处理请求的。

从`Servlet`中知道，处理请求是`HttpServlet`中`service`，`HttpServlet`中`doPost`,`doGet`等方法，从`service`路由到各个方法。详见`HttpServlet`代码。

在`HttpServletBean`中并没有重写这些方法。

## 1. service

在`FrameworkServlet`中重写了`HttpServlet`中`service`，`HttpServlet`中`doPost`,`doGet`等方法。
```java
public enum HttpMethod {
  GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS, TRACE;
}
```
1. `service`：添加`PATCH`，然后调用`processRequest`方法,其余则由父类`service`方法做处理。
2. `doGet`,`doPost`,`doPut`,`doDelete`：直接调用`processRequest`。
3. `doOptions`,`doTrace`：可有参数配置调用`processRequest`还是交给父类处理。
4. 没有重写`doHead`方法。

## 2. processRequest
来看`processRequest`方法
```java
protected final void processRequest(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException {

    long startTime = System.currentTimeMillis();
    Throwable failureCause = null;
    //获取原来保存的LocaleContext
    //private static final ThreadLocal<LocaleContext> localeContextHolder =
    //			new NamedThreadLocal<>("LocaleContext");
    //
    //	private static final ThreadLocal<LocaleContext> inheritableLocaleContextHolder =
    //			new NamedInheritableThreadLocal<>("LocaleContext");
    LocaleContext previousLocaleContext = LocaleContextHolder.getLocaleContext();
    //根据request中locale创建当前LocaleContext
    //new SimpleLocaleContext(request.getLocale())
    LocaleContext localeContext = buildLocaleContext(request);
    //获取原来保存的的RequestAttributes
    RequestAttributes previousAttributes = RequestContextHolder.getRequestAttributes();
    //根据request, response创建当前的ServletRequestAttributes
    //new ServletRequestAttributes(request, response);
    ServletRequestAttributes requestAttributes = buildRequestAttributes(request, response, previousAttributes);
    //异步请求
    WebAsyncManager asyncManager = WebAsyncUtils.getAsyncManager(request);
    //设置Interceptor
    asyncManager.registerCallableInterceptor(FrameworkServlet.class.getName(), new RequestBindingInterceptor());
    //初始化ContextHolders,设置当前的LocaleContext，ServletRequestAttributes到Holder中
    //if (localeContext != null) {
    //	LocaleContextHolder.setLocaleContext(localeContext, this.threadContextInheritable);
    //}
    //if (requestAttributes != null) {
    //	RequestContextHolder.setRequestAttributes(requestAttributes, this.threadContextInheritable);
    //}
    initContextHolders(request, localeContext, requestAttributes);

    try {
        //调用doService
        doService(request, response);
    }
    catch (ServletException | IOException ex) {
        failureCause = ex;
        throw ex;
    }
    catch (Throwable ex) {
        failureCause = ex;
        throw new NestedServletException("Request processing failed", ex);
    }

    finally {
        //request还原原始的LocaleContext，RequestAttributes
        resetContextHolders(request, previousLocaleContext, previousAttributes);
        if (requestAttributes != null) {
            requestAttributes.requestCompleted();
        }
        //日志
        logResult(request, response, failureCause, asyncManager);
        //发布时间消息
        publishRequestHandledEvent(request, response, startTime, failureCause);
    }
}
```

1. 可以通过`LocaleContextHolder`,`RequestContextHolder`获取到`LocaleContext`,`RequestAttributes`。
2. `publishRequestHandledEvent`,可以实现`ApplicationListener`来使用这个监听：
```java
@Component
public class RequestHandlerListener implements ApplicationListener<ServletRequestHandledEvent> {

    private final Logger log = LoggerFactory.getLogger(ServletRequestHandledEvent.class);

    @Override
    public void onApplicationEvent(ServletRequestHandledEvent event) {
        log.info("request event: {}",event);
    }
}
```

## 3. doService

可以看到交由`doService`请求：
```java
protected abstract void doService(HttpServletRequest request, HttpServletResponse response)
			throws Exception;
```
这是一个抽象方法，来看子类`DispatcherServlet`中实现：
```java
protected void doService(HttpServletRequest request, HttpServletResponse response) throws Exception {
    //日志
    logRequest(request);

    // Keep a snapshot of the request attributes in case of an include,
    // to be able to restore the original attributes after the include.
    //当include请求时，将Attribute保存到备份attributesSnapshot中
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

    // Make framework objects available to handlers and view objects.
    //设置WebApplicationContext，localeResolver属性
    request.setAttribute(WEB_APPLICATION_CONTEXT_ATTRIBUTE, getWebApplicationContext());
    request.setAttribute(LOCALE_RESOLVER_ATTRIBUTE, this.localeResolver);
    request.setAttribute(THEME_RESOLVER_ATTRIBUTE, this.themeResolver);
    request.setAttribute(THEME_SOURCE_ATTRIBUTE, getThemeSource());
    //对Redirect参数传递
    if (this.flashMapManager != null) {
        FlashMap inputFlashMap = this.flashMapManager.retrieveAndUpdate(request, response);
        if (inputFlashMap != null) {
            request.setAttribute(INPUT_FLASH_MAP_ATTRIBUTE, Collections.unmodifiableMap(inputFlashMap));
        }
        request.setAttribute(OUTPUT_FLASH_MAP_ATTRIBUTE, new FlashMap());
        request.setAttribute(FLASH_MAP_MANAGER_ATTRIBUTE, this.flashMapManager);
    }

    try {
        //交给doDispatch处理
        doDispatch(request, response);
    }
    finally {
        //还原，将attributesSnapshot设置回去
        if (!WebAsyncUtils.getAsyncManager(request).isConcurrentHandlingStarted()) {
            // Restore the original attribute snapshot, in case of an include.
            if (attributesSnapshot != null) {
                restoreAttributesAfterInclude(request, attributesSnapshot);
            }
        }
    }
}
```

## 4. doDispatch
```java
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) throws Exception {
    HttpServletRequest processedRequest = request;
    HandlerExecutionChain mappedHandler = null;
    boolean multipartRequestParsed = false;
    //异步请求
    WebAsyncManager asyncManager = WebAsyncUtils.getAsyncManager(request);

    try {
        ModelAndView mv = null;
        Exception dispatchException = null;

        try {
            //检查是否为上传请求，如果是则返回MultipartHttpServletRequest，不是则原样返回
            processedRequest = checkMultipart(request);
            //true:上传请求 false:飞上传请求
            multipartRequestParsed = (processedRequest != request);

            // Determine handler for the current request.
            //从HandlerMapping中获取Handler
            //if (this.handlerMappings != null) {
            //	for (HandlerMapping mapping : this.handlerMappings) {
            //		HandlerExecutionChain handler = mapping.getHandler(request);
            //		if (handler != null) {
            //			return handler;
            //		}
            //	}
            //}
            mappedHandler = getHandler(processedRequest);
            //未获取到抛出异常，SC_NOT_FOUND=404
            if (mappedHandler == null) {
                noHandlerFound(processedRequest, response);
                return;
            }

            // Determine handler adapter for the current request.
            //获取handler adapter
            HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());

            // Process last-modified header, if supported by the handler.
            // 处理GET、HEAD请求的Last-Modified
            String method = request.getMethod();
            boolean isGet = "GET".equals(method);
            if (isGet || "HEAD".equals(method)) {
                long lastModified = ha.getLastModified(request, mappedHandler.getHandler());
                //PRECONDITION_FAILED=412
                if (new ServletWebRequest(request, response).checkNotModified(lastModified) && isGet) {
                    return;
                }
            }
            //执行相应的Interceptor的preHandle
            if (!mappedHandler.applyPreHandle(processedRequest, response)) {
                return;
            }

            // Actually invoke the handler.
            //调用handler处理请求
            mv = ha.handle(processedRequest, response, mappedHandler.getHandler());
            //异步直接返回
            if (asyncManager.isConcurrentHandlingStarted()) {
                return;
            }
            //if (mv != null && !mv.hasView()) {
            //    String defaultViewName = getDefaultViewName(request);
            //    if (defaultViewName != null) {
            //        mv.setViewName(defaultViewName);
            //    }
            //}
            //如果view为空，根据processedRequest设置默认view
            applyDefaultViewName(processedRequest, mv);
            //执行相应Interceptor的postHandle
            mappedHandler.applyPostHandle(processedRequest, response, mv);
        }
        catch (Exception ex) {
            dispatchException = ex;
        }
        catch (Throwable err) {
            // As of 4.3, we're processing Errors thrown from handler methods as well,
            // making them available for @ExceptionHandler methods and other scenarios.
            dispatchException = new NestedServletException("Handler dispatch failed", err);
        }
        //处理结果
        processDispatchResult(processedRequest, response, mappedHandler, mv, dispatchException);
    }
    catch (Exception ex) {
        triggerAfterCompletion(processedRequest, response, mappedHandler, ex);
    }
    catch (Throwable err) {
        triggerAfterCompletion(processedRequest, response, mappedHandler,
                new NestedServletException("Handler processing failed", err));
    }
    finally {
        //异步
        if (asyncManager.isConcurrentHandlingStarted()) {
            // Instead of postHandle and afterCompletion
            if (mappedHandler != null) {
                mappedHandler.applyAfterConcurrentHandlingStarted(processedRequest, response);
            }
        }
        else {
            // Clean up any resources used by a multipart request.
            if (multipartRequestParsed) {
                //删除资源
                cleanupMultipart(processedRequest);
            }
        }
    }
}
```

## 5. processDispatchResult

`Handler`,`HandlerMapping`,`HandlerAdapter`在后面的文章中将详细描述，先看`processDispatchResult`:
```java
private void processDispatchResult(HttpServletRequest request, HttpServletResponse response,
                                    @Nullable HandlerExecutionChain mappedHandler, @Nullable ModelAndView mv,
                                    @Nullable Exception exception) throws Exception {

    boolean errorView = false;
    //如果有异常,设置到view
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

    // Did the handler return a view to render?
    ////设置local,构建view,渲染
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
        // Concurrent handling started during a forward
        return;
    }
    //请求处理完，触发Interceptor的afterCompletion,释放。
    if (mappedHandler != null) {
        mappedHandler.triggerAfterCompletion(request, response, null);
    }
}
```

到此，也就是Spring MVC处理请求流程简介。具体`HandlerMapping`，`HandlerAdapter`如何工作在后文中详细描述。