---
title: 忽略eslint检查
date: 2020-06-02 14:25:45
categories: 
- ReactJS
tags: 
- ReactJS
---
本文分享了忽略eslint检查提交代码。
<!-- more -->

前端同学反映代码提交不上去，查看后是`eslint`阻止了提交，而整个项目规范化需要大量人力只能跳过`eslint`检查。如下几种方法：

1. 设置`eslint`忽略文件提交
2. `git commit --no-verify -m commigmessage`
3. 删除预提交文件。`.git/pre-commit`