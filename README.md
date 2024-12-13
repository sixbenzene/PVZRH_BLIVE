# PVZRH_BLIVE ![License](https://img.shields.io/badge/license-GPL-yellow)![Language](https://img.shields.io/badge/language-Python-brightgreen) 
✏️与PVZ融合版结合，专为bilibili直播打造的弹幕互动玩法🥳  
😜想要查看效果，关注直播间：http://live.bilibili.com/4638098

### 日志
- 🔥2024/12/13:将代码整体上传到仓库🔥

### 前置要求
- b站获取主播身份码，应用id，access_key,access_key_secret. 后三项需要申请开发者入驻
- csrf_token,cookie,和roomid.前两项的教程[点击这里](https://github.com/sixbenzene/PVZRH_BLIVE?tab=readme-ov-file#%E8%8E%B7%E5%8F%96csrf_tokencookie)
### 如何开始
- 拉取代码
```
git clone https://github.com/sixbenzene/PVZRH_BLIVE.git
cd PVZRH_BLIVE
```
- 创建conda环境
```
conda create -n blive python=3.10
pip install -r requirements.txt
```
在config.py填写需要的参数
- 在[releases](https://github.com/sixbenzene/PVZRH_BLIVE/releases/tag/pvzRH)下载植物大战僵尸v2.1.3压缩包
打开植物大战僵尸，进入我是僵尸模式，开启自动斗蛐蛐
```
python receive_msg.py
```
- 直播使用obs或直播姬

### 获取csrf_token,cookie
- 打开自己直播间，按下f12，查看network  
  检索关键字检索send。手动发送一个弹幕。  
  这时会跳出来一个请求，查看这个请求的payload。里面有csrf_token如图
  
![image](https://github.com/user-attachments/assets/19ad5024-4877-4d26-ae4b-1f07012c949b)
- 在headers可以找到cookie如图

![image](https://github.com/user-attachments/assets/d1cd8190-f0e2-4a73-92e2-35efc9799f0a)























