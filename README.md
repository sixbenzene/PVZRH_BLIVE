# PVZRH_BLIVE ![License](https://img.shields.io/badge/license-GPL-yellow)![Language](https://img.shields.io/badge/language-Python-brightgreen) 
与PVZ融合版结合，专为bilibili直播打造的弹幕互动玩法🥳

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


### 获取csrf_token,cookie
