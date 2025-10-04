# 📈 每周龙头自动选股 + 邮件推送（带估值温度 & K 线图）

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Schedule](https://img.shields.io/badge/schedule-Fri18:00(CN)-orange)

---

## 🎯 项目用途

1. 每周五收盘后自动运行 **"严格档低估值 + 底部放量 + 行业龙头"** 策略
2. 生成 **沪深300估值温度条** 与 **个股周K线缩略图**
3. 对比上期信号，给出 **新增/剔除** 二次提醒
4. 邮件推送全部结果（含图片附件）→ 手机/PC 一键查看

---

## 🛠 技术栈

| 模块 | 用途 |
|------|------|
| [akshare](https://github.com/akfamily/akshare) | A股行情/财务/行业数据 |
| pandas | 数据清洗与筛选 |
| matplotlib + mplfinance | 估值温度条 & 周K线图 |
| yagmail | 一键发邮件（支持163/QQ/Gmail） |
| GitHub Actions | 定时任务 + 免费云运行 |

---

## 🚀 5 分钟上手

### ① Fork 本仓库
点击右上角 **Fork** → 得到你的副本

### ② 配置密钥
进入 **Settings → Secrets → Actions** → 添加：

| Name | Value 说明 |
|------|------------|
| `MAIL_USER` | 发件邮箱地址 |
| `MAIL_PASS` | 邮箱 **SMTP授权码**（非登录密码！）<br>163/QQ：邮箱设置→SMTP→生成授权码 |
| `MAIL_TO` | 收件人地址（可与自己相同） |

### ③ 首次测试
仓库 → Actions → Weekly-Strict-Pick-plus → **Run workflow**  
→ 等待 1-2 分钟 → 查收邮件（含估值温度图 & K线）

### ④ 本地运行测试
在本地环境中，可以使用以下命令直接运行选股脚本：
```bash
cd scripts
python pick.py
```

注意：脚本需要网络连接以从akshare获取实时数据。

### ⑤ 自动运行
已设定 **每周五 18:00 (CN)** 自动触发，无需干预。

---

## 📬 邮件样例

| 区域 | 内容 |
|------|------|
| 顶部 | 沪深300 **PB温度条**（红>80% 橙>50% 绿<50%） |
| 中段 | 每只标的 **周K线缩略图**（50/200周均线+触发周▲） |
| 底部 | **新增** & **剔除** 股票清单（与上期对比） |

<img src="https://user-images.githubusercontent.com/xxxx/mail_demo.png" width="500"/>

---

## 📁 文件说明

```
stock-pick-email/
├─ .github/workflows/pick.yml      # GitHub Actions 定时任务
├─ scripts/
│  ├─ pick.py                     # 选股+画图+缓存对比
│  ├─ draw.py                     # 估值温度条 & K线绘制
│  ├─ mail.py                     # 发邮件（html+附件）
│  └─ requirements.txt            # 依赖库
├─ cache/                         # 自动缓存上期信号（勿删）
└─ README.md                      # 本文件
```

---

## ⚙ 进阶玩法

| 需求 | 快速修改点 |
|------|------------|
| 改为 **月频** | `cron: '0 10 1 * *'` 每月1号 |
| 加入 **企业微信/飞书** 推送 | 在 `mail.py` 后追加 webhook 请求 |
| 画 **日K/30分钟K** | 改 `plot_kline()` 的 `period="daily"` 或 `period="1min"` |
| 使用 **融资融券** 过滤 | 在 `pick.py` 加 `ak.stock_margin_detail_szse()` 判断 |

---

## ⚠ 免责声明

本项目仅供学习与研究，**不构成任何投资建议**。投资有风险，决策需谨慎！

---

## 📄 License

MIT © 2024 YourName  
欢迎 Star / Fork / PR 共同完善！