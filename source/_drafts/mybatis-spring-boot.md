---
title: Mybatis中SQL执行，插件以及缓存 
date: 2021-04-07 09:15:16
categories: 
- Mybatis
tags: 
- Mybatis
---
本文分享了Mybatis-Mapper扫描及代理 
<!-- more -->

1. 流程
1.1 SqlSession创建流程

首先看看SqlSession的创建流程。
创建SqlSessionFactory实例SqlSessionFactoryBeanSqlSessionFactoryBeanSqlSessionFactoryBuilderSqlSessionFactoryBuilderSqlSessionFactorySqlSessionFactorygetObject实现FactoryBean接口，根据Configuration来buildSqlSessionFactory，包括事务，DataSource等afterPropertiesSetbuild> 创建SqlSession实例DefaultSqlSessionFactoryDefaultSqlSessionFactoryDefaultSqlSessionDefaultSqlSessionopenSession默认实现为DefaultSqlSessionFactory，根据Configuration创建事务，Executor等，并以此创建DefaultSqlSession实例openSessionFromDataSource/openSessionFromConnection
1.2 DAO执行流程

如下图所示:
DAO执行流程UserMapperUserMapperMapperProxyMapperProxyMapperMethodMapperMethodSqlSessionTemplateSqlSessionTemplatethis.sqlSessionProxythis.sqlSessionProxySqlSessionSqlSessionExecutorExecutor查询用户: selectinvoke代理扫描到的DAO接口execute以执行query为例selectSqlSessionTemplate的sqlSessionProxy持有SqlSession接口的代理invoke具体可查看SqlSessionTemplate的内部类SqlSessionInterceptorselectqueryExecutor负责具体的SQL执行，包含SIMPLE, REUSE, BATCH三种
2. 代码分析

经过以上分析可了解到Myabtis的基本执行流程和相关类，下面我们来看具体的代码实现。
2.1 创建 SqlSession

SqlSessionFactoryBean，Spring容器调用它来创建SqlSessionFactory。

// 创建 SqlSessionFactory
public SqlSessionFactory getObject() throws Exception {
  if (this.sqlSessionFactory == null) {
    afterPropertiesSet();
  }

  return this.sqlSessionFactory;
}

@Override
public void afterPropertiesSet() throws Exception {
  // 检查基础数据
  notNull(dataSource, "Property 'dataSource' is required");
  notNull(sqlSessionFactoryBuilder, "Property 'sqlSessionFactoryBuilder' is required");
  state((configuration == null && configLocation == null) || !(configuration != null && configLocation != null),
            "Property 'configuration' and 'configLocation' can not specified with together");

  this.sqlSessionFactory = buildSqlSessionFactory();
}

// 创建 SqlSessionFactory
protected SqlSessionFactory buildSqlSessionFactory() throws IOException {

  Configuration configuration;

  XMLConfigBuilder xmlConfigBuilder = null;
  if (this.configuration != null) {
	// 配置 Properties
    configuration = this.configuration;
    if (configuration.getVariables() == null) {
      configuration.setVariables(this.configurationProperties);
    } else if (this.configurationProperties != null) {
      configuration.getVariables().putAll(this.configurationProperties);
    }
  } else if (this.configLocation != null) {
	// 读取Configuration的XML配置
    xmlConfigBuilder = new XMLConfigBuilder(this.configLocation.getInputStream(), null, this.configurationProperties);
    configuration = xmlConfigBuilder.getConfiguration();
  } else {
    if (LOGGER.isDebugEnabled()) {
      LOGGER.debug("Property `configuration` or 'configLocation' not specified, using default MyBatis Configuration");
    }
    configuration = new Configuration();
    configuration.setVariables(this.configurationProperties);
  }

  // 创建Bean的相关类
  if (this.objectFactory != null) {
    configuration.setObjectFactory(this.objectFactory);
  }

  if (this.objectWrapperFactory != null) {
    configuration.setObjectWrapperFactory(this.objectWrapperFactory);
  }
  ...

  // 配置事务工厂
  // 如果未手动配置，则使用Spring中配置的事务工厂
  if (this.transactionFactory == null) {
    this.transactionFactory = new SpringManagedTransactionFactory();
  }

  // 配置基础环境，传入datasource，事务工厂等
  configuration.setEnvironment(new Environment(this.environment, this.transactionFactory, this.dataSource));
  ...

  return this.sqlSessionFactoryBuilder.build(configuration);
}

@Override
public void onApplicationEvent(ApplicationEvent event) {
    if (failFast && event instanceof ContextRefreshedEvent) {
      // 检查statements，确保所有 mapper statement 解析完毕
      this.sqlSessionFactory.getConfiguration().getMappedStatementNames();
    }
}

SqlSessionFactory的默认实现DefaultSqlSessionFactory，openSession方法调用openSessionFromDataSource或openSessionFromConnection函数来创建SqlSession实例。

// 创建 SqlSession
private SqlSession openSessionFromDataSource(ExecutorType execType, TransactionIsolationLevel level, boolean autoCommit) {
  Transaction tx = null;
  try {
    // 环境配置
    final Environment environment = configuration.getEnvironment();
    // 事务工厂
    final TransactionFactory transactionFactory = getTransactionFactoryFromEnvironment(environment);
    // 创建事务
    tx = transactionFactory.newTransaction(environment.getDataSource(), level, autoCommit);
    // 创建 executor
    final Executor executor = configuration.newExecutor(tx, execType);
    // 返回 DefaultSqlSession
    return new DefaultSqlSession(configuration, executor, autoCommit);
  } catch (Exception e) {
    closeTransaction(tx);
    throw ExceptionFactory.wrapException("Error opening session.  Cause: " + e, e);
  } finally {
    ErrorContext.instance().reset();
  }
}

// 事务工厂
private TransactionFactory getTransactionFactoryFromEnvironment(Environment environment) {
  if (environment == null || environment.getTransactionFactory() == null) {
    // 默认为 ManagedTransactionFactory
    // ManagedTransaction 把事务管理交给容器处理
    // JdbcTransaction Mybatis直接管理事务
    return new ManagedTransactionFactory();
  }
  return environment.getTransactionFactory();
}

2.2 SQL执行
2.2.1 SqlSession简要介绍

在Mybatis中，DAO操作依靠SqlSession来执行。独立使用时，sqlSession实例为DefaultSqlSession，需要手动管理该实例，以及事务处理等；若使用了mybatis-spring，则为SqlSessionTemplate，它的创建以及管理等由Spring负责。
1. 独立使用

Mybatis提供了SqlSessionManager，可由它来创建和管理SqlSession，也可直接通过SqlSessionFactory来创建SqlSession实例。

SqlSessionManager代理了SqlSession，相关操作借由SqlSessionManager的私有类SqlSessionInterceptor完成。

private class SqlSessionInterceptor implements InvocationHandler {
  ...

  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    // 从线程中获取SqlSession
    final SqlSession sqlSession = SqlSessionManager.this.localSqlSession.get();
    if (sqlSession != null) {
      try {
        // 若不为NULL则直接调用
        // 未包含事务等操作
        return method.invoke(sqlSession, args);
      } catch (Throwable t) {
        throw ExceptionUtil.unwrapThrowable(t);
      }
    } else {
      // 未从线程中取到
      // 创建SqlSession
      // 自动提交事务，回滚以及关闭
      final SqlSession autoSqlSession = openSession();
      try {
        final Object result = method.invoke(autoSqlSession, args);
        autoSqlSession.commit();
        return result;
      } catch (Throwable t) {
        autoSqlSession.rollback();
        throw ExceptionUtil.unwrapThrowable(t);
      } finally {
        autoSqlSession.close();
      }
    }
  }
}

2. Spring容器中运行

在上一篇文章介绍到MapperFactoryBean会代理定义的DAO接口，并把 SqlSessionTemplate赋值给this.sqlSession。SqlSessionTemplate实现SqlSession接口，并持有SqlSessionFactory实例，是一个特殊的SqlSession实例，主要功能为把Spring容器中的操作转换为Mybaits中SqlSession对应的操作。

public class SqlSessionTemplate implements SqlSession, DisposableBean {

  public SqlSessionTemplate(SqlSessionFactory sqlSessionFactory, ExecutorType executorType,
        PersistenceExceptionTranslator exceptionTranslator) {

  notNull(sqlSessionFactory, "Property 'sqlSessionFactory' is required");
  notNull(executorType, "Property 'executorType' is required");

  this.sqlSessionFactory = sqlSessionFactory;
  this.executorType = executorType;
  this.exceptionTranslator = exceptionTranslator;

  // 创建代理
  this.sqlSessionProxy = (SqlSession) newProxyInstance(
    SqlSessionFactory.class.getClassLoader(),
    new Class[] { SqlSession.class },
    new SqlSessionInterceptor());
  }
  ...
}

当执行DAO方法时，代理类经过一系列调用会调用到SqlSessionTemplate的系列方法，SqlSessionTemplate的sqlSessionProxy代理了SqlSession的实例，在调用这些方法时实际会调用SqlSessionTemplate的内部类SqlSessionInterceptor的invoke方法。

private class SqlSessionInterceptor implements InvocationHandler {
  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    // 获取 SqlSession，通过Spring的TransactionSynchronizationManager管理
    SqlSession sqlSession = getSqlSession(
        SqlSessionTemplate.this.sqlSessionFactory,
        SqlSessionTemplate.this.executorType,
        SqlSessionTemplate.this.exceptionTranslator);
    try {
      // 调用SqlSession的方法
      Object result = method.invoke(sqlSession, args);
      if (!isSqlSessionTransactional(sqlSession, SqlSessionTemplate.this.sqlSessionFactory)) {
        // 提交事务
        sqlSession.commit(true);
      }
      return result;
    } catch (Throwable t) {
      Throwable unwrapped = unwrapThrowable(t);
      if (SqlSessionTemplate.this.exceptionTranslator != null && unwrapped instanceof PersistenceException) {
        // 抛出异常时关闭sqlSession，并置为NULL
        closeSqlSession(sqlSession, SqlSessionTemplate.this.sqlSessionFactory);
        sqlSession = null;
        // 异常转换，转为Spring定义的数据库访问异常
        Throwable translated = SqlSessionTemplate.this.exceptionTranslator.translateExceptionIfPossible((PersistenceException) unwrapped);
        if (translated != null) {
          unwrapped = translated;
        }
      }
      throw unwrapped;
    } finally {
      if (sqlSession != null) {
        closeSqlSession(sqlSession, SqlSessionTemplate.this.sqlSessionFactory);
      }
    }
  }
}

2.2.2 执行

由“MapperProxy代理DAO接口类过程”可知，MapperProxy为真正的DAO接口实例，该类持有sqlSession，mapperInterface，其中mapperInterface为定义的DAO接口类。

public class MapperProxy<T> implements InvocationHandler, Serializable {

  private final SqlSession sqlSession;
  private final Class<T> mapperInterface;
  private final Map<Method, MapperMethod> methodCache;

  ...

  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    // 如果是Object的方法，则直接调用
    if (Object.class.equals(method.getDeclaringClass())) {
      try {
        return method.invoke(this, args);
      } catch (Throwable t) {
        throw ExceptionUtil.unwrapThrowable(t);
      }
    }
    // 执行代理方法
    // MapperMethod封装了MethodSignature(方法参数，返回值等)和SqlCommand(Sql类型，方法ID)
    final MapperMethod mapperMethod = cachedMapperMethod(method);
    // 通过sqlSession执行sql
    return mapperMethod.execute(sqlSession, args);
  }

  // 缓存Method，MapperMethod
  private MapperMethod cachedMapperMethod(Method method) {
    MapperMethod mapperMethod = methodCache.get(method);
    if (mapperMethod == null) {
      mapperMethod = new MapperMethod(mapperInterface, method, sqlSession.getConfiguration());
      methodCache.put(method, mapperMethod);
    }
    return mapperMethod;
  }
}

MapperMethod封装了MethodSignature(方法参数，返回值等)和SqlCommand(Sql类型，方法ID)，把接口定义方法转换为对应的SqlSession方法，从而执行SQL语句。

public class MapperMethod {

  // 封装方法名和类型
  private final SqlCommand command;
  // 封装方法参数，返回值等
  private final MethodSignature method;

  public MapperMethod(Class<?> mapperInterface, Method method, Configuration config) {
    // Configuration封装了MappedStatement，根据传入的mapperInterface获取对应的SqlCommand，MethodSignature
    this.command = new SqlCommand(config, mapperInterface, method);
    this.method = new MethodSignature(config, mapperInterface, method);
  }

  // 执行
  // 根据SQL类型调用sqlSession对应的方法
  public Object execute(SqlSession sqlSession, Object[] args) {
      Object result;
      switch (command.getType()) {
        case INSERT: {
          // 插入数据
      	  Object param = method.convertArgsToSqlCommandParam(args);
          result = rowCountResult(sqlSession.insert(command.getName(), param));
          break;
        }
        ...
        // 查询
        case SELECT:
          if (method.returnsVoid() && method.hasResultHandler()) {
            // 含有参数类型为ResultHandler且没有返回值
            executeWithResultHandler(sqlSession, args);
            result = null;
          } else if (method.returnsMany()) {
            // set或array
            result = executeForMany(sqlSession, args);
          } else if (method.returnsMap()) {
            // 返回值类型为Map，且有注解MapKey（定义key）
            // 把返回结果以key-value的形式存储
            result = executeForMap(sqlSession, args);
          } else if (method.returnsCursor()) {
            // 返回值类型为Cursor
            result = executeForCursor(sqlSession, args);
          } else {
            // 方法有返回值
            Object param = method.convertArgsToSqlCommandParam(args);
            result = sqlSession.selectOne(command.getName(), param);
          }
          break;
        case FLUSH:
          // 处理批量执行结果
          result = sqlSession.flushStatements();
          break;
        default:
          throw new BindingException("Unknown execution method for: " + command.getName());
      }
      ...
      return result;
    }

    ...
}

经过MapperMethod处理之后，SqlSession开始登场，定义的DAO方法通过SqlSession开始执行。

SqlSession的默认实现为DefaultSqlSession，它的构造方法为public DefaultSqlSession(Configuration configuration, Executor executor, boolean autoCommit)，在创建实例的时候传入Configuration。DefaultSqlSession在执行Sql时需要获取配置的动态sql以及相关参数等，MappedStatement封装了这些数据，可通过Configuration获取MappedStatement实例。

以DefaultSqlSession的selectList为例：

@Override
public <E> List<E> selectList(String statement, Object parameter, RowBounds rowBounds) {
  try {
    // MappedStatement
    MappedStatement ms = configuration.getMappedStatement(statement);
    // executor执行查询
    return executor.query(ms, wrapCollection(parameter), rowBounds, Executor.NO_RESULT_HANDLER);
  } catch (Exception e) {
    throw ExceptionFactory.wrapException("Error querying database.  Cause: " + e, e);
  } finally {
    ErrorContext.instance().reset();
  }
}

执行查询操作可分为两步：创建MappedStatement，Executor执行查询。
1. 创建 MappedStatement

MappedStatement,该类封装了Mapper定义的方法执行时需要的各种参数定义和配置。

public final class MappedStatement {
  // sql语句
  private String resource;
  private Configuration configuration;
  // 方法名
  private String id;
  private Integer fetchSize;
  private Integer timeout;
  // MyBatis 支持 STATEMENT，PREPARED 和 CALLABLE 语句的映射类型，分别代表 PreparedStatement 和 CallableStatement 类型。
  private StatementType statementType;
  // FORWARD_ONLY，SCROLL_SENSITIVE 或 SCROLL_INSENSITIVE 中的一个，默认未设置
  // FORWARD_ONLY: Cursor只能向前迭代
  // SCROLL_SENSITIVE：Cursor前后迭代都可以，对ResultSet创建之后数据库数据发生改变不敏感
  // SCROLL_INSENSITIVE：Cursor前后迭代都可以，对ResultSet创建之后数据库数据发生改变敏感
  private ResultSetType resultSetType;
  // Represents the content of a mapped statement read from an XML file or an annotation
  private SqlSource sqlSource;
  private Cache cache;
  private ParameterMap parameterMap;
  // resultMap 元素是 MyBatis 中最重要最强大的元素。它可以让你从 90% 的 JDBC ResultSets 数据提取代码中解放出来, 并在一些情形下允许你做一些 JDBC 不支持的事情。 实际上，在对复杂语句进行联合映射的时候，它很可能可以代替数千行的同等功能的代码。 ResultMap 的设计思想是，简单的语句不需要明确的结果映射，而复杂一点的语句只需要描述它们的关系就行了。
  private List<ResultMap> resultMaps;
  private boolean flushCacheRequired;
  private boolean useCache;
  private boolean resultOrdered;
  // sql类型，插入，查询等
  private SqlCommandType sqlCommandType;
  // 自增生成器
  private KeyGenerator keyGenerator;
  // 唯一标记一个属性，MyBatis 会通过 getGeneratedKeys 的返回值或者通过 insert 语句的 selectKey 子元素设置它的键值，默认：unset。如果希望得到多个生成的列，也可以是逗号分隔的属性名称列表。
  private String[] keyProperties;
  // （仅对 insert 和 update 有用）通过生成的键值设置表中的列名，这个设置仅在某些数据库（像 PostgreSQL）是必须的，当主键列不是表中的第一列的时候需要设置。如果希望得到多个生成的列，也可以是逗号分隔的属性名称列表。
  private String[] keyColumns;
  private boolean hasNestedResultMaps;
  // 如果配置了 databaseIdProvider，MyBatis 会加载所有的不带 databaseId 或匹配当前 databaseId 的语句；如果带或者不带的语句都有，则不带的会被忽略。
  private String databaseId;
  private Log statementLog;
  private LanguageDriver lang;
  // 这个设置仅对多结果集的情况适用，它将列出语句执行后返回的结果集并每个结果集给一个名称，名称是逗号分隔的。
  private String[] resultSets;

  // 构建 MappedStatement
  public static class Builder {
    private MappedStatement mappedStatement = new MappedStatement();

    public Builder(Configuration configuration, String id, SqlSource sqlSource, SqlCommandType sqlCommandType) {
      mappedStatement.configuration = configuration;
      mappedStatement.id = id;
      mappedStatement.sqlSource = sqlSource;
      mappedStatement.statementType = StatementType.PREPARED;
      mappedStatement.parameterMap = new ParameterMap.Builder(configuration, "defaultParameterMap", null, new ArrayList<ParameterMapping>()).build();
      mappedStatement.resultMaps = new ArrayList<ResultMap>();
      mappedStatement.sqlCommandType = sqlCommandType;
      mappedStatement.keyGenerator = configuration.isUseGeneratedKeys() && SqlCommandType.INSERT.equals(sqlCommandType) ? new Jdbc3KeyGenerator() : new NoKeyGenerator();
      String logId = id;
      if (configuration.getLogPrefix() != null) {
        logId = configuration.getLogPrefix() + id;
      }
      mappedStatement.statementLog = LogFactory.getLog(logId);
      mappedStatement.lang = configuration.getDefaultScriptingLanuageInstance();
    }

    ...

    public Builder resultMaps(List<ResultMap> resultMaps) {
      mappedStatement.resultMaps = resultMaps;
      for (ResultMap resultMap : resultMaps) {
        mappedStatement.hasNestedResultMaps = mappedStatement.hasNestedResultMaps || resultMap.hasNestedResultMaps();
      }
      return this;
    }

    ...

    public MappedStatement build() {
      assert mappedStatement.configuration != null;
      assert mappedStatement.id != null;
      assert mappedStatement.sqlSource != null;
      assert mappedStatement.lang != null;
      mappedStatement.resultMaps = Collections.unmodifiableList(mappedStatement.resultMaps);
      return mappedStatement;
    }
  }
  ...

  // BoundSql封装了xml或注解中定义的动态sql
  // sql，parameterMappings，parameterObject，additionalParameters，metaParameters;
  public BoundSql getBoundSql(Object parameterObject) {
    BoundSql boundSql = sqlSource.getBoundSql(parameterObject);
    List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();
    if (parameterMappings == null || parameterMappings.isEmpty()) {
      boundSql = new BoundSql(configuration, boundSql.getSql(), parameterMap.getParameterMappings(), parameterObject);
    }

    for (ParameterMapping pm : boundSql.getParameterMappings()) {
      String rmId = pm.getResultMapId();
      if (rmId != null) {
        ResultMap rm = configuration.getResultMap(rmId);
        if (rm != null) {
          hasNestedResultMaps |= rm.hasNestedResultMaps();
        }
      }
    }

    return boundSql;
  }
}

MappedStatement创建成功之后，通过Executor执行Sql。
2. Executor执行Sql

Executor负责执行具体的sql，定义了CURD等各种方法，包括事务处理等。

public interface Executor {

  ...

  int update(MappedStatement ms, Object parameter) throws SQLException;

  <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler, CacheKey cacheKey, BoundSql boundSql) throws SQLException;

  <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler) throws SQLException;

  <E> Cursor<E> queryCursor(MappedStatement ms, Object parameter, RowBounds rowBounds) throws SQLException;

  List<BatchResult> flushStatements() throws SQLException;

  void commit(boolean required) throws SQLException;

  void rollback(boolean required) throws SQLException;

  void close(boolean forceRollback);

  boolean isClosed();

  ...

}

Executor由Configuration创建，在创建Executor时，提供三种BatchExecutor，ReuseExecutor，SimpleExecutor。CachingExecutor通过代理模式调用上述Executor，并缓存结果。

public Executor newExecutor(Transaction transaction, ExecutorType executorType) {
  executorType = executorType == null ? defaultExecutorType : executorType;
  executorType = executorType == null ? ExecutorType.SIMPLE : executorType;
  Executor executor;
  if (ExecutorType.BATCH == executorType) {
    executor = new BatchExecutor(this, transaction);
  } else if (ExecutorType.REUSE == executorType) {
    executor = new ReuseExecutor(this, transaction);
  } else {
    executor = new SimpleExecutor(this, transaction);
  }
  if (cacheEnabled) {
    executor = new CachingExecutor(executor);
  }
  executor = (Executor) interceptorChain.pluginAll(executor);
  return executor;
}

类图如下所示:

SqlSession
SqlSessionDefaultSqlSessionSqlSessionTemplatesqlSessionProxySqlSessionFactorySqlSession

Executor
ExecutorBaseExecutorBatchExecutorSimpleExecutorReuseExecutor

Executor内部通过StatementHandler执行Sql，具体细节可查看相关源码。
2.3 事务处理

Mybatis已经包含了事务管理，如果和Spring集成的话，也可使用Spring提供的事务管理，开发更为方便，利于管理维护。
2.3.1 Mybatis管理

SqlSession提供提交，回滚等事务相关API，以DefaultSqlSession为例。

// 提交
@Override
public void commit(boolean force) {
  try {
    // 调用Executor的相关方法
    executor.commit(isCommitOrRollbackRequired(force));
    dirty = false;
  } catch (Exception e) {
    throw ExceptionFactory.wrapException("Error committing transaction.  Cause: " + e, e);
  } finally {
    ErrorContext.instance().reset();
  }
}

// 回滚
@Override
public void rollback(boolean force) {
  try {
    executor.rollback(isCommitOrRollbackRequired(force));
    dirty = false;
  } catch (Exception e) {
    throw ExceptionFactory.wrapException("Error rolling back transaction.  Cause: " + e, e);
  } finally {
    ErrorContext.instance().reset();
  }
}

// 关闭连接
@Override
public void close() {
  try {
    executor.close(isCommitOrRollbackRequired(false));
    closeCursors();
    dirty = false;
  } finally {
    ErrorContext.instance().reset();
  }
}

Executor的实现类BaseExecutor实现了相关方法。

// 关闭Connection，通过Transaction实现
@Override
public void close(boolean forceRollback) {
  try {
    try {
      rollback(forceRollback);
    } finally {
      if (transaction != null) {
        transaction.close();
      }
    }
  } catch (SQLException e) {
    // Ignore.  There's nothing that can be done at this point.
    log.warn("Unexpected exception on closing transaction.  Cause: " + e);
  } finally {
    // 清除相关数据
    transaction = null;
    deferredLoads = null;
    localCache = null;
    localOutputParameterCache = null;
    closed = true;
  }
}

// 提交，通过Transaction实现
@Override
public void commit(boolean required) throws SQLException {
  if (closed) {
    throw new ExecutorException("Cannot commit, transaction is already closed");
  }
  clearLocalCache();
  flushStatements();
  if (required) {
    transaction.commit();
  }
}

// 回滚，通过Transaction实现
@Override
public void rollback(boolean required) throws SQLException {
  if (!closed) {
    try {
      clearLocalCache();
      flushStatements(true);
    } finally {
      if (required) {
        transaction.rollback();
      }
    }
  }
}

protected Connection getConnection(Log statementLog) throws SQLException {
  // 通过Transaction获取Connection
  Connection connection = transaction.getConnection();
  if (statementLog.isDebugEnabled()) {
    return ConnectionLogger.newInstance(connection, statementLog, queryStack);
  } else {
    return connection;
  }
}

Mybatis有两种事务管理器：

    JdbcTransaction
    ManagedTransaction

1. JdbcTransaction

通过传入的DataSource创建Connection，并调用Connection的相关方法来处理事务。

public class JdbcTransaction implements Transaction {

  public JdbcTransaction(DataSource ds, TransactionIsolationLevel desiredLevel, boolean desiredAutoCommit) {
    dataSource = ds;
    level = desiredLevel;
    autoCommmit = desiredAutoCommit;
  }

  public JdbcTransaction(Connection connection) {
    this.connection = connection;
  }

  @Override
  public void commit() throws SQLException {
    if (connection != null && !connection.getAutoCommit()) {
      if (log.isDebugEnabled()) {
        log.debug("Committing JDBC Connection [" + connection + "]");
      }
      connection.commit();
    }
  }
  ...

  @Override
  public void close() throws SQLException {
    if (connection != null) {
      resetAutoCommit();
      if (log.isDebugEnabled()) {
        log.debug("Closing JDBC Connection [" + connection + "]");
      }
      connection.close();
    }
  }

  @Override
  public void rollback() throws SQLException {
    if (connection != null && !connection.getAutoCommit()) {
      if (log.isDebugEnabled()) {
        log.debug("Rolling back JDBC Connection [" + connection + "]");
      }
      connection.rollback();
    }
  }

  // 创建 Connection
  protected void openConnection() throws SQLException {
    if (log.isDebugEnabled()) {
      log.debug("Opening JDBC Connection");
    }
    connection = dataSource.getConnection();
    if (level != null) {
      connection.setTransactionIsolation(level.getLevel());
    }
    setDesiredAutoCommit(autoCommmit);
  }
  ...
}

2. ManagedTransaction

把事务提交和回滚操作交给运行Mybatis的容器处理，未实现提交和回滚相关方法。
2.3.2 Spring管理
TransactionFactorySpringManagedTransactionFactorySpringManagedTransactionopenConnection()Transaction调用Spring的DataSourceUtils.getConnection()获取连接

MyBatis使用SpringManagedTransactionFactory来获取通过Spring配置的Transaction。

@Override
public Transaction newTransaction(DataSource dataSource, TransactionIsolationLevel level, boolean autoCommit) {
  // 创建 SpringManagedTransaction
  return new SpringManagedTransaction(dataSource);
}

SpringManagedTransaction

private void openConnection() throws SQLException {
  // 通过DataSourceUtils获取connection
  this.connection = DataSourceUtils.getConnection(this.dataSource);
  // 是否自动提交
  this.autoCommit = this.connection.getAutoCommit();
  // 是否启用事务管理，Spring配置
  this.isConnectionTransactional = DataSourceUtils.isConnectionTransactional(this.connection, this.dataSource);

  if (LOGGER.isDebugEnabled()) {
    LOGGER.debug(
        "JDBC Connection ["
            + this.connection
            + "] will"
            + (this.isConnectionTransactional ? " " : " not ")
            + "be managed by Spring");
  }
}

@Override
public void commit() throws SQLException {
  // 根据connection，autoCommit，isConnectionTransactional的值判断是否需要执行提交
  if (this.connection != null && !this.isConnectionTransactional && !this.autoCommit) {
    if (LOGGER.isDebugEnabled()) {
      LOGGER.debug("Committing JDBC Connection [" + this.connection + "]");
    }
    this.connection.commit();
  }
}

@Override
public void rollback() throws SQLException {
  // 根据connection，autoCommit，isConnectionTransactional的值判断是否需要执行回滚
  if (this.connection != null && !this.isConnectionTransactional && !this.autoCommit) {
    if (LOGGER.isDebugEnabled()) {
      LOGGER.debug("Rolling back JDBC Connection [" + this.connection + "]");
    }
    this.connection.rollback();
  }
}

@Override
public void close() throws SQLException {
  // 调用Spring的方法，关闭数据库连接操作交给Spring处理
  DataSourceUtils.releaseConnection(this.connection, this.dataSource);
}

DataSourceUtils，该类为spring-jdbc包中提供的一个工具类。DataSourceUtils提供了静态方法，可根据数据源获取JDBC Connections，包含spring管理的事务连接，也可在自己程序中使用该类。

    Helper class that provides static methods for obtaining JDBC Connections from a DataSource. Includes special support for Spring-managed transactional Connections, e.g. managed by DataSourceTransactionManager or org.springframework.transaction.jta.JtaTransactionManager. Used internally by Spring’s org.springframework.jdbc.core.JdbcTemplate, Spring’s JDBC operation objects and the JDBC DataSourceTransactionManager. Can also be used directly in application code

/**
 * Obtain a Connection from the given DataSource. Translates SQLExceptions into
 * the Spring hierarchy of unchecked generic data access exceptions, simplifying
 * calling code and making any exception that is thrown more meaningful.
 * <p>Is aware of a corresponding Connection bound to the current thread, for example
 * when using {@link DataSourceTransactionManager}. Will bind a Connection to the
 * thread if transaction synchronization is active, e.g. when running within a
 * {@link org.springframework.transaction.jta.JtaTransactionManager JTA} transaction).
 * @param dataSource the DataSource to obtain Connections from
 * @return a JDBC Connection from the given DataSource
 * @throws org.springframework.jdbc.CannotGetJdbcConnectionException
 * if the attempt to get a Connection failed
 * @see #releaseConnection
 */
public static Connection getConnection(DataSource dataSource) throws CannotGetJdbcConnectionException {
  try {
    return doGetConnection(dataSource);
  }
  catch (SQLException ex) {
    throw new CannotGetJdbcConnectionException("Could not get JDBC Connection", ex);
  }
}

/**
 * Actually obtain a JDBC Connection from the given DataSource.
 * Same as {@link #getConnection}, but throwing the original SQLException.
 * <p>Is aware of a corresponding Connection bound to the current thread, for example
 * when using {@link DataSourceTransactionManager}. Will bind a Connection to the thread
 * if transaction synchronization is active (e.g. if in a JTA transaction).
 * <p>Directly accessed by {@link TransactionAwareDataSourceProxy}.
 * @param dataSource the DataSource to obtain Connections from
 * @return a JDBC Connection from the given DataSource
 * @throws SQLException if thrown by JDBC methods
 * @see #doReleaseConnection
 */
public static Connection doGetConnection(DataSource dataSource) throws SQLException {
  Assert.notNull(dataSource, "No DataSource specified");

  ConnectionHolder conHolder = (ConnectionHolder) TransactionSynchronizationManager.getResource(dataSource);
  if (conHolder != null && (conHolder.hasConnection() || conHolder.isSynchronizedWithTransaction())) {
    conHolder.requested();
    if (!conHolder.hasConnection()) {
      logger.debug("Fetching resumed JDBC Connection from DataSource");
      conHolder.setConnection(dataSource.getConnection());
    }
    return conHolder.getConnection();
  }
  // Else we either got no holder or an empty thread-bound holder here.

  logger.debug("Fetching JDBC Connection from DataSource");
  Connection con = dataSource.getConnection();

  if (TransactionSynchronizationManager.isSynchronizationActive()) {
    logger.debug("Registering transaction synchronization for JDBC Connection");
    // Use same Connection for further JDBC actions within the transaction.
    // Thread-bound object will get removed by synchronization at transaction completion.
    ConnectionHolder holderToUse = conHolder;
    if (holderToUse == null) {
      holderToUse = new ConnectionHolder(con);
    }
    else {
      holderToUse.setConnection(con);
    }
    holderToUse.requested();
    TransactionSynchronizationManager.registerSynchronization(
        new ConnectionSynchronization(holderToUse, dataSource));
    holderToUse.setSynchronizedWithTransaction(true);
    if (holderToUse != conHolder) {
      TransactionSynchronizationManager.bindResource(dataSource, holderToUse);
    }
  }

  return con;
}

2.4 插件

 通过Mybatis的插件系统，我们可以很容易的实现一些自定义逻辑，如查询分页等。

Plugin类是插件体系的核心，Plugin.wrap()方法通过JDK的Proxy代理Myabtis在查询中的的相关对象，并调用相关逻辑。

public class Plugin implements InvocationHandler {

  private Object target;
  private Interceptor interceptor;
  private Map<Class<?>, Set<Method>> signatureMap;

  private Plugin(Object target, Interceptor interceptor, Map<Class<?>, Set<Method>> signatureMap) {
    this.target = target;
    this.interceptor = interceptor;
    this.signatureMap = signatureMap;
  }

  // 代理操作，具体参考下文中的 Configuration 定义的相关方法
  public static Object wrap(Object target, Interceptor interceptor) {
    Map<Class<?>, Set<Method>> signatureMap = getSignatureMap(interceptor);
    Class<?> type = target.getClass();
    Class<?>[] interfaces = getAllInterfaces(type, signatureMap);
    if (interfaces.length > 0) {
      return Proxy.newProxyInstance(
          type.getClassLoader(),
          interfaces,
          new Plugin(target, interceptor, signatureMap));
    }
    return target;
  }

  // 调用插件自定义逻辑
  @Override
  public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    try {
      Set<Method> methods = signatureMap.get(method.getDeclaringClass());
      if (methods != null && methods.contains(method)) {
        // 若为插件配置方法，则调用
        return interceptor.intercept(new Invocation(target, method, args));
      }
      return method.invoke(target, args);
    } catch (Exception e) {
      throw ExceptionUtil.unwrapThrowable(e);
    }
  }

  // 解析插件中配置的触发条件，注入数据等
  private static Map<Class<?>, Set<Method>> getSignatureMap(Interceptor interceptor) {
    Intercepts interceptsAnnotation = interceptor.getClass().getAnnotation(Intercepts.class);
    // issue #251
    if (interceptsAnnotation == null) {
      throw new PluginException("No @Intercepts annotation was found in interceptor " + interceptor.getClass().getName());
    }
    Signature[] sigs = interceptsAnnotation.value();
    Map<Class<?>, Set<Method>> signatureMap = new HashMap<Class<?>, Set<Method>>();
    for (Signature sig : sigs) {
      Set<Method> methods = signatureMap.get(sig.type());
      if (methods == null) {
        methods = new HashSet<Method>();
        signatureMap.put(sig.type(), methods);
      }
      try {
        Method method = sig.type().getMethod(sig.method(), sig.args());
        methods.add(method);
      } catch (NoSuchMethodException e) {
        throw new PluginException("Could not find method on " + sig.type() + " named " + sig.method() + ". Cause: " + e, e);
      }
    }
    return signatureMap;
  }

  // 读取被代理对象的实现接口，包括父接口
  private static Class<?>[] getAllInterfaces(Class<?> type, Map<Class<?>, Set<Method>> signatureMap) {
    Set<Class<?>> interfaces = new HashSet<Class<?>>();
    while (type != null) {
      for (Class<?> c : type.getInterfaces()) {
        if (signatureMap.containsKey(c)) {
          interfaces.add(c);
        }
      }
      type = type.getSuperclass();
    }
    return interfaces.toArray(new Class<?>[interfaces.size()]);
  }

}

Configuration类定义了如下方法，创建相关对象的代理对象，使Mybatis在相关操作中调用插件逻辑。

public ParameterHandler newParameterHandler(MappedStatement mappedStatement, Object parameterObject, BoundSql boundSql) {
  ParameterHandler parameterHandler = mappedStatement.getLang().createParameterHandler(mappedStatement, parameterObject, boundSql);
  parameterHandler = (ParameterHandler) interceptorChain.pluginAll(parameterHandler);
  return parameterHandler;
}

public ResultSetHandler newResultSetHandler(Executor executor, MappedStatement mappedStatement, RowBounds rowBounds, ParameterHandler parameterHandler,
    ResultHandler resultHandler, BoundSql boundSql) {
  ResultSetHandler resultSetHandler = new DefaultResultSetHandler(executor, mappedStatement, parameterHandler, resultHandler, boundSql, rowBounds);
  resultSetHandler = (ResultSetHandler) interceptorChain.pluginAll(resultSetHandler);
  return resultSetHandler;
}

public StatementHandler newStatementHandler(Executor executor, MappedStatement mappedStatement, Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) {
  StatementHandler statementHandler = new RoutingStatementHandler(executor, mappedStatement, parameterObject, rowBounds, resultHandler, boundSql);
  statementHandler = (StatementHandler) interceptorChain.pluginAll(statementHandler);
  return statementHandler;
}

插件开发时，插件类继承Interceptor类。

public interface Interceptor {

  // 逻辑处理
  Object intercept(Invocation invocation) throws Throwable;

  // 装饰包裹target
  // 调用 Plugin.wrap()，该方法会创建 target 类的代理对象，具体参考 Plugin 类
  Object plugin(Object target);

  // 设置属性
  void setProperties(Properties properties);

}

InterceptorChain，管理Interceptor实例，Mybatis会根据插件的设定条件在合适的时机进行调用。

public class InterceptorChain {

  private final List<Interceptor> interceptors = new ArrayList<Interceptor>();

 // 调用自定义类的 plugin 方法
  public Object pluginAll(Object target) {
    for (Interceptor interceptor : interceptors) {
      target = interceptor.plugin(target);
    }
    return target;
  }

  public void addInterceptor(Interceptor interceptor) {
    interceptors.add(interceptor);
  }

  public List<Interceptor> getInterceptors() {
    return Collections.unmodifiableList(interceptors);
  }

}

Mybatis提供了一些注解用来定义插件的相关逻辑等，如触发条件，需要注入的数据等。

// 配置拦截器
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Intercepts {
  Signature[] value();
}

// 配置拦截对象，方法等
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Signature {
  // 代理类
  Class<?> type();

  // 代理方法名
  String method();

 // 代理方法参数
  Class<?>[] args();
}

如下示例：

@Intercepts(
    {
        @Signature(type = Executor.class, method = "query", args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class}),
        @Signature(type = Executor.class, method = "query", args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class, CacheKey.class, BoundSql.class}),
    }
)

3. 缓存

Mybatis默认开启缓存，参考Configuration类：

protected boolean cacheEnabled = true;

缓存数据时，使用CacheKey实例为key。该类存储了查询时的方法名，参数，SQL语句，分页等元数据，保证缓存数据时使用的key（与查询绑定）惟一。

public class CacheKey implements Cloneable, Serializable {

  private final int multiplier;
  private int hashcode;
  private long checksum;
  private int count;
  private List<Object> updateList;

  ...

  // 计算更新 hashcode
  public void update(Object object) {
    int baseHashCode = object == null ? 1 : ArrayUtil.hashCode(object);

    count++;
    checksum += baseHashCode;
    baseHashCode *= count;

    hashcode = multiplier * hashcode + baseHashCode;

    updateList.add(object);
  }

}

BaseExecutor定义了创建CacheKey的方法createCacheKey。

public abstract class BaseExecutor implements Executor {

  public CacheKey createCacheKey(MappedStatement ms, Object parameterObject, RowBounds rowBounds, BoundSql boundSql) {
    if (closed) {
      throw new ExecutorException("Executor was closed.");
    }

    // 保证同一查询具有相同的CacheKey
    CacheKey cacheKey = new CacheKey();
    cacheKey.update(ms.getId());
    cacheKey.update(rowBounds.getOffset());
    cacheKey.update(rowBounds.getLimit());
    cacheKey.update(boundSql.getSql());
    List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();
    TypeHandlerRegistry typeHandlerRegistry = ms.getConfiguration().getTypeHandlerRegistry();
    // mimic DefaultParameterHandler logic
    for (ParameterMapping parameterMapping : parameterMappings) {
      if (parameterMapping.getMode() != ParameterMode.OUT) {
        Object value;
        String propertyName = parameterMapping.getProperty();
        if (boundSql.hasAdditionalParameter(propertyName)) {
          value = boundSql.getAdditionalParameter(propertyName);
        } else if (parameterObject == null) {
          value = null;
        } else if (typeHandlerRegistry.hasTypeHandler(parameterObject.getClass())) {
          value = parameterObject;
        } else {
          MetaObject metaObject = configuration.newMetaObject(parameterObject);
          value = metaObject.getValue(propertyName);
        }
        cacheKey.update(value);
      }
    }
    if (configuration.getEnvironment() != null) {
      // issue #176
      cacheKey.update(configuration.getEnvironment().getId());
    }
    return cacheKey;
  }

  ...
}

CachingExecutor通过过包裹其它Executor来缓存查询数据。

public class CachingExecutor implements Executor {

  @Override
  public <E> List<E> query(MappedStatement ms, Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler, CacheKey key, BoundSql boundSql)
      throws SQLException {
    Cache cache = ms.getCache();
    // 是否有缓存
    if (cache != null) {
      flushCacheIfRequired(ms);
      if (ms.isUseCache() && resultHandler == null) {
        ensureNoOutParams(ms, parameterObject, boundSql);
        @SuppressWarnings("unchecked")
        List<E> list = (List<E>) tcm.getObject(cache, key);
        if (list == null) {
          list = delegate.<E> query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);
          tcm.putObject(cache, key, list);
        }
        return list;
      }
    }
    return delegate.<E> query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);
  }

  ...
}

Cache的默认实现为PerpetualCache。该类使用HashMap来储存缓存数据。并通过“装饰者模式”来处理缓存失效等。默认为LruCache类，该类使用LRU算法，即“最近最少使用”原则。

public class LruCache implements Cache {
  private final Cache delegate;
  private Map<Object, Object> keyMap;
  private Object eldestKey;

  public LruCache(Cache delegate) {
    this.delegate = delegate;
    setSize(1024);
  }

  public void setSize(final int size) {
    // LinkedHashMap 的 accessOrder 值为 true，即调用get()方法时会进行排序，并通过重写 removeEldestEntry 来移除超出最大数量的元素，即实现LRU
    keyMap = new LinkedHashMap<Object, Object>(size, .75F, true) {
      private static final long serialVersionUID = 4267176411845948333L;

      @Override
      protected boolean removeEldestEntry(Map.Entry<Object, Object> eldest) {
        boolean tooBig = size() > size;
        if (tooBig) {
          eldestKey = eldest.getKey();
        }
        return tooBig;
      }
    };
  }

  ...
}

缓存的配置有两种方式：

    注解
    XML

本文以解析XML中定义的Cache标签为例，注解方式的解析可查看MapperAnnotationBuilder类。

public class XMLMapperBuilder extends BaseBuilder {

  private void cacheElement(XNode context) throws Exception {
    if (context != null) {
      String type = context.getStringAttribute("type", "PERPETUAL");
      Class<? extends Cache> typeClass = typeAliasRegistry.resolveAlias(type);
      String eviction = context.getStringAttribute("eviction", "LRU");
      Class<? extends Cache> evictionClass = typeAliasRegistry.resolveAlias(eviction);
      Long flushInterval = context.getLongAttribute("flushInterval");
      Integer size = context.getIntAttribute("size");
      boolean readWrite = !context.getBooleanAttribute("readOnly", false);
      boolean blocking = context.getBooleanAttribute("blocking", false);
      Properties props = context.getChildrenAsProperties();
      builderAssistant.useNewCache(typeClass, evictionClass, flushInterval, size, readWrite, blocking, props);
    }
  }
  ...
}

通过MapperBuilderAssistant构建Cache实例：

public class MapperBuilderAssistant extends BaseBuilder {
  public Cache useNewCache(Class<? extends Cache> typeClass,
      Class<? extends Cache> evictionClass,
      Long flushInterval,
      Integer size,
      boolean readWrite,
      boolean blocking,
      Properties props) {
    Cache cache = new CacheBuilder(currentNamespace)
        .implementation(valueOrDefault(typeClass, PerpetualCache.class))
        .addDecorator(valueOrDefault(evictionClass, LruCache.class))
        .clearInterval(flushInterval)
        .size(size)
        .readWrite(readWrite)
        .blocking(blocking)
        .properties(props)
        .build();
    configuration.addCache(cache);
    currentCache = cache;
    return cache;
  }

  ...
}

以上就是Mybaits源码解析的全部内容了。