from queue import Queue
import threading 
import traceback
import requests
import logging
import asyncio
import config 
import json
import time
import re
import os
import subprocess
import sys
import websockets
import random

from scripts.ws import BiliClient
from scripts.proto import Proto
from scripts.cheat_game import PvzCheat
# from scripts.cheat_game_282 import PvzCheat
from scripts.SqlControl import SqlControl
from scripts.send_msg import send_danmu
from scripts.check_screen import CheckScreen
from scripts.LLMapi import QwenLLM,ConvertHistory


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

class ScreenRequest:

    def __init__(self):
        self.uri = "ws://localhost:8765"
        self.req_msg = asyncio.Queue()
        self.control_msg = Queue()
        self.blive_usr = None
        self.seat_info = {}
        self.user_info = {}
        self.loop = asyncio.get_event_loop()
        self.guess_users_list = []
        self.time_length = 60
        self.start_time = time.time()

    async def client(self):
        async with websockets.connect(self.uri) as websocket:
            while True:
                try:
                    msg = await self.req_msg.get()
                    # 发送一条消息
                    await websocket.send(msg)
                except Exception as e:
                    await asyncio.sleep(1)
                    print(f"Screen client erro {e}")

    def send_msg(self,msg):
        asyncio.run_coroutine_threadsafe(self.req_msg.put(msg), self.loop)

    def start(self):
        self.blive_usr = SqlControl()
        while True:
            try:
                msg = self.control_msg.get()
                if msg["info"] == "sit_down":
                    self.__sit_down(msg['uname'],msg['open_id'],msg['seat'])
                elif msg["info"] == "change_sun":
                    self.__change_sun(msg['uname'],msg['open_id'],msg['changed_value'])
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error(f"screen error:{e}")

    def roll_text(self,text):
        data = {
            "info":"roll_text",
            "text":text
        }
        self.send_msg(json.dumps(data,ensure_ascii=False))
    
    def sit_down(self,uname,open_id,seat):
        data = {
            'info':'sit_down',
            'uname':uname,
            'open_id':open_id,
            'seat':seat
        }
        self.control_msg.put(data)

    def __sit_down(self,uname,open_id,seat):
        remain_sun = self.blive_usr.search_usr(open_id,uname)
        if remain_sun <= 1000:
            self.roll_text(f"{uname},剩余阳光不足1000,不允许入座")
            return
        if uname in self.user_info:
            self.roll_text(f"{uname} 你已经在座位上了")
            return
        if seat in self.seat_info:
            self.roll_text(f"{seat}路座位已经有人在了")
            return
        remain_sun-=500
        self.blive_usr.update_data(open_id,remain_sun)
        self.roll_text(f"{uname},成功消耗500阳光入座。输入离坐离开")
        self.seat_info[seat] = {
            "uname":uname,
            "open_id":open_id,
            "win_pool":0
        }
        self.user_info[uname] = {
            "seat":seat,
            "open_id":open_id,
        }
        text = f"{uname}\n阳光：{remain_sun}\n连胜奖励池:0"
        data = {
            "info":"sit_down",
            "uname":uname,
            "open_id":open_id,
            "text":text,
            "seat":seat
        }
        self.send_msg(json.dumps(data,ensure_ascii=False))
    
    def stand_up(self,uname):
        seat_info = self.user_info.get(uname)
        if seat_info == None:
            return
        seat = seat_info.get("seat")
        self.roll_text(f"{uname},离开座位")
        del self.seat_info[seat]
        del self.user_info[uname]
        if seat:
            data = {
                "info":"stand_up",
                "seat":seat,
            }
            self.send_msg(json.dumps(data,ensure_ascii=False))

    def change_sun(self,uname,open_id,changed_value):
        data = {
            "info":"change_sun",
            "uname":uname,
            "open_id":open_id,
            "changed_value":changed_value
        }
        self.control_msg.put(data)

    def __change_sun(self,uname,open_id,changed_value):
        remain_sun = self.blive_usr.search_usr(open_id,uname)
        remain_sun += changed_value
        self.blive_usr.update_data(open_id,remain_sun)
        seat_info = self.user_info.get(uname)
        if seat_info == None:
            return
        seat = seat_info.get("seat")
        win_pool = self.seat_info[seat]["win_pool"]
        text = f"{uname}\n阳光：{remain_sun}\n连胜奖励池:{win_pool}"
        data = {
            "info":"sit_down",
            "uname":uname,
            "open_id":open_id,
            "text":text,
            "seat":seat
        }
        self.send_msg(json.dumps(data,ensure_ascii=False))

    def guess_game_start(self,time_length):
        self.time_length = time_length
        self.start_time = time.time()
        data = {
            "info":"limit_text",
            "time":time_length
        }
        self.send_msg(json.dumps(data,ensure_ascii=False))
        logger.info("竞猜倒计时开始")
    
    def user_guess(self,uname,open_id,seat):
        end_time = time.time()
        self.change_sun(uname,open_id,-500)
        if end_time-self.start_time<self.time_length:
            self.roll_text(f"{uname}猜{seat}会赢，扣500阳光，买定离手，不允许更改。")
            self.guess_users_list.append({
                "uname":uname,
                "open_id":open_id,
                "seat":seat
            })
    
    def speech(self,text):
        data = {
            "info":"speech",
            "text":text
        }
        self.send_msg(json.dumps(data,ensure_ascii=False))
        

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



def check_usrs(screen: ScreenRequest):
    try:
        CS = CheckScreen()
        img1 = CS.grab_img()
    except:
        pass
    while True:
        try:
            usr_list = get_usr_list()
            time.sleep(10)

            if config.check_screen:
                img2 = CS.grab_img()
                stuck = CS.mse(img1,img2)
                img1 = img2
                # logger.info(stuck)
                if stuck:
                    logger.error(f"卡住，执行stuck")
                    receive_queue.put({
                        "cmd":"stuck"
                    })
            if usr_list == -1:
                continue

            kick_list = []
            for key,value in list(screen.user_info.items()):
                if key not in usr_list:
                    kick_list.append(key)
                    screen.stand_up(key)
            

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"check_usrs_error:{e}")

def check_win(pvzcheat: PvzCheat,screen : ScreenRequest):
    count_num = 0
    zombie_id = 218
    while True:
        time.sleep(1)
        count_num += 1
        if count_num == 180:
            # screen.roll_text("BOSS来临")
            screen.roll_text("Boss来临")
            for i in range(5):
                pvzcheat.plant_zombie(zombie_id,str((i+1)*10))
            zombie_id+=1
            # pvzcheat.change_speed(3)

        elif count_num == 240:
            screen.roll_text("Boss来临")
            for i in range(5):
                pvzcheat.plant_zombie(zombie_id,str((i+1)*10))
            zombie_id+=1
            # pvzcheat.change_speed(2)
        elif count_num >240 and count_num%20 == 0:
            screen.roll_text("Boss来临")
            for i in range(5):
                pvzcheat.plant_zombie(zombie_id,str((i+1)*10))
            zombie_id+=1
        try:
            win_road_num = pvzcheat.get_win_road()
            if win_road_num != -1:
                # pvzcheat.save_lineup()
                # pvzcheat.change_speed(1)
                count_num = 0
                zombie_id = 218
                send_danmu(f"{win_road_num}路获得最终胜利！")

                for key,value in screen.seat_info.items():
                    uname = value["uname"]
                    open_id = value["open_id"]
                    win_pool = value["win_pool"]
                    if int(key) == win_road_num:
                        win_sun = 1500+win_pool
                        screen.roll_text(f"{uname}获得最终胜利！获取{win_sun}阳光")
                        value["win_pool"] += 100
                        screen.change_sun(uname,open_id,win_sun)
                    elif int(key)<6:
                        screen.roll_text(f"{uname}失败，扣除300阳光")
                        value["win_pool"] = 0
                        screen.change_sun(uname,open_id,-300)
                for users in screen.guess_users_list:
                    if int(users["seat"]) == win_road_num:
                        screen.roll_text(f"{users['uname']}猜对了{win_road_num}路会赢，获取1000阳光")
                        screen.change_sun(users['uname'],users["open_id"],1000)
                    else:
                        screen.roll_text(f"{users['uname']}可惜没猜中")
                screen.guess_users_list = []
                time.sleep(2)
                # pvzcheat.select_zp_to_board()
                receive_queue.put({
                    'cmd':'RESET'
                })
                
                receive_queue.put({
                    'cmd':'shovel',
                    'road':win_road_num
                })
                screen.guess_game_start(60)

            

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
        try:
            recvBuf = await websocket.recv()
            item = resp_pro.unpack(recvBuf)
            if item==None:
                continue
            if "cmd" in item:
                receive_queue.put(item)
                # if item['cmd'] == "LIVE_OPEN_PLATFORM_DM":
                #     danmu = item['data']['msg']
                #     # logger.info(item)
                #     if danmu == "error":
                #         raise Exception("test error")
                #     logger.info(f"{item['data']['uname']}：{danmu}")
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"receive:{e}")
            await asyncio.sleep(1)
            continue
            


def start(pvzcheat: PvzCheat, screen: ScreenRequest):

    # UI = Interface()
    blive_usr = SqlControl()
    like_count = 0
    # 保证入座用户在直播间
    threading.Thread(target=check_usrs, args = (screen,),daemon=True).start()
    # 每秒检测是否有玩家获胜
    threading.Thread(target=check_win, args = (pvzcheat,screen),daemon=True).start()
    hanzi = {"一":"1","二":"2","三":"3","四":"4","五":"5","六":"6","七":"7","八":"8","九":"9","十":"10"}
    control_instructions = ["p","t","z","m","c"]
    with open("data/zombie_id.json",'r',encoding='utf-8') as f:
        zombie_ids_list = json.load(f)
    llm = QwenLLM(enable_thinking=False)
    ch = ConvertHistory()
    system_prompt = config.system_prompt
    ch.add_history(system_prompt,"system")

    while True:
        try:
            item = receive_queue.get()
            if item['cmd'] != "LIVE_OPEN_PLATFORM_DM":
                if item['cmd'] == "LIVE_OPEN_PLATFORM_LIKE":
                    logger.info(f"{item['data']['uname']} 点赞了,点赞次数：{item['data']['like_count']}")
                    like_count += item['data']['like_count']
                    usr = item['data']['uname']
                    open_id = item['data']['open_id']
                    # print(usr,open_id)

                    screen.change_sun(usr,open_id,item['data']['like_count']*10)
                    while like_count >=50:
                        screen.roll_text(f"{usr}触发随机僵尸")
                        like_count -= 50
                        for i in range(5):
                            rannum = random.randint(0,72)
                            # pvzcheat.plant_zombie(0,str((i+1)*10))
                            pvzcheat.plant_zombie(zombie_ids_list[rannum],str((i+1)*10))

                if item['cmd'] == 'LIVE_OPEN_PLATFORM_LIVE_ROOM_ENTER':
                    logger.info(f"{item['data']['uname']} 进入直播间")
                    screen.roll_text(f"欢迎{item['data']['uname']}进入直播间")
                if item['cmd'] == 'RESET':
                    pvzcheat.select_zp_to_board()
                    pvzcheat.show_blood()
                    # pvzcheat.load_lineup()


                if item['cmd'] == 'stuck':
                    pvzcheat.stuck()
                if item['cmd'] == 'shovel':
                    win_road = item['road']
                    for i in range(5):
                        pvzcheat.shovel_plants(str((win_road-1)*10+i+1))
                        # pvzcheat.plant_plants(927,str((win_road-1)*10+i+1))
                    pvzcheat.click_random_plant()
                continue
            danmu = item['data']['msg']
            usr =  item['data']['uname']
            logger.info(f"{usr}：{danmu}")
            # logger.info(item)
            open_id = item['data']['open_id']
            danmu = danmu.lower()
            for key,value in hanzi.items():
                danmu = danmu.replace(key,value)
            digist_l = re.findall(r'\d+', danmu)
            if danmu.startswith("入"):
                if len(digist_l) == 0:
                    continue
                screen.sit_down(usr,open_id,digist_l[0])
            elif danmu.startswith("离"):
                screen.stand_up(usr)

            remain_sun = blive_usr.search_usr(open_id,usr)
            for instruct in danmu.split(","):
                if len(instruct)>0 and instruct[1:3].replace(" ","").isdigit():
                    if instruct[0] not in control_instructions:
                        break
                    position_num = int(instruct[1:3])
                    if usr == config.author:
                        if instruct[0]=="t":
                            pvzcheat.shovel_plants(instruct[1:3])
                        elif instruct[0]=="p":
                            pvzcheat.plant_plants(256,instruct[1:3])
                        elif instruct[0] == "m":
                            figures = instruct[1:].split(" ")
                            if len(figures) >=2:
                                pvzcheat.move_plants(figures[0],figures[1])
                        elif instruct[0] == "c":
                            pvzcheat.click_positoin(instruct[1:3])
                        continue

                    user_info = screen.user_info.get(usr)
                    if user_info == None:
                        screen.roll_text(f"{usr}  未入座，不允许操作")
                        break
                    else:
                        usr_seat = int(user_info['seat'])
                    if usr_seat <=5 :
                        if remain_sun<100:
                            screen.roll_text(f"{usr}  阳光不足")
                            break
                        elif (position_num//10)+(0!=(position_num%10)) != usr_seat:
                            screen.roll_text(f"{usr}  请操作自己那一路")
                        elif instruct[0]=="t":
                            pvzcheat.shovel_plants(instruct[1:3])
                        elif instruct[0]=="p":
                            screen.change_sun(usr,open_id,-100)
                            pvzcheat.plant_plants(256,instruct[1:3])
                        elif instruct[0] == "m":
                            figures = instruct[1:].split(" ")
                            if len(figures) >=2:
                                pvzcheat.move_plants(figures[0],figures[1])
                        elif instruct[0] == "c":
                            screen.change_sun(usr,open_id,-100)
                            pvzcheat.click_positoin(instruct[1:3])
                    else:
                        if (position_num//10)+(0!=(position_num%10)) != int(usr_seat)-5:
                            screen.roll_text(f"{usr}  请操作自己那一路")
                        elif instruct[0] == 'z':
                            # blive_usr.update_data(usr,remain_sun-100)
                            pvzcheat.plant_zombie(21,instruct[1:3])
            if danmu == "签到":
                status = blive_usr.sign_in(open_id,usr)
                if status == True:
                    screen.roll_text(f"{usr}  成功签到！获取1000阳光")
                    screen.change_sun(usr,open_id,0)
                    send_danmu(f"{usr}  成功签到！获取1000阳光")
                else:
                    screen.roll_text(f"{usr}  你今天已经签到过了嗷！")
                    send_danmu(f"{usr}  你今天已经签到过了嗷！")
            elif danmu == "查询":
                remain_sun = blive_usr.search_usr(open_id,usr)
                send_danmu(f"@{usr} 剩余阳光:{remain_sun}")
            elif danmu[1:4] == "路会赢":
                if len(digist_l)==0:
                    continue
                else:
                    if remain_sun < 500:
                        continue
                    screen.user_guess(usr,open_id,digist_l[0])
            elif danmu.startswith("清哥") and config.use_llm:
                prompt = f"观众名称为“{usr}”的用户说：{danmu}"
                history = ch.add_history(prompt)
                llm_res = llm.chat(history)
                if len(ch.history) > 30:
                    del ch.history[1:3]
                print(f"大模型回复：{llm_res}")
                sentences = re.findall(r'[^。！？!?；;]+[。！？!?；;]?', llm_res)
                screen.speech(json.dumps(sentences,ensure_ascii=False))
            elif danmu=="cache":
                pvzcheat.clear_cache()
            elif danmu == "stuck":
                pvzcheat.stuck()


        except Exception as e:
            logger.error(f"start_error:{e}")
            logger.error(traceback.format_exc())
            continue

    


from typing import List

def shutdown(tasks: List[asyncio.Task]):
    """清理所有任务和连接"""
        # 1. 取消所有未完成的任务
    for task in tasks:
        if not task.done():
            task.cancel()

    # websocket.close()
def main(screen: ScreenRequest):
    cli = BiliClient(
        idCode=config.idCode,  
        appId=config.appId,  
        key=config.key,  
        secret=config.secret, 
        host=config.host)
    loop = asyncio.get_event_loop()
    websocket = loop.run_until_complete(cli.connect())
    # websocket = await cli.connect()
    # while True:
    #     try:
           
    tasks = [
        # 读取信息
        asyncio.ensure_future(receive(websocket)),
        # 发送心跳
        asyncio.ensure_future(cli.heartBeat(websocket)),
        # 发送游戏心跳
        asyncio.ensure_future(cli.appheartBeat()),
        asyncio.ensure_future(screen.client())
    ]
    loop.run_until_complete(asyncio.gather(*tasks))
        # except KeyboardInterrupt:
        #     logger.info("^C 退出")
        #     break
        # except Exception as e:
        #     # shutdown(tasks)
        #     logger.error(f"main_error:{e}")
        #     logger.error(traceback.format_exc())
        #     logger.error("重连。。。")
        #     time.sleep(1)
        #     continue

if __name__ == "__main__":
    pvzcheat = PvzCheat()
    screen = ScreenRequest()
    pvzcheat.inject()
    pvzcheat.load_data()
    p = subprocess.Popen([sys.executable, "-m", "scripts.Screen"])
    logger.info(f"子进程启动，PID:{p.pid}")
    with pvzcheat:
        logger.info("加载screen")
        threading.Thread(target=screen.start,daemon=True).start()
        logger.info("加载消息处理")
        threading.Thread(target=start,args = (pvzcheat,screen),daemon=True).start()
        main(screen)
    p.terminate()  
    # p.wait()
    # main()