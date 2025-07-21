from queue import Queue
import threading 
import traceback
import requests
import logging
import asyncio
import config 
import json
import time

from scripts.ws import BiliClient
from scripts.proto import Proto
from scripts.cheat_game_250 import PvzCheat
from scripts.Show_Text import Show_Text
from scripts.SqlControl import SqlControl
from scripts.send_msg import send_danmu


logger = logging.getLogger("receive_msg")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("data/receive_msg.log",encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

resp_pro = Proto()
receive_queue = Queue() # 接收到的消息队列

def get_usr_list():
    url = "https://api.live.bilibili.com/xlive/general-interface/v1/rank/queryContributionRank"
    headers = {
        "cookie": config.cookie,
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    params = {
        "ruid":config.ruid,
        "room_id" : config.room_id,
        "page_size":100,
        "type":"online_rank",
        "page":1,
    }
    usr_list = []
    try:
        response = requests.get(url,headers = headers,params = params,timeout = 5)
        data = json.loads(response.text)['data']["item"]
        if data == None:
            usr_list = []
        else:
            usr_list = [usr["name"] for usr in data]
    except:
        return -1

    return usr_list

def change_usr_sun(show_text,blive_usr,usr : str,processed_value: int):
    # blive_usr = SqlControl()

    remain_sun = blive_usr.search_usr(usr)
    remain_sun += processed_value
    blive_usr.update_data(usr,remain_sun)
    road = show_text.usr_dict.get(usr)
    if road != None:
        show_text.change_text(show_text.road_dict[road]["label"],f"{usr}\n阳光:{remain_sun}")


def check_usrs(show_text):
    while True:
        try:
            sit_down_usr = show_text.usr_dict.copy()
            usr_list = get_usr_list()
            time.sleep(10)
            if usr_list == -1:
                continue
            # print(usr_list)
            for usr,status in sit_down_usr.items():
                if usr not in usr_list:
                    show_text.stand_up(usr,"离")
                    receive_queue.put({
                        "cmd":"LIVE_OPEN_PLATFORM_DM",
                        "data":{
                            "msg":"离",
                            "uname":usr
                        }
                    })
                    break

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"check_usrs_error:{e}")

def check_win(pvzcheat,show_text):
    blive_usr = SqlControl()
    # global guess_win_usr
    count_num = 0
    while True:
        time.sleep(1)
        count_num += 1
        if count_num == 180:
            pvzcheat.change_speed(3)
        elif count_num == 120:
            pvzcheat.change_speed(2)
        try:
            win_road_num = pvzcheat.get_win_road()
            if win_road_num != -1:
                pvzcheat.change_speed(1)
                count_num = 0
                send_danmu(f"{win_road_num}路获得最终胜利！")
                for usr,road in show_text.usr_dict.items():
                    # print(usr,road,win_road_num)
                    if int(road) == win_road_num:
                        show_text.maintext_queue.put(f"{usr}\n获得最终胜利！获取1000阳光")
                        # remain_sun = blive_usr.search_usr(usr)
                        # blive_usr.update_data(usr,remain_sun+1000)
                        receive_queue.put({
                            'cmd':'add_sun',
                            'usr':usr,
                            "count":1000
                        })
                        # change_usr_sun(show_text,blive_usr,usr,1000)

                time.sleep(2.5)
                # pvzcheat.select_zp_to_board()
                receive_queue.put({
                    'cmd':'RESET'
                })
            

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"check_error:{e}")
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

    while True:
        recvBuf = await websocket.recv()
        item = resp_pro.unpack(recvBuf)
        if item==None:
            continue
        if "cmd" in item:
            receive_queue.put(item)
            # if item['cmd'] == "LIVE_OPEN_PLATFORM_DM":
            #     danmu = item['data']['msg']
            #     logger.info(f"{item['data']['uname']}：{danmu}")

def start(pvzcheat):
    show_text = Show_Text()
    blive_usr = SqlControl()
    like_count = 0
    # 保证入座用户在直播间
    threading.Thread(target=check_usrs, args = (show_text,),daemon=True).start()
    # 每秒检测是否有玩家获胜
    threading.Thread(target=check_win, args = (pvzcheat,show_text),daemon=True).start()
    while True:
        try:
            item = receive_queue.get()
            if item['cmd'] != "LIVE_OPEN_PLATFORM_DM":
                if item['cmd'] == "LIVE_OPEN_PLATFORM_LIKE":
                    logger.info(f"{item['data']['uname']} 点赞了,点赞次数：{item['data']['like_count']}")
                    like_count += item['data']['like_count']
                    usr = item['data']['uname']
                    while like_count >=5:
                        like_count -= 5
                        for i in range(5):
                            pvzcheat.plant_zombie(0,str((i+1)*10))
                    show_text.maintext_queue.put(f"{usr}触发普通僵尸")
                if item['cmd'] == 'LIVE_OPEN_PLATFORM_LIVE_ROOM_ENTER':
                    logger.info(f"{item['data']['uname']} 进入直播间")
                    show_text.text2voice(f"欢迎{item['data']['uname']}进入直播间")
                if item['cmd'] == 'RESET':
                    pvzcheat.select_zp_to_board()
                if item['cmd'] == 'add_sun':
                    change_usr_sun(show_text,blive_usr,item['usr'],item['count'])
                continue
            danmu = item['data']['msg']
            usr =  item['data']['uname']
            logger.info(f"{usr}：{danmu}")
            show_text.sit_down(usr,danmu)
            show_text.stand_up(usr,danmu)
            danmu = danmu.lower()
            for instruct in danmu.split(","):
                instruct = instruct.replace(" ","")
                remain_sun = blive_usr.search_usr(usr)
                if len(instruct)>0 and instruct[1:3].isdigit():
                    position_num = int(instruct[1:3])
                    usr_seat = int(show_text.usr_dict.get(usr, -1))
                    if usr_seat == -1:
                        show_text.maintext_queue.put(f"{usr}\n未入座，不允许操作")
                        break
                    elif usr_seat <=5:
                        if remain_sun<100:
                            show_text.maintext_queue.put(f"{usr}\n阳光不足")
                            break
                        elif (position_num//10)+(0!=(position_num%10)) != int(show_text.usr_dict[usr]):
                            show_text.maintext_queue.put(f"{usr}\n请操作自己那一路")
                        elif instruct[0]=="t":

                            pvzcheat.shovel_plants(instruct[1:3])
                        elif instruct[0]=="p":

                            change_usr_sun(show_text,blive_usr,usr,-100)
                            pvzcheat.plant_plants(256,instruct[1:3])
                    else:
                        if (position_num//10)+(0!=(position_num%10)) != int(show_text.usr_dict[usr])-5:
                            show_text.maintext_queue.put(f"{usr}\n请操作自己那一路")
                        elif instruct[0] == 'z':
                            # blive_usr.update_data(usr,remain_sun-100)
                            pvzcheat.plant_zombie(21,instruct[1:3])
            if danmu == "签到":
                status = blive_usr.sign_in(usr)
                if status == True:
                    show_text.maintext_queue.put(f"{usr}\n成功签到！获取1000阳光")
                    send_danmu(f"{usr}\n成功签到！获取1000阳光")
                else:
                    show_text.maintext_queue.put(f"{usr}\n你今天已经签到过了嗷！")
                    send_danmu(f"{usr}\n你今天已经签到过了嗷！")
            elif danmu == "查询":
                remain_sun = blive_usr.search_usr(usr)
                send_danmu(f"@{usr} 剩余阳光:{remain_sun}")

        except Exception as e:
            logger.error(f"start_error:{e}")
            logger.error(traceback.format_exc())
            continue

def main():
    cli = BiliClient(
        idCode=config.idCode,  
        appId=config.appId,  
        key=config.key,  
        secret=config.secret, 
        host=config.host)
    loop = asyncio.get_event_loop()
    websocket = loop.run_until_complete(cli.connect())
    # websocket = await cli.connect()
    while True:
        try:
            tasks = [
                # 读取信息
                asyncio.ensure_future(receive(websocket)),
                # 发送心跳
                asyncio.ensure_future(cli.heartBeat(websocket)),
                # 发送游戏心跳
                asyncio.ensure_future(cli.appheartBeat()),
            ]
            loop.run_until_complete(asyncio.gather(*tasks))
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"main_error:{e}")
            logger.error(traceback.format_exc())
            logger.error("重连。。。")
            continue

if __name__ == "__main__":
    pvzcheat = PvzCheat()
    with pvzcheat:
        threading.Thread(target=start,args = (pvzcheat,),daemon = True).start()
        # threading.Thread(target=LLM_response,daemon = True).start()
        main()
