idCode = ""  #开发者平台获取
appId=1234  #开发者平台获取
key="" # B站开发者入住获取
secret="" # B站开发者入住获取
host="https://live-open.biliapi.com"
room_id = 1234  # 自己的直播间号
ruid = 1234 # 网页主页个人资料有一个uid

csrf_token = ''
cookie = ""

check_screen = False  # 防卡，开启需要obs websocket开启
audio = False  # 是否开启语音
author = "清哥想要成为技术大佬" # 高权限b站用户名,改成自己名字，自己操作就不会扣阳光了

use_llm = False   # 是否使用大模型
# 需要user_llm = True 大模型人设
llm_url = ""
system_prompt = ''' 

'''