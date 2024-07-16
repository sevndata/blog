---
title: Spring MVC和Hibernate Validator 国际化
date: 2021-04-07 09:15:16
categories: 
- Spring
tags: 
- Spring
---
本文分享了 Spring MVC和Hibernate Validator 国际化
<!-- more -->

## 1. Spring MVC

### 配置

spring.xml
```xml
<!--
配置语言资源文件
basename： 语言资源文件名
useCodeAsDefaultMessage： 设置为true时，如果没有找到对应的语言字符，则使用传入的code作为返回值
-->
<bean id="messageSource" class="org.springframework.context.support.ResourceBundleMessageSource">
    <property name="basename" value="messages"/>
    <property name="useCodeAsDefaultMessage" value="true"/>
    <property name="defaultEncoding" value="UTF-8"/>
</bean>
```
spring-mvc.xml
```xml
<!-- 地区解析器，可存储和解析request中的地区信息 -->
<bean id="localeResolver" class="org.springframework.web.servlet.i18n.SessionLocaleResolver" />

<!-- 拦截器，可获取request中携带的地区信息，并通过localeResolver来处理 -->
<mvc:interceptors>
	<bean id="localeChangeInterceptor" class="org.springframework.web.servlet.i18n.LocaleChangeInterceptor" />
</mvc:interceptors>
```
### 处理过程
```java
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) throws Exception {
    ...
    mappedHandler = getHandler(processedRequest);
    ...
    // 调用拦截器的预处理方法
    if (!mappedHandler.applyPreHandle(processedRequest, response)) {
        return;·
    }
    ...
}
```
LocaleChangeInterceptor
```java
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws ServletException {
    // 根据paramName属性读取地区信息
    // 注意：改拦截器只会判断请求是否携带地区信息，如果想从请求的HEADER中获取，需重写preHandle方法
    // SessionLocaleResolver的resolveLocale方法已实现从HEADER中获取locale信息
    String newLocale = request.getParameter(getParamName());
    if (newLocale != null) {
        if (checkHttpMethod(request.getMethod())) {
            // 获取 LocaleResolver
            LocaleResolver localeResolver = RequestContextUtils.getLocaleResolver(request);
            if (localeResolver == null) {
                throw new IllegalStateException(
                        "No LocaleResolver found: not in a DispatcherServlet request?");
            }
            try {
                // 调用localeResolver来存储地区信息
                localeResolver.setLocale(request, response, parseLocaleValue(newLocale));
            }
            catch (IllegalArgumentException ex) {
                if (isIgnoreInvalidLocale()) {
                    logger.debug("Ignoring invalid locale value [" + newLocale + "]: " + ex.getMessage());
                }
                else {
                    throw ex;
                }
            }
        }
    }
    // Proceed in any case.
    return true;
}

```

```java
public class MyLocaleChangeInterceptor extends LocaleChangeInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
        Object handler) throws ServletException {
        String newLocale = request.getParameter(getParamName());

        if (newLocale == null) {
            // SessionLocaleResolver
            // try to get locale message by Accept-Language of request-header or default locale of localeResolver

            LocaleResolver localeResolver = RequestContextUtils.getLocaleResolver(request);

            if (localeResolver == null) {
                throw new IllegalStateException(
                    "No LocaleResolver found: not in a DispatcherServlet request?");
            }

            // the web context will cache the request locale
            Locale requestLocale = localeResolver.resolveLocale(request);
            try {
                localeResolver.setLocale(request, response, requestLocale);
            }
            catch (IllegalArgumentException ex) {
                if (isIgnoreInvalidLocale()) {
                    logger.debug("Ignoring invalid locale value [" + requestLocale.toString() + "]: " + ex.getMessage());
                }
                else {
                    throw ex;
                }
            }
        } else {
            return super.preHandle(request, response, handler);
        }

        return true;
    }
}
```
AbstractLocaleContextResolver，该类实现了setLocale方法，在该方法中调用抽象方法setLocaleContext。
```java
@Override
public void setLocale(HttpServletRequest request, HttpServletResponse response, Locale locale) {
    // LocaleContextResolver
    setLocaleContext(request, response, (locale != null ? new SimpleLocaleContext(locale) : null));
}
```
SessionLocaleResolver，实现了抽象方法setLocaleContext，把请求中携带的locale信息存储在session中。
```java
@Override
public void setLocaleContext(HttpServletRequest request, HttpServletResponse response, LocaleContext localeContext) {
    Locale locale = null;
    TimeZone timeZone = null;
    if (localeContext != null) {
        locale = localeContext.getLocale();
        if (localeContext instanceof TimeZoneAwareLocaleContext) {
            timeZone = ((TimeZoneAwareLocaleContext) localeContext).getTimeZone();
        }
    }

    // 存储地区和时区信息
    // this.localeAttributeName默认值为LOCALE_SESSION_ATTRIBUTE_NAME
    // public static final String LOCALE_SESSION_ATTRIBUTE_NAME = SessionLocaleResolver.class.getName() + ".LOCALE";
    WebUtils.setSessionAttribute(request, this.localeAttributeName, locale);
    WebUtils.setSessionAttribute(request, this.timeZoneAttributeName, timeZone);
}
```
以上为Spring MVC获取和存储locale信息的流程，下面我们来看看它是如何根据locale信息处理预先定义的国际化资源。

MessageSource定义了根据locale信息获取对应code的字符信息方法，该接口的组织关系如下图所示。在这里以ResourceBundleMessageSource为例，分析不带参数并未使用MessageFormat时的处理过程。

MessageSource
```java
public interface MessageSource {

	String getMessage(String code, Object[] args, String defaultMessage, Locale locale);

	String getMessage(String code, Object[] args, Locale locale) throws NoSuchMessageException;

	String getMessage(MessageSourceResolvable resolvable, Locale locale) throws NoSuchMessageException;

}
```
AbstractMessageSource，根据传入的locale和code返回具体的语言信息，定义protected String resolveCodeWithoutArguments(String code, Locale locale)，把资源的解析交给子类完成。
```java
@Override
public final String getMessage(String code, Object[] args, Locale locale) throws NoSuchMessageException {
    // 读取code对应的语言信息
    String msg = getMessageInternal(code, args, locale);
    if (msg != null) {
        return msg;
    }
    String fallback = getDefaultMessage(code);
    if (fallback != null) {
        return fallback;
    }
    throw new NoSuchMessageException(code, locale);
}
```
```java
protected String getMessageInternal(String code, Object[] args, Locale locale) {
    if (code == null) {
        return null;
    }
    if (locale == null) {
        locale = Locale.getDefault();
    }
    Object[] argsToUse = args;

    if (!isAlwaysUseMessageFormat() && ObjectUtils.isEmpty(args)) {
        // Optimized resolution: no arguments to apply,
        // therefore no MessageFormat needs to be involved.
        // Note that the default implementation still uses MessageFormat;
        // this can be overridden in specific subclasses.
        // 解析资源文件获取语言信息
        String message = resolveCodeWithoutArguments(code, locale);
        if (message != null) {
            return message;
        }
    }

    else {
        // Resolve arguments eagerly, for the case where the message
        // is defined in a parent MessageSource but resolvable arguments
        // are defined in the child MessageSource.
        // 解析带参数的语言信息
        argsToUse = resolveArguments(args, locale);

        MessageFormat messageFormat = resolveCode(code, locale);
        if (messageFormat != null) {
            synchronized (messageFormat) {
                return messageFormat.format(argsToUse);
            }
        }
    }

    // Check locale-independent common messages for the given message code.
    Properties commonMessages = getCommonMessages();
    if (commonMessages != null) {
        String commonMessage = commonMessages.getProperty(code);
        if (commonMessage != null) {
            return formatMessage(commonMessage, args, locale);
        }
    }

    // Not found -> check parent, if any.
    return getMessageFromParent(code, argsToUse, locale);
}
```
ResourceBundleMessageSource，重写父类的resolveCodeWithoutArguments方法，只可解析properties资源。
```java
@Override
protected String resolveCodeWithoutArguments(String code, Locale locale) {
    Set<String> basenames = getBasenameSet();
    for (String basename : basenames) {
        // 通过ResourceBundle类读取properties文件
        ResourceBundle bundle = getResourceBundle(basename, locale);
        if (bundle != null) {
            String result = getStringOrNull(bundle, code);
            if (result != null) {
                return result;
            }
        }
    }
    return null;
}
```
除了ResourceBundleMessageSource可解析资源信息之外，还有ReloadableResourceBundleMessageSource类也可处理，而且支持的资源不止properties文件，还可处理XML文件。

以上就是Spring MVC国际化的主要处理类，如需在业务中做国际化，只需从容器的上下文获取localeResolver和messageSource两个bean实例即可。
2. Hibernate Validator
2.1 配置

spring-mvc.xml
```xml
<bean id="validator" class="org.springframework.validation.beanvalidation.LocalValidatorFactoryBean">
	<property name="providerClass" value="org.hibernate.validator.HibernateValidator" />
	<property name="validationMessageSource" ref="messageSource" />
</bean>
```
2.2 源码解析

Hibernate Validator默认使用ResourceBundleMessageInterpolator进行资源解析。该类实现了javax.validation定义的MessageInterpolator接口，该类支持EL表达式(${foo})和参数({foo})两种字符串定义方式。
```java
// 具体的解析由以下方法完成
private String interpolateMessage(String message, Context context, Locale locale) throws MessageDescriptorFormatException {
	LocalizedMessage localisedMessage = new LocalizedMessage( message, locale );
	String resolvedMessage = null;

    // 如果有缓存则取出缓存中的存储的资源信息
    if ( cachingEnabled ) {
    	resolvedMessage = resolvedMessages.get( localisedMessage );
    }

    // 未缓存，则从资源文件获取，通过以下三步完成
    if ( resolvedMessage == null ) {
        // 用户定义的资源
    	ResourceBundle userResourceBundle = userResourceBundleLocator
            .getResourceBundle( locale );
        //  hibernate validator 内置资源
    	ResourceBundle defaultResourceBundle = defaultResourceBundleLocator
            .getResourceBundle( locale );

    	String userBundleResolvedMessage;
    	resolvedMessage = message;
    	boolean evaluatedDefaultBundleOnce = false;
    	do {
            // 1. 在userResourceBundle中搜索resolvedMessage对应的字符串(递归)
            userBundleResolvedMessage = interpolateBundleMessage(
                resolvedMessage, userResourceBundle, locale, true
            );

            // 3. 检测中断循环条件
            // 3.1 至少执行一次
            // 3.2 userBundleResolvedMessage和resolvedMessage相同
            if ( evaluatedDefaultBundleOnce &&
                    !hasReplacementTakenPlace( userBundleResolvedMessage, resolvedMessage ) ) {
            	break;
            }

            // 2. 在defaultResourceBundle中搜索userBundleResolvedMessage对应的字符串(非递归)
            resolvedMessage = interpolateBundleMessage(
                userBundleResolvedMessage,
                defaultResourceBundle,
                locale,
                false
            );
            evaluatedDefaultBundleOnce = true;
    	} while ( true );
    }

    // 缓存处理后的资源信息
    if ( cachingEnabled ) {
    	String cachedResolvedMessage = resolvedMessages.putIfAbsent( localisedMessage, resolvedMessage );
    	if ( cachedResolvedMessage != null ) {
    		resolvedMessage = cachedResolvedMessage;
    	}
    }

    // 根据缓存处理资源信息
    // 4. 解析 参数表达式（内置资源）
    List<Token> tokens = null;
    if ( cachingEnabled ) {
    	tokens = tokenizedParameterMessages.get( resolvedMessage );
    }
    if ( tokens == null ) {
    	TokenCollector tokenCollector = new TokenCollector( resolvedMessage, InterpolationTermType.PARAMETER );
    	tokens = tokenCollector.getTokenList();

    	if ( cachingEnabled ) {
    		tokenizedParameterMessages.putIfAbsent( resolvedMessage, tokens );
    	}
    }
    resolvedMessage = interpolateExpression(
    		new TokenIterator( tokens ),
    		context,
    		locale
    );

    // 5. 解析 EL表达式（内置资源）
    tokens = null;
    if ( cachingEnabled ) {
    	tokens = tokenizedELMessages.get( resolvedMessage );
    }
    if ( tokens == null ) {
    	TokenCollector tokenCollector = new TokenCollector( resolvedMessage, InterpolationTermType.EL );
    	tokens = tokenCollector.getTokenList();

    	if ( cachingEnabled ) {
    		tokenizedELMessages.putIfAbsent( resolvedMessage, tokens );
    	}
    }
    resolvedMessage = interpolateExpression(
    		new TokenIterator( tokens ),
    		context,
    		locale
    );

    // 检测带转义符的字符串,替换为原始字符串
    resolvedMessage = replaceEscapedLiterals( resolvedMessage );

    return resolvedMessage;
}

...

// 获取message对应的value并处理表达式
private String interpolateBundleMessage(String message, ResourceBundle bundle, Locale locale, boolean recursive)
        throws MessageDescriptorFormatException {
    TokenCollector tokenCollector = new TokenCollector( message, InterpolationTermType.PARAMETER );
    TokenIterator tokenIterator = new TokenIterator( tokenCollector.getTokenList() );
    while ( tokenIterator.hasMoreInterpolationTerms() ) {
        String term = tokenIterator.nextInterpolationTerm();

        // 根据表达式中的key获取对应的值
        String resolvedParameterValue = resolveParameter(
                term, bundle, locale, recursive
        );

        // 用resolvedParameterValue的值替换key
        tokenIterator.replaceCurrentInterpolationTerm( resolvedParameterValue );
    }

    // 返回处理之后的字符
    return tokenIterator.getInterpolatedMessage();
}

// 处理内置资源中的表达式，如注解和表达式的值绑定处理等
private String interpolateExpression(TokenIterator tokenIterator, Context context, Locale locale)
        throws MessageDescriptorFormatException {
    while ( tokenIterator.hasMoreInterpolationTerms() ) {
        String term = tokenIterator.nextInterpolationTerm();

        InterpolationTerm expression = new InterpolationTerm( term, locale );
        String resolvedExpression = expression.interpolate( context );
        tokenIterator.replaceCurrentInterpolationTerm( resolvedExpression );
    }
    return tokenIterator.getInterpolatedMessage();
}

// 以parameterName为key获取对应的value，如果recursive为true，则调用interpolateBundleMessage循环往复,直到value中的表达式全部解析
private String resolveParameter(String parameterName, ResourceBundle bundle, Locale locale, boolean recursive)
        throws MessageDescriptorFormatException {
    String parameterValue;
    try {
        if ( bundle != null ) {
            parameterValue = bundle.getString( removeCurlyBraces( parameterName ) );
            if ( recursive ) {
                parameterValue = interpolateBundleMessage( parameterValue, bundle, locale, recursive );
            }
        }
        else {
            parameterValue = parameterName;
        }
    }
    catch ( MissingResourceException e ) {
        // 返回传入的key
        parameterValue = parameterName;
    }
    return parameterValue;
}

// 移除"{"和"}"字符
private String removeCurlyBraces(String parameter) {
    return parameter.substring( 1, parameter.length() - 1 );
}
```