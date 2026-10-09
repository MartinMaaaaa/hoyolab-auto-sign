# 设计目的 — HoYoLAB 国际服自动签到（GitHub Actions 版）

> 文档版本：v1.0（2026-10-09）
> 配套文档：[FLOW.md](FLOW.md)（流程规划）、[CODE_STANDARDS.md](CODE_STANDARDS.md)（代码规范）

## 一句话目标

用 GitHub Actions 定时任务，每天自动完成 HoYoLAB（国际服）的**原神、崩坏：星穹铁道、绝区零**每日签到领奖，零服务器成本、零日常维护、失败可感知。

## 用户画像与使用场景

- 玩 HoYoLAB 国际服，日常忘记签到，损失原石 / 星琼 / 菲林等月度奖励
- 有 GitHub 账号，愿意一次性配置 Secrets，之后不想再管
- 希望只在"出问题"时被打扰（Cookie 失效、风控、签到失败）

## 设计原则（按优先级排序）

1. **零成本**
   - 公开仓库的 GitHub Actions 免费额度完全覆盖：每天 1 次运行 × 约 2 分钟。
2. **低维护**
   - keep-alive workflow 每月产生一次活跃提交，规避"公开仓库 60 天无活动 → schedule 被自动停用"。
   - API 易变参数（`x-rpc-app_version`、User-Agent）可经环境变量覆盖，**不改代码即可调整**。
   - 轻度模块化：新增游戏改 `games.py` 注册表一处；换通知渠道改 `notify.py` 一处。
3. **安全**
   - Cookie 只经 GitHub Secrets → 环境变量传入，代码与日志零落盘。
   - 日志统一脱敏（cookie / token 掩码，只保留首尾几位）。
   - workflow 最小权限（`permissions: contents: read`）。
4. **可观测**
   - 结构化日志（INFO 级别输出到 stdout，Actions 自动采集）。
   - 运行结果映射为进程退出码：全成功/已签到 = 0，任何失败 = 1，Actions 页面红绿即可判断。
   - 可选 Telegram / PushPlus 双通道推送；默认只在失败时推送，手动触发必推送。
5. **可测试**
   - 纯函数 + 注入式 HTTP 封装，`unittest` + `mock` 离线全覆盖核心逻辑，测试先于签到运行（失败即阻断）。

## 范围（Scope）

### 支持
| 项 | 说明 |
|---|---|
| 游戏 | 原神、星穹铁道、绝区零（均为 HoYoLAB 国际服） |
| 账号 | 多账号（Secrets 中换行分隔） |
| 游戏开关 | 环境变量 `HOYOLAB_GAMES` 逗号分隔，默认三游戏全开 |
| 触发 | cron 每日 1 次 + `workflow_dispatch` 手动 |
| 通知 | Telegram Bot、PushPlus（二者可只配其一） |

### 明确排除
- **国服（米游社）**：API 域名、Cookie 字段（Stoken 体系）与风控均不同，混在一个实现里极易混淆，v1 不做。
- **崩坏3、未定事件簿**：端点已在 `games.py` 注册表中预留注释位，后续按需开启。
- **自动过验证码**：触发风控（`gt_result.is_risk`）时只报告、不破解，提醒用户手动处理。

## 成功标准

1. 连续 30 天无人值守签到成功率 ≥ 95%（网络抖动由脚本内重试消化）。
2. Cookie 失效 / 风控 / 全失败发生时，用户 5 分钟内收到通知。
3. 任何一次历史运行，都能只看 Actions 日志回答："今天每个账号、每个游戏签成什么样"。

## 关键技术决策记录（ADR 摘要）

| # | 决策点 | 选择 | 理由 | 放弃的替代方案 |
|---|---|---|---|---|
| 1 | 语言/运行时 | Python 3.11 | Actions 原生支持、生态成熟；参考项目 2 同栈 | Node.js |
| 2 | HTTP 库 | requests（唯一依赖） | 参考项目 2 同款；够用、审计面小 | httpx、aiohttp |
| 3 | 代码组织 | 轻度模块化包 + 单入口 | 可测试、可维护；参考项目 1 的 90 行单文件不可测 | 单文件 |
| 4 | 通知渠道 | Telegram + PushPlus 双通道 | 参考项目 1 用 TG、项目 2 用 PushPlus+TG；覆盖国内外用户 | Server酱、邮件 |
| 5 | 已签判断 | 先 GET info 接口预判 `is_sign` | 少打无效 sign 请求（降低风控概率）、报告可含"本月第 N 天" | 直接 sign 读 message |
| 6 | cron 时间 | `0 2 * * *`（北京 10:00） | 参考项目建议 09:00–15:00（UTC+8）窗口；北京 10:00 跨过 HoYoLAB 日重置且避开 Actions 高峰延迟 | — |
| 7 | 多账号分隔符 | 换行符 | GitHub Secrets 原生支持多行值 | `&` 等符号（存在转义歧义） |
| 8 | 失败重试 | 脚本内业务级重试（默认 3 次 / 60s 间隔） | 参考项目 2 模式；Actions 层重试会重跑全流程，粒度太粗 | workflow 级 retry |

## 参考

- [canaria3406/hoyolab-auto-sign](https://github.com/canaria3406/hoyolab-auto-sign)：HoYoLAB 签到 API、请求头、风控判断依据（`gt_result.is_risk`）、多账号配置形态。
- [MartinMaaaaa/2026-glados-checkin](https://github.com/MartinMaaaaa/2026-glados-checkin)：GitHub Actions 定时任务形态（cron / secrets 注入 / 重试参数 / keep-alive / 先测后跑）。
- 调研细节存档：`_reference/RESEARCH.md`。
