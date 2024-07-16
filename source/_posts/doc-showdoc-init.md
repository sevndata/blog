---
title: ShowDoc的导入与安装
date: 2020-09-09 09:15:16
categories: 
- ShowDoc
- python
tags: 
- ShowDoc
- python
---
本文分享了ShowDoc安装，使用及导入。
<!-- more -->

分享一款好用的在线文档分享工具。一直在寻找一款好用的接口文档工具，曾经尝试过`Swagger`，`YApi`，`gitLab wiki`都差强人意。发现`ShowDoc`后十分惊喜，并且它可以私有化部署。

### 简介

ShowDoc是一个非常适合IT团队的在线文档分享工具，可以访问[github](https://github.com/star7th/showdoc)详细了解。同时可以参考[帮助文档](https://www.showdoc.cc/help)进行私有化部署。下文主要为私有化部署过程，导入的分享。

### 安装

官方提供了自动脚本部署，Docker部署，PHP部署，二次开发等方法进行私有化部署，强烈推荐使用自动脚本部署，[详细脚本内容](https://www.showdoc.com.cn/script/showdoc)下载查看

```shell
  #下载脚本并赋予权限
   wget https://www.showdoc.com.cn/script/showdoc;
   chmod +x showdoc;
  #默认安装中文版。如果想安装英文版，请加上en参数，如 ./showdoc en
  ./showdoc
```

### md导入

安装完成后登录到web可以看到简洁的文档操作界面。然而碰到一个问题，原有的文档在gitLab wiki中，查找到官方没有提供导入`.md`的功能，但是提供了[开放API接口](https://www.showdoc.com.cn/page/102098)，可以利用此接口导入。

以下为通过python读取文件下的`.md`文件，并通过开放API接口导入到`ShowDoc`中

```py
import os
import json
import urllib.parse
import urllib.request
import fileinput
import operator

# 需要导入的文件夹地址
wiki_dir = '/Users/xx/work/doc'

# showdoc开放API参数
data = {
    'api_key' : 'xx', 
    'api_token' : 'xx',
    'cat_name' : 'API',
    'page_title' : '',
    'page_content' : ''
    }
# showdoc开放API地址
url = 'http://xxx.com/server/index.php?s=/api/item/updateByApi'

def get_filelist(dir):
    # 获取文件夹中所有文件，去除mac下.DS_Store文件。并排序文件
    for home, dirs, files in os.walk(dir):
        for dir in dirs:
            print(dir)
        if '.DS_Store' in files:
            files.remove('.DS_Store')
        files.sort()
        for filename in files:
            fullname = os.path.join(home, filename)
            get_file(filename,fullname)

def get_file(filename,fullname):
    # 读取文件，拼接showdoc参数
    try:
        with open(fullname, encoding='utf-8') as file_obj:
            lines = file_obj.read()
        data['page_title'] = filename.replace('.md','')
        data['page_content'] = lines
        do_post(data)
    except UnicodeDecodeError:
        print(fullname)

def do_post(data):
    # 请求showdoc开放API
    data = urllib.parse.urlencode(data)
    req = urllib.request.Request(url, data.encode())
    opener = urllib.request.urlopen(req)
    json.loads(opener.read().decode())

if __name__ == "__main__":
    get_filelist(wiki_dir)
```

### 数据库字典导入
  
官方提供了数据库字典的导入方法。

```shell
   wget https://www.showdoc.cc/script/showdoc_db.sh
```

```shell
   sh showdoc_db.sh
```

需要修改脚本内容后执行`showdoc_db.sh`

```shell
#!/bin/bash

host="xxx"				#数据库所在地址。默认是localhost
port=3306						#数据库所在端口。默认是3306
user="xxx"   	 			#数据库的用户名
password="xxx" 			#密码
db="xxx" 					#要同步的数据库名。要同步多个db可以将本脚本复制多份
api_key="xxx" 			#api_key
api_token="xxx" 	#api_token
cat_name="xxx" 	#可选。如果想把生成的文档都放在项目的子目录下，则这里填写子目录名。
url="http://xxx.com/server/index.php?s=/api/open/updateDbItem" #可选。同步到的url。如果是使用www.showdoc.com.cn ，则不需要再改此项。如果是部署私有版版showdoc，请改此项为http://xx.com/server/index.php?s=/api/open/updateDbItem 。其中xx.com为你的部署域名

export MYSQL_PWD=${password}
COMMAND="set names utf8;select TABLE_NAME ,TABLE_COMMENT from tables where TABLE_SCHEMA ='${db}'  "
declare table_info=`mysql -h${host} -P${port} -u${user}  --show-warnings=false -D information_schema -e "${COMMAND}" `
#echo $table_info
COMMAND="set names utf8;select TABLE_NAME ,COLUMN_NAME, COLUMN_DEFAULT ,IS_NULLABLE ,COLUMN_TYPE ,COLUMN_COMMENT from COLUMNS where TABLE_SCHEMA ='${db}'  "
declare table_detail=`mysql -h${host} -P${port} -u${user}  --show-warnings=false -D information_schema -e "${COMMAND}" `
#echo $table_detail
table_info2=${table_info//&/_this_and_change_}
table_detail2=${table_detail//&/_this_and_change_}
curl -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8'  "${url}" --data-binary @- <<CURL_DATA
from=shell&table_info=${table_info2}&table_detail=${table_detail2}&api_key=${api_key}&api_token=${api_token}&cat_name=${cat_name}
CURL_DATA
export MYSQL_PWD=""
```

