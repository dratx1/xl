import time
from datetime import datetime
from app.service.auth import AuthInstance
from app.client.engsel import get_balance, get_quota, get_profile
from app.client.engsel2 import get_tiering_info, segments

_cached = None
_last_fetch = 0

def get_user_context(force=False):
    global _cached, _last_fetch
    now = time.time()
    if not force and _cached and now - _last_fetch < 60:
        return _cached

    user = AuthInstance.get_active_user()
    if not user:
        return None

    api_key = AuthInstance.api_key
    tokens = user["tokens"]
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    balance = get_balance(api_key, id_token)
    quota = get_quota(api_key, id_token) or {}
    profile = get_profile(api_key, access_token, id_token)

    tiering = {}
    if profile["profile"].get("subscription_type") == "PREPAID":
        tiering = get_tiering_info(api_key, tokens)

    _cached = {
        "api_key": api_key,
        "tokens": tokens,
        "number": user["number"],
        "subscriber_id": profile["profile"].get("subscriber_id", "-"),
        "subscription_type": profile["profile"].get("subscription_type", "-"),
        "balance": balance.get("remaining", 0),
        "balance_expired_at": balance.get("expired_at", 0),
        "quota": quota,
        "tier": tiering.get("tier", 0),
        "points": tiering.get("current_point", 0),
        "segments": segments(api_key, id_token, access_token, balance.get("remaining", 0)) or {}
    }
    _last_fetch = now
    return _cached
