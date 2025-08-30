import asyncio
import os
from playsound import playsound
import threading
import uuid
import edge_tts
# TTS 类
class TTS:
    def __init__(self):
        self.old_text = None
        self.flag = None
        self.voices = ["zh-CN-XiaoxiaoNeural","zh-CN-XiaoyiNeural","zh-CN-YunjianNeural","zh-CN-YunyangNeural","zh-CN-liaoning-XiaobeiNeural","zh-CN-shaanxi-XiaoniNeural","zh-HK-HiuGaaiNeural","zh-HK-HiuMaanNeural","zh-HK-WanLungNeural","zh-TW-HsiaoChenNeural"]
        os.makedirs("audio_temp",exist_ok = True)

    def play_audio(self, text):
        if self.old_text != text:
            self.old_text = text
            threading.Thread(target=self.text_to_speech, args=(text,), daemon=True).start()

    def play_sentence(self,sentences:list,obj = None):
        if obj:
            obj.text = "清哥思考中..."
        file_list = asyncio.run(self.create_files(sentences))
        for f,text in file_list:
            if obj:
                obj.text = text
            playsound(f)
            if obj:
                obj.text = None
        for f,text in file_list:
            os.remove(f)


    def text_to_speech(self, text,obj = None):
        if self.flag:
            return
        self.flag = 1
        UUID = str(uuid.uuid1())
        mp3_file = f"audio_temp/{UUID}.mp3"

        try:
            asyncio.run(self.edge_text2speech(text, mp3_file))
            if obj:
                obj.text = text
            playsound(mp3_file)
        except:
            pass
        os.remove(mp3_file)
        self.flag = None

    async def create_files(self,sentences:list):
        tasks = []
        file_list = []
        # print(sentences)
        for sent in sentences:
            UUID = str(uuid.uuid1())
            mp3_file = f"audio_temp/{UUID}.mp3"
            file_list.append((mp3_file,sent))
            tasks.append(self.edge_text2speech(sent,mp3_file))
        await asyncio.gather(*tasks)
        return file_list

    async def edge_text2speech(self, text, file_path):
        voice = self.voices[1]
        tts = edge_tts.Communicate(text, voice)
        await tts.save(file_path)

if __name__== "__main__":
    tts = TTS()
    tts.play_sentence(['清哥：技术大佬的路在脚下，', '有问题随时问我！', '一起玩转植物大战僵尸～'])
    input("等待播放中。。。")