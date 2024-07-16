---
title: Mybatis中Mapper扫描及代理 
date: 2021-04-07 09:15:16
categories: 
- Mybatis
tags: 
- Mybatis
---
本文分享了Mybatis-Mapper扫描及代理 
<!-- more -->


## 1. 流程
### 1.1 Mapper扫描

Mybatis依靠XML文件来映射数据库和对象之间关系，配置Mapper如下所示（也可使用MapperScan注解），其中basePackage定义了需要扫描的包路径。实现BeanDefinitionRegistryPostProcessor接口，Spring会在项目启动时触发扫描。
```xml
<bean class="org.mybatis.spring.mapper.MapperScannerConfigurer">
  <!-- 扫描路径 -->
  <property name="basePackage" value="net.cofcool.api.server.dao" />
  <!-- sqlSessionFactory -->
  <property name="sqlSessionFactoryBeanName" value="sqlSessionFactory" />
</bean>
```
我们来看看它的扫描过程。MapperScannerConfigurer负责读取配置和在项目启动时触发扫描过程，ClassPathMapperScanner负责执行扫描。
扫描流程MapperScannerConfigurerMapperScannerConfigurerClassPathMapperScannerClassPathMapperScannerscandoScan扫描配置的XML和Class，缓存对应关系，并把真实类替换为MapperFactoryBean，由它负责创建MapperProxy类

MyBatis在扫描Mapper接口时，由GenericBeanDefinition包装DAO接口。
1.2 Myabtis代理DAO接口类

Mybatis通过代理的方式把定义的接口转换为可执行方法，最终实现SQL代码执行。通过MapperFactoryBean工厂类创建MapperProxy实例。
MapperProxy代理DAO接口类过程MapperFactoryBeanMapperFactoryBeanSqlSessionSqlSessionConfigurationConfigurationMapperRegistryMapperRegistryMapperProxyFactoryMapperProxyFactoryMapperProxyMapperProxygetObject()getSqlSession()ClassPathMapperScanner在创建MapperFactoryBean时，会把sqlSessionFactory,sqlSessionTemplate等参数传递给MapperFactoryBean，从而创建SqlSession(SqlSessionTemplate)，通过getObject返回代理类getConfiguration()getMapper()getMapper()调用mapperRegistry的getMapper(type, sqlSession)，并由代理工厂类创建代理类实例newInstance()
## 2. 源码解析
### 2.1 配置类

MapperScannerConfigurer，根据basePackage，调用ClassPathMapperScanner的扫描方法进行扫描，可配置扫描路径，扫描条件，包括注解，父类等。

```java
public class MapperScannerConfigurer implements BeanDefinitionRegistryPostProcessor, InitializingBean, ApplicationContextAware, BeanNameAware {

  // 扫描包路径，如果有多个路径，可用,或;等字符分割
  private String basePackage;

  private boolean addToConfig = true;

  // SqlSession相关对象
  private SqlSessionFactory sqlSessionFactory;
  private SqlSessionTemplate sqlSessionTemplate;
  private String sqlSessionFactoryBeanName;
  private String sqlSessionTemplateBeanName;

  private Class<? extends Annotation> annotationClass;

  // 扫描继承该接口的接口
  private Class<?> markerInterface;

  @Override
  public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
    if (this.processPropertyPlaceHolders) {
      processPropertyPlaceHolders();
    }

    // 创建扫描器
    ClassPathMapperScanner scanner = new ClassPathMapperScanner(registry);
    scanner.setAddToConfig(this.addToConfig);
    scanner.setAnnotationClass(this.annotationClass);
    scanner.setMarkerInterface(this.markerInterface);
    scanner.setSqlSessionFactory(this.sqlSessionFactory);
    scanner.setSqlSessionTemplate(this.sqlSessionTemplate);
    scanner.setSqlSessionFactoryBeanName(this.sqlSessionFactoryBeanName);
    scanner.setSqlSessionTemplateBeanName(this.sqlSessionTemplateBeanName);
    scanner.setResourceLoader(this.applicationContext);
    scanner.setBeanNameGenerator(this.nameGenerator);
    // 注册Filter
    scanner.registerFilters();
    // 扫描
    scanner.scan(StringUtils.tokenizeToStringArray(this.basePackage, ConfigurableApplicationContext.CONFIG_LOCATION_DELIMITERS));
  }
}
```
2.2 扫描类

ClassPathMapperScanner，执行具体的扫描，继承Spring的ClassPathBeanDefinitionScanner类，ClassPathBeanDefinitionScanner是Spring提供的一个用于扫描Bean定义配置的基础类，ClassPathMapperScanner在其基础上配置了扫描类的过滤条件和类定义替换等。
```java
public class ClassPathMapperScanner extends ClassPathBeanDefinitionScanner {

  // 是否添加mapper到Configuration
  private boolean addToConfig = true;

  private SqlSessionFactory sqlSessionFactory;
  private SqlSessionTemplate sqlSessionTemplate;
  private String sqlSessionTemplateBeanName;
  private String sqlSessionFactoryBeanName;

  // 扫描注解
  private Class<? extends Annotation> annotationClass;

  // DAO接口的父类
  private Class<?> markerInterface;

  // 创建被MapperProxy代理的DAO接口实例
  private MapperFactoryBean<?> mapperFactoryBean = new MapperFactoryBean<Object>();

  ...

  /**
   * 保证父类扫描器扫到正确的接口，包括所有接口或继承markerInterface的接口和使用annotationClass注解的接口
   */
  public void registerFilters() {
    // 默认扫描所有接口
    boolean acceptAllInterfaces = true;

    // 如果定义了annotationClass，则扫描使用该注解的接口
    if (this.annotationClass != null) {
      addIncludeFilter(new AnnotationTypeFilter(this.annotationClass));
      // 不会扫描所有接口
      acceptAllInterfaces = false;
    }

    // 扫描继承markerInterface的接口
    if (this.markerInterface != null) {
      addIncludeFilter(new AssignableTypeFilter(this.markerInterface) {
        // 不以类名作为匹配条件
        @Override
        protected boolean matchClassName(String className) {
          return false;
        }
      });
      // 不会扫描所有接口
      acceptAllInterfaces = false;
    }

    // 扫描所有接口
    if (acceptAllInterfaces) {
      // 包含所有类
      addIncludeFilter(new TypeFilter() {
        @Override
        public boolean match(MetadataReader metadataReader, MetadataReaderFactory metadataReaderFactory) throws IOException {
          return true;
        }
      });
    }

    // 排除 package-info.java
    addExcludeFilter(new TypeFilter() {
      @Override
      public boolean match(MetadataReader metadataReader, MetadataReaderFactory metadataReaderFactory) throws IOException {
        String className = metadataReader.getClassMetadata().getClassName();
        return className.endsWith("package-info");
      }
    });
  }

  /**
   * 先调用父类扫描器获取扫描结果，然后注册所有bean的class为MapperFactoryBean，也就是说把它们定义为MapperFactoryBean
   */
  @Override
  public Set<BeanDefinitionHolder> doScan(String... basePackages) {
    // 调用父类的doScan方法
    Set<BeanDefinitionHolder> beanDefinitions = super.doScan(basePackages);

    if (beanDefinitions.isEmpty()) {
      logger.warn("No MyBatis mapper was found in '" + Arrays.toString(basePackages) + "' package. Please check your configuration.");
    } else {
      // 处理 beanDefinitions
      processBeanDefinitions(beanDefinitions);
    }

    return beanDefinitions;
  }

  private void processBeanDefinitions(Set<BeanDefinitionHolder> beanDefinitions) {
    GenericBeanDefinition definition;
    // 遍历 beanDefinitions
    for (BeanDefinitionHolder holder : beanDefinitions) {
      definition = (GenericBeanDefinition) holder.getBeanDefinition();

      if (logger.isDebugEnabled()) {
        logger.debug("Creating MapperFactoryBean with name '" + holder.getBeanName()
          + "' and '" + definition.getBeanClassName() + "' mapperInterface");
      }

      // 获取真实接口class，并作为构造方法的参数
      definition.getConstructorArgumentValues().addGenericArgumentValue(definition.getBeanClassName());
      // 修改类为MapperFactoryBean
      definition.setBeanClass(this.mapperFactoryBean.getClass());

      // 为MapperFactoryBean的成员变量赋值
      // addToConfig
      definition.getPropertyValues().add("addToConfig", this.addToConfig);

      // sqlSession
      // 是否定义了 sqlSessionFactory，影响sqlSessionTemplate，和自动注入方式
      boolean explicitFactoryUsed = false;
      if (StringUtils.hasText(this.sqlSessionFactoryBeanName)) {
        definition.getPropertyValues().add("sqlSessionFactory", new RuntimeBeanReference(this.sqlSessionFactoryBeanName));
        explicitFactoryUsed = true;
      } else if (this.sqlSessionFactory != null) {
        definition.getPropertyValues().add("sqlSessionFactory", this.sqlSessionFactory);
        explicitFactoryUsed = true;
      }

      // 定以sqlSessionTemplate
      // 如果已定义sqlSessionFactory，则忽略sqlSessionFactory
      if (StringUtils.hasText(this.sqlSessionTemplateBeanName)) {
        if (explicitFactoryUsed) {
          logger.warn("Cannot use both: sqlSessionTemplate and sqlSessionFactory together. sqlSessionFactory is ignored.");
        }
        definition.getPropertyValues().add("sqlSessionTemplate", new RuntimeBeanReference(this.sqlSessionTemplateBeanName));
        explicitFactoryUsed = true;
      } else if (this.sqlSessionTemplate != null) {
        if (explicitFactoryUsed) {
          logger.warn("Cannot use both: sqlSessionTemplate and sqlSessionFactory together. sqlSessionFactory is ignored.");
        }
        definition.getPropertyValues().add("sqlSessionTemplate", this.sqlSessionTemplate);
        explicitFactoryUsed = true;
      }

      if (!explicitFactoryUsed) {
        if (logger.isDebugEnabled()) {
          logger.debug("Enabling autowire by type for MapperFactoryBean with name '" + holder.getBeanName() + "'.");
        }
        // 采用按照类型注入的方式
        definition.setAutowireMode(AbstractBeanDefinition.AUTOWIRE_BY_TYPE);
      }
    }
  }
}
```
2.3 代理类

MapperFactoryBean，该类会代理项目定义的DAO接口，由于实现了FactoryBean接口，通过调用getObject方法获取实例，也就是MapperProxy对象。
```java
public class MapperFactoryBean<T> extends SqlSessionDaoSupport implements FactoryBean<T> {

  private Class<T> mapperInterface;

  private boolean addToConfig = true;

  ...

  // 添加mapper，会在bean创建之后调用
  @Override
  protected void checkDaoConfig() {
    super.checkDaoConfig();

    notNull(this.mapperInterface, "Property 'mapperInterface' is required");

    // 通过Configuration来添加Mapper
    Configuration configuration = getSqlSession().getConfiguration();
    if (this.addToConfig && !configuration.hasMapper(this.mapperInterface)) {
      try {
        configuration.addMapper(this.mapperInterface);
      } catch (Exception e) {
        logger.error("Error while adding the mapper '" + this.mapperInterface + "' to configuration.", e);
        throw new IllegalArgumentException(e);
      } finally {
        ErrorContext.instance().reset();
      }
    }
  }

  // 返回由MapperProxy代理的DAO对象
  @Override
  public T getObject() throws Exception {
    // 调用父类的 getSqlSession() 获取SqlSession
    return getSqlSession().getMapper(this.mapperInterface);
  }
}
```
MapperFactoryBean的父类为SqlSessionDaoSupport，存储了sqlSession对象。
```java
public abstract class SqlSessionDaoSupport extends DaoSupport {

  private SqlSession sqlSession;

  private boolean externalSqlSession;

  // 上文提到ClassPathMapperScanner通过GenericBeanDefinition给MapperFactoryBean的sqlSessionFactory，sqlSessionTemplate属性赋值，也就是调用它们的setter方法
  // 在setter中给sqlSession进行赋值
  public void setSqlSessionFactory(SqlSessionFactory sqlSessionFactory) {
    if (!this.externalSqlSession) {
      this.sqlSession = new SqlSessionTemplate(sqlSessionFactory);
    }
  }

  public void setSqlSessionTemplate(SqlSessionTemplate sqlSessionTemplate) {
    this.sqlSession = sqlSessionTemplate;
    this.externalSqlSession = true;
  }

  public SqlSession getSqlSession() {
    return this.sqlSession;
  }

  // 检查属性，sqlSessionFactory或sqlSessionTemplate至少存在一个
  // 具体可查看ClassPathMapperScanner的processBeanDefinitions方法
  @Override
  protected void checkDaoConfig() {
    notNull(this.sqlSession, "Property 'sqlSessionFactory' or 'sqlSessionTemplate' are required");
  }

}
```

上文提到，Configuration类存储和管理Mapper，它通过MapperRegistry来添加和存储Mapper。
```java
public class Configuration {

  protected final MapperRegistry mapperRegistry = new MapperRegistry(this);

  public <T> void addMapper(Class<T> type) {
    mapperRegistry.addMapper(type);
  }

  public boolean hasMapper(Class<?> type) {
    return mapperRegistry.hasMapper(type);
  }

  public <T> T getMapper(Class<T> type, SqlSession sqlSession) {
    return mapperRegistry.getMapper(type, sqlSession);
  }

  ...
}
```
MapperRegistry，管理Mapper的具体创建，通过MapperProxyFactory来创建MapperProxy实例。
```java
public class MapperRegistry {

  private final Configuration config;

  // 缓存MapperProxyFactory和MapperInterface的关系，MapperInterface为key
  private final Map<Class<?>, MapperProxyFactory<?>> knownMappers = new HashMap<Class<?>, MapperProxyFactory<?>>();

  public MapperRegistry(Configuration config) {
    this.config = config;
  }

  // 通过MapperInterface获取MapperProxy实例
  @SuppressWarnings("unchecked")
  public <T> T getMapper(Class<T> type, SqlSession sqlSession) {
    // 从缓存中读取MapperProxyFactory
    final MapperProxyFactory<T> mapperProxyFactory = (MapperProxyFactory<T>) knownMappers.get(type);
    if (mapperProxyFactory == null) {
      throw new BindingException("Type " + type + " is not known to the MapperRegistry.");
    }
    try {
      // 由MapperProxyFactory创建MapperProxy实例
      return mapperProxyFactory.newInstance(sqlSession);
    } catch (Exception e) {
      throw new BindingException("Error getting mapper instance. Cause: " + e, e);
    }
  }

  // 添加Mapper
  public <T> void addMapper(Class<T> type) {
    // 是否是接口类型
    if (type.isInterface()) {
      // 是否已存在
      if (hasMapper(type)) {
        throw new BindingException("Type " + type + " is already known to the MapperRegistry.");
      }
      boolean loadCompleted = false;
      try {
        // 缓存
        knownMappers.put(type, new MapperProxyFactory<T>(type));
        // 方法解析，包括方法定义合法性检查，接口与XML映射，注解解析，缓存设置等，更多可查看MapperAnnotationBuilder类
        MapperAnnotationBuilder parser = new MapperAnnotationBuilder(config, type);
        parser.parse();
        loadCompleted = true;
      } finally {
        if (!loadCompleted) {
          knownMappers.remove(type);
        }
      }
    }
  }

  ...

}
```
MapperProxyFactory，MapperProxy的工厂方法，负责创建MapperProxy实例。
```java
public class MapperProxyFactory<T> {

  // 定义的接口
  private final Class<T> mapperInterface;
  // 方法和sql执行缓存
  // MapperMethod封装了SqlSession的执行
  private final Map<Method, MapperMethod> methodCache = new ConcurrentHashMap<Method, MapperMethod>();

  public MapperProxyFactory(Class<T> mapperInterface) {
    this.mapperInterface = mapperInterface;
  }

  ...

  // 由MapperProxy代理定义的接口
  @SuppressWarnings("unchecked")
  protected T newInstance(MapperProxy<T> mapperProxy) {
    return (T) Proxy.newProxyInstance(mapperInterface.getClassLoader(), new Class[] { mapperInterface }, mapperProxy);
  }

  // 根据SqlSession创建MapperProxy实例
  public T newInstance(SqlSession sqlSession) {
    final MapperProxy<T> mapperProxy = new MapperProxy<T>(sqlSession, mapperInterface, methodCache);
    return newInstance(mapperProxy);
  }

}
```
通过一系列的调用，最终创建了MapperProxy实例。该类负责把我们定义的DAO方法以代理的方式转换为可执行的SQL代码，至于它的具体作用以及代码解析将会在下一节中做详细介绍。