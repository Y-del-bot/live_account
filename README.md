# 直播收入台账管理系统
> 基于Flask+SQLite开发，用于记录、管理直播场次与销售台账。

## ✨ 功能介绍
- 直播场次录入：填写直播时间、直播间名称、产品品类、主播、备注
- 顶部筛选：**按直播时间、产品品类过滤直播记录**（本次迭代新增功能）
- 销售台账管理：给每场直播新增多条销售记录
- 数据详情查看：单场直播的完整销售明细
- 回收站：软删除直播记录，可留存数据，不直接删库
- 数据统计页面：直播营收汇总统计
- Excel导出：支持导出台账数据

## 🛠️ 环境依赖
Python >=3.8

安装第三方依赖：
```bash
pip install flask openpyxl

## 🚀 项目启动步骤

1. 克隆项目到本地

```
git clone https://github.com/Y-del-bot/live_account.git
cd live_account
```

2. 安装依赖包

```
pip install flask openpyxl
```

3. 启动 Flask 服务

```
flask run
```

4. 浏览器访问地址

```
http://127.0.0.1:5000
```

## 📁 项目目录结构

```
live_account/
├── app.py                # Flask后端主程序
├── live.db               # SQLite数据库（首次运行自动生成，不上传git）
├── .gitignore            # Git忽略配置
└── templates/            # 前端网页模板
    ├── index.html        # 首页（带顶部筛选框）
    ├── add_live.html     # 新增直播场次页面
    ├── add_sale.html     # 新增销售记录页面
    ├── live_detail.html  # 直播详情页
    ├── recycle.html      # 回收站页面
    └── stat.html         # 数据统计页面
```

## 💡 说明

1. 数据库`live.db`不会提交到 GitHub，每个人本地运行会自动新建独立数据库。
2. 软删除设计：删除直播记录不会直接删除，移入回收站，可防止误删丢失数据。
3. 开发服务器仅用于本地测试，**不要用于公网正式部署**。

## 📌 项目更新记录

- 2026-09：首页新增顶部筛选框，支持按直播时间、品类筛选直播记录

```
