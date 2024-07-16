---
title: 使用mybatis-plus-generator,freemarker模板生成代码
date: 2019-04-07 09:15:16
categories: 
- Java
tags: 
- mybatis-plus
- freemarker
---

在使用mybatis-plus时也可以快速生成代码，并且可以自定义模板，这里使用freemarker模板
<!-- more -->
1. maven引入
2. 创建模板文件
3. 配置
4. 生成代码

## 1. maven引入
需要引入如下依赖：
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus</artifactId>
    <version>3.1.0</version>
</dependency>
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-generator</artifactId>
    <version>3.1.2</version>
</dependency>
<dependency>
    <groupId>org.freemarker</groupId>
    <artifactId>freemarker</artifactId>
    <version>2.3.28</version>
</dependency>
```
## 2. 创建模板文件
常规需要创建controller.java.ftl，entity.java.ftl，mapper.java.ftl，service.java.ftl， serviceImpl.java.ftl这些模板。可根据差异变化模板内容。这里提供参考模板：
controller.java.ftl
```FreeMarker
package ${package.Controller};

import javax.annotation.Resource;
import org.springframework.stereotype.Controller;
import org.springframework.validation.BindingResult;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import ${package.Service}.${table.serviceName};
import ${package.Entity}.${table.entityName};

/**
 * <p>
 * ${table.comment!}接口
 * </p>
 *
 * @author ${author}
 * @since ${date}
 */
@Controller
@RequestMapping(value = "${table.entityName?lower_case}", method = {RequestMethod.POST})
public class ${table.controllerName}{

    @Resource
    private ${table.serviceName}<${table.entityName}> ${table.entityName?lower_case}Service;

    /**
     * ${table.comment!}列表查询
     * @param page 查询条件
     * @return QueryResult<${table.entityName}>
     */
    @RequestMapping("/query")
    public @ResponseBody
    QueryResult<${table.entityName}> query(@RequestBody Page<${table.entityName}> page) {
        return ${table.entityName?lower_case}Service.selectByCondition(page, page.getCondition(${table.entityName}.class));
    }

    /**
     * ${table.comment!}添加
     * @param ${table.entityName?lower_case} ${table.comment!}实体类
     * @param bindingResult　验参信息
     * @return SqlExecuteResult<${table.entityName}>
     */
    @RequestMapping("/add")
    public @ResponseBody
    SqlExecuteResult<${table.entityName}> add(@RequestBody @Validated({Insert.class}) ${table.entityName} ${table.entityName?lower_case}, BindingResult bindingResult) {
       return ${table.entityName?lower_case}Service.add(${table.entityName?lower_case});
    }

    /**
     * ${table.comment!}删除
     * @param baseParam baseParam
     * @return SqlExecuteResult<${table.entityName}>
     */
    @RequestMapping(value = "/delete")
    public @ResponseBody
    Integer delete(@RequestBody @Validated BaseParam baseParam, BindingResult bindingResult) {
       ${table.entityName} ${table.entityName?lower_case} = new ${table.entityName}();
       ${table.entityName?lower_case}.setId(Long.valueOf(baseParam.getId()));
       return ${table.entityName?lower_case}Service.delete(${table.entityName?lower_case});
    }
            
    /**
     * ${table.comment!}修改
     * @param ${table.entityName?lower_case}　${table.comment!}实体类
     * @param bindingResult　验参信息
     * @return SqlExecuteResult<${table.entityName}>
     */
    @RequestMapping("/update")
    public @ResponseBody
    SqlExecuteResult<${table.entityName}> update(@RequestBody @Validated({Update.class}) ${table.entityName} ${table.entityName?lower_case}, BindingResult bindingResult) {
        return ${table.entityName?lower_case}Service.update(${table.entityName?lower_case});
    }

    /**
     * ${table.comment!}详情
     * @param baseParam baseParam
     * @return SqlExecuteResult<${table.entityName}>
     */
    @RequestMapping("/detail")
    public @ResponseBody
    SqlExecuteResult<${table.entityName}> detail(@RequestBody @Validated BaseParam baseParam, BindingResult bindingResult) {
        ${table.entityName} ${table.entityName?lower_case} = new ${table.entityName}();
        ${table.entityName?lower_case}.setId(new Long(baseParam.getId()));
        return ${table.entityName?lower_case}Service.selectById(${table.entityName?lower_case});
    }
}
```

mapper.java.ftl
```freemarker
package ${package.Mapper};

import ${package.Entity}.${entity};
import ${superMapperClassPackage};
import org.springframework.stereotype.Component;

/**
 * <p>
 * ${table.comment!} Mapper
 * </p>
 *
 * @author ${author}
 * @since ${date}
 */
<#if kotlin>
interface ${table.mapperName} : ${superMapperClass}<${entity}>
<#else>
@Component
public interface ${table.mapperName} extends ${superMapperClass}<${entity}> {

}
</#if>
```

## 3. 配置
创建CodeGenerator.java

```java
package com.generator;

import com.baomidou.mybatisplus.generator.AutoGenerator;
import com.baomidou.mybatisplus.generator.InjectionConfig;
import com.baomidou.mybatisplus.generator.config.*;
import com.baomidou.mybatisplus.generator.config.rules.NamingStrategy;
import com.baomidou.mybatisplus.generator.engine.FreemarkerTemplateEngine;

public class CodeGenerator {

    /**
     * 可以看mybatis-plus官方文档，详细了解
     * 项目位置及author
     */
    private static String projectPath = "";
    private static String outputDir = "";
    private static String author = "";

    /**
     * 数据库配置
     */
    private static String dataUrl = "j";
    private static String dataUserName = "";
    private static String dataPassword = "";
    private static String dataDriver = "";

    /**
     * 输出文件位置
     */
    private static String moduleName = "";
    private static String parent = "";
    private static String dao = "";
    private static String service = "";
    private static String domian = "";
    private static String controller = "";
    private static String serviceImpl = "";
    private static String xml = "";

    /**
     * 要生成的数据库表名，以逗号分割 示例:cfg_skutype,node_rchg
     */
    private static String tableName = "";

    /**
     * 执行该主方法生成
     * @param args null
     */
    public static void main(String[] args) {
        generator();
    }

    private static void generator() {
        AutoGenerator mpg = new AutoGenerator();
        GlobalConfig gc = new GlobalConfig();
        gc.setOutputDir(projectPath + outputDir);
        gc.setAuthor(author);
        gc.setOpen(false);
        mpg.setGlobalConfig(gc);

        // 数据源配置
        DataSourceConfig dsc = new DataSourceConfig();
        dsc.setUrl(dataUrl);
        dsc.setDriverName(dataDriver);
        dsc.setUsername(dataUserName);
        dsc.setPassword(dataPassword);
        mpg.setDataSource(dsc);

        // 包配置
        PackageConfig pc = new PackageConfig();
        pc.setModuleName(moduleName);
        pc.setParent(parent);
        pc.setController(controller);
        pc.setEntity(domian);
        pc.setService(service);
        pc.setServiceImpl(serviceImpl);
        pc.setMapper(dao);
        pc.setXml(xml);
        mpg.setPackageInfo(pc);

        // 自定义配置
        InjectionConfig cfg = new InjectionConfig() {
            @Override
            public void initMap() {

            }
        };
        mpg.setCfg(cfg);

        // 配置模板，也就是2中的模板
        TemplateConfig templateConfig = new TemplateConfig();
        templateConfig.setController("controller.java");
        templateConfig.setEntity("entity.java");
        templateConfig.setMapper("mapper.java");
        templateConfig.setService("service.java");
        templateConfig.setServiceImpl("serviceImpl.java");
        templateConfig.setXml(null);
        mpg.setTemplate(templateConfig);

        // 策略配置
        StrategyConfig strategy = new StrategyConfig();
        strategy.setNaming(NamingStrategy.underline_to_camel);
        strategy.setColumnNaming(NamingStrategy.underline_to_camel);
        strategy.setSuperEntityClass("com.baomidou.ant.common.BaseEntity");
        strategy.setEntityLombokModel(true);
        strategy.setRestControllerStyle(true);
        strategy.setSuperEntityColumns("id");
        strategy.setInclude(tableName.split(","));
        strategy.setControllerMappingHyphenStyle(true);
        strategy.setTablePrefix(pc.getModuleName() + "_");
        mpg.setStrategy(strategy);
        mpg.setTemplateEngine(new FreemarkerTemplateEngine());
        mpg.execute();
    }
}

```

## 4. 生成代码
执行CodeGenerator中main方法生成代码。

这样，就快速生成了代码。
