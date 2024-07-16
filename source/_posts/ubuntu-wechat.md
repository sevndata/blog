---
title: 在Ubuntu中使用微信(deepin-wine)
date: 2021-02-26c 18:45:16
categories: 
- Ubuntu
tags: 
- Ubuntu
- deepin-wine
---
本文分享了在Ubuntu环境中使用微信
<!-- more -->

最近给同学们更换了`Ubuntu`开发环境，问题是微信等官方并没有提供`Ubuntu`支持版本。同样还有QQ，输入法等，这里分享一些在`Ubuntu`中微信的使用。推荐使用第四种，第五种方式。

## 1. 封装web应用
可以利用`nativefier`，`nw.js`等打包工具或者设置快捷方式将微信网页版`web`打包成应用。目前这种办法不能使用了，`Ubuntu`下微信网页版不能正常打开。
## 2. wewechat
可以使用开源第三方，如`wewechat`,`electronic-wechat`等，大概率现在也不能正常使用。
## 3. wine

下载安装后发现有输入框不显示，缺少依赖等问题。

```shell
sudo apt-get install wine
```
下载exe运行：
```shell
wine WeChatSetup.exe
```
## 4. deepin-wine
使用`deepin-wine`环境和`deepin`官方原版软件包
1. 下载安装`deepin-wine`环境
2. 下载软件包
3. 安装软件包
```
dpkg -i xxx.deb
```
微信不能发送图片：
```
sudo apt-get install libjpeg62:i386
```
拷贝字体：
```
/usr/share/deepin-wine/wine/fonts
```

## 5. deepin-wine

同样也可以使用[开源快速方法](https://github.com/zq1997/deepin-wine)，其中有很详细的介绍

```shell
wget -O- https://deepin-wine.i-m.dev/setup.sh | sh
```
详细配置可详见`setup.sh`与文档介绍
```shell
sudo apt-get install com.qq.weixin.deepin
```


