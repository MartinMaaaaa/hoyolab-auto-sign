# HoYoLAB 国际服每日自动签到（GitHub Actions 版）

基于 GitHub Actions 的 HoYoLAB（国际服）全自动签到助手。支持多账号、防风控随机等待、网络失败自动重试、Telegram 与 PushPlus 消息推送，且自带防 60 天闲置停用保活机制。

---

## 🎮 支持游戏

| 游戏 | Key | 默认状态 | 签到奖励 |
|---|---|---|---|
| **原神** (Genshin Impact) | `genshin` | 启用 | 原石、经验书、摩拉等 |
| **崩坏：星穹铁道** (Honkai: Star Rail) | `star_rail` | 启用 | 星琼、信用点、材料等 |
| **绝区零** (Zenless Zone Zero) | `zzz` | 启用 | 菲林、丁尼、调查员经验等 |

> 如需指定运行游戏，可通过 Repository Variables 配置 `HOYOLAB_GAMES`（例如：`genshin,star_rail`）。

---

## 🔑 Cookie 获取步骤

由于 HoYoLAB 国际服已启用 `HttpOnly` Cookie 策略，控制台自动脚本无法读取，需手动通过浏览器开发者工具复制：

1. 浏览器打开 [HoYoLAB 官网](https://www.hoyolab.com/) 并登录您的账号；
2. 按 `F12` 打开开发者工具（DevTools），切换到 **Network（网络）** 标签页；
3. 刷新页面，在请求列表中随意点击一个属于 `hoyolab.com` 的请求（如 `getGameRecord` 或首页请求）；
4. 在右侧 **Request Headers（请求标头）** 中找到 `Cookie` 项，复制其完整的整串值；
5. **格式说明**：整串 Cookie 中至少必须包含 `ltoken_v2` 与 `ltuid_v2`（或 `ltoken` 与 `ltuid`）。
   示例占位符格式如下：
   ```text
   ltoken_v2=v2_XXXX…XXXX; ltuid_v2=26XXXXX20; account_id_v2=26XXXXX20;
   ```

> ⚠️ **多账号说明**：如果有多个账号，每个账号的 Cookie 占据单独一行，多行传入即可。

---

## 🚀 部署指引

### 1. Fork 本仓库
点击本页面右上角 **Fork** 按钮，将本仓库复制到您的个人 GitHub 账号下。

### 2. 配置 Repository Secrets
进入您 Fork 的仓库，依次点击 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`，添加以下机密项：

| Secret 变量名 | 是否必填 | 说明 |
|---|---|---|
| `HOYOLAB_COOKIES` | **必填** | 您的 HoYoLAB 国际服 Cookie（多账号一行一个） |
| `PUSHPLUS_TOKEN` | 可选 | [PushPlus](https://www.pushplus.plus/) 微信推送 Token |
| `TELEGRAM_BOT_TOKEN` | 可选 | Telegram Bot Token（格式形如 `bot123456:ABC-DEF...`） |
| `TELEGRAM_CHAT_ID` | 可选 | Telegram 接收消息的用户或群组 ID |

### 3. 配置 Repository Variables（可选）
在同一页面的 `Variables` 标签页下，可根据需要配置以下参数：

| Variable 变量名 | 默认值 | 说明 |
|---|---|---|
| `HOYOLAB_GAMES` | `genshin,star_rail,zzz` | 启用的游戏列表（逗号分隔） |
| `PUSH_LEVEL` | `fail_only` | 推送策略：`fail_only`（仅失败/风控时推送）或 `all`（每次必推） |
| `HOYOLAB_APP_VERSION` | `2.34.1` | 自定义客户端版本号（遇接口版本更新时覆盖） |
| `HOYOLAB_USER_AGENT` | 默认 Chrome UA | 自定义请求头 User-Agent |

### 4. 首次运行验证
1. 在仓库页面点击 **Actions** 标签；
2. 在左侧选择 **HoYoLAB Checkin** 工作流；
3. 点击右侧 **Run workflow** 按钮进行手动触发；
4. 手动触发时系统会强制开启全量推送（`PUSH_LEVEL=all`），请观察运行日志与微信/Telegram 推送通知，确认签到成功。

---

## ⏰ 定时与保活机制

- **定时签到**：每天 UTC 时间 02:00（北京时间 10:00）自动运行。该时间点避开了米哈游每日 04:00 的服务器刷新高峰与 GitHub Actions 整点拥堵。
- **自动防休眠（Keep-alive）**：GitHub 会在公开仓库连续 60 天无活动后停用定时调度。本仓库内置 `.github/workflows/keep-alive.yml`，每月 1 号自动提交一次轻量时间戳以持续保持 Actions 处于活跃状态。

---

## ❓ 常见问题排查（FAQ）

1. **触发风控验证码（CAPTCHA_RISK）怎么办？**
   - HoYoLAB 偶发会对异地登录触发滑块验证码。本脚本遵循安全合规原则，**不会暴力破解验证码**，而是立即标记异常并通过通知提醒您。
   - 解决方法：用电脑或手机浏览器打开 HoYoLAB 签到页面手动完成一次签到，通常次日即可恢复自动签到。
2. **提示 Cookie 失效（INVALID_COOKIE）？**
   - 国际服 Cookie 通常有数月有效期，但修改密码或主动登出会导致失效。重新按上述步骤抓取最新 Cookie 并更新 GitHub Secrets 即可。
3. **版本号过期？**
   - 若米哈游未来更新了接口版本校验，您只需在 GitHub 仓库中增加环境变量 `HOYOLAB_APP_VERSION` 填入最新版本号，**无需改动任何代码**。

---

## 📄 免责声明

1. 本项目仅供个人学习、研究 Python 网络编程及自动化工具使用。
2. 请勿滥用本工具向服务器发起高频或恶意请求。
3. 开发者不对因使用本工具导致的任何账号异常、风控限制承担责任。
