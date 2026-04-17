# Day 12 Lab — Mission Answers

> **Student:** Pham Van Thanh &nbsp;|&nbsp; **ID:** 2A202600272 &nbsp;|&nbsp; **Date:** 17/04/2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in `develop/app.py`

1. **Hardcoded secrets** — `OPENAI_API_KEY` và `DATABASE_URL` viết thẳng trong source; lộ khi push Git, không rotate được.
2. **No config management** — `DEBUG`, `MAX_TOKENS` là hằng số ngay trong code, muốn đổi phải rebuild.
3. **`print()` thay logging** — không có level, không structured, còn in cả secret ra stdout.
4. **Không có health/readiness endpoint** — platform không biết khi nào restart container.
5. **Port cứng `8000`** — Railway/Render inject `$PORT` động, app cứng port sẽ không bind được.
6. **`host="localhost"`** — chỉ listen loopback, container ngoài không truy cập được.
7. **`reload=True` trong production** — watcher tiêu tốn CPU, restart bất thường khi file touch.
8. **Không authentication** — endpoint `/ask` mở, ai cũng gọi được, gây lạm dụng chi phí LLM.
9. **Không rate limit / cost guard** — một user spam có thể đốt hết ngân sách.
10. **Chạy container as root** — tăng bề mặt tấn công nếu chiếm được process.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why important? |
|---|---|---|---|
| Config | Hardcoded / default values | Env vars (12-factor) | Portable, rotate được, cùng image chạy nhiều env |
| Secrets | Trong source | Secret manager / platform vars | Giảm rủi ro lộ khóa qua Git history |
| Logging | `print()` | JSON structured logging | Log aggregator parse được, filter theo field |
| Auth | Mở | API key / JWT | Chống lạm dụng, tính tiền đúng user |
| Rate limit | Không | Redis-backed sliding window | Bảo vệ backend, giữ SLA |
| Cost guard | Không | Monthly budget check | Tránh "bill shock" |
| State | In-memory | Stateless + Redis | Horizontal scale an toàn |
| Health | Không | `/health` + `/ready` probes | Orchestrator auto-restart, route traffic đúng lúc |
| Shutdown | Kill -9 | SIGTERM graceful | Không mất request đang xử lý |
| User | root | non-root (`agent`) | Tối thiểu hóa thiệt hại khi bị RCE |
| Network | `localhost` + port cứng | `0.0.0.0` + `$PORT` | Hoạt động trong container/cloud |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions (trả lời cho `Dockerfile` của bài nộp)

1. **Base image:** `python:3.11-slim` cho cả builder và runtime — nhỏ (~130 MB), có pip, tránh full `python:3.11` (~900 MB).
2. **Working directory:** `/build` ở stage builder (tạo venv), `/app` ở stage runtime (chứa code + ownership cho user `agent`).
3. **Multi-stage:** có. `builder` compile/cài deps vào `/opt/venv`, `runtime` chỉ copy venv + `app/` → image gọn, không kèm `gcc`, header files.
4. **Runtime user:** non-root, `agent` (uid hệ thống), home `/app`, shell `/sbin/nologin`.
5. **Health check:** có. `HEALTHCHECK` gọi `http://127.0.0.1:$PORT/health` mỗi 30s, timeout 10s, 3 retries.
6. **Secrets handling:** không có secret trong image — tất cả qua env vars (`AGENT_API_KEY`, `JWT_SECRET`, `OPENAI_API_KEY`).
7. **Layer order:** copy `requirements.txt` + `pip install` trước, copy `app/` sau → đổi code không invalidate layer deps.

### Exercise 2.3: Image size comparison

| Build | Approx. size | Notes |
|---|---|---|
| Develop (single-stage `python:3.11` + dev tools) | ~950 MB | Full Python, gcc, build tools giữ lại |
| Production (multi-stage `python:3.11-slim`, submission Dockerfile) | ~230 MB | Chỉ venv + app, không có toolchain |
| Difference | ~75% nhỏ hơn | Pull nhanh hơn, cold start thấp hơn, bề mặt tấn công ít hơn |

> Đo thực tế bằng `docker images | grep agent` sau khi build. Số trên là ước tính dựa trên `python:3.11-slim` base (~130 MB) + deps của `requirements.txt`.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- **Platform:** Railway
- **Config file:** `railway.toml` (ở root submission)
- **Build:** Dockerfile multi-stage (tự động detect)
- **Healthcheck path:** `/health`, timeout 30s
- **Restart policy:** `ON_FAILURE`, max 3 retries

**Environment variables đã set trên Railway:**
```
ENVIRONMENT=production
AGENT_API_KEY=<32-byte random>
JWT_SECRET=<32-byte random>
ALLOWED_ORIGINS=*
RATE_LIMIT_PER_MINUTE=10
MONTHLY_BUDGET_USD=10.0
LLM_MODEL=gpt-4o-mini
```
> `OPENAI_API_KEY` để trống → fallback `mock_llm` cho demo. `REDIS_URL` optional (nếu có Redis plugin thì mới set).

- **Public URL:** xem `DEPLOYMENT.md`
- **Screenshots:** `screenshots/` (dashboard, running, test)

---

## Part 4: API Security

### Exercise 4.1 — Missing API key → 401
```bash
$ curl -X POST $URL/ask -H "Content-Type: application/json" \
       -d '{"user_id":"t","question":"hi"}'
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```
Status: **401 Unauthorized** — xem `app/auth.py::verify_api_key` (raise `HTTPException(401)` nếu header thiếu hoặc sai).

### Exercise 4.2 — Valid API key → 200
```bash
$ curl -X POST $URL/ask -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
       -d '{"user_id":"t","question":"Hello"}'
{"user_id":"t","question":"Hello","answer":"...","model":"gpt-4o-mini","timestamp":"..."}
```
Status: **200 OK**.

### Exercise 4.3 — Rate limit 10/min → 429
```bash
$ for i in $(seq 1 15); do curl -s -o /dev/null -w "%{http_code}\n" \
      -X POST $URL/ask -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
      -d '{"user_id":"t","question":"spam"}'; done
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```
Từ request thứ 11 trong cùng phút trả **429 Too Many Requests** với header `Retry-After: 60`.

### Exercise 4.4 — Cost guard implementation

- **File:** `app/cost_guard.py`
- **Ý tưởng:** ước tính chi phí mỗi call bằng token count × đơn giá (input `$0.00015/1K`, output `$0.00060/1K`), cộng dồn theo key `budget:YYYY-MM`.
- **Storage:** Redis (`INCRBYFLOAT` atomic, chia sẻ giữa nhiều instance). Fallback in-memory nếu không có Redis — vẫn đúng với 1 instance, warn nếu scale out.
- **Hành vi khi hết budget:** raise `HTTPException(503, "Monthly budget exhausted.")` — chặn request, KHÔNG gọi LLM.
- **Reset:** dùng key theo tháng (`time.strftime("%Y-%m")`) nên tự động reset đầu mỗi tháng.

---

## Part 5: Scaling & Reliability

### Exercise 5.1 — Stateless design
- App không giữ state cục bộ ngoài counter metrics. Rate limit và cost guard dùng Redis làm source of truth → chạy N replica đồng thời vẫn chính xác.
- File: `app/rate_limiter.py` (sliding window qua `INCR` + `EXPIRE`), `app/cost_guard.py` (`INCRBYFLOAT` theo tháng).

### Exercise 5.2 — Liveness probe `/health`
- Luôn trả 200 nếu process chạy. Kubernetes/Railway dùng để quyết định restart container.
- Body bao gồm `uptime_seconds`, `total_requests`, `checks` (mock vs openai) để debug nhanh.

### Exercise 5.3 — Readiness probe `/ready`
- Trả 503 trước khi `lifespan` set `_is_ready = True`. Load balancer thấy 503 thì KHÔNG route traffic tới pod đang warm-up.
- Tách liveness/readiness tránh restart loop khi pod chỉ đang khởi động.

### Exercise 5.4 — Graceful shutdown
- `signal.signal(SIGTERM, _handle_signal)` log lại signal.
- Uvicorn chạy với `timeout_graceful_shutdown=30` → cho request đang xử lý 30s hoàn tất trước khi kill.
- `lifespan` context set `_is_ready = False` khi shutdown → `/ready` trả 503 ngay → platform ngừng route traffic mới.

### Exercise 5.5 — Docker Compose full stack
- File: `docker-compose.yml`. Dịch vụ `app` depends_on `redis`, cả hai có healthcheck, app chỉ start khi redis healthy → không có race condition.

---

## Evidence pointers (tất cả đều ở cùng thư mục này)

| Nội dung | Đường dẫn |
|---|---|
| Entrypoint | `app/main.py` |
| Config 12-factor | `app/config.py` |
| API key auth | `app/auth.py` |
| Rate limiter (Redis) | `app/rate_limiter.py` |
| Cost guard (Redis) | `app/cost_guard.py` |
| Mock LLM | `app/mock_llm.py` |
| Dockerfile multi-stage | `Dockerfile` |
| Compose | `docker-compose.yml` |
| Railway config | `railway.toml` |
| Render config | `render.yaml` |
| Env template | `.env.example` |
| Deployment info | `DEPLOYMENT.md` |
