import json
import os
from datetime import datetime


class DBManager:
    def __init__(self, db_path: str = "data/processed_posts.json"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_data(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, data) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_post(self, post_data) -> bool:
        data = self._load_data()
        if any(p["post_id"] == post_data["post_id"] for p in data):
            return False
        post_data["status"] = "pending"
        post_data["timestamp"] = datetime.now().isoformat()
        data.append(post_data)
        self._save_data(data)
        return True

    def get_pending_posts(self):
        data = self._load_data()
        return [p for p in data if p.get("status") == "pending"]

    def mark_as_published(self, post_id: str) -> bool:
        data = self._load_data()
        for post in data:
            if post["post_id"] == post_id:
                post["status"] = "published"
                self._save_data(data)
                return True
        return False

