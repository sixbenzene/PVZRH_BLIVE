import base64
import io
from obswebsocket import obsws, requests
from PIL import Image 
import cv2
import numpy as np
import time
class CheckScreen(object):

    def __init__(self):
        self.ws = obsws("localhost",4455)
        self.ws.connect()

    def grab_img(self):
        resp = self.ws.call(requests.GetSourceScreenshot(
            sourceName="游戏采集",   # 必须是 OBS 里存在的输入或场景名
            imageFormat="png",
            imageWidth=640,       # 可选，缩放到 640×360
            imageHeight=360,
            imageCompressionQuality=-1
        )) 
        b64_data = resp.datain["imageData"].split(",", 1)[-1]
        img_bytes = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(img_bytes))
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    def mse(self,img1, img2):
        """计算两张图的均方误差；全等时返回 0"""
        diff = cv2.absdiff(img1, img2)
        value = np.mean(diff.astype(np.float32) ** 2)
        # print(value)
        if value < 100:
            return True
        else:
            return False
    
    def check(self):
        img1 = self.grab_img()
        
        while True:
            time.sleep(5)
            img2 = self.grab_img()
            value = self.mse(img1,img2)
            if value:          # 经验阈值，完全无损时 MSE 接近 0
                print("两张图相同")
            else:
                print("两张图不同")
            img1 = img2

    def __exit__(self):
        self.ws.disconnect()

if __name__ == "__main__":
    CS = CheckScreen()
    CS.check()