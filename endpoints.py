# ─────────────────────────────────────────────────────────────
#  endpoints.py — All OTP endpoint configurations
# ─────────────────────────────────────────────────────────────

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _json_headers(extra: dict | None = None) -> dict:
    """Common JSON headers merged with extras."""
    base = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": UA,
    }
    if extra:
        base.update(extra)
    return base


# ── Each endpoint is a dict ──────────────────────────────────
#   name      — display name with emoji
#   method    — HTTP method
#   url       — target URL ({phone} placeholder for path-param)
#   headers   — request headers dict
#   body      — callable(phone) → dict/str or None for GET
#   form      — True if body should be sent as form-data
#   cooldown  — approx cooldown in seconds

ENDPOINTS: list[dict] = [
    # 1 ── Meesho ──────────────────────────────────────────────
    {
        "name": "🛍️ Meesho",
        "method": "POST",
        "url": "https://www.meesho.com/api/v1/user/login/request-otp",
        "headers": _json_headers({
            "meesho-iso-country-code": "IN",
            "Referer": "https://www.meesho.com/auth",
        }),
        "body": lambda phone: {"phone_number": phone},
        "form": False,
        "cooldown": 60,
    },

    # 2 ── Ram Fincorp ─────────────────────────────────────────
    {
        "name": "🏦 Ram Fincorp",
        "method": "POST",
        "url": "https://loans-api.ramfincorp.com/customers/customer-login-byMobile",
        "headers": _json_headers({
            "Referer": "https://loans.ramfincorp.com/",
        }),
        "body": lambda phone: {"mobile": phone},
        "form": False,
        "cooldown": 60,
    },

    # 3 ── Maruti Suzuki ───────────────────────────────────────
    {
        "name": "🚗 Maruti Suzuki",
        "method": "POST",
        "url": "https://www.marutisuzuki.com/app-service/api/v1/authenticate/send/otp",
        "headers": _json_headers({
            "Referer": "https://www.marutisuzuki.com/subscribe/myaccount",
        }),
        "body": lambda phone: {"mobile": phone},
        "form": False,
        "cooldown": 120,
    },

    # 4 ── NoBroker ────────────────────────────────────────────
    {
        "name": "🏠 NoBroker",
        "method": "POST",
        "url": "https://www.nobroker.in/api/v3/account/otp/send",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Referer": "https://www.nobroker.in/",
            "User-Agent": UA,
        },
        "body": lambda phone: {"phone": phone, "countryCode": "IN"},
        "form": True,
        "cooldown": 60,
    },

    # 5 ── District.in (Zomato Entertainment) ──────────────────
    {
        "name": "🎫 District.in",
        "method": "POST",
        "url": "https://www.district.in/gw/auth/generate_otp",
        "headers": _json_headers({
            "Accept": "*/*",
            "Referer": "https://www.district.in/",
            "x-client-id": "district-web",
            "x-app-type": "ed_web",
            "x-app-version": "11.11.1",
            "x-device-id": "41e28432-a302-4f00-aaf8-d65aa5b54650",
            "x-guest-token": "1212",
        }),
        "body": lambda phone: {"phone_number": phone, "country_code": "91"},
        "form": False,
        "cooldown": 30,
    },

    # 6 ── Delhivery ───────────────────────────────────────────
    {
        "name": "📦 Delhivery",
        "method": "GET",
        "url": "https://dlv-api.delhivery.com/v4/otp/generate/{phone}",
        "headers": {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.delhivery.com/",
            "User-Agent": UA,
        },
        "body": None,
        "form": False,
        "cooldown": 60,
    },

    # 7 ── BookMyShow ──────────────────────────────────────────
    {
        "name": "🎬 BookMyShow",
        "method": "POST",
        "url": "https://in.bookmyshow.com/api/members/otp/send",
        "headers": _json_headers({
            "x-app-code": "WEB",
            "x-platform-code": "WEB",
            "x-platform": "WEB",
            "x-region-code": "AHD",
            "x-region-slug": "ahmedabad",
            "x-bms-id": "1.431100687.1792332113263",
            "Referer": "https://in.bookmyshow.com/explore/home/ahmedabad",
        }),
        "body": lambda phone: {
            "channel": "phone",
            "subChannel": "sms",
            "details": {
                "phone": phone,
                "origin": "https://in.bookmyshow.com",
                "isdCountryCode": "IN",
                "isdCode": "+91",
            },
        },
        "form": False,
        "cooldown": 30,
    },

    # 8 ── Blinkit ─────────────────────────────────────────────
    {
        "name": "⚡ Blinkit",
        "method": "POST",
        "url": "https://blinkit.com/v2/accounts/",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "app_client": "consumer_web",
            "platform": "desktop_web",
            "auth_key": "c761ec3633c22afad934fb17a66385c1c06c5472b4898b866b7306186d0bb477",
            "device_id": "70e580386aa8f63c",
            "session_uuid": "13ca2164-feef-47b4-8826-e37a22f78eff",
            "lat": "28.4465616",
            "lon": "77.040489",
            "web_app_version": "1008010016",
            "app_version": "52434332",
            "Referer": "https://blinkit.com/",
            "User-Agent": UA,
        },
        "body": lambda phone: {"user_phone": phone},
        "form": True,
        "cooldown": 60,
    },

    # 9 ── Jio ─────────────────────────────────────────────────
    {
        "name": "📱 Jio",
        "method": "POST",
        "url": "https://www.jio.com/api/jio-login-service/login/sendOtp",
        "headers": _json_headers({
            "Referer": "https://www.jio.com/selfcare/login/",
        }),
        "body": lambda phone: {
            "mobileNumber": phone,
            "loginFlowType": "MOBILE",
            "alternateNumber": "",
        },
        "form": False,
        "cooldown": 60,
    },
]
