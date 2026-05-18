# 个人信息速递 V1.0

安全、快捷的个人信息分享工具。"数据本地存储 + 临时中转"架构，用户的个人信息只保存在手机本地，后端不永久存储任何用户数据。

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（可选，默认可运行）
cp .env.example .env

# 3. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问 `http://localhost:8000` 即可使用。

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `FRONTEND_BASE_URL` | 前端页面访问地址，用于生成二维码中的完整 URL | `http://localhost:8000` |
| `CACHE_TTL_SECONDS` | 后端内存缓存过期时间（秒） | `300` |

## 架构

- **前端**：纯 HTML + JavaScript 单页应用，数据存储在 `localStorage`
- **后端**：Python FastAPI，使用 `cachetools.TTLCache` 内存缓存（TTL 5分钟，最大 100 条）
- **数据流**：用户勾选字段 → 前端 POST 到后端 → 后端缓存数据返回 token → 前端获取二维码图片 → 对方扫码查看
