---
title: 浅析Spring MVC:Controller
date: 2018-04-13 10:00:00
categories: 
- Spring MVC
tags: 
- Spring MVC
---

使用Spring Web MVC，开发者可以直接访问官方文档[Spring Web MVC文档Version 5.2.1.RELEASE](https://docs.spring.io/spring/docs/5.2.1.RELEASE/spring-framework-reference/web.html#mvc)，本文及Spring MVC系列文章都参考于此文档及源码。

这一节来看Spring MVC具体使用方法。
<!-- more -->
## 1. @Controller

### 1. @Controller
Spring MVC provides an annotation-based programming model where `@Controller` and `@RestController` components use annotations to express request mappings, request input, exception handling, and more. Annotated controllers have flexible method signatures and do not have to extend base classes nor implement specific interfaces. 

使用`@Controller`，`@RestController`就可以实现一个接口，不需要继承或者实现base。

The following example shows a controller defined by annotations：

```java
@Controller
public class HelloController {

    @GetMapping("/hello")
    public String handle(Model model) {
        model.addAttribute("message", "Hello World!");
        return "index";
    }
}
```

### 2. 声明

需要配置configuration来自动扫描`@Controller`beans。

1. java configuration
```java
@Configuration
@ComponentScan("org.example.web")
public class WebConfig {
    // ...
}
```
2. spring.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:p="http://www.springframework.org/schema/p"
    xmlns:context="http://www.springframework.org/schema/context"
    xsi:schemaLocation="
        http://www.springframework.org/schema/beans
        https://www.springframework.org/schema/beans/spring-beans.xsd
        http://www.springframework.org/schema/context
        https://www.springframework.org/schema/context/spring-context.xsd">

    <context:component-scan base-package="org.example.web"/>
    <!-- more -->
</beans>
```

引申内容
```java
public @interface RestController {

    //@AliasFor互为别名
	@AliasFor(annotation = Controller.class)
	String value() default "";

}

```
### 3. 映射

1. 可以使用`@RequestMapping`映射request到方法上，也可以使用`@RequestMapping`的其他注解：`@GetMapping`,`@PostMapping`...
```java
@RestController
@RequestMapping("/persons")
class PersonController {

    @GetMapping("/{id}")
    public Person getPerson(@PathVariable Long id) {
        // ...
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public void add(@RequestBody Person person) {
        // ...
    }
}
```

2. 可以使用通配符来映射如:
```java
@Controller
@RequestMapping("/owners/{ownerId}")
public class OwnerController {

    @GetMapping("/pets/{petId}")
    public Pet findPet(@PathVariable Long ownerId, @PathVariable Long petId) {
        // ...
    }
}
```

3. 也可以使用`@GetMapping("/{name:[a-z-]+}-{version:\\d\\.\\d\\.\\d}{ext:\\.[a-z]+}")`。多种模式匹配，会进行最优匹配。

4. 注解中还一些其他参数：`consumes`,`produces`,`params`

5. Spring MVC还支持带有自定义请求匹配逻辑的自定义请求映射属性。需要`RequestMappingHandlerMapping`对`getCustomMethodCondition`方法进行覆盖，可以在其中检查`custom`属性并返回您自己的方法`RequestCondition`。

6. 可以通过代码注册
```java
@Configuration
public class MyConfig {

    @Autowired
    public void setHandlerMapping(RequestMappingHandlerMapping mapping, UserHandler handler) 
            throws NoSuchMethodException {
        
        //映射数据
        RequestMappingInfo info = RequestMappingInfo
                .paths("/user/{id}").methods(RequestMethod.GET).build(); 
        
        //方法数据
        Method method = UserHandler.class.getMethod("getUser", Long.class); 

        //注册方法映射
        mapping.registerMapping(info, handler, method); 
    }
}
```

### 4. 处理方法

Spring MVC提供许多注解和参数供我们使用，详细可参照官方文档。这里简单的介绍一部分内容

1. @PathVariable: 用于访问URI模板变量。

2. @MatrixVariable: 用于访问URI路径段中的名称/值对。

3. @RequestParam: 用于访问Servlet请求参数，包括Multipart。

4. @RequestHeader: 用于访问请求头。

5. @CookieValue: 用于访问cookie。

6. @RequestBody: 用于访问HTTP请求Body。通过使用`HttpMessageConverter`实现转换，具体方法见下文。

7. @RequestPart: 用于`multipart/form-data`请求中的内容。

8. @ResponseBody: 用于返回值通过`HttpMessageConverter`实现进行转换并写入响应。

这里简单举个例子：

```java
@Controller
@RequestMapping("/pets")
public class EditPetForm {

    // ...

    @GetMapping
    public String setupForm(@RequestParam("petId") int petId, Model model) { 
        Pet pet = this.clinic.loadPet(petId);
        model.addAttribute("pet", pet);
        return "petForm";
    }

    // ...

}
```

更加常用的是通过`HttpMessageConverter`序列化和反序列化到对象。`@RequestBody`,`@ResponseBody`

```java
@PostMapping("/accounts")
public @ResponseBody Account handle(@RequestBody Account account) {
    return account;
}
```

可以覆盖`HttpMessageConverter`中`configureMessageConverters()`方法或者`extendMessageConverters()`方法进行配置：

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

9. @ModelAttribute: 可以注解在参数等地方，简单的理解就是作为一个模板覆盖或者实例化请求参数对象或者其他的对象。

10. @InitBinder: 可以继承`PropertyEditorSupport`自定义

11. @ExceptionHandler: 异常处理

`@ExceptionHandler`,`@InitBinder`和`@ModelAttribute`应该使用在Base中，这样就可以做到跨控制器。如果我们需要更加全局的使用，则可以是用`@ControllerAdvice`或者`@RestControllerAdvice`。

默认情况下，`@ControllerAdvice`方法适用于每个请求。当然也可以缩小范围:

```java
// Target all Controllers annotated with @RestController
@ControllerAdvice(annotations = RestController.class)
public class ExampleAdvice1 {}

// Target all Controllers within specific packages
@ControllerAdvice("org.example.controllers")
public class ExampleAdvice2 {}

// Target all Controllers assignable to specific classes
@ControllerAdvice(assignableTypes = {ControllerInterface.class, AbstractController.class})
public class ExampleAdvice3 {}
```