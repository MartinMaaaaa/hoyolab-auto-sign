# 流程规划 — HoYoLAB 自动签到（GitHub Actions 版）

> 文档版本：v1.0（2026-10-09）
> 配套文档：[DESIGN.md](DESIGN.md)（设计目的）、[CODE_STANDARDS.md](CODE_STANDARDS.md)（代码规范）

## 1. 总体架构与数据流

```
GitHub Actions 触发（cron UTC 02:00 / 手动 dispatch）
        │  注入 Secrets & Vars 为环境变量
        ▼
┌──────────────────┐
│ config.py        │  解析 env → 冻结 Config 对象（多账号、游戏开关、通知、重试参数）
└────────┬─────────┘
         ▼
┌──────────────────┐   对每个账号 × 每个启用游戏：
│ runner.py 编排    │ ──► GET  {sign_base}/info   → is_sign? total_sign_day?
│ （重试/退避在此） │ ──► 未签 → POST {sign_base}/sign
└────────┬─────────┘        │
         │                  ▼
         │           ┌─────────────┐
         │           │ api.py      │ ──► HoYoLAB 国际 API（sg-hk4e-api / sg-public-api）
         │           │ 分类响应状态 │
         │           └─────────────┘
         ▼
┌──────────────────┐
│ 汇总 CheckinResult│  SUCCESS / ALREADY_SIGNED / CAPTCHA_RISK / INVALID_COOKIE / API_ERR / NET_ERR
└────────┬─────────┘
         ▼
┌──────────────────┐   PUSH_LEVEL 过滤（手动触发视为 all）
│ notify.py 推送    │ ──► Telegram Bot API / PushPlus
└────────┬─────────┘
         ▼
  exit code：全部 ∈ {SUCCESS, ALREADY_SIGNED} → 0；否则 → 1
```

## 2. API 明细（HoYoLAB 国际服）

### 2.1 游戏注册表（实现为 `games.py` 中的纯数据表）

| 游戏 | key | 签到端点（POST） | act_id | 附加 header |
|---|---|---|---|---|
| 原神 | `genshin` | `https://sg-hk4e-api.hoyolab.com/event/sol/sign?lang=en-us&act_id={act_id}` | `e202102251931481` | — |
| 星穹铁道 | `star_rail` | `https://sg-public-api.hoyolab.com/event/luna/os/sign?lang=en-us&act_id={act_id}` | `e202303301540311` | — |
| 绝区零 | `zzz` | `https://sg-public-api.hoyolab.com/event/luna/zzz/os/sign?lang=en-us&act_id={act_id}` | `e202406031448091` | `x-rpc-signgame: zzz` |

预留（v1 不启用，注释留位）：崩坏3 `…/event/mani/sign`，act_id `e202110291205111`；未定事件簿 `…/event/luna/os/sign`，act_id `e202308141137581`。

### 2.2 info 端点（GET）

把对应游戏 sign 端点路径中的 `/sign` 替换为 `/info`，查询参数相同（`lang=en-us&act_id={act_id}`）。

响应字段（`data` 内）：
- `is_sign: bool` — 今日是否已签到
- `total_sign_day: int` — 本月累计签到天数

用途：签到前预检。已签到则跳过 sign 请求（减少无效请求、降低风控触发面），并把累计天数写进通知报告。

### 2.3 公共请求头（sign 与 info 通用）

```
Accept:             application/json, text/plain, */*
Origin:             https://act.hoyolab.com/
Referer:            https://act.hoyolab.com/
User-Agent:         {HOYOLAB_USER_AGENT，默认 Chrome/114 桌面 UA}
x-rpc-app_version:  {HOYOLAB_APP_VERSION，默认 2.34.1}
x-rpc-client_type:  4
Cookie:             {用户 cookie 原样整串}
```

- 绝区零追加：`x-rpc-signgame: zzz`。
- sign 为 POST，请求体为空（act_id 已在查询串中；参考项目 1 此形态验证可用）。若实现期实测被拒，降级方案：带 `Content-Type: application/json;charset=UTF-8` 与 JSON 体 `{"act_id": "..."}`——该降级只允许在 `api.py` 一处实现。
- 若实测返回设备校验类错误（如 retcode -3448 等），降级方案：补充 `x-rpc-device_id` / `x-rpc-device_name` 头（随机 UUID / 固定字符串），同样只动 `api.py`。

### 2.4 响应分类状态机（核心，单测全覆盖）

```
HTTP/网络层
 ├─ requests 异常 / 超时 ──────────────► NET_ERR ──重试──► 仍失败 → 最终 NET_ERR
 └─ HTTP 200
      └─ JSON retcode
           ├─ retcode == 0 且 data.gt_result.is_risk 为真 ─► CAPTCHA_RISK（不重试）
           ├─ retcode == 0                                 ─► SUCCESS
           ├─ retcode == -5003                             ─► ALREADY_SIGNED（不重试）
           ├─ message 含 login/cookie 失效特征             ─► INVALID_COOKIE（不重试）
           └─ 其他非 0 retcode / HTTP 5xx / 429            ─► API_ERR（可重试）

info 预检
 └─ data.is_sign == true ────────────────► ALREADY_SIGNED（直接跳过 sign 调用）
```

> retcode 具体数值以实现期实测为准（当前依据参考项目与社区共识）；分类逻辑集中在 `api.py::classify_response()` 一处，调整不需要动流程。

## 3. 执行时序（防风控节奏）

单账号三游戏：

```
GET genshin/info → 未签 → sleep rand(3~8)s → POST genshin/sign
GET star_rail/info → 未签 → sleep rand(3~8)s → POST star_rail/sign
GET zzz/info → 未签 → sleep rand(3~8)s → POST zzz/sign
```

- 游戏间随机 3–8 秒；多账号之间随机 5–15 秒。
- 所有随机 sleep 一律 `random.uniform`，禁止固定间隔（降低风控特征）。

## 4. 重试策略

| 参数 | 默认值 | 说明 |
|---|---|---|
| `CHECKIN_MAX_ATTEMPTS` | 3 | 单游戏 sign 请求的最大总尝试次数 |
| `CHECKIN_RETRY_DELAY_SECONDS` | 60 | 重试间隔 |

- **重试**：NET_ERR、HTTP 5xx、HTTP 429、API_ERR。
- **不重试**：CAPTCHA_RISK、INVALID_COOKIE、ALREADY_SIGNED（重试无意义或有害）。
- workflow 签到步骤 `timeout-minutes: 8`，重试参数默认值必须在其内完成（3 游戏 × 3 次 × 60s 上界 ≈ 9 分钟极端情况，超出由 timeout 兜底中断，视为失败并按通知策略推送）。

## 5. GitHub Actions 编排

### 5.1 `.github/workflows/checkin.yml`

```yaml
name: HoYoLAB Checkin
on:
  schedule:
    - cron: '0 2 * * *'        # UTC 02:00 = 北京 10:00
  workflow_dispatch:
concurrency:
  group: hoyolab-checkin
  cancel-in-progress: false
permissions:
  contents: read
jobs:
  checkin:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v6          # 若 v6 不可用降级 v4
      - uses: actions/setup-python@v6      # 同上
        with: { python-version: '3.11', cache: 'pip' }
      - run: python -m pip install -r requirements.txt
      - run: python -m unittest discover -s tests -v   # 测试失败 → 阻断签到
      - name: Run Checkin
        run: python checkin.py
        timeout-minutes: 8
        env:
          HOYOLAB_COOKIES: ${{ secrets.HOYOLAB_COOKIES }}
          HOYOLAB_GAMES: ${{ vars.HOYOLAB_GAMES }}                 # 可选，空则用代码默认
          HOYOLAB_APP_VERSION: ${{ vars.HOYOLAB_APP_VERSION }}     # 可选
          HOYOLAB_USER_AGENT: ${{ vars.HOYOLAB_USER_AGENT }}       # 可选
          PUSHPLUS_TOKEN: ${{ secrets.PUSHPLUS_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          PUSH_LEVEL: ${{ github.event_name == 'workflow_dispatch' && 'all' || vars.PUSH_LEVEL || 'fail_only' }}
          CHECKIN_MAX_ATTEMPTS: '3'
          CHECKIN_RETRY_DELAY_SECONDS: '60'
```

要点：`PUSH_LEVEL` 表达式保证**手动触发必推送全量报告**，定时任务默认只在失败时推送。

### 5.2 `.github/workflows/keep-alive.yml`

- cron `23 3 1 * *`（每月 1 号 UTC 03:23）+ `workflow_dispatch`。
- 步骤：写时间戳到 `.github/last-active.txt` → 以 `github-actions[bot]` 身份提交并推送。
- 目的：GitHub 会在公开仓库连续 60 天无活动后停用 schedule 触发器，每月一次自动提交保持活跃。

## 6. 环境变量总表

| 变量 | 必填 | 来源 | 默认值 | 说明 |
|---|---|---|---|---|
| `HOYOLAB_COOKIES` | ✅ | Secrets | — | 多账号换行分隔；每行一个账号的 cookie 整串，至少包含 `ltoken_v2` 与 `ltuid_v2` |
| `HOYOLAB_GAMES` | ❌ | Vars | `genshin,star_rail,zzz` | 逗号分隔的启用游戏 key |
| `PUSHPLUS_TOKEN` | ❌ | Secrets | — | PushPlus 推送 token |
| `TELEGRAM_BOT_TOKEN` | ❌ | Secrets | — | Telegram Bot token |
| `TELEGRAM_CHAT_ID` | ❌ | Secrets | — | Telegram 接收人/群 ID |
| `PUSH_LEVEL` | ❌ | Vars | `fail_only` | `all` / `fail_only`；手动 dispatch 强制 `all` |
| `CHECKIN_MAX_ATTEMPTS` | ❌ | — | `3` | 重试次数 |
| `CHECKIN_RETRY_DELAY_SECONDS` | ❌ | — | `60` | 重试间隔（秒） |
| `HOYOLAB_APP_VERSION` | ❌ | Vars | `2.34.1` | 覆盖 `x-rpc-app_version` |
| `HOYOLAB_USER_AGENT` | ❌ | Vars | Chrome/114 UA | 覆盖 User-Agent |

## 7. 通知报告格式（notify.py 产出）

```
🎮 HoYoLAB 签到报告 2026-10-09 (UTC)
账号 1（ltuid 26***20）
  ✅ 原神：签到成功（本月第 8 天）
  ⏭️ 星穹铁道：今日已签（本月第 8 天）
  ⚠️ 绝区零：触发风控验证码，需人工处理
统计：成功 1 / 已签 1 / 失败 1 —— 共 3 项
```

- `fail_only`：任一项 ∉ {SUCCESS, ALREADY_SIGNED} 才发送。
- 两通道都配置时都发送（内容一致）；单通道失败不影响退出码，仅记 WARNING。

## 8. 退出码约定

| 退出码 | 条件 |
|---|---|
| 0 | 所有账号 × 游戏结果 ∈ {SUCCESS, ALREADY_SIGNED} |
| 1 | 任一结果 ∈ {CAPTCHA_RISK, INVALID_COOKIE, API_ERR, NET_ERR}，或配置解析失败 |

## 9. Cookie 获取指引（写入 README，供使用者参考）

1. 浏览器登录 `https://www.hoyolab.com`；
2. F12 → Network → 任选一个 `hoyolab.com` 请求 → Request Headers → 复制整串 `Cookie` 值；
3. （等价方式）F12 → Application → Cookies → `hoyolab.com`，至少取 `ltoken_v2`、`ltuid_v2`；
4. 存入 GitHub Secret `HOYOLAB_COOKIES`；多账号一行一个。

> 注意：HoYoLAB 自 2023-07 起 cookie 改为 HttpOnly，无法用控制台脚本（`getToken.js` 时代的方法）自动读取，必须手动复制（参考项目 1 的 README 明确说明）。
