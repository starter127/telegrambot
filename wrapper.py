#!/usr/bin/env python
#coding:utf-8
"""
  Author: Marco Mescalchin  --<>
  Purpose: Wrapper to telegram bot api
  Created: 06/25/15
"""
import requests,json
from threading import Timer
from django.core.cache import cache
from django.conf import settings
from telegrambot.signals import message_received
DEBUG_GET_POST = False

########################################################################
class Bot:
    """"""
    api_url = "https://api.telegram.org"
    #----------------------------------------------------------------------
    def __init__(self,token):
        """Constructor"""
        self.token = token
  
    def setWebhook(self):
        from django.core.urlresolvers import reverse
        whurl = "%s%s" % (settings.TELEGRAM_WEBHOOK_URL,reverse('telegrambot.views.webhook'))
        r = self.post('setWebhook',{'url':whurl.replace('http:','https:')})
        print("Telegram WebHook Setup: %s" % r)
            
  
    def get(self,method,params=None):
        
        if DEBUG_GET_POST: print("GET --> %s %s" % (method,params))
        
        r = requests.get("%s/bot%s/%s" % (self.api_url,self.token,method),params,timeout=30)
        
        if DEBUG_GET_POST: print("GET <-- %s" % r)
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            print("GET Error %s" % r.text)
                    
        
        return False
  
    def post(self,method,params=None,files=None):
        
        if DEBUG_GET_POST: print("POST --> %s %s" % (method,params))

        r = requests.post("%s/bot%s/%s" % (self.api_url,self.token,method),params,files=files,timeout=60)
        
        if DEBUG_GET_POST: print("POST <-- %s" % (r))
            
        if r.status_code == requests.codes.ok:
            j = r.json()
            if j['ok']:
                if j['result']:
                    return j['result']
        else:
            print("POST Error %s" % r.text)
        return False        
  
    def webhook(self,request):
        data = json.loads(request.body.decode('utf8'))
        print("<-- WH %s" % data['message'])
        message_received.send(self,message=data['message'])
        return 'ok'
  
    def action_typing(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'typing'})

    def action_upload_photo(self,chat_id):
        self.post('sendChatAction',{'chat_id':chat_id,'action':'upload_photo'})
        
  
    def sendMessage(self,chat_id,text,disable_web_page_preview=True,reply_to_message_id=None,reply_markup=None):
        r = self.post('sendMessage',{
            'chat_id':chat_id,
            'text':text,
            'disable_web_page_preview':disable_web_page_preview,
            'reply_to_message_id':reply_to_message_id,
            'reply_markup':json.dumps(reply_markup)
        })

        
    def sendPhoto(self,chat_id,photo,caption=None,reply_to_message_id=None,reply_markup=None):
        r = self.post('sendPhoto',{
            'chat_id':chat_id,
            'caption':caption,
            'reply_to_message_id':reply_to_message_id,
            'reply_markup':json.dumps(reply_markup)
        },files={'photo':('image.jpg', photo, 'image/jpeg', {'Expires': '0'})})        
        #print("--> %s" % r)
    
    def getUpdates(self):
        updates = self.get('getUpdates',{'offset':cache.get('tgbot-update-id')})
        try:
            if updates:
                cache.set('tgbot-update-id',updates[-1]['update_id'] + 1)
                for update in updates:
                    from telegrambot.signals import message_received
                    message_received.send(sender=self, message=update['message'])
        except Exception as e:
            print("Getupdates Error %s" % e)
        finally:
            Timer(10,self.getUpdates).start()   
