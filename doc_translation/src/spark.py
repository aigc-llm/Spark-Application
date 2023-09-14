import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import ssl
import websocket
import langchain
import logging
from config import SPARK_APPID, SPARK_API_KEY, SPARK_API_SECRET
from urllib.parse import urlparse
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from typing import Optional, List, Dict, Mapping, Any
from langchain.llms.base import LLM
from langchain.cache import InMemoryCache
  
logging.basicConfig(level=logging.INFO)
langchain.llm_cache = InMemoryCache()
result_list = []
  
  
def _construct_query(prompt, temperature, max_tokens):
    data = {
        "header": {
            "app_id": SPARK_APPID,
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                # "domain": "general",
                "domain": "generalv2",
                "random_threshold": temperature,
                "max_tokens": max_tokens,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": [
                    {"role": "user", "content": prompt}
                ]
            }
        }
    }
    return data
  
  
def _run(ws, *args):
    data = json.dumps(_construct_query(prompt=ws.question, 
                                       temperature=ws.temperature, 
                                       max_tokens=ws.max_tokens))
    ws.send(data)
  
  
def on_error(ws, error):
    print("error:", error)
  
  
def on_close(ws, close_status_code, close_msg):
    print("closed...")
  
  
def on_open(ws):
    thread.start_new_thread(_run, (ws,))
  
  
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        result_list.append(content)
        if status == 2:
            ws.close()
            setattr(ws, "content", "".join(result_list))
            result_list.clear()
  
  
class Spark(LLM):
    # gpt_url = "ws://spark-api.xf-yun.com/v1.1/chat"
    gpt_url = "ws://spark-api.xf-yun.com/v2.1/chat"
    host = urlparse(gpt_url).netloc
    path = urlparse(gpt_url).path
    max_tokens = 1024
    temperature = 0.5
  
    @property
    def _llm_type(self) -> str:
        return "Spark"
  
    def _get_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
  
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"
  
        signature_sha = hmac.new(SPARK_API_SECRET.encode('utf-8'), 
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
  
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = f'api_key="{SPARK_API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
  
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.gpt_url + '?' + urlencode(v)
        return url
  
    def _post(self, prompt):
        websocket.enableTrace(False)
        wsUrl = self._get_url()
        ws = websocket.WebSocketApp(wsUrl, 
                                    on_message=on_message, 
                                    on_error=on_error,
                                    on_close=on_close, 
                                    on_open=on_open)
        ws.question = prompt
        setattr(ws, "temperature", self.temperature)
        setattr(ws, "max_tokens", self.max_tokens)
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        return ws.content if hasattr(ws, "content") else ""
  
    def _call(self, prompt: str,stop: Optional[List[str]] = None) -> str:
        content = self._post(prompt)
        return content
  
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        _param_dict = {
            "url": self.gpt_url
        }
        return _param_dict
  
  
