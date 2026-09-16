from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import time
from openpyxl import Workbook
from io import BytesIO
from urllib.parse import quote

app = Flask(__name__)
DB_FILE = "live.db"

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS live_session(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        live_time TEXT,
        live_room_name TEXT,
        product_category TEXT,
        anchor_name TEXT,
        remark TEXT,
        is_deleted INTEGER DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sale_record(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        live_session_id INTEGER,
        goods_name TEXT,
        spec TEXT,
        price REAL,
        num INTEGER,
        total_amount REAL
    )''')
    conn.commit()
    conn.close()

init_db()

# 计算今日总销售额（修复浮点数精度）
def today_total():
    today_str = time.strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''SELECT COALESCE(SUM(sr.total_amount), 0)
        FROM sale_record sr
        LEFT JOIN live_session ls ON sr.live_session_id = ls.id
        WHERE ls.live_time LIKE ? AND ls.is_deleted=0''', (today_str + '%',))
    total = cur.fetchone()[0]
    conn.close()
    return round(total, 2)

# 首页：只展示正常未删除直播场次 + 顶部筛选
@app.route("/")
def index():
    # 获取筛选参数
    start_time = request.args.get("start_time", "")
    end_time = request.args.get("end_time", "")
    category = request.args.get("category", "")

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # 基础SQL
    sql = "SELECT * FROM live_session WHERE is_deleted=0"
    params = []

    # 动态拼接筛选条件
    if start_time:
        sql += " AND live_time >= ?"
        params.append(start_time)
    if end_time:
        sql += " AND live_time <= ?"
        params.append(end_time + " 23:59:59")
    if category:
        sql += " AND product_category = ?"
        params.append(category)

    sql += " ORDER BY id DESC"
    cur.execute(sql, params)
    live_list = cur.fetchall()

    # 获取所有不重复品类，用于下拉选项
    cur.execute("SELECT DISTINCT product_category FROM live_session WHERE is_deleted=0")
    category_list = [row[0] for row in cur.fetchall()]

    conn.close()
    today_total_money = today_total()
    return render_template("index.html",
                           live_list=live_list,
                           today_total_money=today_total_money,
                           start_time=start_time,
                           end_time=end_time,
                           category=category,
                           category_list=category_list)

# 回收站页面
@app.route("/recycle")
def recycle():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_session WHERE is_deleted=1 ORDER BY id DESC")
    del_list = cur.fetchall()
    conn.close()
    return render_template("recycle.html", del_list=del_list)

# 移入回收站
@app.route("/soft_delete_live/<int:live_id>")
def soft_delete_live(live_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE live_session SET is_deleted=1 WHERE id=?", (live_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# 恢复
@app.route("/restore_live/<int:live_id>")
def restore_live(live_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE live_session SET is_deleted=0 WHERE id=?", (live_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("recycle"))

# 永久删除
@app.route("/hard_delete_live/<int:live_id>")
def hard_delete_live(live_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM sale_record WHERE live_session_id=?", (live_id,))
    cur.execute("DELETE FROM live_session WHERE id=?", (live_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("recycle"))

# 新增直播场次
@app.route("/add_live", methods=["GET", "POST"])
def add_live():
    if request.method == "POST":
        live_time = request.form["live_time"]
        live_room_name = request.form["live_room_name"]
        product_category = request.form["product_category"]
        anchor_name = request.form["anchor_name"]
        remark = request.form["remark"]
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute('''INSERT INTO live_session(live_time, live_room_name, product_category, anchor_name, remark)
        VALUES (?,?,?,?,?)''', (live_time, live_room_name, product_category, anchor_name, remark))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_live.html")

# 登记销售台账
@app.route("/add_sale/<int:live_id>", methods=["GET", "POST"])
def add_sale(live_id):
    if request.method == "POST":
        goods_name = request.form["goods_name"]
        spec = request.form["spec"]
        price = float(request.form["price"])
        num = int(request.form["num"])
        total_amount = round(price * num, 2)  # 修复浮点
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute('''INSERT INTO sale_record(live_session_id, goods_name, spec, price, num, total_amount)
        VALUES (?,?,?,?,?,?)''', (live_id, goods_name, spec, price, num, total_amount))
        conn.commit()
        conn.close()
        return redirect(url_for("live_detail", live_id=live_id))
    return render_template("add_sale.html", live_id=live_id)

# 直播销售明细
@app.route("/live_detail/<int:live_id>")
def live_detail(live_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM live_session WHERE id=?", (live_id,))
    live = cur.fetchone()
    cur.execute("SELECT * FROM sale_record WHERE live_session_id=? ORDER BY id DESC", (live_id,))
    sale_list = cur.fetchall()
    cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM sale_record WHERE live_session_id=?", (live_id,))
    sum_money = round(cur.fetchone()[0], 2)  # 修复浮点
    conn.close()
    return render_template("live_detail.html", live=live, sale_list=sale_list, sum_money=sum_money)

# 删除单条销售记录
@app.route("/delete_sale/<int:sale_id>")
def delete_sale(sale_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT live_session_id FROM sale_record WHERE id=?", (sale_id,))
    row = cur.fetchone()
    live_id = row[0] if row else 0
    cur.execute("DELETE FROM sale_record WHERE id=?", (sale_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("live_detail", live_id=live_id))

# 销量统计
@app.route("/stat")
def stat():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''SELECT goods_name, SUM(num) as total_num, SUM(total_amount) as total_money
    FROM sale_record sr
    LEFT JOIN live_session ls ON sr.live_session_id = ls.id
    WHERE ls.is_deleted=0
    GROUP BY goods_name''')
    raw_stat = cur.fetchall()
    # 修复浮点
    stat_list = [(row[0], row[1], round(row[2] if row[2] else 0, 2)) for row in raw_stat]
    cur.execute('''SELECT COALESCE(SUM(sr.total_amount),0)
        FROM sale_record sr
        LEFT JOIN live_session ls ON sr.live_session_id = ls.id
        WHERE ls.is_deleted=0''')
    all_total = round(cur.fetchone()[0], 2)  # 修复浮点
    conn.close()
    today_total_money = today_total()
    return render_template("stat.html", stat_list=stat_list, all_total=all_total, today_total_money=today_total_money)

# 导出Excel
@app.route("/export")
def export():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''SELECT ls.live_time, ls.live_room_name, ls.anchor_name, sr.goods_name, sr.spec, sr.price, sr.num, sr.total_amount
    FROM sale_record sr LEFT JOIN live_session ls ON sr.live_session_id = ls.id
    WHERE ls.is_deleted=0''')
    all_data = cur.fetchall()
    today_total_money = today_total()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["直播时间", "直播间", "直播人", "商品名称", "规格", "单价", "成交数量", "销售额"])
    for row in all_data:
        ws.append(row)
    ws.append([])
    ws.append(["当日总销售额（元）", today_total_money])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    resp = make_response(output.getvalue())
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = "直播复盘报表.xlsx"
    resp.headers["Content-Disposition"] = f"attachment; filename*=utf-8''{quote(filename)}"
    return resp

if __name__ == "__main__":
    app.run(debug=True)
