import asyncio
import json
import websockets
import requests
import time
import hashlib
import hmac
import random
from hashlib import sha256
from . import proto
import os
# 该示例仅为demo，如需使用在生产环境需要自行按需调整
# from nls_tts import TestTts
# from playsound import playsound
import threading
import uuid
class BiliClient:
    def __init__(self, idCode, appId, key, secret, host):
        self.idCode = idCode
        self.appId = appId
        self.key = key
        self.secret = secret
        self.host = host
        self.gameId = ''
        pass

    # def play_sound_file(self,text):
    #     UUID = str(uuid.uuid4())
    #     mp3_file = f"audio_temp/{UUID}.mp3"
    #     t = TestTts(UUID, mp3_file)
    #     t.start(text)
    #     playsound(mp3_file)
    #     os.remove(mp3_file)
    # def text2voice(self,text):
    #     threading.Thread(target=self.play_sound_file,args=(text,)).start()

    # 事件循环
    def run(self):
        loop = asyncio.get_event_loop()
        # 建立连接
        websocket = loop.run_until_complete(self.connect())

        tasks = [
            # 读取信息
            asyncio.ensure_future(self.recvLoop(websocket)),
            # 发送心跳
            asyncio.ensure_future(self.heartBeat(websocket)),
             # 发送游戏心跳
            asyncio.ensure_future(self.appheartBeat()),
        ]
        loop.run_until_complete(asyncio.gather(*tasks))

    # http的签名
    def sign(self, params):
        key = self.key
        secret = self.secret
        md5 = hashlib.md5()
        md5.update(params.encode())
        ts = time.time()
        nonce = random.randint(1, 100000)+time.time()
        md5data = md5.hexdigest()
        headerMap = {
            "x-bili-timestamp": str(int(ts)),
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": str(nonce),
            "x-bili-accesskeyid": key,
            "x-bili-signature-version": "1.0",
            "x-bili-content-md5": md5data,
        }

        headerList = sorted(headerMap)
        headerStr = ''

        for key in headerList:
            headerStr = headerStr + key+":"+str(headerMap[key])+"\n"
        headerStr = headerStr.rstrip("\n")

        appsecret = secret.encode()
        data = headerStr.encode()
        signature = hmac.new(appsecret, data, digestmod=sha256).hexdigest()
        headerMap["Authorization"] = signature
        headerMap["Content-Type"] = "application/json"
        headerMap["Accept"] = "application/json"
        return headerMap

    # 获取长连信息
    def getWebsocketInfo(self):
        # 开启应用
        postUrl = "%s/v2/app/start" % self.host
        params = '{"code":"%s","app_id":%d}' % (self.idCode, self.appId)
        headerMap = self.sign(params)
        r = requests.post(url=postUrl, headers=headerMap,
                          data=params) # verify=False
        data = json.loads(r.content)
        # print("data:")
        # print(json.dumps(data,indent=4,ensure_ascii=False))
        self.gameId = str(data['data']['game_info']['game_id'])

        # 获取长连地址和鉴权体
        return str(data['data']['websocket_info']['wss_link'][0]), str(data['data']['websocket_info']['auth_body'])

     # 发送游戏心跳
    async def appheartBeat(self):
        while True:
            await asyncio.ensure_future(asyncio.sleep(20))
            postUrl = "%s/v2/app/heartbeat" % self.host
            params = '{"game_id":"%s"}' % (self.gameId)
            headerMap = self.sign(params)
            r = requests.post(url=postUrl, headers=headerMap,
                            data=params) # verify=False
            # data = json.loads(r.content)
            # print("[BiliClient] send appheartBeat success")


    # 发送鉴权信息
    async def auth(self, websocket, authBody):
        req = proto.Proto()
        req.body = authBody
        req.op = 7
        await websocket.send(req.pack())
        buf = await websocket.recv()
        resp = proto.Proto()
        resp.unpack(buf)
        respBody = json.loads(resp.body)
        if respBody["code"] != 0:
            print("auth 失败")
        else:
            print("auth 成功")

    # 发送心跳
    async def heartBeat(self, websocket):
        while True:
            await asyncio.ensure_future(asyncio.sleep(20))
            req = proto.Proto()
            req.op = 2

            await websocket.send(req.pack())
            # print("[BiliClient] send heartBeat success")

    # 读取信息
    async def recvLoop(self, websocket):
        print("[BiliClient] run recv...")
        while True:
            recvBuf = await websocket.recv()
            resp = proto.Proto()
            # print("recv:")
            item = resp.unpack(recvBuf)
            if item != None:
                if "cmd" in item:
                    if item['cmd'] == "LIVE_OPEN_PLATFORM_DM":
                        danmu = item['data']['msg']
                        voice_text = f"{item['data']['uname']}说：{danmu}"
                        print(f"{item['data']['uname']}：{danmu}")
                        # self.text2voice(voice_text)


    # 建立连接
    async def connect(self):
        addr, authBody = self.getWebsocketInfo()
        # print(addr, authBody)
        # print("addr:",addr)
        # print("audthBody",authBody)
        websocket = await websockets.connect(addr)
        # 鉴权
        await self.auth(websocket, authBody)
        return websocket

    def __enter__(self):
        print("[BiliClient] enter")

    def close(self):
        postUrl = "%s/v2/app/end" % self.host
        params = '{"game_id":"%s","app_id":%d}' % (self.gameId, self.appId)
        headerMap = self.sign(params)
        r = requests.post(url=postUrl, headers=headerMap,
                          data=params) # verify=False
        print("[BiliClient] end app success", params)
    def __exit__(self, type, value, trace):
        # 关闭应用
        postUrl = "%s/v2/app/end" % self.host
        params = '{"game_id":"%s","app_id":%d}' % (self.gameId, self.appId)
        headerMap = self.sign(params)
        r = requests.post(url=postUrl, headers=headerMap,
                          data=params) # verify=False
        print("[BiliClient] end app success", params)


if __name__ == '__main__':

    cli = BiliClient(
            idCode="E1P62JMCYQRK9",  # 主播身份码
            appId=1733022254287,  # 应用id/
            key="LNorYk0KmMbs92lEqgrqC4vz",  # access_key
            secret="onoCyO99ZidlqqlcBNOnFiSGtdqY85",  # access_key_secret
            host="https://live-open.biliapi.com") # 开放平台 (线上环境)
    with cli:
        cli.run()

        
