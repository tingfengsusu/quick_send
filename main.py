import os
import secrets
from io import BytesIO

import qrcode
from cachetools import TTLCache
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:8000").rstrip("/")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

_MISSING = object()
for _var, _default, _label in [
    ("FRONTEND_BASE_URL", "http://localhost:8000", "前端地址"),
    ("CACHE_TTL_SECONDS", "300", "缓存过期秒数"),
]:
    if os.getenv(_var, _MISSING) is _MISSING:
        print(f"[WARNING] 环境变量 {_var} 未设置，使用默认值：{_default}（{_label}）")

app = FastAPI(title="个人信息速递", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = TTLCache(maxsize=100, ttl=CACHE_TTL_SECONDS)


class ShareRequest(BaseModel):
    data: dict
    expire_minutes: int = 5


class ShareResponse(BaseModel):
    token: str


FIELD_LABELS = {
    "phone": "手机号",
    "detail_address": "详细地址",
    "recipient_name": "收件人",
    "recipient_phone": "联系电话",
    "nickname": "昵称",
}


@app.post("/create_share", response_model=ShareResponse)
async def create_share(req: ShareRequest):
    token = secrets.token_urlsafe(16)
    cache[token] = req.data
    return {"token": token}


@app.get("/s/{token}", response_class=HTMLResponse)
async def view_share(token: str):
    data = cache.get(token)
    if data is None:
        return _expired_page()

    rows = []
    for key, label in FIELD_LABELS.items():
        value = data.get(key, "")
        if value and str(value).strip():
            rows.append(
                f"<tr><td class='label'>{label}</td>"
                f"<td class='value'>{value}</td></tr>"
            )

    rows_html = "\n".join(rows) if rows else (
        "<tr><td colspan='2' class='empty'>无分享内容</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>分享的个人信息</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f0f4f8;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:1rem}}
.card{{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:1.5rem 1.8rem;max-width:400px;width:100%}}
h1{{font-size:1.2rem;color:#2c3e50;margin-bottom:1.2rem;text-align:center}}
table{{width:100%;border-collapse:collapse}}
td{{padding:.7rem .4rem;border-bottom:1px solid #f0f0f0}}
td:last-child{{border-bottom:none}}
.label{{color:#888;font-size:.82rem;white-space:nowrap;width:28%}}
.value{{color:#2c3e50;font-size:.95rem;word-break:break-all}}
.empty{{text-align:center;color:#bbb;padding:1.5rem}}
.footer{{text-align:center;margin-top:1.2rem;color:#bbb;font-size:.72rem}}
</style>
</head>
<body>
<div class="card">
<h1>📋 分享的个人信息</h1>
<table>{rows_html}</table>
<div class="footer">个人信息速递 · 信息阅后即焚</div>
</div>
</body>
</html>"""


@app.get("/qrcode/{token}")
async def get_qrcode(token: str):
    url = f"{FRONTEND_BASE_URL}/s/{token}"
    img = qrcode.make(url, box_size=10, border=2)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


def _expired_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>链接已失效</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f5f5}
.card{background:#fff;padding:2rem 1.8rem;border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,.08);text-align:center;max-width:360px;width:90%}
h1{font-size:1.2rem;color:#e74c3c;margin-bottom:.8rem}
p{color:#888;font-size:.9rem}
</style>
</head>
<body>
<div class="card">
<h1>链接已失效</h1>
<p>该分享链接不存在或已过期。</p>
</div>
</body>
</html>"""


app.mount("/", StaticFiles(directory="static", html=True), name="static")
