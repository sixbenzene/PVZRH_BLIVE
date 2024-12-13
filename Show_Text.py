from SqlControl import SqlControl
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

from playsound import playsound
from nls_tts import TestTts
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
                self.road_dict[key]["position"][1]
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
        self.blive_usr = SqlControl()
        self.update_sound_text = None
        

    def build_text(self,font_size,text,color,bg_color,x,y):
        label = tk.Label(self.root,text=text,font=("Microsoft YaHei", font_size,"bold"),fg=color,bg=bg_color)
        label.place(x=x,y=y)
        self.root.update()
        return label

    def change_text(self,label,text):
        label.config(text=text)
        self.root.update()

    def play_sound_file(self,text):
        UUID = str(uuid.uuid4())
        mp3_file = f"audio_temp/{UUID}.mp3"
        t = TestTts(UUID, mp3_file)
        t.start(text)
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
        # root_1.attributes("-fullscreen", True)
        root_1.configure(bg = "black")
        root_1.geometry(f"{self.windows_with}x{self.windows_height}")
        # 创建画布
        canvas = tk.Canvas(root_1, width=1920, height=1080, bg="black")
        canvas.pack()
        canvas_list = []
        cx, cy = 960, 540  # 圆心位置
        r = 450            # 半径
        self.start_time = time.time()
        self.end_time = self.start_time +3
        label = tk.Label(root_1,text=" ",font=("Microsoft YaHei", 50,"bold"),fg='#5be1f9',bg="black")
        label.place(relx=0.5,rely=0.5,anchor='center')

        def update():
            if self.end_time-self.start_time > 3:
                self.msg = ""
                if not self.maintext_queue.empty():
                    self.start_time = time.time()
                    self.msg = self.maintext_queue.get()
                    self.text2voice(self.msg)
            self.end_time = time.time()
            total_text = self.guess_win_text + self.msg
            label.config(text=total_text)
            # if not self.get_guess_queue.empty():
            #     canvas_text = self.get_guess_queue.get()
            #     ra_angle = random.randint(0,359)
            #     x = cx + r * math.cos(math.radians(ra_angle))
            #     y = cy + r * math.sin(math.radians(ra_angle))
            #     canvas_list.append({
            #         "canvas":canvas.create_text(x, y, text=canvas_text, font = ("Microsoft YaHei", 50,"bold"),fill = '#5be1f9'),
            #         "x":x,
            #         "y":y,
            #         "r":r,
            #         "text":canvas_text,
            #         "angle":ra_angle,
            #         "font_size":50
            #     })
            # i = 0
            # while i < len(canvas_list):
            #     canvas_dict = canvas_list[i]
            #     canvas.coords(canvas_dict["canvas"], canvas_dict["x"], canvas_dict["y"])
            #     canvas.itemconfig(canvas_dict["canvas"], text=canvas_dict["text"], font= ("Microsoft YaHei", int(canvas_dict["font_size"]),"bold"),fill = '#5be1f9')
            #     if canvas_dict["font_size"] <10:
            #         canvas.delete(canvas_dict["canvas"])
            #         canvas_list.pop(i)
            #         continue
            #     canvas_dict["r"] -= 2
            #     x = cx + canvas_dict['r'] * math.cos(math.radians(canvas_dict["angle"]))
            #     y = cy + canvas_dict['r'] * math.sin(math.radians(canvas_dict["angle"]))
            #     canvas_dict["x"] = x
            #     canvas_dict["y"] = y
            #     canvas_dict["font_size"] -= 0.3
            #     i+=1

            root_1.after(16, update)
        update()
        root_1.mainloop()
        '''
        label = tk.Label(root_1,text=" ",font=("Microsoft YaHei", 50,"bold"),fg='#5be1f9',bg="black")
        label.place(relx=0.5,rely=0.5,anchor='center')
        root_1.update()
        start_time = time.time()
        text = ""
        while True:
            end_time = time.time()
            if end_time-start_time >5:
                text = " "
                if not self.maintext_queue.empty():
                    start_time = time.time()
                    text = self.maintext_queue.get()
                    text2voice(text)
            aim_text = self.guess_win_text+text
            label.config(text=text)
            root_1.update()
            time.sleep(1)
        '''

    def sit_down(self,usr,usr_input):
        if usr_input[0] == "入" and len(usr_input) > 2:
            usr_input = usr_input.replace("一","1")
            usr_input = usr_input.replace("二","2")
            usr_input = usr_input.replace("三","3")
            usr_input = usr_input.replace("四","4")
            usr_input = usr_input.replace("五","5")
            if usr in self.usr_dict and self.usr_dict[usr] != "0":
                self.maintext_queue.put(f"{usr} 不能占两个位置噢")
                return 
            if usr_input[2] in self.road_dict:
                row = usr_input[2]
                if self.road_dict[row]["text"] == f"输入“入座{row}路”入座" :
                    remain_sun = self.blive_usr.search_usr(usr)
                    self.change_text(self.road_dict[row]["label"],f"{usr}\n阳光:{remain_sun}")
                    self.road_dict[row]["text"] = usr
                    self.maintext_queue.put(f"{usr}\n入座成功，输入“离座”离开\n目标:存活下来!")
                    self.usr_dict[usr] = row
                else:
                    self.maintext_queue.put(f"{row}路已经有人入座了")
                
    def stand_up(self,usr,usr_input):
        if usr_input.startswith("离"):
            for key,value in self.road_dict.items():
                if value["text"] == usr:
                    self.change_text(value["label"],f"输入“入座{key}路”入座")
                    value["text"] = f"输入“入座{key}路”入座"
                    self.maintext_queue.put(f"{usr}\n离开座位")
                    del self.usr_dict[usr]

if __name__=="__main__":
    show_text = Show_Text()
    cx, cy = 960, 540  # 圆心位置
    r = 450            # 半径
    def seconds_to_mmss(seconds):
        minutes = seconds // 60  # 整数除法得到分钟
        remaining_seconds = seconds % 60  # 取余得到剩余的秒数
        return f"{minutes:02}:{remaining_seconds:02}"  # 格式化为 MM:SS
    remain_time = 60
    while True:
        # usr = input("输入用户：")
        # if usr == "0":
        #     break
        # text = input("输入文字：")
        # show_text.sit_down(usr,text)
        # show_text.stand_up(usr,text)
        # text = input("输入：")
        # show_text.get_guess_queue.put(text)
        show_text.guess_win_text = seconds_to_mmss(remain_time)+"\n输入x路会赢,赢500阳光\n"
        remain_time -= 1
        time.sleep(1)