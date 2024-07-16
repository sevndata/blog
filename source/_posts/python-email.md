---
title: python自动发送邮件
date: 2019-06-02 09:15:16
categories: 
- python
tags: 
- python
---

分享使用python自动发送类似日报邮件
<!-- more -->

这里是我的自动发送邮件，示例：
```py
import timefrom email.mime.application 
import MIMEApplicationfrom email.mime.multipart 
import MIMEMultipartfrom email.mime.text 
import MIMETextimport smtplibfrom email 
import utils

class EMailer(object):
def __init__(self,contacts):        
    self.address = '' # 发送的邮箱地址        
    auth_info = {}        
    auth_info['server'] = ''  # 邮箱服务器        
    auth_info['user'] = self.address        
    auth_info['password'] = '' # 邮箱密码        
    self.user_info = auth_info        
    self.contacts = contacts # 接受邮件的邮箱        
    print (self.contacts)
def send_mail(self, subject, content):        
    str_to = '; '.join(self.contacts)        
    server = self.user_info.get('server')       
    smtp_port = 25        
    user = self.user_info.get('user')        
    passwd = self.user_info.get('password')
    
    if not (server and user and passwd):            
        print ('incomplete login info, exit now')            
        return
        
    msg_root = MIMEMultipart('related')        
    msg_root['Subject'] = subject        
    msg_root['From'] = self.address        
    msg_root['To'] = str_to
    
    msg_alternative = MIMEMultipart('alternative')        
    msg_root.attach(msg_alternative)
    main_msg = MIMEMultipart()        
    textApart=MIMEText(subject)
    
    zipFile = subject+".docx"        
    zipApart = MIMEApplication(open(zipFile, 'rb').read())        
    zipApart.add_header('Content-Disposition', 'attachment', filename=zipFile)
    main_msg.attach(textApart)        
    main_msg.attach(zipApart)
    main_msg['From'] = self.address       
    main_msg['To'] = str_to        
    main_msg['Subject'] = subject        
    main_msg['Date'] = utils.formatdate()        
    full_text = main_msg.as_string()        
    try:
        smtp = smtplib.SMTP(server, smtp_port)            
        smtp.ehlo()            
        smtp.starttls()            
        smtp.ehlo()            
        smtp.login(user, passwd)            
        smtp.sendmail(self.address, self.contacts, full_text)            
        smtp.quit()            
        print ("success!")        
        except Exception as e:            
        print ("fail:" + str(e))

if __name__ == "__main__":    
    firstContacts = ""    
    EMailer(firstContacts).send_mail("xxx_"+time.strftime("%Y年_%m月_%d日", time.localtime())+"_工作日报", "")
```
需要去邮箱设置开启smtp。可以去学习下邮件传输协议。

执行python3 emailer.py测试发送

准备一台服务器，定时执行就可以自动发邮件了。当然这是发送固定文件。具体如何创建word并写入内容有时间了再做研究。