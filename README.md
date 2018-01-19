# zabbix-wechat-alarm
发送zabbix图文告警到微信

## 依赖
- python3

```bash
pip3 install pyzabbix wechatpy pycrypto
```

## 修改配置文件

```bash
vim setting.conf
```

## 添加 nginx 配置

```bash
cp zabbix-wechat.conf path/nginx/conf/
nginx -t
nginx -s reload
```

## zabbix添加 Media types

Administration => Media types => Create media type

- Type = Script
  - wechat-alarm.py

- Script parameters
  - {ALERT.SENDTO}
  - {ALERT.MESSAGE}

## zabbix 添加 user - Media

Administration => Users => Media  

> 添加一个新的报警媒介


## zabbix 添加 action

Configuration => Actions => Event source = Triggers => Create action

- Operations
  - Default message
  ```
  {"trigger_statue":"{TRIGGER.STATUS}","trigger_severity":"{TRIGGER.SEVERITY}","event_id":"{EVENT.ID}","trigger_hostgroup_name":"{TRIGGER.HOSTGROUP.NAME}","host_name":"{HOST.NAME}","host_ip":"{HOST.IP}","event_value":"{EVENT.VALUE}","event_date":"{EVENT.DATE}","event_time":"{EVENT.TIME}","trigger_description":"{TRIGGER.DESCRIPTION}","item_id":"{ITEM.ID}","trigger_name":"{TRIGGER.NAME}","trigger_id":"{TRIGGER.ID}","event_age":"","event_recovery_date":"","event_recovery_time":"","event_recovery_value":""}
  ```
  
- Recovery operations
  - Default message
  ```
  {"trigger_statue":"{TRIGGER.STATUS}","trigger_severity":"{TRIGGER.SEVERITY}","event_id":"{EVENT.ID}","trigger_hostgroup_name":"{TRIGGER.HOSTGROUP.NAME}","host_name":"{HOST.NAME}","host_ip":"{HOST.IP}","event_value":"","event_date":"{EVENT.DATE}","event_time":"{EVENT.TIME}","trigger_description":"{TRIGGER.DESCRIPTION}","item_id":"{ITEM.ID}","trigger_name":"{TRIGGER.NAME}","trigger_id":"{TRIGGER.ID}","event_age":"{EVENT.AGE}","event_recovery_date":"{EVENT.RECOVERY.DATE}","event_recovery_time":"{EVENT.RECOVERY.TIME}","event_recovery_value":"{EVENT.RECOVERY.VALUE}"}
  ```
