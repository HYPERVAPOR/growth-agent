import requests


class BrowserEngine:
    def __init__(self, api_key: str, base_url: str, user_id: str):
        self.api_key = api_key
        self.base_url = base_url
        self.user_id = user_id

    def get_ws_url(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        start_url = f"{self.base_url}/api/v1/browser/start?user_id={self.user_id}"
        print(f"🚀 正在请求 AdsPower 环境: {self.user_id}...")

        try:
            # proxies={'http': None} 防止全局代理干扰本地 API 调用
            resp = requests.get(
                start_url,
                headers=headers,
                proxies={"http": None, "https": None},
                timeout=20,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]["ws"]["puppeteer"]
            print(f"❌ AdsPower 启动失败: {data.get('msg')}")
            return None
        except Exception as e:
            print(f"❌ 连接 AdsPower API 异常: {e}")
            return None

