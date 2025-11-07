import os
import json
import time
from app.client.ciam import get_new_token
from app.client.engsel import get_profile
from app.util import ensure_api_key

class Auth:
    _instance_ = None
    _initialized_ = False

    api_key = ""
    refresh_tokens = []
    active_user = None
    last_refresh_time = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_

    def __init__(self):
        if not self._initialized_:
            self.api_key = ensure_api_key()
            if os.path.exists("refresh-tokens.json"):
                self.load_tokens()
            else:
                with open("refresh-tokens.json", "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4)

            self.load_active_number()
            self.last_refresh_time = int(time.time())
            self._initialized_ = True

    def load_tokens(self):
        with open("refresh-tokens.json", "r", encoding="utf-8") as f:
            tokens = json.load(f)
            self.refresh_tokens = []
            for rt in tokens:
                if "number" in rt and "refresh_token" in rt:
                    self.refresh_tokens.append(rt)
                else:
                    print(f"⚠️ Invalid token entry: {rt}")

    def write_tokens_to_file(self):
        with open("refresh-tokens.json", "w", encoding="utf-8") as f:
            json.dump(self.refresh_tokens, f, indent=4)

    def write_active_number(self):
        if self.active_user:
            with open("active.number", "w", encoding="utf-8") as f:
                f.write(str(self.active_user["number"]))
        elif os.path.exists("active.number"):
            os.remove("active.number")

    def load_active_number(self):
        if os.path.exists("active.number"):
            with open("active.number", "r", encoding="utf-8") as f:
                number_str = f.read().strip()
                if number_str.isdigit():
                    number = int(number_str)
                    self.set_active_user(number)

    def add_refresh_token(self, number: int, refresh_token: str):
        existing = next((rt for rt in self.refresh_tokens if rt["number"] == number), None)
        tokens = get_new_token(self.api_key, refresh_token, "")
        if not tokens:
            print(f"⚠️ Gagal mendapatkan token untuk {number}")
            return

        profile_data = get_profile(self.api_key, tokens["access_token"], tokens["id_token"])
        if not profile_data or "profile" not in profile_data:
            print(f"⚠️ Gagal mengambil profil untuk {number}")
            return

        sub_id = profile_data["profile"].get("subscriber_id", "-")
        sub_type = profile_data["profile"].get("subscription_type", "-")

        if existing:
            existing.update({
                "refresh_token": refresh_token,
                "subscriber_id": sub_id,
                "subscription_type": sub_type
            })
        else:
            self.refresh_tokens.append({
                "number": int(number),
                "subscriber_id": sub_id,
                "subscription_type": sub_type,
                "refresh_token": refresh_token
            })

        self.write_tokens_to_file()
        self.set_active_user(number)

    def remove_refresh_token(self, number: int):
        self.refresh_tokens = [rt for rt in self.refresh_tokens if rt["number"] != number]
        self.write_tokens_to_file()

        if self.active_user and self.active_user["number"] == number:
            if self.refresh_tokens:
                first = self.refresh_tokens[0]
                self.set_active_user(first["number"])
            else:
                input("⚠️ Tidak ada akun tersisa. Tekan Enter untuk lanjut...")
                self.active_user = None

    def set_active_user(self, number: int):
        rt_entry = next((rt for rt in self.refresh_tokens if rt["number"] == number), None)
        if not rt_entry:
            print(f"⚠️ Tidak ditemukan refresh token untuk {number}")
            input("Tekan Enter untuk lanjut...")
            return False

        tokens = get_new_token(self.api_key, rt_entry["refresh_token"], rt_entry.get("subscriber_id", ""))
        if not tokens:
            print(f"⚠️ Gagal mendapatkan token untuk {number}")
            input("Tekan Enter untuk lanjut...")
            return False

        profile_data = get_profile(self.api_key, tokens["access_token"], tokens["id_token"])
        if not profile_data or "profile" not in profile_data:
            print(f"⚠️ Gagal mengambil data profil untuk {number}")
            input("Tekan Enter untuk lanjut...")
            return False

        subscriber_id = profile_data["profile"].get("subscriber_id", "-")
        subscription_type = profile_data["profile"].get("subscription_type", "-")

        self.active_user = {
            "number": int(number),
            "subscriber_id": subscriber_id,
            "subscription_type": subscription_type,
            "tokens": tokens
        }

        rt_entry.update({
            "subscriber_id": subscriber_id,
            "subscription_type": subscription_type,
            "refresh_token": tokens["refresh_token"]
        })

        self.write_tokens_to_file()
        self.write_active_number()
        self.last_refresh_time = int(time.time())
        return True

    def renew_active_user_token(self):
        if not self.active_user:
            print("⚠️ Tidak ada user aktif.")
            input("Tekan Enter untuk lanjut...")
            return False

        tokens = get_new_token(self.api_key, self.active_user["tokens"]["refresh_token"], self.active_user["subscriber_id"])
        if not tokens:
            print("⚠️ Gagal memperbarui token.")
            input("Tekan Enter untuk lanjut...")
            return False

        self.active_user["tokens"] = tokens
        self.last_refresh_time = int(time.time())
        self.add_refresh_token(self.active_user["number"], tokens["refresh_token"])
        print("✅ Token berhasil diperbarui.")
        return True

    def get_active_user(self):
        if not self.active_user and self.refresh_tokens:
            self.set_active_user(self.refresh_tokens[0]["number"])

        if self.last_refresh_time is None or (int(time.time()) - self.last_refresh_time) > 300:
            self.renew_active_user_token()

        return self.active_user

    def get_active_tokens(self):
        user = self.get_active_user()
        return user["tokens"] if user else None

AuthInstance = Auth()
