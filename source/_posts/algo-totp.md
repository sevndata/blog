---
title: 支付动态码设计及TOTP算法Luhm算法过程解析
date: 2021-03-30 14:23:57
categories: 
- algorithm
tags: 
- TOTP
- Luhm
---
本文分享了支付动态码设计实现，及TOTP算法和Luhm算法过程解析。
<!-- more -->
## 支付动态码

业务需求会员余额可被扫动态码直接扣款，暂未查询到相关资料，于是在引用成熟算法的基础上简单设计了一个支付动态码规则。大佬指点请发邮件。

### 设计思路
参考现有成熟支付码为18位数字，且每分钟变化一次，同时动态码唯一并识别到会员，并且有一定安全性。
- 1.会员id不能明文出现在支付码中，且位数太长，只能映射到存储
- 2.支付码有业务规则，不能通过uuid或者其他类似规则生成，并且要区别于其他支付码，使用前俩位识别
- 3.每分钟更新可通过设置过期时间实现，定为TOTP算法生成部分位数
- 4.映射会员需要校验识别会员，定为4位随机数缓存映射+会员id十进制转八进制后三位校验
- 5.参考银行卡号等生成规则使用Luhm算法校验支付码的正确性。
- 6.保证支付码的当前唯一性，通过支付码为key保存，确保支付码唯一。

### 示例
`xx,xxxxxxxx,xxxx,xxx,x`
`43,55878487,6107,262,9`
- 1-2位：识别码，固定数字xx（2位），区别于其他支付码，如支付宝11-15开头等。
- 3-10位：TOTP算法，每60秒更新一次（8位）。
- 11-14位：随机数（4位）通过获取登录用户的随机数在缓存中校验。
- 15-17：会员id十进制转八进制后截取最后三位，校验用户（3位）。
- 18：Luhm算法，付款码正确性校验位（1位）。

## TOTP算法

```java
public static String generate(){
    //使用会员id+会员支付密码密文+共享密码组成作为HmacSHA256秘钥
    String key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
    long step=60000;
    String crypto="HmacSHA256";
    //取时间
    long now = new Date().getTime();
    //(时间-0)/60000后转换为16进制
    //time=19B4AD8
    String time = Long.toHexString((now-0)/step).toUpperCase();
    StringBuilder timeBuilder = new StringBuilder(time);
    //不够十六位前补0
    //time=00000000019B4AD8
    while (timeBuilder.length() < 16)
        timeBuilder.insert(0, "0");
    time = timeBuilder.toString();
    //time转byte
    byte[] msg = hexStr2Bytes(time);
    //key转byte
    byte[] k = key.getBytes();
    //Mac HmacSHA256算法加密 Mac还包含HmacSHA1等其他算法
    Mac hmac;
    hmac = Mac.getInstance(crypto);
    SecretKeySpec macKey = new SecretKeySpec(k, "AES");
    hmac.init(macKey);
    byte[] target = hmac.doFinal(msg);
    StringBuilder result;
    //取最后一个字节(60)和0xf做按位与操作，取低四位 offset=1101(13)
    //111101&1111->1101(13)
    int offset = target[target.length - 1] & 0xf;
    //从offset开始取4个字节，大端模式组成整数
    int binary = ((target[offset] & 0x7f) << 24)
            | ((target[offset + 1] & 0xff) << 16)
            | ((target[offset + 2] & 0xff) << 8) | (target[offset + 3] & 0xff);
    //取余
    int otp = binary % 10000000;
    result = new StringBuilder(Integer.toString(otp));
    //不够位数前补0
    while (result.length() < 10000000) {
        result.insert(0, "0");
    }
    //得到加密后8位字符
    return result.toString();
}
```
## Luhm算法

```java
public static char getCheckCode(String nonCheckCode) {
    //43558784876107262
    char[] chs = nonCheckCode.trim().toCharArray();
    int luhmSum = 0;
    //i从最后一位开始
    //j从第一位开始
    for (int i = chs.length - 1, j = 0; i >= 0; i--, j++) {
        int k = chs[i] - '0';
        if (j % 2 == 0) {
            //如果为奇数位，则*2
            //从最后一位开始，校验的时候为（包含校验位）偶数位，要得到校验位则是奇数位，也就是除了校验位第一位
            k *= 2;
            //如果是俩位数则十位数+个位数（-9）
            k = k / 10 + k % 10;
        }
        //其他位不做处理，将所有值相加
        luhmSum += k;
    }
    //示例43558784876107262
    //2->4 2->4 0->0 6->3 8->7 8->7 8->7 5->1 4->8
    //4+4+0+3+7+7+7+1+8+6+7+1+7+4+7+5+3=81
    //如果为0取0，10-luhmSum%10得到最后校验位
    //10-81%10=9
    //得到的校验位是9 所以正确号码为435587848761072629
    return (luhmSum % 10 == 0) ? '0' : (char) ((10 - luhmSum % 10) + '0');
}
```