---
title: Java递归不建议使用对象参数本身
date: 2022-03-28 09:15:16
categories: 
- Java
tags: 
- Java
---
本文分享了Java在使用递归时，不建议使用对象参数本身。
<!-- more -->

开发反映一个奇怪现象，菜单列表出现奇怪错误，此环境使用`spring-data-jpa`，现象如下：


正常为：

    X:一级菜单A1-二级菜单A2

    Y:一级菜单A1-二级菜单A2-三级菜单A3

错误显示：

    X:二级菜单A2-三级菜单A3    //出错

    Y:一级菜单A1-二级菜单A2-三级菜单A3

查看代码后，发现使用`setDetailData`此递归获取拼接的菜单名称。出错在`X`上，原因是如下：

1. 递归`X`对象，获取到菜单名称为`一级菜单A1-二级菜单A2`,正确
2. 递归`Y`对象，再递归到第二级时获取对象`menu`其实为`X`，拼接菜单名称使用`setDetailMenuName`，导致`X`对象发生改变，所以已经做完递归的`X`数据变化为错误数据`二级菜单A2-三级菜单A3`。

```java
private String setDetailData(Menu menu) {
    if (menu.getMenuPid() == 0) {
        return menu.getDetailMenuName();
    } else {
        Optional<Menu> optionalMenu = getJpaRepository().findByMenuId(menu.getMenuPid());
        if (optionalMenu.isPresent()) {
            Menu menuTemp = optionalMenu.get();
            menuTemp.setDetailMenuName(menuTemp.getMenuTitle() + "-" + menu.getDetailMenuName());
            return setDetailData(menuTemp);
        } else {
            return menu.getDetailMenuName();
        }
    }
}
```
此错误类似于遍历数组时修改数组本身，此问题只要简单将`Menu`对象更换即可修复，如下：
```java
private String setDetailData(String detailMenuName, Integer menuPid) {
    if (menuPid == 0) {
        return detailMenuName;
    } else {
        Optional<Menu> optionalMenu = getJpaRepository().findByMenuId(menuPid);
        if (optionalMenu.isPresent()) {
            Menu menuTemp = optionalMenu.get();
            if (menuTemp.getMenuPid().equals(menuTemp.getMenuId())) {
                //todo 死循环情况处理
            }
            return setDetailData(menuTemp.getMenuTitle() + "-" + detailMenuName, menuTemp.getMenuPid());
        } else {
            return detailMenuName;
        }
    }
}
```




