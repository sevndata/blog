---
title: Spring MVC默认异常处理器及异常处理过程解析
date: 2019-07-12 11:34:23
categories: 
- Spring MVC
tags: 
- Spring MVC
---
本文分享了Spring MVC默认异常处理器`DefaultHandlerExceptionResolver`,`ExceptionHandlerExceptionResolver`,`ResponseStatusExceptionResolver`的处理异常过程。
<!-- more -->
## 1. DefaultHandlerExceptionResolver
```java
protected ModelAndView doResolveException(
			HttpServletRequest request, HttpServletResponse response, @Nullable Object handler, Exception ex) {

  try {
    //405
    if (ex instanceof HttpRequestMethodNotSupportedException) {
      return handleHttpRequestMethodNotSupported(
          (HttpRequestMethodNotSupportedException) ex, request, response, handler);
    }
    //415
    else if (ex instanceof HttpMediaTypeNotSupportedException) {
      return handleHttpMediaTypeNotSupported(
          (HttpMediaTypeNotSupportedException) ex, request, response, handler);
    }
    //406
    else if (ex instanceof HttpMediaTypeNotAcceptableException) {
      return handleHttpMediaTypeNotAcceptable(
          (HttpMediaTypeNotAcceptableException) ex, request, response, handler);
    }
    //500
    else if (ex instanceof MissingPathVariableException) {
      return handleMissingPathVariable(
          (MissingPathVariableException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof MissingServletRequestParameterException) {
      return handleMissingServletRequestParameter(
          (MissingServletRequestParameterException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof ServletRequestBindingException) {
      return handleServletRequestBindingException(
          (ServletRequestBindingException) ex, request, response, handler);
    }
    //new ModelAndView()
    else if (ex instanceof ConversionNotSupportedException) {
      return handleConversionNotSupported(
          (ConversionNotSupportedException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof TypeMismatchException) {
      return handleTypeMismatch(
          (TypeMismatchException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof HttpMessageNotReadableException) {
      return handleHttpMessageNotReadable(
          (HttpMessageNotReadableException) ex, request, response, handler);
    }
    //new ModelAndView()
    else if (ex instanceof HttpMessageNotWritableException) {
      return handleHttpMessageNotWritable(
          (HttpMessageNotWritableException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof MethodArgumentNotValidException) {
      return handleMethodArgumentNotValidException(
          (MethodArgumentNotValidException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof MissingServletRequestPartException) {
      return handleMissingServletRequestPartException(
          (MissingServletRequestPartException) ex, request, response, handler);
    }
    //400
    else if (ex instanceof BindException) {
      return handleBindException((BindException) ex, request, response, handler);
    }
    //404
    else if (ex instanceof NoHandlerFoundException) {
      return handleNoHandlerFoundException(
          (NoHandlerFoundException) ex, request, response, handler);
    }
    //503
    else if (ex instanceof AsyncRequestTimeoutException) {
      return handleAsyncRequestTimeoutException(
          (AsyncRequestTimeoutException) ex, request, response, handler);
    }
  }
  catch (Exception handlerEx) {
    if (logger.isWarnEnabled()) {
      logger.warn("Failure while trying to resolve exception [" + ex.getClass().getName() + "]", handlerEx);
    }
  }
  return null;
}
```
## 6. ExceptionHandlerExceptionResolver
该类默认优先级较高,负责解析含有@ControllerAdvice和@ExceptionHandler注解的Controller抛出的异常
```java
@Override
@Nullable
protected ModelAndView doResolveHandlerMethodException(HttpServletRequest request,
    HttpServletResponse response, @Nullable HandlerMethod handlerMethod, Exception exception) {

  ServletInvocableHandlerMethod exceptionHandlerMethod = getExceptionHandlerMethod(handlerMethod, exception);
  if (exceptionHandlerMethod == null) {
    return null;
  }

  if (this.argumentResolvers != null) {
    exceptionHandlerMethod.setHandlerMethodArgumentResolvers(this.argumentResolvers);
  }
  if (this.returnValueHandlers != null) {
    exceptionHandlerMethod.setHandlerMethodReturnValueHandlers(this.returnValueHandlers);
  }

  ServletWebRequest webRequest = new ServletWebRequest(request, response);
  ModelAndViewContainer mavContainer = new ModelAndViewContainer();

  try {
    if (logger.isDebugEnabled()) {
      logger.debug("Using @ExceptionHandler " + exceptionHandlerMethod);
    }
    // 通过ServletInvocableHandlerMethod处理异常
    Throwable cause = exception.getCause();
    if (cause != null) {
      // Expose cause as provided argument as well
      exceptionHandlerMethod.invokeAndHandle(webRequest, mavContainer, exception, cause, handlerMethod);
    }
    else {
      // Otherwise, just the given exception as-is
      exceptionHandlerMethod.invokeAndHandle(webRequest, mavContainer, exception, handlerMethod);
    }
  }
  catch (Throwable invocationEx) {
    // Any other than the original exception (or its cause) is unintended here,
    // probably an accident (e.g. failed assertion or the like).
    if (invocationEx != exception && invocationEx != exception.getCause() && logger.isWarnEnabled()) {
      logger.warn("Failure in @ExceptionHandler " + exceptionHandlerMethod, invocationEx);
    }
    // Continue with default processing of the original exception...
    return null;
  }

  if (mavContainer.isRequestHandled()) {
    return new ModelAndView();
  }
  else {
    ModelMap model = mavContainer.getModel();
    HttpStatus status = mavContainer.getStatus();
    ModelAndView mav = new ModelAndView(mavContainer.getViewName(), model, status);
    mav.setViewName(mavContainer.getViewName());
    if (!mavContainer.isViewReference()) {
      mav.setView((View) mavContainer.getView());
    }
    if (model instanceof RedirectAttributes) {
      Map<String, ?> flashAttributes = ((RedirectAttributes) model).getFlashAttributes();
      RequestContextUtils.getOutputFlashMap(request).putAll(flashAttributes);
    }
    return mav;
  }
}
```
## 3. ResponseStatusExceptionResolver
```java
@Override
@Nullable
protected ModelAndView doResolveException(
    HttpServletRequest request, HttpServletResponse response, @Nullable Object handler, Exception ex) {

  try {
    if (ex instanceof ResponseStatusException) {
      return resolveResponseStatusException((ResponseStatusException) ex, request, response, handler);
    }
    // 解析@ResponseStatus
    ResponseStatus status = AnnotatedElementUtils.findMergedAnnotation(ex.getClass(), ResponseStatus.class);
    if (status != null) {
      return resolveResponseStatus(status, request, response, handler, ex);
    }
    // 解析其他异常
    if (ex.getCause() instanceof Exception) {
      return doResolveException(request, response, handler, (Exception) ex.getCause());
    }
  }
  catch (Exception resolveEx) {
    if (logger.isWarnEnabled()) {
      logger.warn("Failure while trying to resolve exception [" + ex.getClass().getName() + "]", resolveEx);
    }
  }
  return null;
}
```