---
title: 浅析Spring MVC:响应式Web应用
date: 2018-07-05 12:00:00
categories: 
- Spring MVC
tags: 
- Spring MVC
---

使用Spring Web MVC，开发者可以直接访问官方文档[Spring Web MVC文档Version 5.2.1.RELEASE](https://docs.spring.io/spring/docs/5.2.1.RELEASE/spring-framework-reference/web.html#mvc)，本文及Spring MVC系列文章都参考于此文档及源码。

Spring 5支持响应式Web应用。
<!-- more -->
Spring Web MVC includes `WebMvc.fn`, a lightweight functional programming model in which functions are used to route and handle requests and contracts are designed for immutability. It is an alternative to the annotation-based programming model but otherwise runs on the same DispatcherServlet.

主要包括`RouterFunction`，`HandlerFunction`和`HandlerFilterFunction`，分别对应`@RequestMapping`，`@Controller`和`HandlerInterceptor`。

简单示例
```java
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.web.servlet.function.RequestPredicates.*;
import static org.springframework.web.servlet.function.RouterFunctions.route;

PersonRepository repository = ...
PersonHandler handler = new PersonHandler(repository);

RouterFunction<ServerResponse> route = route()
    .GET("/person/{id}", accept(APPLICATION_JSON), handler::getPerson)
    .GET("/person", accept(APPLICATION_JSON), handler::listPeople)
    .POST("/person", handler::createPerson)
    .build();


public class PersonHandler {

    // ...

    public ServerResponse listPeople(ServerRequest request) {
        // ...
    }

    public ServerResponse createPerson(ServerRequest request) {
        // ...
    }

    public ServerResponse getPerson(ServerRequest request) {
        // ...
    }
}
```

## 1. HandlerFunction
```java
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.web.reactive.function.server.ServerResponse.ok;

public class PersonHandler {

    private final PersonRepository repository;

    public PersonHandler(PersonRepository repository) {
        this.repository = repository;
    }

    public ServerResponse listPeople(ServerRequest request) { 
        List<Person> people = repository.allPeople();
		//转换成JSON对象返回
        return ok().contentType(APPLICATION_JSON).body(people);
    }

    public ServerResponse createPerson(ServerRequest request) throws Exception { 
		//获取request body内容
        Person person = request.body(Person.class);
        repository.savePerson(person);
        return ok().build();
    }

    public ServerResponse getPerson(ServerRequest request) { 
		//获取参数request中id
        int personId = Integer.parseInt(request.pathVariable("id"));
		//通过id查询Person
        Person person = repository.getPerson(personId);
        if (person != null) {
			//查询到结果后转换成json返回
            return ok().contentType(APPLICATION_JSON).body(person))
        }
        else {
			//未查询到结构返回notFound404
            return ServerResponse.notFound().build();
        }
    }

}
```

数据校验示例：
```java
public class PersonHandler {

    private final Validator validator = new PersonValidator(); 

    // ...

    public ServerResponse createPerson(ServerRequest request) {
		//获取参数正文
        Person person = request.body(Person.class);
		//校验参数
        validate(person); 
		//保存person
        repository.savePerson(person);
	    //返回成功
        return ok().build();
    }

    private void validate(Person person) {
        Errors errors = new BeanPropertyBindingResult(person, "person");
        validator.validate(person, errors);
		//抛出异常
        if (errors.hasErrors()) {
            throw new ServerWebInputException(errors.toString()); 
        }
    }
}
```
## 2. RouterFunction

`RouterFunction`将请求路由到`HandlerFunction`,通过`RouterFunctions.route()`，`RouterFunctions.route(RequestPredicate, HandlerFunction)`创建路由.

简单示例：
```java
RouterFunction<ServerResponse> route = RouterFunctions.route()
    .GET("/hello-world", accept(MediaType.TEXT_PLAIN),
        request -> ServerResponse.ok().body("Hello World"));
```

更加强大的示例：
```java
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.web.servlet.function.RequestPredicates.*;

PersonRepository repository = ...
PersonHandler handler = new PersonHandler(repository);

RouterFunction<ServerResponse> otherRoute = ...

RouterFunction<ServerResponse> route = route()
    .GET("/person/{id}", accept(APPLICATION_JSON), handler::getPerson) //匹配accept JSON的PersonHandler.getPerson
    .GET("/person", accept(APPLICATION_JSON), handler::listPeople) //匹配accept JSON的PersonHandler.listPeople
    .POST("/person", handler::createPerson) //PersonHandler.createPerson
    .add(otherRoute) 
    .build();
```

嵌套示例：
```java
RouterFunction<ServerResponse> route = route()
    .path("/person", b1 -> b1
        .nest(accept(APPLICATION_JSON), b2 -> b2
            .GET("/{id}", handler::getPerson)
            .GET("", handler::listPeople))
        .POST("/person", handler::createPerson))
    .build();
```

## 3. run

```java
@Configuration
@EnableMvc
public class WebConfig implements WebMvcConfigurer {

    @Bean
    public RouterFunction<?> routerFunctionA() {
        // ...
    }

    @Bean
    public RouterFunction<?> routerFunctionB() {
        // ...
    }

    // ...

    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        // configure message conversion...
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        // configure CORS...
    }

    @Override
    public void configureViewResolvers(ViewResolverRegistry registry) {
        // configure view resolution for HTML rendering...
    }
}
```

## 4. HandlerFilterFunction

可以使用`HandlerFilterFunction`的`before`，`after`或`filter`

`before`，`after`：
```java
RouterFunction<ServerResponse> route = route()
    .path("/person", b1 -> b1
        .nest(accept(APPLICATION_JSON), b2 -> b2
            .GET("/{id}", handler::getPerson)
            .GET("", handler::listPeople)
            .before(request -> ServerRequest.from(request) //前，build
                .header("X-RequestHeader", "Value")
                .build()))
        .POST("/person", handler::createPerson))
    .after((request, response) -> logResponse(response)) //后，logResponse
    .build();
```
`filter`：
```java
SecurityManager securityManager = ...

RouterFunction<ServerResponse> route = route()
    .path("/person", b1 -> b1
        .nest(accept(APPLICATION_JSON), b2 -> b2
            .GET("/{id}", handler::getPerson)
            .GET("", handler::listPeople))
        .POST("/person", handler::createPerson))
    .filter((request, next) -> { //添加安全拦截
        if (securityManager.allowAccessTo(request.path())) {
            return next.handle(request);
        }
        else {
            return ServerResponse.status(UNAUTHORIZED).build();
        }
    })
    .build();
```