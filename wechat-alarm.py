#!/usr/bin/env python3
# @Author: seven
# @Date:   2017-12-16T15:35:08+08:00
# @Last modified by:   seven
# @Last modified time: 2018-01-22 10:59:34


import os
import sys
import requests
import json
from pyzabbix import ZabbixAPI
from configparser import ConfigParser
from wechatpy.enterprise import WeChatClient
from pprint import pprint as p


def get_graph(zbx_url, zbx_user, zbx_pass, itemid, eventid, zbx_image_path, zbx_image_url):
    # 获取图片id

    zapi = ZabbixAPI(zbx_url)
    zapi.login(zbx_user, zbx_pass)

    try:
        graphid = zapi.graphitem.get(itemids=itemid)[0]['graphid']

        login_url = zbx_url + '/index.php'
        login_data = {
            'autologin': 1, 'enter': 'Sign in', 'name': zbx_user, 'password': zbx_pass
        }
        graph_url = zbx_url + '/chart2.php'
        graph_payload = {
            'graphid': graphid, 'height': 200, 'period': 3600, 'width': 650, 'isNow': 1
        }

        # 获取图片
        s = requests.Session()
        login_response = s.request('POST', login_url, params=login_data)
        graph_response = s.request('GET', graph_url, params=graph_payload)

        flag = 'network'

    except IndexError as e:
        graph_url = conf.get('zbx', 'noimage')

        if graph_url.startswith('http://') or graph_url.startswith('https://'):
            s = requests.Session()
            graph_response = s.request('GET', graph_url)
            flag = 'network'
        else:
            with open(graph_url, 'rb') as f:
                graph_response = f.read()
            flag = 'local'

    # 保存图片
    image_name = '%s_%s.png' %(itemid, eventid)
    image = os.path.join(zbx_image_path, image_name)
    with open(image, 'wb') as f:
        if flag == 'network':
            f.write(graph_response.content)
        elif flag == 'local':
            f.write(graph_response)


    # 转换成url
    image_url = zbx_image_url + '/' + image_name

    return image_url


class PingStr():
    '''拼接数据'''
    def __init__(self, conf, opts):
        self.conf = conf
        if isinstance(opts, dict):
            self.opts = opts
        else:
            print('数据格式错误')
            sys.exit()

    def __get_event_level_image(self):
        '''获取消息标题的缩略图'''
        conf=self.conf
        opts=self.opts
        trigger_severity = opts['trigger_severity']
        trigger_statue = opts['trigger_statue']
        print(trigger_severity)
        level_list = ('未分类', '信息', '警告', '一般严重', '严重', '灾难',
                'Not classified', 'Information', 'Warning', 'Average', 'High', 'Disaster')

        if trigger_statue == 'PROBLEM':
            if trigger_severity in level_list:
                if trigger_severity == '未分类' or trigger_severity == 'Not classified':
                    return conf.get('media', 'problem_pro_not_classified')
                elif trigger_severity == '信息' or trigger_severity == 'Information':
                    return conf.get('media', 'problem_information')
                elif trigger_severity == '警告' or trigger_severity == 'Warning':
                    return conf.get('media', 'problem_warning')
                elif trigger_severity == '一般严重' or trigger_severity == 'Average':
                    return conf.get('media', 'problem_average')
                elif trigger_severity == '严重' or trigger_severity == 'High':
                    return conf.get('media', 'problem_high')
                elif trigger_severity == '灾难' or trigger_severity == 'Disaster':
                    return conf.get('media', 'problem_disaster')
            else:
                print('告警级别获取错误: %s'%trigger_severity)
        elif trigger_statue == 'OK':
            return conf.get('media', 'restore')
        else:
            print('告警状态获取错误: %s'%trigger_statue)



    def __get_event_source_url(self):
        '''拼接zabbix事件url,通过点击查看原文访问'''
        conf=self.conf
        opts=self.opts
        trigger_id = opts['trigger_id']
        event_id = opts['event_id']
        zbx_url = conf.get('zbx', 'url')
        event_url = '/tr_events.php?triggerid=%s&eventid=%s' %(trigger_id, event_id)
        return zbx_url + event_url

    def __get_content(self):
        '''拼接消息内容'''
        conf=self.conf
        opts=self.opts
        itemid = opts['item_id']
        eventid = opts['event_id']

        zbx_url = conf.get('zbx', 'url')
        zbx_user = conf.get('zbx', 'user')
        zbx_pass = conf.get('zbx', 'passwd')
        zbx_image_path = conf.get('zbx', 'imagepath')
        zbx_image_url = conf.get('zbx', 'imageurl')

        image = get_graph(zbx_url, zbx_user, zbx_pass, itemid, eventid, zbx_image_path, zbx_image_url)

        if opts['trigger_statue'] == 'PROBLEM':
            content = '''
            <img src={graph_url} width="550" />
            <br><br>
            <div class="gray">                                                                                        
                当前状态: {problem_state}<br>                                                                         
                告警级别: {problem_level}<br>                                                                         
                问题时间: {problem_date} {problem_time}<br>                                                           
                问题区域: {problem_hostgroup}<br>                                                                     
                问题主机: {problem_host_name}<br>                                                                     
                主机地址: {problem_host_ip}<br>                                                                       
                问题详情: {problem_value}<br>                                                                         
                问题描述: {problem_desc}                                                                              
            </div>                                                                                                    
            <br><br>                                                                                                  
            <img src={split_line_url} width="550" />                                                                  
            '''.format(                                                                                               
                graph_url=image,                                                                                      
                split_line_url=conf.get('wx', 'split'),                                                               
                problem_state=opts['trigger_statue'],                                                                 
                problem_level=opts['trigger_severity'],                                                               
                problem_date=opts['event_date'],                                                                      
                problem_time=opts['event_time'],                                                                      
                problem_hostgroup=opts['trigger_hostgroup_name'],                                                     
                problem_host_name=opts['host_name'],                                                                  
                problem_host_ip=opts['host_ip'],                                                                      
                problem_value='%s: %s' % (opts['item_name'], opts['item_value']),                                     
                problem_desc=opts['trigger_description'],                                                             
            )
        elif opts['trigger_statue'] == 'OK':
            content = '''
            <img src={graph_url} width="550" />
            <br><br>
            <div class="gray">                                                                                        
                当前状态: {problem_state}<br>                                                                         
                告警级别: {problem_level}<br>                                                                         
                问题时间: {problem_date} {problem_time}<br>                                                           
                问题区域: {problem_hostgroup}<br>                                                                     
                问题主机: {problem_host_name}<br>                                                                     
                主机地址: {problem_host_ip}<br>                                                                       
                问题详情: {problem_value}<br>                                                                         
                问题描述: {problem_desc}<br>                                                                          
                恢复时间: {recovery_date} {recovery_time}<br>                                                         
                持续时长: {recovery_age}                                                                              
            </div>                                                                                                    
            <br><br>                                                                                                  
            <img src={split_line_url} width="550" />                                                                  
            '''.format(                                                                                               
                graph_url=image,                                                                                      
                split_line_url=conf.get('wx', 'split'),                                                               
                problem_state=opts['trigger_statue'],                                                                 
                problem_level=opts['trigger_severity'],                                                               
                problem_date=opts['event_date'],                                                                      
                problem_time=opts['event_time'],                                                                      
                problem_hostgroup=opts['trigger_hostgroup_name'],                                                     
                problem_host_name=opts['host_name'],                                                                  
                problem_host_ip=opts['host_ip'],                                                                      
                problem_value='%s: %s' % (opts['item_name'], opts['item_value']),                                     
                problem_desc=opts['trigger_description'],                                                             
                recovery_date=opts['event_recovery_date'],                                                            
                recovery_time=opts['event_recovery_time'],                                                            
                recovery_age=opts['event_age']                                                                        
            )
        else:
            print('不对')

        return content

    def __get_digest(self):
        '''拼接消息简介'''

        opts=self.opts

        if opts['trigger_statue'] == 'PROBLEM':
            digest = '''
    问题时间: {problem_date} {problem_time}
    问题区域: {problem_hostgroup}
    问题主机: {problem_host_name}
    问题描述: {problem_desc}
            '''.format(
                problem_date = opts['event_date'],
                problem_time = opts['event_time'],
                problem_hostgroup = opts['trigger_hostgroup_name'],
                problem_host_name = opts['host_name'],
                problem_desc = opts['trigger_description']
            )
        elif opts['trigger_statue'] == 'OK':
            digest = '''
    问题时间: {problem_date} {problem_time}
    问题区域: {problem_hostgroup}
    问题主机: {problem_host_name}
    恢复时间: {recovery_date} {recovery_time}
    持续时长: {recovery_age}
            '''.format(
                problem_date = opts['event_date'],
                problem_time = opts['event_time'],
                problem_hostgroup = opts['trigger_hostgroup_name'],
                problem_host_name = opts['host_name'],
                recovery_date = opts['event_recovery_date'],
                recovery_time = opts['event_recovery_time'],
                recovery_age = opts['event_age']
            )
        return digest

    def __upload_media(self, image):
        '''上传图片获取 media_id'''
        pass

    def get_articles(self):
        '''返回消息数据'''

        conf=self.conf
        opts=self.opts

        return [
            {
                "title": opts['trigger_name'],
                "thumb_media_id": self.__get_event_level_image(),
                "author": conf.get('wx', 'author'),
                "content_source_url": self.__get_event_source_url(),
                "content": self.__get_content(),
                "digest": self.__get_digest(),
                "show_cover_pic": ''
            }
        ]


class SendWechat():
    '''微信'''
    def connection(self, CorpId, secret):
        '''连接微信'''
        self.wechat_client = WeChatClient(CorpId, secret)

    def upimage(self, image):
        '''上传图片到微信服务器并返回media_id'''
        with open(image, 'rb') as f:
            media = self.wechat_client.media.upload('image', f)
        return media['media_id']

    def sendmsg(self,agentid, user, articles):
        '''发送消息'''
        return self.wechat_client.message.send_mp_articles(agentid, user, articles)


def main(user, opts, conf):

    # 获取消息数据
    s = PingStr(conf, opts)
    articles = s.get_articles()

    # 连接微信
    CorpId = conf.get('wx', 'corpid')
    secret = conf.get('wx', 'secret')
    wx = SendWechat()
    wx.connection(CorpId, secret)

    # 发送消息
    ToUser = user
    agentid = conf.get('wx', 'agentid')
    r = wx.sendmsg(agentid, ToUser, articles)
    print(r)



if __name__ == '__main__':

    user = sys.argv[1]
    #opts = eval(sys.argv[2])
    opts = json.loads(sys.argv[2])

    conf = ConfigParser()
    conf.read('/opt/software/wechat-alarm/setting.conf')

    main(user, opts, conf)
