import pygame
import threading
import asyncio
import uuid
import os
import time
import json
from queue import Queue
from playsound import playsound
import edge_tts
import random
import websockets
from datetime import date
import config
from .SqlControl import SqlControl


# 字体加载
def load_font(size):
    return pygame.font.SysFont("Microsoft YaHei", size, bold=True)

# TTS 类
class TTS:
    def __init__(self):
        self.old_text = None

    def play_audio(self, text):
        if self.old_text != text:
            self.old_text = text
            threading.Thread(target=self.text_to_speech, args=(text,), daemon=True).start()

    def text_to_speech(self, text):
        UUID = str(uuid.uuid1())
        mp3_file = f"audio_temp/{UUID}.mp3"
        asyncio.run(self.edge_text2speech(text, mp3_file))
        playsound(mp3_file)
        os.remove(mp3_file)

    async def edge_text2speech(self, text, file_path):
        voice = "zh-CN-XiaoxiaoNeural"
        tts = edge_tts.Communicate(text, voice)
        await tts.save(file_path)

# 滚动文字类
class RollingText:
    def __init__(self, surface):
        self.surface = surface
        self.items = []
        self.font = load_font(40)
        self.tts = TTS()

    def add_text(self, text):
        if config.audio:
            self.tts.play_audio(text)
        text_surface = self.font.render(text, True, (255, 164, 164))  # 粉红
        x = 1920
        y = random.randint(100, 800)
        self.items.append([text_surface, x, y])

    def update(self):
        for item in self.items:
            item[1] -= 5
        self.items = [i for i in self.items if i[1] + i[0].get_width() > 0]

    def draw(self):
        for surface, x, y in self.items:
            self.surface.blit(surface, (x, y))

# 静态文字
class StaticText:
    def __init__(self, text, font_size, x, y, color, anchor='w'):
        self.font = load_font(font_size)
        self.text = text
        self.color = color
        self.pos = (x, y)
        self.anchor = anchor
        # self.surfaces = [self.font.render(line, True, color) for line in self.lines]

    def draw(self, surface):
        x, y = self.pos
        lines = self.text.split("\n")
        surfaces = [self.font.render(line, True, self.color) for line in lines]
        for surf in surfaces:
            draw_x = x
            if self.anchor == 'e':
                draw_x -= surf.get_width()
            surface.blit(surf, (draw_x, y))
            y += self.font.get_linesize()  # 下一行向下移动一行高度

# 滚动公告栏
class Announcement:
    def __init__(self, text):
        self.font = load_font(45)
        self.surface = self.font.render(text, True, (133, 255, 133))
        self.x = 0
        self.y = 0

    def update(self):
        self.x -= 3
        if self.x + self.surface.get_width() < 0:
            self.x = 1920

    def draw(self, surface):
        surface.blit(self.surface, (self.x, self.y))

class RankingAnnouncement(Announcement):
    
    def update_text(self):
        today = date.today()
        today = str(today)
        blive_usr = SqlControl()
        text = today+" 全服阳光排名前10名："
        result = blive_usr.search_ranking()
        for i,value in enumerate(result,1):
            if i >10:
                break
            text += f"{i}.{value[4]} 阳光：{value[2]}。 "
        self.surface = self.font.render(text, True, (133, 255, 133))
        self.y = 45

# 显示竞猜,文字更新
class LimiTextTime:
    def __init__(self, surface):
        self.surface = surface
        self.font = load_font(80)

        self.time = time.time()
        self.num = 0
        self.text = None

    def give_time(self, num):
        self.num = num
        self.time = time.time()

    def update(self):
        if self.num >0:
            end_time = time.time()
            if end_time-self.time >=1:
                self.time = time.time()
                self.num-=1
                self.text = f"输入x路会赢，投入500阳光，猜对赢1000阳光\n倒计时：{self.num}"
        else:
            self.text = None

    def draw(self):
        if self.text:
            lines = self.text.split("\n")
            surfaces = [self.font.render(line, True, (155, 227, 255)) for line in lines]

            # 整段文字高度
            total_height = len(surfaces) * self.font.get_linesize()

            # 居中起始y
            start_y = (self.surface.get_height() - total_height) // 2

            for i, surf in enumerate(surfaces):
                rect = surf.get_rect(center=(self.surface.get_width() // 2, start_y + i * self.font.get_linesize()))
                self.surface.blit(surf, rect)
  

# 主界面类
class Interface:
    def __init__(self):
        # 初始化 pygame
        pygame.init()

        # 屏幕尺寸
        WIDTH, HEIGHT = 1920, 1080
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("PVZ")
        self.clock = pygame.time.Clock()
        self.rolling_queue = Queue()
        self.rolling_text = RollingText(self.screen)
        self.announcement = Announcement("输入“签到”领阳光   输入“查询”查询阳光   输入“入座x路”入座,消耗500阳光，输一局扣200阳光     输入“离座”离座   输入p+数字放置随机礼盒消耗100阳光    t+数字铲除植物   五个点赞一列普通僵尸,一个点赞加十阳光，B站点赞上限1000   在右置位入座的输入z+数字放置僵尸   m1 2代表把1的植物移动到2    c1代表点击1号格子   求关注！！！！！")
        # self.test_ann = Announcement("添加功能开发测试中，游玩有可能让您损失阳光，特此告知！！！")
        # self.test_ann.y = 85
        self.ranking_text = RankingAnnouncement("")
        self.ranking_text.update_text()
        self.userseat = {}
        self.roads_d = {}
        self.positions_d = {}
        self.static_texts = []
        self.ltt = LimiTextTime(self.screen)
        # self.ltt.give_time(60)

    def load_font(size):
        return pygame.font.SysFont("Microsoft YaHei", size, bold=True)
    
    def load_data(self):
        with open("./data/position_show.json", "r", encoding='utf-8') as f:
            self.positions_d = json.load(f)
        with open("./data/user_seat.json", "r", encoding='utf-8') as f:
            self.roads_d = json.load(f)

    def create_static_texts(self):
        # 位置文字
        for key, value in self.positions_d.items():
            text = StaticText(value["text"], value["font_size"]+10,
                              value["position"][0], value["position"][1]+5,
                              (255, 232, 105))
            self.static_texts.append(text)

        # 道路文字
        for key, value in self.roads_d.items():
            anchor = "w"
            if int(key) > 5:
                anchor = "e"
            text = StaticText(value["text"], value["font_size"]+10,
                              value["position"][0], value["position"][1]+5,
                              (155, 227, 255), anchor=anchor)
            self.userseat[key] = {
                "open_id": None,
                "uname": None,
                "text": value["text"],
                "text_obj": text
            }

    def update_roads(self):
        for key, data in self.userseat.items():
            text_obj = data["text_obj"]
            latest_text = data["text"]
            if text_obj.text != latest_text:
                text_obj.text = latest_text
                text_obj.surface = text_obj.font.render(latest_text, True, (155, 227, 255))

    def draw(self):
        # 绘制静态文字
        for text in self.static_texts:
            text.draw(self.screen)

        # 绘制道路文字
        for key, value in self.userseat.items():
            value["text_obj"].draw(self.screen)

        # 滚动文本和公告
        self.rolling_text.draw()
        self.announcement.draw(self.screen)
        # self.test_ann.draw(self.screen)
        self.ltt.draw()
        self.ranking_text.draw(self.screen)

    def update(self):
        self.rolling_text.update()
        self.announcement.update()
        # self.test_ann.update()
        self.ltt.update()
        self.ranking_text.update()
        self.update_roads()
        if not self.rolling_queue.empty():
            msg = self.rolling_queue.get()
            self.rolling_text.add_text(msg)

    def render(self):
        self.screen.fill((0, 0, 0))  # 清屏
        self.update()
        self.draw()
        pygame.display.flip()

    def tick(self,fps = 60):
        self.clock.tick(fps)

    async def handle_client(self,websocket):
        print(f"客户端连接: {websocket.remote_address}")
        try:
            async for message in websocket:
                data = json.loads(message)
                info = data.get("info")
                if info=="sit_down":
                    uname = data['uname']
                    open_id = data['open_id']
                    seat = data['seat']
                    text = data['text']
                    self.userseat[seat]['uname'] = uname
                    self.userseat[seat]['open_id'] = open_id
                    self.userseat[seat]['text'] = text

                elif info=="stand_up":
                    seat = data['seat']
                    self.userseat[seat]['uname'] = None
                    self.userseat[seat]['open_id'] = None
                    self.userseat[seat]['text'] = seat+"路"

                elif info=="roll_text":
                    self.rolling_queue.put(data["text"])

                elif info=="limit_text":
                    time_num = data["time"]
                    self.ltt.give_time(time_num)

                
        except Exception as e:
            print(f"连接出错: {e}")

    async def main(self):
        async with websockets.serve(self.handle_client, "localhost", 8765):
            print("WebSocket 服务已启动: ws://localhost:8765")
            await asyncio.Future()  # 永远运行

    def start_in_thread(self):
        def runner():
            loop = asyncio.new_event_loop()   # 每个线程要有自己的事件循环
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.main())

        t = threading.Thread(target=runner, daemon=True)
        t.start()

# 输入线程
def input_thread(ui: Interface):
    while True:
        text = input("输入内容：")
        ui.rolling_queue.put(text)
        ui.ltt.give_time(10)


# 主程序
def main():
    os.makedirs("audio_temp", exist_ok=True)
    loop = asyncio.get_event_loop()
    ui = Interface()
    ui.load_data()
    ui.create_static_texts()
    threading.Thread(target=input_thread, args=(ui,), daemon=True).start()
    ui.start_in_thread()

    running = True
    while running:
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ui.render()

        ui.tick()

    pygame.quit()

if __name__ == "__main__":
    main()