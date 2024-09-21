import requests
import json
import time


def apido(text: str):
    url = 'https://api.coze.cn/open_api/v2/chat'
    headers = {
        'Authorization': 'Bearer pat_J0kTR3d58Z8bWcFpUisvOMvrOToUDg6aVIk76yoraRCKapOt8jlHa6ghBbXO5a0h',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'api.coze.cn',
        'Connection': 'keep-alive'
    }

    data = {
        "conversation_id": "123",
        "bot_id": "7397359013593743371",
        "user": "29032201862555",
        "query": text,
        "stream": False
    }

    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            response_data = response.json()
            messages = response_data.get("messages", [])
            for message in messages:
                if message.get("role") == "assistant" and message.get("type") == "answer":
                    return message.get("content")
            return None
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    raise ConnectionError("API请求失败: 超过最大重试次数")


def process_and_store_log(log_text):
    try:
        # 使用API处理日志数据
        return apido(log_text)

    except ConnectionError as e:
        print(f"API处理失败: {e}")


