# Deployment Information

> **Student:** Pham Van Thanh — 2A202600272
> **Service:** Production AI Agent (Day 12 Lab)

---

## Public URL

https://ai-agent-production-production-a5cc.up.railway.app

## Platform

**Railway** — build từ Dockerfile multi-stage, auto-deploy trên push `main`.

## Source

- **Repo:** https://github.com/mrbrownnn/2A202600272-PhamVanThanh-Lab12
- **Branch:** `main`
- **Entrypoint:** `app.main:app`
- **Healthcheck path:** `/health` (timeout 30s)
- **Restart policy:** `ON_FAILURE` (max 3 retries)

---

## Environment Variables set trên Railway

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `ENVIRONMENT` | `production` | Bật validate config, tắt `/docs` |
| `AGENT_API_KEY` | `<32-byte random>` | Secret, không commit |
| `JWT_SECRET` | `<32-byte random>` | Secret |
| `ALLOWED_ORIGINS` | `*` | CORS |
| `RATE_LIMIT_PER_MINUTE` | `10` | Per user/key bucket |
| `MONTHLY_BUDGET_USD` | `10.0` | Cost guard ceiling |
| `LLM_MODEL` | `gpt-4o-mini` | Metadata |
| `OPENAI_API_KEY` | `sk-proj-***` | Secret (đã set trên Railway) |
| `REDIS_URL` | *(optional)* | Có Redis plugin thì set, ko thì in-memory |
| `PORT` | *auto* | Railway tự inject |

> **Sinh secret:** `openssl rand -hex 32` (PowerShell: `[Convert]::ToHexString((1..32 | %{Get-Random -Max 256}))`)

---

## Deployment steps (Railway)

### Cách A — Auto deploy từ GitHub (đang dùng)
1. Push code lên GitHub branch `main`.
2. Railway → **New Project → Deploy from GitHub repo** → chọn repo.
3. Railway tự phát hiện `Dockerfile` và build.
4. **Settings → Variables**: thêm các biến ở bảng trên.
5. **Settings → Networking → Generate Domain** để lấy public URL.
6. Mỗi lần `git push origin main` → Railway auto rebuild + deploy.

### Cách B — Railway CLI
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set ENVIRONMENT=production \
                     AGENT_API_KEY=<secret> \
                     JWT_SECRET=<secret> \
                     RATE_LIMIT_PER_MINUTE=10 \
                     MONTHLY_BUDGET_USD=10.0
railway up
railway domain
```

---

## Test commands

```bash
# Windows PowerShell
$URL = "https://ai-agent-production-production-a5cc.up.railway.app"
$KEY = "<AGENT_API_KEY>"

# Bash / macOS / Linux
export URL="https://ai-agent-production-production-a5cc.up.railway.app"
export KEY="<AGENT_API_KEY>"
```

### 1. Health check
```bash
curl $URL/health
# → 200 {"status":"ok","uptime_seconds":...,"checks":{"llm":"mock"}}
```

### 2. Readiness probe
```bash
curl $URL/ready
# → 200 {"ready":true}
```

### 3. Auth required (no key → 401)
```bash
curl -X POST $URL/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# → 401 {"detail":"Invalid or missing API key. ..."}
```

### 4. Valid key → 200
```bash
curl -X POST $URL/ask \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello deployment"}'
# → 200 {"user_id":"test","answer":"...","model":"gpt-4o-mini",...}
```

### 5. Rate limit (request 11+ → 429)
```bash
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "req $i → %{http_code}\n" \
    -X POST $URL/ask -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    -d '{"user_id":"rl","question":"spam"}'
done
# → 10× 200, sau đó 429 với header Retry-After: 60
```

---

## Actual test results

Kết quả test public ngày 2026-04-17:

### `/health`
```json
{"status":"ok","version":"1.0.0","environment":"production","uptime_seconds":1029.6,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-04-17T11:30:31.638887+00:00"}
```

### `/ready`
```json
{"ready":true}
```

### `/ask` thiếu key (401)
```
STATUS=401
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### `/ask` có key (200)
```json
STATUS=200
{"user_id":"test-submit","question":"Hello deployment","answer":"Day la cau tra loi tu AI agent (mock). Trong production, day se la response tu OpenAI/Anthropic.","model":"gpt-4o-mini","timestamp":"2026-04-17T11:45:00.000000+00:00"}
```

### Rate limit burst (429)
```
req 1 -> 200
req 2 -> 200
req 3 -> 200
req 4 -> 200
req 5 -> 200
req 6 -> 200
req 7 -> 200
req 8 -> 200
req 9 -> 200
req 10 -> 200
req 11 -> 429
req 12 -> 429
req 13 -> 429
req 14 -> 429
req 15 -> 429
```

---

## Screenshots

Lưu trong `screenshots/`:

- `screenshots/dashboard.png` — Railway dashboard (build thành công, container running)
- `screenshots/running.png` — service log (`{"event":"ready"}`)
- `screenshots/test.png` — kết quả curl test (health + ask + rate limit 429)

---

## Notes

- **Không commit `.env` hoặc API key thật** — đã thêm `.gitignore`.
- Nếu build fail, xem Railway **Deployments → Build Logs**; chạy lỗi xem **Deploy Logs**.
- Đổi sang Render: chỉ cần `render.yaml` có sẵn + set secret env; test commands giữ nguyên, thay URL.

## Final submission

- **Repository:** https://github.com/mrbrownnn/2A202600272-PhamVanThanh-Lab12
- **Deployed URL:** xem mục *Public URL* phía trên
