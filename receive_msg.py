
from datetime import datetime
from queue import Queue
import traceback
import threading
import requests
import asyncio
import logging
import config
import json
import time
import json

from SqlControl import SqlControl
from cheat_game import PvzCheat
from send_msg import send_danmu
from Show_Text import Show_Text
from ws import BiliClient
from proto import Proto

# 配置日志
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("receive_msg.log",encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

resp_pro = Proto()
msg_queue = Queue()
like_number = 0
user_out_time = {}
guess_win_usr = {"status":0}

import tkinter as tk

def get_usr_list():
    url = "https://api.live.bilibili.com/xlive/general-interface/v1/rank/queryContributionRank"
    headers = {
        "cookie":"buvid3=51091490-8A8B-57CB-876D-B7367411600C48462infoc; b_nut=1725001548; _uuid=C23FE1C4-E5CE-1AD3-8EAE-ABA3EB810355349032infoc; enable_web_push=DISABLE; buvid4=ABE94ED3-B857-FC8C-0E40-BE7BADC1C73E49665-024083007-Yr3%2BhwNCoNYsJzhazPiuoQ%3D%3D; header_theme_version=CLOSE; CURRENT_FNVAL=4048; LIVE_BUVID=AUTO7817253382566032; rpdid=|(ummlmkm||R0J'u~kYRYmuuY; buvid_fp_plain=undefined; DedeUserID=106135359; DedeUserID__ckMd5=041f270fdaee988e; home_feed_column=5; browser_resolution=1920-957; CURRENT_QUALITY=80; bp_t_offset_106135359=996284713041657856; fingerprint=147f1a4fca00c5ac5b1444f7bdf5cbbf; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzEyMzU2NzAsImlhdCI6MTczMDk3NjQxMCwicGx0IjotMX0.lO9rrbo-w1s_SvYCoIvtxttjgYF0VXm9Q_yPGogYpeQ; bili_ticket_expires=1731235610; SESSDATA=f805bfe1%2C1746538856%2C8d8f5%2Ab2CjDRUfNvGcwX8JbGn-Rc_Wb0hAjdvXpGi8-j5gG0vcVUjsBA4GIELz7_Pz52-wjjP9oSVm5PTVZTOTRRWnhsbXpYcjBoYUlDeWJjMExLZm9kR0FaZEFWdk9NN1BSc19FYllBVzhGeUVjZFNKZ0JuR2g1dzV0ZUJDZm12eDBPbmI5MjlYcXA5dTNRIIEC; bili_jct=acc38c5eb6532498f0f5148d222ae3af; sid=826iwrno; b_lsid=BB1E39B2_1930F6BC464; PVID=2; buvid_fp=147f1a4fca00c5ac5b1444f7bdf5cbbf",
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    params = {
        "ruid":106135359,
        "room_id" : 4638098,
        "page_size":100,
        "type":"online_rank",
        "page":1,
    }
    try:
        response = requests.get(url,headers = headers,params = params,timeout = 5)
        usr_list = [usr["name"] for usr in json.loads(response.text)['data']["item"]]
    except:
        usr_list = []
    return usr_list

def check_usrs(sit_down_usr):
    while True:
        try:
            usr_list = get_usr_list()
            time.sleep(10)
            if len(usr_list) == 0:
                continue
            # print(usr_list)
            for usr,status in sit_down_usr.items():
                if usr not in usr_list:
                    msg_queue.put({"uname":usr,"msg":"离座"})
                if usr not in user_out_time:
                    user_out_time[usr] = 0
                else:
                    user_out_time[usr] +=10
                if user_out_time[usr]>=600:
                    msg_queue.put({"uname":usr,"msg":"离座"})
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"check_usrs_error:{e}")

def seconds_to_mmss(seconds):
    minutes = seconds // 60  # 整数除法得到分钟
    remaining_seconds = seconds % 60  # 取余得到剩余的秒数
    return f"{minutes:02}:{remaining_seconds:02}"  # 格式化为 MM:SS
def check_win(pvzcheat,show_text):
    blive_usr = SqlControl()
    global guess_win_usr
    while True:
        time.sleep(1)
        try:
            win_road_num = pvzcheat.get_win_road()
            if win_road_num != -1:
                send_danmu(f"{win_road_num}路获得最终胜利！")
                for usr,road in show_text.usr_dict.items():
                    # print(usr,road,win_road_num)
                    if int(road) == win_road_num:
                        show_text.maintext_queue.put(f"{usr}\n获得最终胜利！获取1000阳光")
                        remain_sun = blive_usr.search_usr(usr)
                        blive_usr.update_data(usr,remain_sun+1000)
                for usr,road in guess_win_usr.items():
                    if int(road) == win_road_num:
                        remain_sun = blive_usr.search_usr(usr)
                        blive_usr.update_data(usr,remain_sun+500)

                time.sleep(6)
                msg_queue.put({"uname":"清哥","msg":"show_shovel"})
                # pvzcheat.show_shovel()
                guess_win_usr = {"status":1}
                for i in range(63,0,-1):
                    show_text.guess_win_text = seconds_to_mmss(i)+"\n输入x路会赢,赢500阳光\n"
                    time.sleep(1)
                show_text.guess_win_text = ""
                guess_win_usr["status"] = 0

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"check_error:{e}")
            continue
            
def start(pvzcheat):
    current_time = datetime.now()
    
    show_text = Show_Text()
    blive_usr = SqlControl()
    # 保证入座用户在直播间
    threading.Thread(target=check_usrs, args = (show_text.usr_dict,),daemon=True).start()
    # 每秒检测是否有玩家获胜
    threading.Thread(target=check_win, args = (pvzcheat,show_text),daemon=True).start()
    with open("data/cost.json","r",encoding="utf-8") as file:
        cost = json.load(file)
    while True:
        message = msg_queue.get()
        
        usr,text = message["uname"],message["msg"]
        if usr in user_out_time:
            user_out_time[usr] = 0
        show_text.sit_down(usr,text)
        show_text.stand_up(usr,text)
        text = text.lower()
        try:
            for instruct in text.split(","):
                instruct = instruct.replace(" ","")
                remain_sun = blive_usr.search_usr(usr)
                if len(instruct)>0 and instruct[1:3].isdigit() and (instruct[0]=="h" or instruct[0]=="t"):
                    if remain_sun<100:
                        show_text.maintext_queue.put(f"{usr}\n阳光不足")
                    if usr not in show_text.usr_dict:
                        show_text.maintext_queue.put(f"{usr}\n未入座，不允许放置")
                    elif show_text.usr_dict[usr] == "0":
                        show_text.maintext_queue.put(f"{usr}\n未入座，不允许放置")
                    elif (int(instruct[1:3])//10)+(0!=(int(instruct[1:3])%10)) != int(show_text.usr_dict[usr]):
                        show_text.maintext_queue.put(f"{usr}\n请操作自己那一路")
                    elif instruct[0]=="h":
                        blive_usr.update_data(usr,remain_sun-100)
                        pvzcheat.plant_plants(instruct[0],instruct[1:3])
                    else:
                        blive_usr.update_data(usr,remain_sun-100)
                        pvzcheat.shovel_plants(instruct[1:3])
            for key,value in show_text.usr_dict.items():
                remain_sun = blive_usr.search_usr(key)
                show_text.change_text(show_text.road_dict[value]["label"] , f"{key}\n阳光:{remain_sun}")
            if text.startswith("sun") and text[3:].strip().isdigit():
                sunvalue = int(text[3:])
                if sunvalue>=0 and sunvalue<=1000000:
                    pvzcheat.change_sun(sunvalue)
                    show_text.maintext_queue.put(f"{usr}\n成功将阳光修改为{sunvalue}")
                else:
                    show_text.maintext_queue.put(f"{usr}\n你给的阳光超出范围了噢")
                    send_danmu("你给的阳光超出范围了噢")
            elif text.startswith("查询"):
                remain_sun = blive_usr.search_usr(usr)
                send_danmu(f"@{usr} 剩余阳光:{remain_sun}")
            elif text.startswith("签到"):
                status = blive_usr.sign_in(usr)
                if status == True:
                    show_text.maintext_queue.put(f"{usr}\n成功签到！获取1000阳光")
                    send_danmu(f"{usr}\n成功签到！获取1000阳光")
                else:
                    show_text.maintext_queue.put(f"{usr}\n你今天已经签到过了嗷！")
                    send_danmu(f"{usr}\n你今天已经签到过了嗷！")
            elif text.startswith("冲冲冲"):
                show_text.maintext_queue.put(f"{usr}\n触发普通僵尸！")
                send_danmu("触发普通僵尸")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("a",str(index*10))
            elif text.startswith("show_shovel"):
                pvzcheat.show_shovel()
            elif text == "路障僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发路障僵尸！")
                send_danmu(f"{usr}:触发路障僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("b",str(index*10))
            elif text == "撑杆僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发撑杆僵尸！")
                send_danmu(f"{usr}:触发撑杆僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("c",str(index*10))
            elif text == "铁通僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发铁通僵尸！")
                send_danmu(f"{usr}:触发铁通僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("d",str(index*10))
            elif text == "橄榄僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发橄榄球僵尸！")
                send_danmu(f"{usr}:触发橄榄球僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("e",str(index*10))
            elif text == "橄榄高坚果僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发橄榄高坚果僵尸！")
                send_danmu(f"{usr}:触发橄榄高坚果僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("f",str(index*10))
            elif text == "樱桃二爷僵尸":
                show_text.maintext_queue.put(f"{usr}\n触发樱桃二爷僵尸！")
                send_danmu(f"{usr}:触发樱桃二爷僵尸!")
                for index in range(1,6):
                    status = pvzcheat.plant_plants("g",str(index*10))
            elif text[1:4] == "路会赢" and guess_win_usr["status"] == 1:
                text = text.replace("一","1")
                text = text.replace("二","2")
                text = text.replace("三","3")
                text = text.replace("四","4")
                text = text.replace("五","5")
                if text[0].isdigit():
                    guess_win_usr[usr] = text[0]
                    # show_text.get_guess_queue.put(usr)

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"start_error: {e}")
            continue


async def receive(websocket):

    '''
    接收弹幕：LIVE_OPEN_PLATFORM_DM
    获取礼物信息：LIVE_OPEN_PLATFORM_SEND_GIFT
    付费留言：LIVE_OPEN_PLATFORM_SUPER_CHAT
    付费留言下线：LIVE_OPEN_PLATFORM_SUPER_CHAT_DEL
    付费大航海：LIVE_OPEN_PLATFORM_GUARD
    点赞信息：LIVE_OPEN_PLATFORM_LIKE
    进入房间：LIVE_OPEN_PLATFORM_LIVE_ROOM_ENTER
    '''
    global like_number
    while True:
        try:
            recvBuf = await websocket.recv()
        except:
            logger.error("receive_error:","可能网络连接问题")
            time.sleep(5)
            continue
        item = resp_pro.unpack(recvBuf)
        if item==None:
            continue
        if "cmd" in item:
            if item['cmd'] == "LIVE_OPEN_PLATFORM_DM":
                danmu = item['data']['msg']
                logger.info(f"{item['data']['uname']}：{danmu}")
                # show_text(f"{item['data']['uname']}：{danmu}",2)
                # update_text_box(f"{item['data']['uname']}：{danmu}")  # 更新文本
                msg_queue.put(item['data'])
            elif item['cmd'] == "LIVE_OPEN_PLATFORM_LIKE":
                logger.info(f"用户：{item['data']['uname']} 点赞了,点赞次数：{item['data']['like_count']}")
                like_number += item['data']['like_count']
                if like_number >=20:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"冲冲冲"})
                    like_number -= 20
            elif item['cmd'] == "LIVE_OPEN_PLATFORM_LIVE_ROOM_ENTER":
                logger.info(f"用户：{item['data']['uname']} 进入房间")
            elif item['cmd'] == "LIVE_OPEN_PLATFORM_SEND_GIFT" :
                price = item['data']['price']
                logger.info(f"用户：{item['data']['uname']} 送礼：{price}")
                if price >0 and price <=100:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"路障僵尸"})
                elif price>100 and price <=200:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"撑杆僵尸"})
                elif price>200 and price <=300:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"铁通僵尸"})
                elif price>300 and price <=400:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"橄榄僵尸"})
                elif price>400 and price <=500:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"橄榄高坚果僵尸"})
                elif price>500:
                    msg_queue.put({"uname":item['data']['uname'],"msg":"樱桃二爷僵尸"})

def main():

    cli = BiliClient(
        idCode=config.idCode,  # 主播身份码
        appId=config.appId,  # 应用id/
        key=config.key,  # access_key
        secret=config.secret,  # access_key_secret
        host="https://live-open.biliapi.com") # 开放平台 (线上环境)
    # 如果
    loop = asyncio.get_event_loop()
    websocket = loop.run_until_complete(cli.connect())
    # websocket = await cli.connect()
    tasks = [
        # 读取信息
        asyncio.ensure_future(receive(websocket)),
        # 发送心跳
        asyncio.ensure_future(cli.heartBeat(websocket)),
        # 发送游戏心跳
        asyncio.ensure_future(cli.appheartBeat()),
    ]
    loop.run_until_complete(asyncio.gather(*tasks))

if __name__ == "__main__":
    pvzcheat = PvzCheat()
    with pvzcheat:
        threading.Thread(target=start,args = (pvzcheat,),daemon = True).start()
        try:
            main()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            temp = input("参数填写错误,按下enter键释放内存资源。。。")
    

