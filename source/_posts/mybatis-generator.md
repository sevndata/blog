---
title: 使用mybatis-generator及git生成代码
date: 2018-06-16 09:50:00
categories: 
- Java
tags: 
- Mybatis
- Git
---

在基于Spring,Spring MVC,mybatis进行java web开发时，往往会需要写大量的重复性代码，可以使用mybatis-generator及git配合生成重复代码。
<!-- more -->
1. mybatis-generator
2. git提交一次模板代码
3. 提取模板patch
4. 生成相关patch
5. 合并patch到分支
4. 修改可能产生的错误

## 1. mybatis-generator
可以通过mybatis-generator jar方式执行生成DAO，这里通过maven方式生成
1. 创建generatorConfig.xml文件
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE generatorConfiguration 
        PUBLIC "-//mybatis.org//DTD MyBatis Generator Configuration 1.0//EN"
        "http://mybatis.org/dtd/mybatis-generator-config_1_0.dtd">

<generatorConfiguration>
    <classPathEntry
            location="mysql-connector-java-x.x.x.jar path"/>
    <context id="zq_mysql_tables" targetRuntime="MyBatis3">
        <plugin type="org.mybatis.generator.plugins.SerializablePlugin"/>

        <commentGenerator>
            <property name="suppressAllComments" value="true"/>
            <property name="suppressDate" value="true"/>
        </commentGenerator>

        <jdbcConnection driverClass="com.mysql.jdbc.Driver"
                        connectionURL="mysql url"
                        userId="mysql username"
                        password="mysql userpassword">
        </jdbcConnection>

        <javaTypeResolver>
            <property name="forceBigDecimals" value="false"/>
        </javaTypeResolver>

        <javaModelGenerator targetPackage="domian package" targetProject="src">
            <property name="enableSubPackages" value="false"/>
            <property name="trimStrings" value="true"/>
        </javaModelGenerator>

        <sqlMapGenerator targetPackage="mapper package" targetProject="src">
            <property name="enableSubPackages" value="false"/>
        </sqlMapGenerator>

        <javaClientGenerator type="XMLMAPPER" targetPackage="xml package" targetProject="src">
            <property name="enableSubPackages" value="false"/>
        </javaClientGenerator>

        <table tableName="tableName" domainObjectName="DomainName">
            <generatedKey column="private key" sqlStatement="MySql" identity="true"/>
        </table>
    </context>
</generatorConfiguration>
```
2. 引入build，pom.xml如下：
```xml
<build>
    <finalName>name</finalName>
    <plugins>
        <plugin>
            <groupId>org.mybatis.generator</groupId>
            <artifactId>mybatis-generator-maven-plugin</artifactId>
            <version>x.x.x</version>
            <configuration>
                <verbose>true</verbose>
                <overwrite>true</overwrite>
            </configuration>
        </plugin>
    </plugins>
</build>
```
3. 执行maven命令
mybatis-generator:generate -e
这样就会生成DAO。

## 2. git提交一次模板代码
写好Controller,Service等相关代码，然后做一次提交。

## 3. 提取模板patch
执行git format-patch HEAD^提取提交的patch文件

## 4. 生成相关patch
1. 创建GenerateCode.java如下：
```java
public class GenerateCode {

    private static final String PATCH_PATH = "模板patch文件地址";

    private static final String PATCH_BASE_PATH = "目标patch生成地址";

    private BufferedReader reader;

    private List<String[]> allKeys;

    public GenerateCode() throws FileNotFoundException {
        this.reader = getBufferedReader();
    }

    public static void main(String[] args) {
        List<String[]> allKeys = new ArrayList<>();
        //新表，定义新的内容（将要替换的内容），每个表都需要添加
        allKeys.add(new String[]{"表前缀", "表model名", "详细描述"});
        allKeys.add(new String[]{"表前缀", "表model名", "详细描述"});
        try {
            GenerateCode generateCode = new GenerateCode();
            generateCode.setAllKeys(allKeys);
            generateCode.generatePatch();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void generatePatch() throws IOException {
        File file = new File(PATCH_BASE_PATH);
        file.mkdirs();

        for (String[] keys : allKeys) {
            reader = getBufferedReader();
            replacePatch(keys);
        }
    }

    private void replacePatch(String[] keys) throws IOException {
        StringBuilder newStrs = new StringBuilder();

        String lineStr = null;
        while ((lineStr = reader.readLine()) != null) {
            newStrs.append(replaceStr(lineStr, keys)).append("\n");
        }

        writePatch(newStrs.toString(), keys[1]);
    }

    private void writePatch(String string, String fileName) throws FileNotFoundException {
        FileOutputStream outputStream = new FileOutputStream(new File(PATCH_BASE_PATH + File.separator + fileName + ".patch"));
        PrintStream ps = new PrintStream(outputStream);
        ps.append(string);
        ps.close();
    }

    private BufferedReader getBufferedReader() throws FileNotFoundException {
        FileReader fileReader = new FileReader(new File(PATCH_PATH));
        return new BufferedReader(fileReader);
    }

    private String replaceStr(String originStr, String[] keys) {
        //原来的内容，要被替换掉的内容
        return originStr.replace("表前缀", keys[0])
                .replace("表model名 Foo", keys[1])
                .replace("表model名变量名 foo", toLowerCaseFirstOne(keys[1]))
                .replace("文字描述", keys[2]);
    }

    public List<String[]> getAllKeys() {
        return allKeys;
    }

    public void setAllKeys(List<String[]> allKeys) {
        this.allKeys = allKeys;
    }

    public String toLowerCaseFirstOne(String s) {
        if (Character.isLowerCase(s.charAt(0)))
            return s;
        else
            return (new StringBuilder()).append(Character.toLowerCase(s.charAt(0))).append(s.substring(1)).toString();
    }
}
```
2. 执行main方法，生成patch文件
原理为：生成模板patch，然后通过构建新表的对象名，描述等信息替换模板patch中的关键字内容并生成新的patch文件。

## 5. 合并patch到分支
执行git am *.patch，将新生成的patch文件合并到代码分支

## 6. 修改可能产生的错误
批量生成避免不了产生语法错误的代码，稍做修改并完善即可。

这样就快速的生成了代码，大大提高了生产力。