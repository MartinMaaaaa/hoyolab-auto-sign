# 🌟 HoYoLAB Auto Check-in Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-33%20Passed-brightgreen?style=flat-square)](#-工程化保障)
[![Platform](https://img.shields.io/badge/Cost-Zero%20Server-orange?style=flat-square)](#-核心特性)

轻量、工程化且安全的 HoYoLAB（国际服）每日签到自动化引擎。基于 GitHub Actions 无服务器架构构建，永久零服务器成本，支持原神、崩坏：星穹铁道、绝区零三端联动，具备完善的防风控调度机制与双通道结果推送。

---

## ✨ 核心特性

- **☁️ 0 成本无服务器架构**：基于 GitHub Actions 原生调度，无需自建服务器、不耗费个人电脑电量与内存，每月 Actions 免费额度占用仅约 1%。
- **🛡️ 仿生防风控调度**：
  - **动态随机抖动（Jitter Delay）**：各游戏请求与多账号切换间插入 3~15 秒随机时间间隔，规避机械化高频访问特征；
  - **人机验证优雅降级**：遭遇极端图形滑块验证时，立即终止重试避免封控，并通过推送通知用户手动签到解封；
  - **日志安全脱敏**：控制台输出及推送报告对用户 Cookie、Token、UID 进行哈希掩码处理，无泄露隐患。
- **🔄 网络容错与自愈**：内置可配置的指数退避重试循环（默认 3 次尝试），网络波动时自动重试，接口报错自动识别。
- **🔋 永久生命周期保活**：自带专属保活工作流（`keep-alive.yml`），自动破解 GitHub 仓库 60 天闲置停用定时任务的限制。
- **📢 多通道通知中枢**：支持 **微信（PushPlus）** 与 **Telegram Bot** 报告推送，支持 `fail_only`（仅异常报警）与 `all`（每日必推）两种策略。

---

## 🎮 当前支持游戏矩阵

| 游戏名称 | 游戏标识 (`Key`) | 默认状态 | 包含奖励内容 |
| :--- | :--- | :--- | :--- |
| **原神 (Genshin Impact)** | `genshin` | ✅ 默认开启 | 原石、大英雄的经验、摩拉、精锻魔矿等 |
| **崩坏：星穹铁道 (Honkai: Star Rail)** | `star_rail` | ✅ 默认开启 | 星琼、漫游指南、信用点、遗失碎金等 |
| **绝区零 (Zenless Zone Zero)** | `zzz` | ✅ 默认开启 | 菲林、丁尼、资深调查员记录、音擎能源等 |

> 💡 默认策略为三款游戏全部参与签到。如需筛选，可在环境变量中指定 `HOYOLAB_GAMES`。

---

## 🚀 极速部署指南

### 第一步：Fork 本仓库
点击右上角 **Fork** 按钮，将本仓库完整复制到你的 GitHub 个人账号下。

---

### 第二步：提取 HoYoLAB 凭据（极简 2 选 1）

在浏览器中打开并登录 [HoYoLAB 签到中心](https://act.hoyolab.com/bbs/event/signin/index.html)，按 `F12` 打开开发者工具：

#### 选项 A：网络面板一键复制整串（推荐，耗时 5 秒）
1. 开发者工具切换到 **Network（网络）** 标签页，按 `F5` 刷新页面；
2. 在左侧列表中选中任意一个 `hoyolab.com` 域名的请求；
3. 在右侧面板 **Headers（标头）** 下滚动找到 **Request Headers -> Cookie**；
4. **右键点击该条 Cookie -> 选择【Copy value（复制值）】**。
   > ⚠️ **注意**：请务必使用右键“复制值”菜单，切勿用鼠标划选手打，避免 Base64 签名产生漏字符或换行符问题。

#### 选项 B：应用面板提取核心字段
1. 开发者工具切换到 **Application（应用）** -> 左侧展开 **Cookies** -> 选中 `https://act.hoyolab.com`；
2. 复制 `ltoken_v2` 与 `ltuid_v2` 的值，按以下格式拼接：
   ```text
   ltoken_v2=v2_xxxx...; ltuid_v2=12345678;
   ```

---

### 第三步：配置 GitHub Secrets

进入你 Fork 出来的个人仓库：
点击 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**。

#### 1. 核心凭证（必须配置）
* **Name**：`HOYOLAB_COOKIES`
* **Secret**：粘贴第二步获取到的完整 Cookie 字符串。
  > 👥 **多账号支持**：如需签到多个账号，只需将每个账号的完整 Cookie 单独起一行，按行排列即可。

#### 2. 推送配置（可选）
| Secret 变量名 | 说明 | 获取途径 |
| :--- | :--- | :--- |
| `PUSHPLUS_TOKEN` | 微信推送令牌 | [PushPlus 官网](https://www.pushplus.plus/) 微信扫码获取 |
| `TELEGRAM_BOT_TOKEN` | Telegram 机器人密钥 | 通过官方 [@BotFather](https://t.me/BotFather) 创建获取 |
| `TELEGRAM_CHAT_ID` | Telegram 接收者 ID | 通过 [@userinfobot](https://t.me/userinfobot) 获取 |

---

### 第四步：启用自动保活写权限

为确保仓库在连续 60 天无手动提交时不受 GitHub 策略影响而暂停定时任务：
1. 进入仓库 **Settings** → **Actions** → **General**；
2. 页面底部找到 **Workflow permissions**；
3. 选择 **Read and write permissions**，点击 **Save** 保存。

---

### 第五步：立即手动验证

1. 切换到仓库的 **Actions** 标签页；
2. 在左侧点击 **HoYoLAB Checkin** 工作流；
3. 点击右侧 **Run workflow** 下拉框中的绿色按钮；
4. 等待约 30~40 秒，点击进入查看运行日志，确认出现 `retcode=0 status=SUCCESS` 即代表配置大功告成！

---

## ⏰ 定时调度与自动化逻辑

```
[每日 13:40 (UTC 05:40)]  ──>  GitHub 调度启动虚拟机  ──>  单元测试自检 (33 tests)
                                                                 │
                                                                 ▼
[完成销毁 (约40秒)]      <──  推送通知 (PushPlus/TG)  <──  执行签到 (原神+星铁+绝区零)
```

- **执行时间**：每日**北京时间 13:40**（UTC 时间 05:40，Cron: `40 5 * * *`）。
- **运行模式**：云端无状态按需执行，签到完成后虚拟机即刻销毁，无需驻留后台。
- **保活机制**：每月 1 号 `keep-alive.yml` 会自动更新心跳记录，保障任务永久自运行。

---

## ⚙️ 高级配置字典（Variables）

可在仓库 **Settings** → **Secrets and variables** → **Actions** → **Variables** 标签页自由调整：

| 变量名 | 默认值 | 作用说明 |
| :--- | :--- | :--- |
| `HOYOLAB_GAMES` | `genshin,star_rail,zzz` | 参与签到的游戏，多个以英文逗号分割 |
| `PUSH_LEVEL` | `fail_only` | 推送频次：`fail_only`（仅失败时提醒）或 `all`（每日成功均推送） |
| `HOYOLAB_APP_VERSION` | `2.34.1` | 客户端模拟版本号，米哈游更新客户端时可热覆盖 |
| `HOYOLAB_USER_AGENT` | Chrome 最新标准 UA | 自定义客户端浏览器标识符 |

---

## 🧪 工程化保障

本项目采用严谨的测试驱动开发（TDD）规范实现：

```bash
# 本地运行完整单元测试集
python -m unittest discover -s tests -v
```

- **测试套件**：涵盖 API 状态机判定、参数配置校验、游戏注册表完整性、日志脱敏机制、推送路由分发及流程编排。
- **纯粹隔离**：所有测试用例 100% 内存 Mock，保证 CI 构建阶段零外网网络出口，构建时间低于 1 秒。

---

## 📂 项目结构

```text
├── .github/
│   └── workflows/
│       ├── checkin.yml          # 主流程：定时调度与签到执行
│       └── keep-alive.yml       # 保活流：每月提交防仓库休眠
├── hoyolab_checkin/             # 核心模块源码
│   ├── __init__.py
│   ├── api.py                   # HTTP 客户端与响应状态机
│   ├── config.py                # 环境变量配置加载与强校验
│   ├── exceptions.py            # 自定义异常分级
│   ├── games.py                 # 游戏规范与端点路由注册表
│   ├── log.py                   # 日志与脱敏处理器
│   ├── notify.py                # Telegram / PushPlus 报告分发器
│   └── runner.py                # 多账号、多游戏执行编排器
├── tests/                       # 单元测试集（33 个用例全部通过）
├── checkin.py                   # CLI 顶层执行入口
├── requirements.txt             # 基础依赖清单
└── README.md                    # 项目说明文档
```

---

## 💡 常见问题排查 (FAQ)

<details>
<summary><b>Q1: 运行提示 <code>retcode=-100 status=INVALID_COOKIE message=Not logged in</code>？</b></summary>

**A:** 这是身份验证失效报错。请检查：
1. 复制 Cookie 时是否误用了文字划选造成了隐形截断或换行；
2. 是否在浏览器中点击过 HoYoLAB 官方网页的“Log out（退出登录）”使 Token 废弃。
建议按照部署文档第二步的 **方案 A**，在 Network 面板右键选择【Copy value】后重新保存 Secret。
</details>

<details>
<summary><b>Q2: 遇到 <code>CAPTCHA_RISK</code> 验证码风控如何处理？</b></summary>

**A:** 为防止账号受到米哈游更严格的安全策略限制，本引擎**坚决不暴力破解人机验证**。当提示此状态时，引擎会自动跳过后续重试并发出通知。您只需使用常用网络环境打开 HoYoLAB 签到网页手动点击一次签到，通常次日即可恢复自动签到。
</details>

<details>
<summary><b>Q3: 定时任务每天会在 13:40 准秒开始吗？</b></summary>

**A:** GitHub Actions 云端共享资源池在定时任务触发时可能存在 3～15 分钟的队列排队延迟，这完全属于正常现象。米哈游签到是以自然日为单位统计，只要在当天完成均视为全勤。
</details>

---

## ⚖️ 免责声明

1. 本项目仅供 Python 自动化及网络工程学习与技术研究之用；
2. 请遵守相关游戏服务条款，切勿利用本工具进行高频非理性请求；
3. 本项目作者不对任何账号状态异常或使用纠纷承担责任。
