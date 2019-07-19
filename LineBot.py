# -*- coding: UTF-8 -*-

#Python module requirement: line-bot-sdk, flask
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError 
from linebot.models import MessageEvent, TextMessage, TextSendMessage

#for threading(because Flask will run program continuosly so cannot run other while loop in this program)
import threading
import time

#to run bash comand "iwconfig wlan0 | grep ...."
from subprocess import *

#for GPIO use
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
input_pin = 17
output_pin = 13
GPIO.setup(input_pin,GPIO.IN)
GPIO.setup(output_pin,GPIO.OUT)

###########################
########Line_Bot USE#######
##########################
line_bot_api = LineBotApi('key in Line Chanenel accress token here') #LineBot's Channel access token
handler = WebhookHandler('key in Line Chanenel Secret here')        #LineBot's Channel secret
user_id_set=set()                                         #LineBot's Friend's user id 
app = Flask(__name__)


def loadUserId():
    try:
        idFile = open('idfile', 'r')
        idList = idFile.readlines()
        idFile.close()
        idList = idList[0].split(';')
        idList.pop()
        return idList
    except Exception as e:
        print(e)
        return None


def saveUserId(userId):
        idFile = open('idfile', 'a')
        idFile.write(userId+';')
        idFile.close()


@app.route("/", methods=['GET'])
def hello():
    return "HTTPS Test OK."

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']    # get X-Line-Signature header value
    body = request.get_data(as_text=True)              # get request body as text
    print("Request body: " + body, "Signature: " + signature)
    try:
        handler.handle(body, signature)                # handle webhook body
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    Msg = event.message.text
    if Msg == 'Hello, world': return
    print('GotMsg:{}'.format(Msg))

    line_bot_api.reply_message(event.reply_token,TextSendMessage(text="收到訊息!!"))   # Reply API example
    
    userId = event.source.user_id
    if not userId in user_id_set:
        user_id_set.add(userId)
        saveUserId(userId)


#############################
########Check Distance#######
############################
def target_distance():
    while True:
        cmd = 'iwconfig wlan0 | grep -oP "(?<=Signal level=).*"'
        proc = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
        output,err = proc.communicate()
        msg=output.strip()
        signal_level = int(msg.strip('dBm'))
        print('signal level={}'.format(signal_level))
        if signal_level < -60 :
            for userId in user_id_set:
                line_bot_api.push_message(userId,TextSendMessage(text='Your Baby is far away from you'))
                print('msg:"Away ALERT!!!!!baby is far away from u" sent')
                time.sleep(10)
        time.sleep(1)


###########################
########GPIO USE###########
##########################
def gpio_use():
    try:
        while True:
            if GPIO.input(input_pin):
                print ('caught input signal from ARC board')     
                for userId in user_id_set:
                    line_bot_api.push_message(userId,TextSendMessage(text='***FALL DOWN ALERT***Your Baby has fell down'))
                    time.sleep(10)
            else:
                print('GPIO input is LOW')
            time.sleep(0.5)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":

    idList = loadUserId()
    if idList: user_id_set = set(idList)

    try:
        for userId in user_id_set:
            line_bot_api.push_message(userId, TextSendMessage(text='Baby car LineBot is ready for you.'))  # Push API example
    except Exception as e:
        print(e)
    
    t1 = threading.Thread(target=target_distance,args=())
    t1.daemon = True
    t1.start()
    t2 = threading.Thread(target = gpio_use,args=())
    t2.daemon = True
    t2.start()
    app.run('127.0.0.1', port=32768, threaded=True, use_reloader=False)

    

