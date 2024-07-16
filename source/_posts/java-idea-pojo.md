---
title: 使用IntelliJ IDEA生成代码
date: 2019-05-26 11:05:56
categories: 
- Java
tags: 
- IntelliJ IDEA
- POJO
---

IntelliJ IDEA可以根据数据库生成“POJO"代码，在此基础上，可以通过修改Generate POJOs.groovy文件来生成自定义的代码如：Controller, Service。
<!-- more -->

## 1. 编写Generate POJOs.groovy
```Groovy
import com.intellij.database.model.DasTable
import com.intellij.database.model.DasColumn
import com.intellij.database.model.ObjectKind
import com.intellij.database.util.Case
import com.intellij.database.util.DasUtil


basePackageName = "basePackageName"
packageName = basePackageName + ".repository.entity"
repositoryPackageName = basePackageName + ".repository"
servicePackageName = basePackageName + ".service"
serviceImplPackageName = basePackageName + ".service.impl"
ControllerPackageName = basePackageName + ".controller"

allTables=new HashMap<>()

schemeName = "tk_ct"

typeMapping = [
        (~/(?i)int/)                      : "Integer",
        (~/(?i)long|bigint/)              : "Long",
        (~/(?i)number/)                   : "String",
        (~/(?i)float|double|decimal|real/): "Double",
        (~/(?i)datetime|timestamp/)       : "java.sql.Timestamp",
        (~/(?i)date/)                     : "java.sql.Date",
        (~/(?i)time/)                     : "java.sql.Time",
        (~/(?i)/)                         : "String"
]


FILES.chooseDirectoryAndSave("Choose entity directory", "Choose where to store generated files") { dir ->
    SELECTION.filter { it instanceof DasTable && it.getKind() == ObjectKind.TABLE }.each {
        generate(it, dir)
    }
}

FILES.chooseDirectoryAndSave("Choose repository directory", "Choose where to store generated files") { dir ->
    allTables.each { className, table ->
        new File(dir, className + "Repository.java").withPrintWriter { out ->
            generateRepository(out, className, table, getId(table))
        }
    }
}

FILES.chooseDirectoryAndSave("Choose service directory", "Choose where to store generated files") { dir ->
    allTables.each { className, table ->
        new File(dir, className + "Service.java").withPrintWriter { out ->
            generateService(out, className, table,  getId(table))
        }
    }
}
FILES.chooseDirectoryAndSave("Choose service impl directory", "Choose where to store generated files") { dir ->
    allTables.each { className, table ->
        new File(dir, className + "ServiceImpl.java").withPrintWriter { out ->
            generateServiceImpl(out, className, table,  getId(table))
        }
    }
}
FILES.chooseDirectoryAndSave("Choose  controller directory", "Choose where to store generated files") { dir ->
    allTables.each { className, table ->
        new File(dir, className + "Controller.java").withPrintWriter { out ->
            generateController(out, className, table)
        }
    }
}


def generate(table, dir) {
    def className = javaName(table.getName(), true)
    allTables.put(className, table)
    def fields = calcFields(table, className)
    new File(dir, className + ".java").withPrintWriter { out ->
        generate(out, className, fields,table)
    }
}

def generate(out, className, fields, table) {
    out.println "package $packageName ;"
    out.println ""
    out.println '''
import java.io.Serializable;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import javax.validation.constraints.NotNull;
import net.cofcool.chaos.server.common.util.ValidationGroups.Insert;
'''
    out.println ""
    out.println ""
    out.println ""
    generateComment(out, table.getComment().replaceAll("表",""))
    out.println ""
    out.println "@Table(name =\"" + table.getName() + "\", schema = \""  + schemeName +  "\")"
    out.println "@Entity"
    out.println "@Getter"
    out.println "@Setter"
    out.println "@NoArgsConstructor"
    out.println "@ToString"
    out.println "public class $className  implements Serializable {"
    out.println ""
    out.println ""
    out.println genSerialID()
    out.println ""
    fields.each() {
        out.println "    /**"
        out.println "     * " + it.comment
        out.println "     */"

        if (it.annos.size() >0)
        {
            it.annos.each() {
                out.println "    ${it}"
            }
        }
        out.println "    private ${it.type} ${it.name};"
        out.println ""
    }
    out.println ""

    out.println "}"
}

def generateRepository(out, className, table, idType) {
    out.println "package $repositoryPackageName ;"
    out.println ""
    out.println "import $packageName.$className;"
    out.println "import org.springframework.data.jpa.repository.JpaRepository;"
    out.println "import org.springframework.data.jpa.repository.JpaSpecificationExecutor;"
    out.println ""
    out.println ""
    generateComment(out, table.getComment())
    out.println "public interface " + className + "Repository extends JpaRepository<$className, $idType>, JpaSpecificationExecutor<$className> {"
    out.println ""
    out.println "}"
}

private void generateComment(out, comment = null) {
    out.println "/**"
    out.println " * " + comment
    out.println " *"
    out.println " * <p>Date: " + new java.util.Date().toString() + "</p>"
    out.println " */"
}

def generateController(out, className, table) {
    def lit = toLowerCaseFirstOne(className)
    out.println "package $ControllerPackageName;"
    out.println ""
    out.println '''
import javax.annotation.Resource;
import net.cofcool.chaos.server.common.core.Message;
import com.xingdata.server.ct.api.MyPage;
import net.cofcool.chaos.server.common.core.Result.ResultState;
import net.cofcool.chaos.server.common.util.ValidationGroups.Delete;
import net.cofcool.chaos.server.common.util.ValidationGroups.Insert;
import net.cofcool.chaos.server.common.util.ValidationGroups.Select;
import net.cofcool.chaos.server.common.util.ValidationGroups.Update;
import net.cofcool.chaos.server.core.annotation.Api;
import java.util.List;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
// 这里的注释用于yapi自动上传文档
'''
    out.println "import $packageName.$className;"
    out.println "import $servicePackageName" + "." + className + "Service;"
    out.println ""
    out.println ""
    out.println ""
    out.println "/**"
    out.println " * @description: " + table.getComment().replaceAll("表","")
    out.println " * @menu " + table.getComment().replaceAll("表","")
    out.println " *"
    out.println " * <p>Date: " + new java.util.Date().toString() + "</p>"
    out.println " */"
    out.println "@Api"
    out.println "@RestController"
    out.println "@RequestMapping(value = \"/$lit\", method = RequestMethod.POST)"
    out.println "public class " + className + "Controller {"
    out.println ""
    out.println "    @Resource"
    out.println "    private " + className + "Service " + lit + "Service;"
    out.println ""
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "分页查询"
    out.println "     * @param: [Page<" + className + ">]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message"
    out.println "     * @data: "+ new java.util.Date().toString()
    out.println "     */"
    out.println "    @PostMapping(\"/query\")"
    out.println "    public Message query(@RequestBody MyPage<$className> page) {"
    out.println "        return " + lit + "Service.query(page, page.getCondition()).result();"
    out.println "    }"
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "添加"
    out.println "     * @param: [" + className + "]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message<$className>"
    out.println "     */"
    out.println "    @PostMapping(\"/add\")"
    out.println "    public Message<$className> add(@RequestBody @Validated(Insert.class) $className entity) {"
    out.println "        return " + lit + "Service.add(entity).result();"
    out.println "    }"
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "修改"
    out.println "     * @param: [" + className + "]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message<$className>"
    out.println "     * @data: "+ new java.util.Date().toString()
    out.println "     */"
    out.println "    @PostMapping(\"/update\")"
    out.println "    public Message<$className> update(@RequestBody @Validated(Update.class) $className entity) {"
    out.println "        return " + lit + "Service.update(entity).result();"
    out.println "    }"
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "详情"
    out.println "     * @param: [" + className + "]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message<$className>"
    out.println "     * @data: "+ new java.util.Date().toString()
    out.println "     */"
    out.println "    @PostMapping(\"/detail\")"
    out.println "    public Message<$className> detail(@RequestBody @Validated(Select.class) $className entity) {"
    out.println "        return " + lit + "Service.queryById(entity).result();"
    out.println "    }"
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "全部查询"
    out.println "     * @param: [" + className + "]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message<List<$className>>"
    out.println "     * @data: "+ new java.util.Date().toString()
    out.println "     */"
    out.println "    @PostMapping(\"/queryAll\")"
    out.println "    public Message<List<$className>> queryAll(@RequestBody $className entity) {"
    out.println "        return " + lit + "Service.queryAll(entity).result();"
    out.println "    }"
    out.println ""
    out.println "    /**"
    out.println "     * @description: " + table.getComment().replaceAll("表","") + "删除"
    out.println "     * @param: [" + className + "]"
    out.println "     * @menu " + table.getComment().replaceAll("表","")
    out.println "     * @return: Message<$className>"
    out.println "     * @data: "+ new java.util.Date().toString()
    out.println "     */"
    out.println "    @PostMapping(\"/delete\")"
    out.println "    public ResultState delete(@RequestBody @Validated(Delete.class) $className entity) {"
    out.println "        return " + lit + "Service.delete(entity);"
    out.println "    }"
    out.println ""
    out.println ""
    out.println "}"
}

def toLowerCaseFirstOne(s){
    if(Character.isLowerCase(s.charAt(0)))
        return s;
    else
        return (new StringBuilder()).append(Character.toLowerCase(s.charAt(0))).append(s.substring(1)).toString();
}

def generateService(out, className, table, idType) {
    out.println "package $servicePackageName;"
    out.println ""
    out.println "import $packageName.$className;"
    out.println "import com.xingdata.server.ct.api.BaseService;"
    out.println ""
    out.println ""
    out.println ""
    generateComment(out, table.getComment())
    out.println "public interface " + className + "Service extends BaseService<$className> {"
    out.println ""
    out.println "}"
}

def generateServiceImpl(out, className, table, idType) {
    out.println "package $serviceImplPackageName;"
    out.println ""
    out.println '''
import net.cofcool.chaos.server.common.core.Page;
import net.cofcool.chaos.server.data.jpa.support.Paging;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import com.xingdata.server.ct.api.BaseServiceImpl;
'''
    out.println "import $packageName" + "." + className + ";"
    out.println "import $repositoryPackageName" + "." + className + "Repository;"
    out.println "import $servicePackageName" + "." + className + "Service;"
    out.println ""
    out.println ""
    out.println ""
    generateComment(out, table.getComment())
    out.println "@Service"
    out.println "public class " + className + "ServiceImpl extends BaseServiceImpl<$className, $idType, $className" + "Repository>  implements " + className + "Service {"
    out.println "    @Override"
    out.println "    protected Object queryWithSp(Specification<$className> sp, Page<$className> condition, $className entity) {"
    out.println "        return getJpaRepository().findAll(sp, Paging.getPageable(condition));"
    out.println "    }"
    out.println ""
    out.println "    @Override"
    out.println "    protected $idType getEntityId($className entity) {"
    out.println "        return entity.getId();"
    out.println "    }"
    out.println ""
    out.println "}"
}

def calcFields(table, javaName) {
    DasUtil.getColumns(table).reduce([]) { fields, col ->
        def spec = Case.LOWER.apply(col.getDataType().getSpecification())
        def typeStr = typeMapping.find { p, t -> p.matcher(spec).find() }.value
        def colName = columnName(col.getName());
        def comm = [
                name : colName,
                type : typeStr,
                annos: [],
                comment: col.getComment()
        ]

        def isTime = colName == "timeUpdate" || colName == "timeCreate"
        def isData = colName=="dataReserve"
        if (isTime) {
            comm.annos += ["@Column(name = \"" + col.getName() + "\", insertable = false, updatable = false)"]
        } else {
            comm.annos += ["@Column(name = \"" + col.getName() + "\")"]
        }

        if (table.getColumnAttrs(col).contains(DasColumn.Attribute.PRIMARY_KEY)) {
            comm.annos += ["@Id"]
            comm.annos += ["@GeneratedValue(strategy = GenerationType.IDENTITY)"]
        } else if (!isTime){
            if(!isData){
                comm.annos += ["@NotNull(groups = {Insert.class})"]
            }
        }

        fields += [comm]
    }
}

def getId(table) {
    def type = "";
    DasUtil.getColumns(table).reduce([]) { fields, col ->
        def spec = Case.LOWER.apply(col.getDataType().getSpecification())
        def typeStr = typeMapping.find { p, t -> p.matcher(spec).find() }.value
        if (table.getColumnAttrs(col).contains(DasColumn.Attribute.PRIMARY_KEY)) {
            type = typeStr
        }
    }

    return type
}


def javaName(str, capitalize) {
    def s = com.intellij.psi.codeStyle.NameUtil.splitNameIntoWords(str)
            .collect { Case.LOWER.apply(it).capitalize() }
            .subList(1, 2)
            .join("")
            .replaceAll(/[^\p{javaJavaIdentifierPart}[_]]/, "_")
    capitalize || s.length() == 1 ? s : Case.LOWER.apply(s[0]) + s[1..-1]
}

def columnName(str) {
    def s = com.intellij.psi.codeStyle.NameUtil.splitNameIntoWords(str)
            .collect { Case.LOWER.apply(it).capitalize() }
            .join("")
            .replaceAll(/[^\p{javaJavaIdentifierPart}[_]]/, "_")
    s.length() == 1? s : Case.LOWER.apply(s[0]) + s[1..-1]
}

static String genSerialID()
{
    return "    private static final long serialVersionUID =  " + Math.abs(new Random().nextLong())+"L;"
}
```

## 2. 生成代码
1. 在idea Database上添加Datasource
2. 在需要生成的表右键
3. 点击Scripted Extensions -> Generate POJOs.groovy
4. 生成代码