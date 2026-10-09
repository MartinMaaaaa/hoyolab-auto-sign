# 代码规范 — HoYoLAB 自动签到（GitHub Actions 版）

> 文档版本：v1.0（2026-10-09）
> 配套文档：[DESIGN.md](DESIGN.md)、[FLOW.md](FLOW.md)

## 1. 语言与依赖

- Python **3.11**；运行时依赖**仅 `requests`**（`requirements.txt` 锁 `requests==2.31.0`，与参考项目一致）。
- 测试用 stdlib `unittest` + `unittest.mock`；**禁止**引入 pytest、coverage 等额外依赖。
- 不使用任何需要编译的第三方库，保证 Actions 开箱即跑。

## 2. 目录结构（最终交付形态）

```
project/                          # 即 GitHub 仓库根目录
├── checkin.py                    # 唯一入口：load_config → run → notify → exit code
├── hoyolab_checkin/
│   ├── __init__.py               # 包声明与版本号
│   ├── games.py                  # GAME_REGISTRY 纯数据表（key/act_id/端点/附加头）
│   ├── config.py                 # 环境变量 → 冻结 dataclass；全项目唯一读 os.environ 处
│   ├── api.py                    # HoyoLabClient：get_info()/sign()/classify_response()
│   ├── runner.py                 # 编排：账号×游戏、随机退避、重试、结果聚合
│   ├── notify.py                 # Telegram / PushPlus 推送 + 报告文本格式化
│   └── log.py                    # logging 配置 + mask_secret() 脱敏工具
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_api.py               # 状态机全分支覆盖（mock requests）
│   ├── test_runner.py
│   └── test_notify.py
├── .github/
│   ├── workflows/
│   │   ├── checkin.yml           # 每日签到（见 FLOW.md §5.1）
│   │   └── keep-alive.yml        # 每月防停用提交（见 FLOW.md §5.2）
│   └── last-active.txt           # keep-alive 产物（首次由 workflow 生成）
├── requirements.txt
├── .gitignore                    # __pycache__/、*.pyc、.venv/
├── README.md                     # 使用者文档：Cookie 获取、Secrets 配置、手动测试步骤
└── docs/                         # 本三份文档随仓库提交
```

## 3. 代码风格

- PEP 8，行宽 **100**，4 空格缩进，禁用 tab。
- 每个模块首行 docstring：一句话说明职责。
- 公共函数/方法一律类型注解；文件头 `from __future__ import annotations`。
- 命名：模块 `snake_case`；常量 `UPPER_SNAKE`；dataclass 字段 `snake_case`；枚举/字面量集合用 `enum.StrEnum` 或 `frozenset[str]`。
- **不可变优先**：config 与结果对象一律 `@dataclass(frozen=True, slots=True)`。
- 禁止模块级可变全局状态；依赖一律经构造函数注入（便于 mock）。

## 4. 异常体系

```python
class CheckinError(Exception): ...        # 基类
class ConfigError(CheckinError): ...      # env 缺失/非法（缺 HOYOLAB_COOKIES 等）
class ApiError(CheckinError): ...         # HTTP 层与响应解析失败
class NotifyError(CheckinError): ...      # 推送失败（不改变退出码，只 WARNING）
```

- `runner.py` 内部必须捕获并归类，`checkin.py::main()` 不出现裸异常栈到退出码之外的信息丢失。
- **禁止 `except Exception: pass`**；每个 except 块至少记一条 WARNING 日志并附带上下文（游戏 key、retcode、脱敏后的 message）。

## 5. 日志与脱敏（安全红线）

- 统一使用 `logging`（`log.py` 配置 root：INFO → stdout，WARNING+ → stderr）；**全项目禁止 `print`**。
- **任何 cookie / token / chat_id 的值不得出现在日志与异常消息中**，必须经 `mask_secret()`（保留前 6 位 + `…` + 后 2 位，不足 10 位整体打码）。
- 上游错误日志格式固定：`"[{game}] retcode={rc} message={msg}"`，其中 `msg` 过 `mask_secret()`。
- 请求对象（含 Cookie 头）禁止 `repr()` / `str()` 直接入日志。

## 6. HTTP 客户端规约

- `api.py::HoyoLabClient` 是**全项目唯一**发起网络请求的地方；`runner.py` / `notify.py` 不得直接 `import requests`（notify 自身的推送请求除外，但同样须封装在函数内并设超时）。
- 超时统一：`timeout=(10, 30)`（连接 10s，读 30s）。
- 重试只存在于 `runner.py`（业务级，遵循 FLOW.md §4 的分类），`api.py` 单次请求即返回；**禁止** requests 自带 `Retry` adapter（避免双层重试叠加）。
- Session 用完即关（context manager 或 `finally: session.close()`）。

## 7. 测试规约（先测后签）

- **离线原则**：所有网络交互经 `unittest.mock` 替换，测试套件零外呼。
- 必测清单：

| 文件 | 必须覆盖 |
|---|---|
| `test_config.py` | 多账号换行解析；空/缺失 `HOYOLAB_COOKIES` → `ConfigError`；非法 `HOYOLAB_GAMES` key → `ConfigError`；所有默认值 |
| `test_api.py` | `classify_response()` 状态机 6 分支全部覆盖（SUCCESS / ALREADY_SIGNED / CAPTCHA_RISK / INVALID_COOKIE / API_ERR / NET_ERR）；ZZZ 附加头存在性 |
| `test_runner.py` | 重试达到上限后仍失败；CAPTCHA/INVALID_COOKIE 不重试；聚合统计与退出码映射；info 预检跳过 sign |
| `test_notify.py` | `PUSH_LEVEL` 过滤逻辑；报告文本包含统计行；token 脱敏出现在日志断言中 |

- 断言消息写清"期望 vs 实际"，失败时能直接定位。
- Actions 中 `python -m unittest discover -s tests -v` 失败 → 阻断签到步骤执行。

## 8. Git 与仓库规约

- 单 `main` 分支；提交信息遵循 Conventional Commits（`feat:` / `fix:` / `docs:` / `chore:` / `test:`）。
- 文件一律 UTF-8 无 BOM、LF 换行；`.gitignore` 至少含 `__pycache__/`、`*.pyc`、`.venv/`。
- 两个 workflow YAML 必须齐全：`on`（schedule + workflow_dispatch）、`concurrency`、`permissions`、`timeout-minutes`、签到步骤的 `env` 注入（对照 FLOW.md §5 逐项核对）。

## 9. 禁止事项（负面清单）

1. 禁止把 cookie / token / 账号数据写入任何文件、缓存、异常字符串或测试 fixture。
2. 禁止 `except: pass` 与吞异常。
3. 禁止硬编码任何账号信息；一切账号数据来自环境变量。
4. 禁止新增第三方运行时依赖（v1 范围内 requests 之外一律不加）。
5. 禁止实现国服米游社分支（域名/Cookie/风控体系不同，防止混淆，见 DESIGN.md 排除项）。
6. 禁止在仓库中出现真实 cookie 样例值——README 示例一律用 `ltoken_v2=v2_XXXX…XXXX; ltuid_v2=26XXXXX20;` 形式的明显占位符。
