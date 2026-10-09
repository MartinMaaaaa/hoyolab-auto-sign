# 🌟 HoYoLAB Auto Check-in Engine
### 崩铁 · 原神 · 绝区零 | 三端全勤 · 云端托管 · 零成本全自动签到

<p align="center">
  <img src="docs/assets/banner.jpg" alt="HoYoLAB Daily Reward Check-in Banner" width="100%" style="border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.12);" />
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" /></a>
  <a href="https://github.com/features/actions"><img src="https://img.shields.io/badge/Platform-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions" /></a>
  <a href="#-测试与工程质量"><img src="https://img.shields.io/badge/Tests-33%20Passed-2ea44f?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests Passed" /></a>
  <a href="#-核心技术特色"><img src="https://img.shields.io/badge/Server%20Cost-Zero%20¥-orange?style=for-the-badge" alt="Zero Server Cost" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License" /></a>
</p>

---

## 🎁 这个项目能为你做什么？

米哈游官方在 **HoYoLAB（国际服）** 为玩家设立了每日签到福利系统。虽然奖励丰厚，但手动签到往往伴随着痛点：
* 每天需要手动开网页或 App、在不同游戏专区来回切换；
* 出差、备考、加班或外出游玩时经常忘签漏签，**月底看着少拿的几十抽资粮扼腕叹息**。

**HoYoLAB Auto Check-in Engine** 就是为了解决这一痛点而生的「云端全自动管家」。一次配置，即可实现 **原神 + 崩坏：星穹铁道 + 绝区零** 三端每日全自动云打卡！

### 💎 签到全勤收益清单

| 游戏平台 | 核心抽卡资源 | 养成与冒险物资 |
| :--- | :--- | :--- |
| **原神** (Genshin Impact) | 💎 **每月 60 原石**（白嫖抽卡基金） | 📕 大英雄的经验 ×多本<br>🔨 精锻魔矿 ×数十个<br>🪙 摩拉、各类提瓦特特色料理 |
| **崩坏：星穹铁道** (Honkai: Star Rail) | ✦ **每月 60 星琼**（通往星海的车票） | 📘 漫游指南、冒险记录<br>✨ 遗失碎金、提纯以太<br>🪙 信用点 ×数十万 |
| **绝区零** (Zenless Zone Zero) | 🎞️ **每月 60 菲林**（绳匠招募资金） | 📼 资深调查员记录<br>🔋 音擎能源、变频音擎电源<br>🪙 丁尼 ×数十万 |

> 攒水如抽丝，积少成多！一年下来，三端签到累计能为你自动入账 **超过 2160+ 抽卡原石/星琼/菲林** 以及海量角色突破材料，再也不用担心因为断签而痛失全勤奖励！

---

## 🛡️ 核心技术特色（保证安全、拟真与无感）

整个引擎在工程实现上高度注重**安全性**与**拟真度**，避免引起风控：

* **☁️ 0 成本无服务器调度（Serverless 邦布特遣）**  
  基于 GitHub Actions 自动化机制，平时完全休眠不消耗任何电脑电量与服务器成本；每天定点由云端虚拟机拉起，耗时仅 40 秒左右完成签到并立即安全销毁，**每月免费额度占用仅约 1%**。
* **🎭 拟真人性化抖动（避免触动天理风控）**  
  摒弃机械化的高并发短时并发请求。在每个游戏签到之间、多账号切换之间，系统会自动插入 **3～15 秒的动态随机延迟（Jitter Delay）**，行为特征完美模拟真实旅行者/开拓者/绳匠的操作节奏。
* **🕊️ 人机验证优雅避险（知更鸟式的绅士礼让）**  
  遇到偶发的图形滑块验证码（`CAPTCHA_RISK`）时，系统**坚决不暴力硬解**，而是立即主动挂起当前签到并触发告警推送，提醒主人手动补签一次，杜绝账号异常风险。
* **🔐 军工级密文日志（黑天鹅的匿影结界）**  
  运行日志与通知推送中，所有涉及 UID、Token、Cookie 等敏感字段均经过严格的哈希脱敏掩码（Masking）处理，即使运行日志完全公开，身份信息也固若金汤。
* **🚂 永久防休眠自愈机制（星穹列车的永动引擎）**  
  GitHub 针对 60 天无活动仓库会强制暂停定时任务。本项目内嵌保活工作流（`keep-alive.yml`），每月初自动为仓库加注“心跳燃料”，实现年复一年的全自动永动签到。

<p align="center">
  <img src="docs/assets/success_stamp.jpg" alt="Checkin Mission Accomplished" width="340px" style="border-radius: 12px; margin: 16px 0;" />
  <br>
  <em>每日打卡完成，战报清晰无误，盖章确认！</em>
</p>

---

## 🚀 极速部署指南（5 分钟完成）

### 第一步：Fork 本仓库
点击本页面右上角 **Fork** 按钮，将本仓库克隆到你的个人 GitHub 账号下。

---

### 第二步：提取 HoYoLAB 凭证（推荐 5 秒极速复制法）

在电脑浏览器登录 [HoYoLAB 签到中心](https://act.hoyolab.com/bbs/event/signin/index.html)，按键盘 `F12` 打开开发者工具：

#### 方案 A：网络面板一键【复制值】（最推荐，零失误）
1. 开发者工具顶部切换到 **Network（网络）** 标签页，按 `F5` 刷新一次网页；
2. 在左侧的请求列表里，随意点击任意一个包含 `hoyolab.com` 的请求（如带有 `home`、`sign`、`getNotice` 的请求）；
3. 在右侧面板中，点击 **Headers（标头）** -> 向下滚动找到 **Request Headers（请求标头）** 下的 **`Cookie`** 这一行；
4. **鼠标移到 `Cookie` 内容上右键 -> 选择【Copy value（复制值）】**。
   > ⚠️ **派蒙的特别提醒**：务必使用右键菜单中的“复制值”，**切勿用鼠标手动涂抹划选手打**！长达两百多位的加密签名在手动划选时极易漏字符或夹杂换行符，导致验证失败。

#### 方案 B：应用面板提取双核心参数（精简格式）
1. 开发者工具顶部选择 **Application（应用）** -> 左侧展开 **Cookies** -> 点击 `https://act.hoyolab.com`；
2. 找到 `ltoken_v2` 与 `ltuid_v2`，按分号拼接成如下格式即可：
   ```text
   ltoken_v2=v2_xxxx...; ltuid_v2=12345678;
   ```

---

### 第三步：配置 GitHub Secrets 机密

进入你 Fork 出的仓库：
点击 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

1. **必填核心机密**：
   * **Name**：`HOYOLAB_COOKIES`
   * **Secret**：粘贴第二步复制出来的完整 Cookie。
   > 👥 **多账号支持**：如果有小号或亲友账号，把多个账号的完整 Cookie **换行排列**（一行一个）即可！

2. **可选推送通道**（如想在手机上实时掌握打卡战报）：
   * **微信推送**：新建 Secret `PUSHPLUS_TOKEN`，填入 [PushPlus 官网](https://www.pushplus.plus/) 扫码获取的 Token。
   * **Telegram 推送**：新建 Secret `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID`。

---

### 第四步：激活永动保活权限

为确保每月自动保活工作流能够正常提交时间戳：
1. 打开仓库 **Settings** → **Actions** → **General**；
2. 滚动到底部找到 **Workflow permissions**；
3. 勾选 **Read and write permissions**，点击 **Save**。

---

### 第五步：立即手动发车验证

1. 打开仓库的 **Actions** 页面；
2. 在左侧选择 **HoYoLAB Checkin** 工作流；
3. 点击右侧 **Run workflow** 按钮启动测试；
4. 约 40 秒后，查看日志看到原神、星铁、绝区零三个游戏均输出 `retcode=0 status=SUCCESS`，即代表配置圆满成功！

---

## ⏰ 运行周期说明

* **默认签到时间**：每天**北京时间 13:40**（UTC 05:40，Cron: `40 5 * * *`）。
* **关于排队波动**：GitHub Actions 云端资源池在高峰期可能会有 3～15 分钟的队列排队延迟，属于官方正常调度，只要在当天 24:00 前完成签到均能成功计入全勤！
* **是否需要常驻？**：**完全不需要**。签到结束后工作流显示 `Complete` 并自动销毁虚拟机，第二天的 13:40 会自动被闹钟唤醒生成新的打卡记录。

---

## ⚙️ 进阶参数调优（Repository Variables）

在仓库 **Settings** → **Secrets and variables** → **Actions** → **Variables** 标签页可添加如下控制项：

| 变量名 | 默认值 | 作用说明 |
| :--- | :--- | :--- |
| `HOYOLAB_GAMES` | `genshin,star_rail,zzz` | 指定签到的游戏（多个用逗号隔开，可任意剔除不需要的游戏） |
| `PUSH_LEVEL` | `fail_only` | 推送策略：`fail_only`（仅失败/风控时报警，平时静默）或 `all`（每天必发战报） |
| `HOYOLAB_APP_VERSION` | `2.34.1` | 客户端模拟版本，米哈游更新客户端校验时可随时覆盖 |
| `HOYOLAB_USER_AGENT` | Chrome 最新标准 UA | 自定义浏览器特征标识 |

---

## 🧪 测试与工程质量

本项目遵循严谨的测试驱动开发（TDD）理念：

```bash
# 本地快速运行全量测试
python -m unittest discover -s tests -v
```

* **33 个单元测试全绿通过**，覆盖 API 状态机判定、参数配置容错、防风控重试退避、多账号编排调度及日志脱敏；
* **测试用例 100% 内存 Mock**，CI 执行期间不发出任何外网请求，确保极速、纯粹与稳定。

---

## 📂 项目结构全景

```text
├── .github/
│   └── workflows/
│       ├── checkin.yml          # 定时调度：每日 13:40 准点打卡任务
│       └── keep-alive.yml       # 永动引擎：每月提交防止仓库休眠
├── docs/
│   └── assets/                  # 角色表情包与视觉插图
├── hoyolab_checkin/             # 核心业务模块
│   ├── api.py                   # HTTP 请求封装与状态分类状态机
│   ├── config.py                # 环境变量配置解析与强类型校验
│   ├── exceptions.py            # 自定义异常分级
│   ├── games.py                 # 游戏规范与端点路由注册表
│   ├── log.py                   # 日志格式化与敏感凭据脱敏器
│   ├── notify.py                # 微信 PushPlus / Telegram 消息分发
│   └── runner.py                # 多账号、多游戏执行编排调度器
├── tests/                       # 33 项内存 Mock 自动化单元测试集
├── checkin.py                   # 主执行入口文件
├── requirements.txt             # 生产依赖（仅 requests）
└── README.md                    # 本说明文档
```

---

## 💬 常见疑问解答 (FAQ)

<details>
<summary><b>Q1: 运行日志出现 <code>retcode=-100 status=INVALID_COOKIE message=Not logged in</code>？</b></summary>

**A:** 这是米哈游服务器返回的“登录凭据失效/不匹配”错误：
1. 请勿手动复制或打字，请使用部署指南第二步的 **方案 A**，在 Network 请求头右键点击【Copy value】完整复制；
2. 确保在网页复制完 Cookie 后，**没有在浏览器上点击“退出登录（Log Out）”**；
3. 将最新复制的整串 Cookie 重新更新到 `HOYOLAB_COOKIES` 即可。
</details>

<details>
<summary><b>Q2: Cookie 有效期有多久？</b></summary>

**A:** HoYoLAB 国际服的 `ltoken_v2` 具备极长的生命周期（通常数月至一年以上）。只要不在网页上手动登出，平时手机、电脑正常玩游戏或浏览网页均不受影响。
</details>

<details>
<summary><b>Q3: 遇到 <code>CAPTCHA_RISK</code> 验证码怎么办？</b></summary>

**A:** 系统检测到米哈游临时弹出的图形验证码时，会放弃重试并通知你。此时只需在手机或电脑浏览器中登录 HoYoLAB 手动签到一次（消除验证码），次日自动签到即可恢复正常。
</details>

---

## 📜 开源免责声明

1. 本项目仅供技术交流与 Python 自动化网络工程研究学习使用；
2. 请严格遵守米哈游相关游戏服务协议，请勿将本工具用于商业用途或发起恶意高频请求；
3. 本项目作者不对任何账号数据异常或使用风险承担担保责任。
