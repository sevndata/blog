---
title: 利用Python做web国际化，提取语言文件
date: 2022-07-08 09:15:16
categories: 
- Python
tags: 
- Python
---
本文分享了Web项目国际化过程中提取语言文件，让代码帮你工作。
<!-- more -->

起因是一次Web项目需要国际化，但项目前期未考虑到项目需要国际化，所以大量汉字在`JS`文件中，未提取到语言文件中。需要人工提取汉字并以映射`key value`方式写入到语言文件中。

此项工作需要大量人力重复工作，所以考虑使用`Python`写一个工具，帮助开发做此项工作。

大体逻辑为通过正则方式提取`"汉字" '汉字' >汉字`三种形式的汉字，排除注释等其他内容，并将内容通过映射`key value`写入语言文件，并去重避免重复的翻译内容。把原JS文件中`"汉字" '汉字' >汉字`替换为`{key}`等表达式，达到语言文件提取目的。

以下为参考代码，可能存在部分问题，可据不同情况修改。

```python
import os
import re
import random
import string
import translate

# 原代码文件夹
old_dir = '/doc'
# 处理后的代码文件夹
new_dir = '/newdoc'
# 语言文件
message_file='zh-CN.js'

# 依次执行除message_file和.DS_Store等无关内容的代码文件
def get_filelist(dir):
    for home, dirs, files in os.walk(dir):
        for dir in dirs:
            print(dir)
        if '.DS_Store' in files:
            files.remove('.DS_Store')
        files.remove(message_file)
        for filename in files:
            fullname = os.path.join(home, filename)
            get_file(fullname,filename,home)

# 读取文件内容
def get_file(fullname,filename,home):
    try: 
        with open(fullname, encoding='utf-8') as file_obj:
            lines = file_obj.read()
        get_key(lines,filename)
    except UnicodeDecodeError:
        print(fullname)

# 提取 "汉字" '汉字' >汉字 三种类型的字符，组成字典
def get_key(lines,filename):
    data1 = {}
    data2 = {}
    data3 = {}
    res1 = re.findall('\"[\u4e00-\u9fa5]{1,}\"',lines)
    for iterating_var in res1:
        pre_key=filename.replace('.js','')
        data1.setdefault(iterating_var,pre_key+'.'+''.join(random.choices(string.ascii_lowercase,k=18)))
    res2 = re.findall('\'[\u4e00-\u9fa5]{1,}\'',lines)
    for iterating_var in res2:
        data2.setdefault(iterating_var,pre_key+'.'+''.join(random.choices(string.ascii_lowercase,k=18)))
    res3 = re.findall('\>[\u4e00-\u9fa5]{1,}',lines)
    for iterating_var in res3:
        data3.setdefault(iterating_var,pre_key+'.'+''.join(random.choices(string.ascii_lowercase,k=18)))
    open_message(lines,data1,data2,data3,filename)

# 打开语言文件，读取已有的翻译，生成已有翻译data
def open_message(oldlines,data1,data2,data3,filename):  
    try:
        data_already = {}
        messagefilename=old_dir+'/'+message_file
        with open(messagefilename, encoding='utf-8') as file_obj:
            lines = file_obj.read()
        res5 = re.findall('\'[\S]{1,}\': \'[\u4e00-\u9fa5]{1,}\'',lines)
        for iterating_var in res5:
            resvalue = re.findall('\'[\S]{1,}\': ',iterating_var)[0].replace(': ','').replace('\'','')
            reskey = re.findall(': \'[\u4e00-\u9fa5]{1,}\'',iterating_var)[0].replace(': ','').replace('\'','')
            data_already.setdefault(reskey,resvalue)
        oldlines=get_neew_data(oldlines,data1,data2,data3,data_already,filename)

    except UnicodeDecodeError:
        print(messagefilename)

# 根据已有翻译替换提取文字的value
def get_neew_data(oldlines,data1,data2,data3,data_already,filename):
    datatemp={}
    data_already_new={}
    sign1='"'
    sign2='\''
    sign3='>'    
    for key,value in data1.items():
        keytemp=key.replace(sign1,'')        
        if data_already.__contains__(keytemp):
            datatemp.setdefault(key,data_already[keytemp])
        else :
            datatemp.setdefault(key,value)
            data_already_new.setdefault(keytemp,value)
    for key,value in data2.items():
        keytemp=key.replace(sign2,'')        
        if data_already.__contains__(keytemp):
            datatemp.setdefault(key,data_already[keytemp])
        else :
            datatemp.setdefault(key,value)
            data_already_new.setdefault(keytemp,value)
    for key,value in data3.items():
        keytemp=key.replace(sign3,'')        
        if data_already.__contains__(keytemp):
            datatemp.setdefault(key,data_already[keytemp])
        else :
            datatemp.setdefault(key,value)
            data_already_new.setdefault(keytemp,value)
    get_new_message_file(data_already_new)
    get_new_file(oldlines,datatemp,filename)
    
# 替换旧js文件中翻译标记位,并记录到新文件中,保存文件
def get_new_file(oldlines,datatemp,filename):
    for key,value in datatemp.items():
        if(key.find('>')==-1):
            oldlines=oldlines.replace(key,"{"+value+"}")
        else:
            oldlines=oldlines.replace(key,">{"+value+"}")

    file = open(new_dir+'/new'+filename, 'w',encoding='utf-8')
    file.write(oldlines)
    file.close()

# 生成新语言,并追加到语言文件中
def get_new_message_file(data_already_new):
    new_message=''
    for key,value in data_already_new.items():
        new_message=new_message+'  \''+value+'\': \''+key+'\','+'\n'
    file = open(os.path.join(old_dir+'/', message_file), 'a+',encoding='utf-8')
    file.write(new_message)
    file.close()

# 程序入口
if __name__ == "__main__":
    get_filelist(old_dir)
```