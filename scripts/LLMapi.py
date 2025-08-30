import requests
import config
import re

class QwenLLM:

    def __init__(self,url = config.llm_url,max_tokens= 4096,temperature=0.7,enable_thinking=False):
        self.url = url
        self.enable_thinking = enable_thinking
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer EMPTY"
        }
        self.payload = {
            "model": "./model",
            "messages": None,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": enable_thinking}
        }

    def analysis(self,text):
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        if cleaned:
            return cleaned
        else:
            return text

    def chat(self,messages):
        self.payload["messages"] = messages
        response = requests.post(self.url, headers=self.headers, json=self.payload)
        if response.status_code != 200:
            return response.json().get("message","Unknown error")
        content = response.json()["choices"][0]["message"]["content"]
        content = self.analysis(content)

        return content

class ConvertHistory:

    def __init__(self,history:list = []):
        self.history = history
    
    def add_history(self,prompt,role="user"):
        data = {
            "role":role,
            "content":prompt
        }
        self.history.append(data)
        return self.history

if __name__ == "__main__":
    llm = QwenLLM(enable_thinking=True)
    ch = ConvertHistory()

    prompt = "你已经有2分钟没有跟观众说话了，说两句"
    history = ch.add_history(config.system_prompt,"system")
    history = ch.add_history(prompt)
    print(llm.chat(history))