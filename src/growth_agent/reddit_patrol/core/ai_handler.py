import json
import time

import requests


class AIHandler:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def call(self, system_rules, user_data, retries: int = 3):
        # 兼容处理：如果是字典则转字符串
        sys_content = (
            system_rules
            if isinstance(system_rules, str)
            else json.dumps(system_rules, ensure_ascii=False)
        )
        user_content = (
            user_data
            if isinstance(user_data, str)
            else json.dumps(user_data, ensure_ascii=False)
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_content},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for i in range(retries):
            try:
                r = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=45
                )
                res_json = r.json()

                if "choices" in res_json:
                    raw_content = (
                        res_json["choices"][0]["message"]["content"].strip()
                    )
                    return self._safe_parse(raw_content)

                # 429 频率限制处理
                if r.status_code == 429:
                    wait_time = (i + 1) * 10
                    print(f"⏳ 触发频率限制，等待 {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                print(f"⚠️ API 错误: {res_json}")
                return None

            except Exception as e:
                print(f"❌ AI 调用异常 (第{i+1}次重试): {e}")
                time.sleep(5)
        return None

    def _safe_parse(self, raw_str: str):
        try:
            data = json.loads(raw_str)
            return data[0] if isinstance(data, list) else data
        except Exception:
            return None

