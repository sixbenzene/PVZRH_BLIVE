from .SqlControl import SqlControl
from queue import Queue
import tkinter as tk
import threading
import keyboard
import requests
import asyncio
import random
import math
import time
import json
import os
import uuid
import re

from playsound import playsound

import edge_tts

class Show_Text:

    def __init__(self):
        self.windows_with = 1920
        self.windows_height = 1080
        root = tk.Tk()
        root.title("show_text")
        # root.overrideredirect(True)  # 移除窗口边框
        # root.attributes("-topmost", True)  # 窗口置顶
        root.attributes("-transparentcolor", "black") 
        # root.attributes("-fullscreen", True)
        root.configure(bg = "black")
        root.geometry(f"{self.windows_with}x{self.windows_height}")
        self.root = root
        self.maintext_queue = Queue()
        self.get_guess_queue = Queue()
        self.guess_win_text = ""
        self.msg = ""
        self.canvas_list = []

        threading.Thread(target=self.main_show,daemon=True).start()
        # threading.Thread(target=self.user_join_game,daemon=True).start()

        with open("data/roads.json","r",encoding='utf-8') as file:
            self.road_dict = json.load(file)

        # 观众入座路和植物字母id
        for key in self.road_dict:
            self.road_dict[key]["label"] = self.build_text(
                self.road_dict[key]["font_size"],
                self.road_dict[key]["text"],
                self.road_dict[key]["color"],
                self.road_dict[key]["bg_color"],
                self.road_dict[key]["position"][0],
                self.road_dict[key]["position"][1],
                t_p = self.road_dict[key].get("t_p")
            )
        with open("data/position_show.json","r",encoding='utf-8') as file:
            position_dict = json.load(file)
        # 显示棋盘位置
        for key,value in position_dict.items():
            self.build_text(
                value["font_size"],
                value["text"],
                value["color"],
                value["bg_color"],
                value["position"][0],
                value["position"][1]
            )
        self.usr_dict = {}
        self.usr_openid = {}
        self.blive_usr = SqlControl()
        self.update_sound_text = None
        self.change_text_queue = Queue()

    def build_text(self,font_size,text,color,bg_color,x,y,**kwargs):
        label = tk.Label(self.root,text=text,font=("Microsoft YaHei", font_size,"bold"),fg=color,bg=bg_color)
        if kwargs.get("t_p") == "e":
            label.place(x=x,y=y,anchor = "e")
        else:
            label.place(x = x,y = y)
        self.root.update()
        return label

    def change_text(self,label,text):
        label.config(text=text)
        self.root.update()

    async def edge_text2speech(self,text,file_path):
        voice = "zh-CN-XiaoxiaoNeural"
        tts = edge_tts.Communicate(text, voice)
        await tts.save(file_path)

    def play_sound_file(self,text):
        UUID = str(uuid.uuid4())
        mp3_file = f"audio_temp/{UUID}.mp3"

        asyncio.run(self.edge_text2speech(text,mp3_file))
        playsound(mp3_file)
        os.remove(mp3_file)

    def text2voice(self,text):
        if text != self.update_sound_text:
            self.update_sound_text = text
            threading.Thread(target=self.play_sound_file,args=(text,)).start()

    def main_show(self):
        root_1 = tk.Tk()
        root_1.title("main_text")
        # root_1.overrideredirect(True)  # 移除窗口边框
        # root_1.attributes("-topmost", True)  # 窗口置顶
        root_1.attributes("-transparentcolor", "black") 
        root_1.attributes("-fullscreen", True)
        root_1.configure(bg = "black")
        root_1.geometry(f"{self.windows_with}x{self.windows_height}")
        # 创建画布
        canvas = tk.Canvas(root_1, width=1920, height=1080, bg="black")
        canvas.pack()
        canvas_list = []

        self.time_step = 0
        label = tk.Label(root_1,text=" ",font=("Microsoft YaHei", 50,"bold"),fg='#5be1f9',bg="black")
        label.place(relx=0.5,rely=0.5,anchor='center')
        self.play_prompt = "1.输入“签到”领阳光  2.输入“查询”查询阳光  3.输入“入座x路”入座  4.输入“离座”离座  5.输入p+数字放置随机礼盒   6.t+数字铲除植物  7.五个点赞一列普通僵尸,一个点赞加十阳光，B站点赞上限1000  8.在右置位入座的输入z+数字放置僵尸 9.点个关注呗，目标1万粉露+vlog 10.m1 2代表把1的植物移动到2           "
        # self.play_prompt = "1.输入“签到”领阳光  2.输入“查询”查询阳光  3.输入“入座x路”入座  4.输入“离座”离座  5.h+数字放置礼盒  6.以“清哥”开头有回应  7.t+数字更换植物  8.僵尸需要礼物触发  9.一个点赞5阳光，5个点赞放置一波僵尸最高点赞1000次  10.僵尸触发挡位为每增加1电池，放置越高级的僵尸  11.僵尸组直接输入字母就行  12.僵尸组的获胜奖励开发中。。。             "
        label_2 = tk.Label(root_1,text=self.play_prompt,font=("Microsoft YaHei", 25,"bold"),fg='#ff0475',bg="#ffaef1")
        label_2.place(relx = 0.5,y = 28,anchor='center')

        def update():
            if self.time_step >= 3:
                self.msg = ""
                if not self.maintext_queue.empty():
                    self.time_step = 0
                    self.msg = self.maintext_queue.get()
                    self.text2voice(self.msg)
            self.time_step+=1
            total_text = self.guess_win_text + self.msg
            label.config(text=total_text)
            self.play_prompt = self.play_prompt[1:]+self.play_prompt[0]
            label_2.config(text=self.play_prompt)
            root_1.after(1000, update)
        update()
        root_1.mainloop()

    '''
    usr_dict = {
        "usr":"1"
    }
    '''
    def sit_down(self,usr,usr_input,openid):
        if usr_input[0] == "入" and len(usr_input) > 2:
            usr_input = usr_input.replace("一","1")
            usr_input = usr_input.replace("二","2")
            usr_input = usr_input.replace("三","3")
            usr_input = usr_input.replace("四","4")
            usr_input = usr_input.replace("五","5")
            usr_input = usr_input.replace("六","6")
            usr_input = usr_input.replace("七","7")
            usr_input = usr_input.replace("八","8") 
            usr_input = usr_input.replace("九","9")
            usr_input = usr_input.replace("十","10")
            digist = re.findall(r'\d+', usr_input)
            if usr in self.usr_dict and self.usr_dict[usr] != "0":      
                self.maintext_queue.put(f"{usr} 不能占两个位置噢")
                return 
            if len(digist) < 1:
                return
            if digist[0] in self.road_dict:
                row = digist[0]
                if self.road_dict[row]["text"] not in self.usr_dict:
                    remain_sun = self.blive_usr.search_usr(openid)
                    self.change_text(self.road_dict[row]["label"],f"{usr}\n阳光:{remain_sun}")
                    self.road_dict[row]["text"] = usr
                    self.maintext_queue.put(f"{usr}\n入座成功，输入“离座”离开")
                    self.usr_dict[usr] = row
                    self.usr_openid[usr] = openid
                else:
                    self.maintext_queue.put(f"{row}路已经有人入座了")
                
    def stand_up(self,usr,usr_input):
        if usr_input.startswith("离"):
            for key,value in self.road_dict.items():
                if value["text"] == usr:
                    self.change_text(value["label"],f"{key}路")
                    # self.root.after(0, self.change_text, value["label"], f"{key}路")

                    value["text"] = f"{key}路"
                    self.maintext_queue.put(f"{usr}\n离开座位")
                    del self.usr_dict[usr]
                    del self.usr_openid[usr]

if __name__=="__main__":
    show_text = Show_Text()
    while True:
        a = input("输入:")
        show_text.text2voice(a)