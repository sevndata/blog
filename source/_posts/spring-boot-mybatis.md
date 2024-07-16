---
title: Spring Boot自定义框架starter方式引入
date: 2021-04-07 09:15:16
categories: 
- Mybatis
tags: 
- Spring Boot
- Mybatis
---
本文分享了Spring Boot自定义框架starter方式引入，以`mybatis-spring-boot-starter`源码作为示例。
<!-- more -->

## 1. 简介
  

分享了如何优雅的将自定义框架以`starter`形式引入到项目中，本文以`mybatis-spring-boot-starter`源码作为示例。

## 2. 命名

`Spring`官方建议了`artifactId`的命名规则，可遵循建议命名规则，如下：
1. 官方通常命名为`spring-boot-starter-{name}`，如：`spring-boot-starter-jdbc`,`spring-data-jpa`。
2. 建议非官方`starter`命名遵循`{name}-spring-boot-starter`，如`mybatis-spring-boot-start`。

## 3. mybatis-spring-boot-start
`mybatis-spring-boot-start`为一个空的项目，只有`pom.xml`引入了`mybatis-spring-boot-autoconfigure`与其他一些依赖项。

```xml
<dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-jdbc</artifactId>
    </dependency>
    <dependency>
      <groupId>org.mybatis.spring.boot</groupId>
      <artifactId>mybatis-spring-boot-autoconfigure</artifactId>
    </dependency>
    <dependency>
      <groupId>org.mybatis</groupId>
      <artifactId>mybatis</artifactId>
    </dependency>
    <dependency>
      <groupId>org.mybatis</groupId>
      <artifactId>mybatis-spring</artifactId>
    </dependency>
  </dependencies>
```
## 4. mybatis-spring-boot-autoconfigure
在`mybatis-spring-boot-autoconfigure`中，可以看到一些核心文件`MybatisProperties`,`MybatisAutoConfiguration`,`ConfigurationCustomizer`,
`MybatisLanguageDriverAutoConfiguration`,`SpringBootVFS`,`spring.factories`,
`additional-spring-configuration-metadata.json`等。下面将一一进行查看。
## 5. Spring Boot自定义配置
1. spring.factories
在`spring-core`中`SpringFactoriesLoader`遍历`META-INF/spring.factories`，此配置实例化了`MybatisLanguageDriverAutoConfiguration`和`MybatisAutoConfiguration`并配置到`Spring`中。

```xml
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.mybatis.spring.boot.autoconfigure.MybatisLanguageDriverAutoConfiguration,\
org.mybatis.spring.boot.autoconfigure.MybatisAutoConfiguration
```
2. MybatisProperties
定义了一些`mybatis`使用的参数，并提供入口，可由开发者通过`application.properties`配置`mybatis`参数，前缀为`mybatis`。如：`mybatis.configLocation=xmlPath`

```java
@ConfigurationProperties(prefix = MybatisProperties.MYBATIS_PREFIX)
public class MybatisProperties {

  public static final String MYBATIS_PREFIX = "mybatis";

  private static final ResourcePatternResolver resourceResolver = new PathMatchingResourcePatternResolver();

  /**
   * Location of MyBatis xml config file.
   */
  private String configLocation;
  ...
}
```
3. ConfigurationCustomizer
提供函数式接口，可由开发者实现接口来自定义配置。

```java
@FunctionalInterface
public interface ConfigurationCustomizer {
  void customize(Configuration configuration);
}
```
4. Metadata
`metadata.json`文件中包含了支持的所有配置属性的详细信息，可以帮助开发者在使用`application.properties`或者`application.yml`提供上下文提示等信息。

模仿以上几个关键点，就可以自定义`starter`的配置，使开发者能够便利的进行配置。

## 6. Mybatis的自动配置

1. MybatisAutoConfiguration

```java
@org.springframework.context.annotation.Configuration
//有这俩个文件配置生效
@ConditionalOnClass({ SqlSessionFactory.class, SqlSessionFactoryBean.class }) 
//有主DataSource生效
@ConditionalOnSingleCandidate(DataSource.class) 
//开启配置properties
@EnableConfigurationProperties(MybatisProperties.class) 
//配置之后配置
@AutoConfigureAfter({ DataSourceAutoConfiguration.class, MybatisLanguageDriverAutoConfiguration.class })
public class MybatisAutoConfiguration implements InitializingBean {
  private static final Logger logger = LoggerFactory.getLogger(MybatisAutoConfiguration.class);
  //开发者配置properties
  private final MybatisProperties properties;
  //拦截器
  private final Interceptor[] interceptors;
  //类型转换处理器
  private final TypeHandler[] typeHandlers;
  //语言驱动
  private final LanguageDriver[] languageDrivers;

  private final ResourceLoader resourceLoader;

  private final DatabaseIdProvider databaseIdProvider;
  //开发者自定义的配置Configuration
  private final List<ConfigurationCustomizer> configurationCustomizers;
  ...
  //检查配置是否存在
  @Override
  public void afterPropertiesSet() {
    checkConfigFileExists();
  }

  private void checkConfigFileExists() {
    if (this.properties.isCheckConfigLocation() && StringUtils.hasText(this.properties.getConfigLocation())) {
      Resource resource = this.resourceLoader.getResource(this.properties.getConfigLocation());
      Assert.state(resource.exists(),
          "Cannot find config location: " + resource + " (please add config file or check your Mybatis configuration)");
    }
  }

  @Bean
  //容器中没有SqlSessionFactory对象才会实例化，优先使用开发者自定义SqlSessionFactory
  @ConditionalOnMissingBean  
  public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
    //初始化
    SqlSessionFactoryBean factory = new SqlSessionFactoryBean();
    //设置开发者dataSource
    factory.setDataSource(dataSource);
    //设置VFS，读取资源文件
    factory.setVfs(SpringBootVFS.class);
    //设置开发者配置的xml路径
    if (StringUtils.hasText(this.properties.getConfigLocation())) {
      factory.setConfigLocation(this.resourceLoader.getResource(this.properties.getConfigLocation()));
    }
    //处理配置
    applyConfiguration(factory);
    ...
    //通过开发者参数设置SqlSessionFactory
    if (!ObjectUtils.isEmpty(this.properties.resolveMapperLocations())) {
      factory.setMapperLocations(this.properties.resolveMapperLocations());
    }
    Set<String> factoryPropertyNames = Stream
        .of(new BeanWrapperImpl(SqlSessionFactoryBean.class).getPropertyDescriptors()).map(PropertyDescriptor::getName)
        .collect(Collectors.toSet());
    //初始化设置动态SQL语言驱动
    Class<? extends LanguageDriver> defaultLanguageDriver = this.properties.getDefaultScriptingLanguageDriver();
    if (factoryPropertyNames.contains("scriptingLanguageDrivers") && !ObjectUtils.isEmpty(this.languageDrivers)) {
      // Need to mybatis-spring 2.0.2+
      factory.setScriptingLanguageDrivers(this.languageDrivers);
      if (defaultLanguageDriver == null && this.languageDrivers.length == 1) {
        defaultLanguageDriver = this.languageDrivers[0].getClass();
      }
    }
    if (factoryPropertyNames.contains("defaultScriptingLanguageDriver")) {
      // Need to mybatis-spring 2.0.2+
      factory.setDefaultScriptingLanguageDriver(defaultLanguageDriver);
    }
    //最终获取到SqlSessionFactory
    return factory.getObject();
  }
  //处理配置
  private void applyConfiguration(SqlSessionFactoryBean factory) {
    Configuration configuration = this.properties.getConfiguration();
    ///配置文件中读取配置
    if (configuration == null && !StringUtils.hasText(this.properties.getConfigLocation())) {
      configuration = new Configuration();
    }
    //从开放的自定义接口实现中读取配置
    if (configuration != null && !CollectionUtils.isEmpty(this.configurationCustomizers)) {
      for (ConfigurationCustomizer customizer : this.configurationCustomizers) {
        customizer.customize(configuration);
      }
    }
    //设置配置
    factory.setConfiguration(configuration);
  }

  @Bean
  //容器中没有该实例则初始化SqlSessionTemplate，优先使用开发者自定义的SqlSessionTemplate
  @ConditionalOnMissingBean  
  public SqlSessionTemplate sqlSessionTemplate(SqlSessionFactory sqlSessionFactory) {
    //指定执行器类型
    ExecutorType executorType = this.properties.getExecutorType();
    if (executorType != null) {
      return new SqlSessionTemplate(sqlSessionFactory, executorType);
    } else {
      return new SqlSessionTemplate(sqlSessionFactory);
    }
  }

  public static class AutoConfiguredMapperScannerRegistrar implements BeanFactoryAware, ImportBeanDefinitionRegistrar {

    private BeanFactory beanFactory;

    @Override
    public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry) {
      //必须存在 @EnableAutoConfiguration 注解
      if (!AutoConfigurationPackages.has(this.beanFactory)) {
        logger.debug("Could not determine auto-configuration package, automatic mapper scanning disabled.");
        return;
      }

      logger.debug("Searching for mappers annotated with @Mapper");
      //@EnableAutoConfiguration 注解 指定类的路径
      List<String> packages = AutoConfigurationPackages.get(this.beanFactory);
      if (logger.isDebugEnabled()) {
        packages.forEach(pkg -> logger.debug("Using auto-configuration base package '{}'", pkg));
      }
      //扫描注册 @Mapper
      BeanDefinitionBuilder builder = BeanDefinitionBuilder.genericBeanDefinition(MapperScannerConfigurer.class);
      builder.addPropertyValue("processPropertyPlaceHolders", true);
      builder.addPropertyValue("annotationClass", Mapper.class);
      builder.addPropertyValue("basePackage", StringUtils.collectionToCommaDelimitedString(packages));
      BeanWrapper beanWrapper = new BeanWrapperImpl(MapperScannerConfigurer.class);
      Stream.of(beanWrapper.getPropertyDescriptors())
          // Need to mybatis-spring 2.0.2+
          .filter(x -> x.getName().equals("lazyInitialization")).findAny()
          .ifPresent(x -> builder.addPropertyValue("lazyInitialization", "${mybatis.lazy-initialization:false}"));
      registry.registerBeanDefinition(MapperScannerConfigurer.class.getName(), builder.getBeanDefinition());
    }

    @Override
    public void setBeanFactory(BeanFactory beanFactory) {
      this.beanFactory = beanFactory;
    }

  }

  @org.springframework.context.annotation.Configuration
  @Import(AutoConfiguredMapperScannerRegistrar.class)
  //没有MapperFactoryBean，MapperScannerConfigurer时扫描注册才会生效
  @ConditionalOnMissingBean({ MapperFactoryBean.class, MapperScannerConfigurer.class }) 
  //未找到注册mapper的配置，如@MapperScan, MapperFactoryBean和MapperScannerConfigurer
  public static class MapperScannerRegistrarNotFoundConfiguration implements InitializingBean {

    @Override
    public void afterPropertiesSet() {
      logger.debug(
          "Not found configuration for registering mapper bean using @MapperScan, MapperFactoryBean and MapperScannerConfigurer.");
    }

  }

}
```
2. MybatisLanguageDriverAutoConfiguration

```java
@Configuration
@ConditionalOnClass(LanguageDriver.class)
public class MybatisLanguageDriverAutoConfiguration {

  private static final String CONFIGURATION_PROPERTY_PREFIX = "mybatis.scripting-language-driver";
  //FreeMarkerLanguageDriver,FreeMarker动态sql语言驱动
  @Configuration
  @ConditionalOnClass(FreeMarkerLanguageDriver.class)
  @ConditionalOnMissingClass("org.mybatis.scripting.freemarker.FreeMarkerLanguageDriverConfig")
  public static class LegacyFreeMarkerConfiguration {
    @Bean
    @ConditionalOnMissingBean
    FreeMarkerLanguageDriver freeMarkerLanguageDriver() {
      return new FreeMarkerLanguageDriver();
    }
  }
  @Configuration
  @ConditionalOnClass({ FreeMarkerLanguageDriver.class, FreeMarkerLanguageDriverConfig.class })
  public static class FreeMarkerConfiguration {
    @Bean
    @ConditionalOnMissingBean
    FreeMarkerLanguageDriver freeMarkerLanguageDriver(FreeMarkerLanguageDriverConfig config) {
      return new FreeMarkerLanguageDriver(config);
    }

    @Bean
    @ConditionalOnMissingBean
    @ConfigurationProperties(CONFIGURATION_PROPERTY_PREFIX + ".freemarker")
    public FreeMarkerLanguageDriverConfig freeMarkerLanguageDriverConfig() {
      return FreeMarkerLanguageDriverConfig.newInstance();
    }
  }
  ...
}
```
3. SpringBootVFS

`mybatis`中`VFS`的默认实现`DefaultVFS`无法读取`Spring Boot`嵌套jar的资源文件，所以更换为SpringBootVFS读取。

```java
protected List<String> list(URL url, String path) throws IOException {
    String urlString = url.toString();
    String baseUrlString = urlString.endsWith("/") ? urlString : urlString.concat("/");
    Resource[] resources = resourceResolver.getResources(baseUrlString + "**/*.class");
    return Stream.of(resources).map(resource -> preserveSubpackageName(baseUrlString, resource, path))
        .collect(Collectors.toList());
}

private static String preserveSubpackageName(final String baseUrlString, final Resource resource,
    final String rootPath) {
    try {
        return rootPath + (rootPath.endsWith("/") ? "" : "/")
            + resource.getURL().toString().substring(baseUrlString.length());
    } catch (IOException e) {
        throw new UncheckedIOException(e);
    }
}
```