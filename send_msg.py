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
        'cookie': "buvid3=51091490-8A8B-57CB-876D-B7367411600C48462infoc; b_nut=1725001548; _uuid=C23FE1C4-E5CE-1AD3-8EAE-ABA3EB810355349032infoc; enable_web_push=DISABLE; buvid4=ABE94ED3-B857-FC8C-0E40-BE7BADC1C73E49665-024083007-Yr3%2BhwNCoNYsJzhazPiuoQ%3D%3D; header_theme_version=CLOSE; CURRENT_FNVAL=4048; LIVE_BUVID=AUTO7817253382566032; rpdid=|(ummlmkm||R0J'u~kYRYmuuY; buvid_fp_plain=undefined; DedeUserID=106135359; DedeUserID__ckMd5=041f270fdaee988e; home_feed_column=5; browser_resolution=1920-957; CURRENT_QUALITY=80; bp_t_offset_106135359=1001894442841407488; bp_video_offset_106135359=1004075345629937664; fingerprint=941aa36bdb8458d9bc469cf901dea075; buvid_fp=941aa36bdb8458d9bc469cf901dea075; PVID=1; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzM2NTgyMDMsImlhdCI6MTczMzM5ODk0MywicGx0IjotMX0.1qbCUAUej2jXLiqpYQm3An90hmt9XJj8HEcrQf2inOo; bili_ticket_expires=1733658143; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1732176959,1732779426,1733046266,1733399021; SESSDATA=860ee2aa%2C1749116633%2C1a72d%2Ac2CjBSum2P3OQ-PUZwF3t1FkvGbRstZgina1pvOyGIk5KX08N6b6xLIM1rdPmVTD6o45wSVmhob0M2OHR5YWtTVkxkRUd6elZJb3ZnbEhYWlZkMk1tVDdIRnBMU0paWXJMSFpBVXVzNE1pLXRWdkJVc2xGdHQ4azM4aHpsNDRxbHVTbVBnSDBYMFRnIIEC; bili_jct=87feb7aaa0d6ab94ec884407797d727a; b_lsid=10E81666C_193A5459D85",
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