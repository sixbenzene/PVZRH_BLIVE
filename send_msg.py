import requests
import config
import time


def send_danmu(msg: str):
    url = "https://api.live.bilibili.com/msg/send"
    form_data = {
        'bubble': 0,
        'msg': "",
        'color': 16777215,
        'mode': 1,
        'room_type': 0,
        'jumpfrom': 0,
        'reply_mid': 0,
        'reply_attr': 0,
        'reply_type': 0,
        'fontsize': 25,
        'rnd': int(time.time()),
        'roomid': config.roomid,
        'csrf': config.csrf_token,
        'csrf_token': config.csrf_token,
    }
    headers = {
        'cookie': config.cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }
    for i in range(0,len(msg),20):
        form_data['msg'] = msg[i:i+20]
        response = requests.post(url=url, data=form_data, headers=headers)
        time.sleep(1)
    print(response.status_code)


if __name__ == "__main__":
    # print(int(time.time()))
    # send_danmu("测试\n测试")
    # send_danmu("查询")
    # while True:
    #     send_danmu("测试")
    #     time.sleep(780)
    while True:
        a = input("输入:")
        send_danmu(a)
    # pass