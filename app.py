from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supermarket-secret-key"

ADMIN_USERNAME = "amir.admin"
ADMIN_PASSWORD = "amir2021"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "supermarket.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def fmt(value):
    return f"{int(value):,}"


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        balance INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price INTEGER NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        total INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'در حال انجام عملیات',
        created_at TEXT NOT NULL,
        order_code TEXT
    );

    CREATE TABLE IF NOT EXISTS purchase_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        total INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS store(
        id INTEGER PRIMARY KEY CHECK(id=1),
        money INTEGER NOT NULL DEFAULT 0,
        total_sales INTEGER NOT NULL DEFAULT 0
    );

    INSERT OR IGNORE INTO store(id,money,total_sales) VALUES(1,0,0);
    """)
    # Upgrade old databases without deleting anything.
    try:
        conn.execute("ALTER TABLE purchases ADD COLUMN order_code TEXT")
    except sqlite3.OperationalError:
        pass

    old = conn.execute(
        "SELECT id FROM purchases WHERE order_code IS NULL OR order_code=''"
    ).fetchall()
    for row in old:
        conn.execute(
            "UPDATE purchases SET order_code=? WHERE id=?",
            ("GW-" + uuid.uuid4().hex[:8].upper(), row["id"])
        )

    conn.commit()
    conn.close()


def page(title, content, active=""):
    return render_template_string(
        HTML,
        title=title,
        content=content,
        active=active
    )


HTML = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} | سوپرمارکت</title>

<!-- اگر اینترنت در دسترس باشد فونت Estedad لود می‌شود؛ در غیر این صورت فونت‌های داخلی استفاده می‌شوند. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Estedad:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
@import url('https://fonts.googleapis.com/css2?family=Estedad:wght@400;500;600;700;800;900&display=swap');

:root{
 --bg:#f3f6fc; --surface:#fff; --surface2:#f8faff;
 --ink:#182238; --muted:#78839a; --line:#e7ebf3;
 --blue:#4568ee; --blue2:#7658e8; --cyan:#39b8df;
 --green:#18a66a; --orange:#f0a329; --red:#e45159;
 --shadow:0 18px 55px rgba(34,50,86,.09);
 --shadow2:0 10px 28px rgba(34,50,86,.08);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
 margin:0;color:var(--ink);
 font-family:'Estedad','Vazirmatn','Tahoma',Arial,sans-serif;
 background:
 radial-gradient(circle at 5% 5%,rgba(69,104,238,.12),transparent 24%),
 radial-gradient(circle at 96% 8%,rgba(118,88,232,.11),transparent 22%),
 linear-gradient(180deg,#f7f9fd 0,#f0f4fb 100%);
 min-height:100vh;
}
body:before{
 content:"";position:fixed;inset:0;pointer-events:none;opacity:.28;
 background-image:radial-gradient(#b9c4d8 .7px,transparent .7px);
 background-size:20px 20px;mask-image:linear-gradient(to bottom,black,transparent 75%);
}
a{color:inherit}
.navbar{
 position:sticky;top:0;z-index:50;
 background:rgba(255,255,255,.78);
 backdrop-filter:blur(22px) saturate(160%);
 border-bottom:1px solid rgba(222,227,238,.8);
 box-shadow:0 5px 25px rgba(40,54,90,.04);
}
.nav-inner{
 width:min(1240px,94%);min-height:76px;margin:auto;
 display:flex;justify-content:space-between;align-items:center;gap:20px;
}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;font-weight:900;font-size:21px}
.brand-icon{
 width:46px;height:46px;border-radius:15px;display:grid;place-items:center;
 color:#fff;font-size:23px;
 background:linear-gradient(135deg,var(--blue),var(--blue2));
 box-shadow:0 9px 22px rgba(69,104,238,.28);
}
.nav-links{display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.nav-links a{
 text-decoration:none;color:#566177;padding:10px 13px;border-radius:13px;
 font-size:14px;font-weight:700;transition:.2s;
}
.nav-links a:hover,.nav-links a.active{color:var(--blue);background:#edf1ff}
.container{width:min(1240px,94%);margin:32px auto 65px;position:relative;z-index:1}
.hero{
 position:relative;overflow:hidden;border-radius:34px;padding:58px 48px;
 color:#fff;min-height:330px;
 background:
 radial-gradient(circle at 80% 20%,rgba(255,255,255,.18),transparent 20%),
 linear-gradient(135deg,#3d63e8 0%,#5b57df 50%,#7957df 100%);
 box-shadow:0 28px 70px rgba(63,83,200,.25);
}
.hero:before{
 content:"";position:absolute;width:390px;height:390px;left:-120px;top:-180px;
 border:70px solid rgba(255,255,255,.07);border-radius:50%;
}
.hero:after{
 content:"🛒";position:absolute;left:8%;bottom:-70px;font-size:260px;
 opacity:.08;transform:rotate(-12deg);
}
.hero-inner{position:relative;z-index:2;max-width:760px}
.hero-kicker{
 display:inline-flex;align-items:center;gap:7px;
 background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.18);
 border-radius:999px;padding:7px 12px;font-size:12px;font-weight:800;
}
.hero h1{font-size:46px;line-height:1.25;margin:14px 0 10px;font-weight:900;letter-spacing:-1px}
.hero p{font-size:17px;opacity:.9;max-width:650px;margin:0 0 25px}
.hero-stat{
 position:absolute;right:42px;top:42px;z-index:2;
 width:225px;padding:20px;border-radius:23px;
 background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.18);
 backdrop-filter:blur(14px);
}
.hero-stat .mini{font-size:12px;opacity:.75}
.hero-stat strong{display:block;font-size:30px;margin-top:4px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
.btn{
 border:0;cursor:pointer;text-decoration:none;display:inline-flex;
 justify-content:center;align-items:center;gap:7px;min-height:44px;
 padding:9px 17px;border-radius:13px;color:#fff;
 background:linear-gradient(135deg,var(--blue),var(--blue2));
 font:inherit;font-weight:800;font-size:14px;
 box-shadow:0 9px 20px rgba(69,104,238,.2);transition:.2s;
}
.btn:hover{transform:translateY(-2px);box-shadow:0 13px 26px rgba(69,104,238,.24)}
.btn.green{background:linear-gradient(135deg,#13a367,#2fc180)}
.btn.red{background:linear-gradient(135deg,#dd4149,#f0676d)}
.btn.orange{background:linear-gradient(135deg,#e8931e,#f4b14b)}
.btn.light,.btn.gray{background:#edf1f7;color:#4e5a70;box-shadow:none}
.btn.full{width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.card{
 background:rgba(255,255,255,.94);border:1px solid rgba(225,230,240,.9);
 border-radius:24px;padding:23px;box-shadow:var(--shadow);
 transition:.2s;
}
.card:hover{box-shadow:0 22px 55px rgba(34,50,86,.11)}
.stat{
 min-height:132px;display:flex;align-items:center;gap:16px;
 position:relative;overflow:hidden;
}
.stat:after{
 content:"";position:absolute;left:-35px;bottom:-55px;width:130px;height:130px;
 border-radius:50%;background:rgba(69,104,238,.05);
}
.stat-icon{
 width:62px;height:62px;flex:0 0 62px;border-radius:19px;
 display:grid;place-items:center;font-size:28px;
 background:linear-gradient(135deg,#edf2ff,#f4efff);
 border:1px solid #e7eafd;
}
.stat small{display:block;color:var(--muted);font-weight:700;font-size:12px}
.stat h2{margin:3px 0 0;font-size:25px;font-weight:900}
.section-title{
 display:flex;justify-content:space-between;align-items:end;gap:15px;margin:38px 0 17px;
}
.section-title h2{margin:0;font-size:28px;font-weight:900}
.section-title p{margin:2px 0 0;color:var(--muted);font-size:13px}
.products-grid{
 display:grid;grid-template-columns:repeat(auto-fill,minmax(245px,1fr));gap:20px;
}
.product-card{
 position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:350px;
 padding:20px;isolation:isolate;
}
.product-card:before{
 content:"";position:absolute;width:180px;height:180px;left:-75px;top:-85px;
 background:linear-gradient(135deg,rgba(69,104,238,.12),rgba(118,88,232,.03));
 border-radius:50%;z-index:-1;
}
.product-card:hover{transform:translateY(-5px)}
.product-art{
 height:125px;border-radius:21px;margin-bottom:15px;
 display:grid;place-items:center;font-size:64px;
 background:
 radial-gradient(circle at 30% 25%,#fff 0,rgba(255,255,255,.5) 20%,transparent 21%),
 linear-gradient(135deg,#eef3ff,#f8f1ff);
 border:1px solid #e7eaf4;
 position:relative;overflow:hidden;
}
.product-art:after{
 content:"";position:absolute;width:130px;height:130px;border-radius:50%;
 border:22px solid rgba(69,104,238,.06);right:-42px;bottom:-48px;
}
.product-name{font-size:20px;font-weight:900;margin:0 0 3px}
.price{font-size:23px;font-weight:900;color:var(--blue);margin:2px 0}
.stock{color:var(--muted);font-size:13px;margin-bottom:13px}
.stock-pill{
 display:inline-flex;width:max-content;padding:5px 9px;border-radius:999px;
 background:#edf9f3;color:#158052;font-size:11px;font-weight:800;margin-bottom:8px;
}
.stock-pill.out{background:#fff0f0;color:#b5353d}
input,select,textarea{
 width:100%;border:1px solid #dfe4ed;background:#fafbfe;color:var(--ink);
 padding:11px 13px;border-radius:13px;margin:5px 0 13px;
 font:inherit;outline:none;transition:.2s;
}
input:focus,select:focus,textarea:focus{
 border-color:#7890ef;background:#fff;box-shadow:0 0 0 4px rgba(69,104,238,.09);
}
label{font-size:13px;font-weight:800;color:#4f5a70}
.alert{border-radius:15px;padding:13px 16px;margin:12px 0;border:1px solid transparent;font-weight:700}
.alert.error{background:#fff0f1;color:#a42c34;border-color:#ffd6d9}
.alert.success{background:#ebfaf2;color:#167447;border-color:#c9efd9}
.form{max-width:500px;margin:60px auto}
.form-head{text-align:center;margin-bottom:26px}
.form-head .big-icon{
 width:78px;height:78px;border-radius:24px;display:grid;place-items:center;
 margin:0 auto 13px;font-size:35px;color:#fff;
 background:linear-gradient(135deg,var(--blue),var(--blue2));
 box-shadow:0 15px 30px rgba(69,104,238,.23);
}
.muted,.small{color:var(--muted);font-size:13px}
.badge{
 display:inline-flex;align-items:center;gap:5px;padding:7px 12px;border-radius:999px;
 font-size:12px;font-weight:900;background:#edf1ff;color:#4258b9;
}
.badge.pending{background:#fff4dc;color:#a66b08}
.badge.done{background:#eaf9f0;color:#167343}
.badge.cancel{background:#fff0f0;color:#a52a30}
.status-box{
 display:flex;align-items:center;gap:10px;background:#fff8e9;border:1px solid #f3dda7;
 border-radius:15px;padding:12px 14px;font-weight:800;color:#9c6a0c;
}
.spinner{
 width:19px;height:19px;border:3px solid #f1d89b;border-top-color:#d88d16;
 border-radius:50%;animation:spin .8s linear infinite;flex:0 0 19px;
}
@keyframes spin{to{transform:rotate(360deg)}}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:18px;background:#fff}
table{width:100%;border-collapse:separate;border-spacing:0;min-width:760px}
th,td{padding:14px 13px;border-bottom:1px solid #edf0f5;text-align:center}
th{background:#f7f8fc;color:#657086;font-weight:900;font-size:12px}
tr:last-child td{border-bottom:0}
.order-card{overflow:hidden}
.order-head{
 display:flex;justify-content:space-between;align-items:center;gap:15px;
 padding-bottom:16px;border-bottom:1px solid var(--line);
}
.order-items{margin-top:7px}
.order-item{
 display:flex;align-items:center;gap:13px;padding:13px 0;border-bottom:1px solid #edf0f5;
}
.order-item:last-child{border-bottom:0}
.order-item-icon{
 width:49px;height:49px;border-radius:15px;display:grid;place-items:center;
 background:linear-gradient(135deg,#edf2ff,#f5efff);font-size:24px;flex:0 0 49px;
}
.order-item-main{flex:1}
.order-total{
 display:flex;justify-content:space-between;align-items:center;margin-top:17px;
 padding:16px 18px;background:linear-gradient(135deg,#f3f5ff,#f8f3ff);
 border-radius:16px;font-size:16px;font-weight:800;
}
.order-total strong{font-size:22px;color:var(--blue)}
.invoice-page{max-width:930px;margin:25px auto}
.invoice-card{
 background:#fff;border:1px solid var(--line);border-radius:28px;padding:38px;
 box-shadow:var(--shadow);
}
.invoice-top{
 display:flex;justify-content:space-between;align-items:center;gap:20px;
 padding-bottom:24px;border-bottom:2px solid #eef1f6;
}
.invoice-logo{
 width:64px;height:64px;border-radius:19px;display:grid;place-items:center;
 font-size:30px;color:#fff;background:linear-gradient(135deg,var(--blue),var(--blue2));
 box-shadow:0 12px 25px rgba(69,104,238,.2);
}
.invoice-title{font-size:31px;font-weight:900;margin-top:8px}
.invoice-subtitle{color:var(--muted)}
.invoice-code{
 background:#f1f4ff;border:1px solid #e0e5ff;border-radius:16px;padding:13px 19px;text-align:center;
}
.invoice-code span{display:block;color:var(--muted);font-size:11px}
.invoice-code strong{font-size:19px;letter-spacing:1px}
.invoice-info{display:grid;grid-template-columns:repeat(3,1fr);gap:13px;padding:22px 0}
.invoice-info div{background:#f8f9fc;border-radius:15px;padding:13px}
.invoice-info span{display:block;color:var(--muted);font-size:11px}
.invoice-table{min-width:650px}
.invoice-total{
 display:flex;justify-content:space-between;align-items:center;margin-top:20px;
 padding:19px 21px;background:linear-gradient(135deg,#f1f4ff,#f7f3ff);
 border-radius:17px;font-size:18px;
}
.invoice-total strong{font-size:25px;color:var(--blue)}
.invoice-footer{
 display:flex;justify-content:space-between;color:var(--muted);font-size:12px;padding-top:18px;
}
.footer{text-align:center;color:#8a94a8;font-size:12px;padding:28px}
.empty{text-align:center;padding:45px 20px;color:var(--muted)}
.admin-title{
 display:flex;align-items:center;justify-content:space-between;gap:15px;
 padding:25px 27px;border-radius:25px;color:#fff;
 background:linear-gradient(135deg,#1d2945,#344d82);
 box-shadow:0 20px 45px rgba(27,41,69,.18);
}
.admin-title h1{margin:0;font-size:28px}
.admin-title p{margin:3px 0 0;opacity:.72;font-size:13px}
@media(max-width:850px){
 .hero-stat{position:static;margin-top:25px;width:100%}
 .hero h1{font-size:35px}
}
@media(max-width:650px){
 .nav-inner{min-height:68px;align-items:flex-start;padding:8px 0}
 .brand{font-size:17px}
 .nav-links a{font-size:12px;padding:7px 8px}
 .container{margin-top:20px}
 .hero{padding:36px 23px}
 .hero h1{font-size:29px}
 .invoice-card{padding:20px}
 .invoice-info{grid-template-columns:1fr}
 .invoice-top{align-items:flex-start}
 .invoice-footer{flex-direction:column;gap:6px}
}
@media print{
 body{background:#fff!important}
 .navbar,.footer,.no-print{display:none!important}
 .container{width:100%!important;margin:0!important}
 .invoice-page{max-width:none!important;margin:0!important}
 .invoice-card{box-shadow:none!important;border:0!important}
}
</style>

<style id="premium-overrides">
/* ===== PREMIUM UI OVERRIDES ===== */
body{font-feature-settings:"ss01";letter-spacing:-.1px}
.container{max-width:1280px}
.nav-inner{max-width:1280px}
.navbar{background:rgba(248,250,255,.86)}
.nav-links{background:#f0f3fa;border:1px solid #e5e9f2;padding:4px;border-radius:16px}
.nav-links a{border-radius:11px}
.hero{min-height:370px;padding:60px 54px}
.hero h1{font-size:52px;letter-spacing:-1.8px}
.hero p{font-size:18px;line-height:2}
.hero:after{font-size:300px}
.products-grid{grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:22px}
.product-card{min-height:390px;padding:18px;border-radius:26px}
.product-art{height:150px;font-size:76px;border-radius:23px}
.product-name{font-size:21px}
.price{font-size:25px}
.card{border-radius:26px}
.section-title{margin-top:44px}
.section-title h2{font-size:30px}
.stat{min-height:145px}
.stat-icon{width:67px;height:67px;flex-basis:67px}
.order-card{padding:0;overflow:hidden}
.order-card .order-head{padding:20px 23px;background:linear-gradient(135deg,#fafbff,#f3f6ff)}
.order-card .order-items{padding:0 23px}
.order-card .order-total{margin:17px 23px 23px}
.order-item-icon{box-shadow:inset 0 0 0 1px #e5e9f3}
.admin-title{padding:30px 32px;margin-bottom:20px;border-radius:29px}
.admin-title h1{font-size:32px}
.table-wrap{box-shadow:0 10px 30px rgba(34,50,86,.05)}
th{padding:16px 13px}
td{padding:16px 13px}
.btn{min-height:46px;border-radius:14px}
.form{max-width:540px}
.form-head .big-icon{width:88px;height:88px;border-radius:27px;font-size:39px}

/* dashboard sections */
.dashboard-shell{display:grid;grid-template-columns:230px 1fr;gap:24px;align-items:start}
.dashboard-sidebar{
 position:sticky;top:96px;background:rgba(255,255,255,.94);border:1px solid #e4e8f1;
 border-radius:25px;padding:15px;box-shadow:var(--shadow2)
}
.dashboard-sidebar .side-title{font-weight:900;padding:11px 12px;color:#303b53}
.dashboard-sidebar a{
 display:flex;align-items:center;gap:10px;padding:12px;border-radius:13px;
 text-decoration:none;color:#68748b;font-weight:800;font-size:13px;margin:3px 0
}
.dashboard-sidebar a:hover,.dashboard-sidebar a.active{background:#edf1ff;color:#4660cf}
.dashboard-main{min-width:0}
.product-meta{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:8px 0}
.qty-box{display:flex;align-items:center;gap:8px;background:#f3f5fa;border-radius:13px;padding:5px}
.qty-box button{
 width:30px;height:30px;border:0;border-radius:9px;background:#fff;cursor:pointer;font-weight:900
}
.qty-box span{min-width:25px;text-align:center;font-weight:900}
.search-box{
 display:flex;gap:10px;align-items:center;background:#fff;border:1px solid #e1e6ef;
 border-radius:17px;padding:7px 8px 7px 15px;box-shadow:0 7px 20px rgba(34,50,86,.05)
}
.search-box input{margin:0;border:0;background:transparent;box-shadow:none}
.search-box .btn{min-width:100px}
@media(max-width:900px){
 .dashboard-shell{grid-template-columns:1fr}
 .dashboard-sidebar{position:static;display:flex;overflow:auto;gap:5px}
 .dashboard-sidebar .side-title{display:none}
 .dashboard-sidebar a{white-space:nowrap}
}
@media(max-width:650px){
 .hero{padding:38px 23px;min-height:330px}
 .hero h1{font-size:34px}
 .hero p{font-size:15px}
 .hero:after{font-size:220px}
 .products-grid{grid-template-columns:1fr}
}
</style>

</head>

<body>
<nav class="navbar">
  <div class="nav-inner">
    <a class="brand" href="{{ url_for('home') }}">
      <span class="brand-icon">🛒</span>
      <span>سوپرمارکت</span>
    </a>
    <div class="nav-links">
      {% if session.get('role') == 'admin' %}
        <a class="{{ 'active' if active=='admin' else '' }}" href="{{ url_for('admin') }}">⚙️ پنل مدیریت</a>
        <a href="{{ url_for('logout') }}">🚪 خروج</a>
      {% elif session.get('role') == 'customer' %}
        <a class="{{ 'active' if active=='shop' else '' }}" href="{{ url_for('shop') }}">🏪 فروشگاه</a>
        <a class="{{ 'active' if active=='cart' else '' }}" href="{{ url_for('cart') }}">🛒 سبد خرید</a>
        <a class="{{ 'active' if active=='history' else '' }}" href="{{ url_for('history') }}">🧾 خریدهای من</a>
        <a href="{{ url_for('logout') }}">🚪 خروج</a>
      {% else %}
        <a href="{{ url_for('login') }}">🔐 ورود</a>
        <a href="{{ url_for('register') }}">📝 ساخت حساب</a>
      {% endif %}
    </div>
  </div>
</nav>

<main class="container">
{% with messages=get_flashed_messages(with_categories=true) %}
  {% for category,message in messages %}
    <div class="alert {{ category }}">{{ message }}</div>
  {% endfor %}
{% endwith %}
{{ content|safe }}
</main>

<div class="footer">سوپرمارکت آنلاین • مدیریت حساب، خرید و سفارش</div>

<script>
document.addEventListener("submit", function(e){
  const form=e.target;
  if(form.action && form.action.includes("/checkout")){
    const btn=form.querySelector('button[type="submit"]');
    if(btn){
      btn.disabled=true;
      btn.innerHTML="⏳ در حال انجام عملیات...";
    }
  }
});
</script>
</body>
</html>
"""


@app.route("/")
def home():
    if session.get("role") == "admin":
        return redirect(url_for("admin"))
    if session.get("role") == "customer":
        return redirect(url_for("shop"))

    content = """
    <section class="hero">
      <div class="hero-stat">
        <div class="mini">تجربه خرید</div>
        <strong>سریع • ساده • مرتب</strong>
        <div class="mini">با فاکتور و پیگیری سفارش</div>
      </div>
      <div class="hero-inner">
        <span class="hero-kicker">✨ فروشگاه مدرن و مدیریت کامل</span>
        <h1>همه‌چیز برای خرید، یکجا.</h1>
        <p>محصول انتخاب کن، سبدت را ببین، پرداخت کن و فاکتور حرفه‌ای تحویل بگیر.</p>
        <div class="actions">
          <a class="btn" href="/login">🔐 ورود به حساب</a>
          <a class="btn green" href="/register">📝 ساخت حساب</a>
        </div>
      </div>
    </section>

    <div class="grid" style="margin-top:20px">
      <div class="card stat">
        <div class="stat-icon">🛍️</div>
        <div><small>خرید آسان</small><h2>سبد خرید</h2></div>
      </div>
      <div class="card stat">
        <div class="stat-icon">🧾</div>
        <div><small>مرتب و قابل چاپ</small><h2>فاکتور خرید</h2></div>
      </div>
      <div class="card stat">
        <div class="stat-icon">⚙️</div>
        <div><small>کنترل توسط مدیر</small><h2>پنل مدیریت</h2></div>
      </div>
    </div>
    """
    return page("خانه", content)


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username=request.form.get("username","").strip()
        password=request.form.get("password","")

        if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:
            session.clear()
            session["role"]="admin"
            session["username"]=username
            return redirect(url_for("admin"))

        conn=get_db()
        user=conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        ).fetchone()
        conn.close()

        if user:
            session.clear()
            session["role"]="customer"
            session["username"]=username
            return redirect(url_for("shop"))

        flash("نام کاربری یا رمز عبور اشتباه است.","error")

    content="""
    <div class="card form">
      <div class="form-head">
        <div class="big-icon">🔐</div>
        <h2>ورود به حساب</h2>
        <p class="muted">برای ورود، اطلاعات حساب خود را وارد کنید.</p>
      </div>
      <form method="post">
        <label>نام کاربری</label>
        <input name="username" autocomplete="username" required>
        <label>رمز عبور</label>
        <input name="password" type="password" autocomplete="current-password" required>
        <button class="btn full">ورود</button>
      </form>
    </div>
    """
    return page("ورود",content)


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username=request.form.get("username","").strip()
        password=request.form.get("password","")

        if not username or not password:
            flash("اطلاعات را کامل وارد کنید.","error")
        elif username==ADMIN_USERNAME:
            flash("این نام کاربری مخصوص مدیر است.","error")
        else:
            conn=get_db()
            try:
                conn.execute(
                    "INSERT INTO users(username,password,balance,created_at) VALUES(?,?,0,?)",
                    (username,password,datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                flash("حساب ساخته شد. شارژ حساب فقط توسط مدیر انجام می‌شود.","success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                conn.close()
                flash("این نام کاربری قبلاً وجود دارد.","error")

    content="""
    <div class="card form">
      <div class="form-head">
        <div class="big-icon">📝</div>
        <h2>ساخت حساب</h2>
        <p class="muted">حساب خودت را بساز و از فروشگاه استفاده کن.</p>
      </div>
      <form method="post">
        <label>نام کاربری</label>
        <input name="username" required>
        <label>رمز عبور</label>
        <input name="password" type="password" required>
        <button class="btn green full">ساخت حساب</button>
      </form>
    </div>
    """
    return page("ساخت حساب",content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/shop")
def shop():
    if session.get("role")!="customer":
        return redirect(url_for("login"))

    conn=get_db()
    products=conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    user=conn.execute(
        "SELECT * FROM users WHERE username=?",
        (session["username"],)
    ).fetchone()
    conn.close()

    cards=""
    for p in products:
        if p["stock"]>0:
            action=f"""
            <form class="product-action" method="post" action="/cart/add/{p['id']}">
              <label>تعداد</label>
              <input type="number" name="quantity" value="1" min="1" max="{p['stock']}">
              <button class="btn full">🛒 افزودن به سبد</button>
            </form>
            """
        else:
            action='<div class="alert error" style="margin-top:auto">این محصول ناموجود است.</div>'

        cards+=f"""
        <article class="card product-card">
          <div class="product-art">🛍️</div>
          <div class="product-name">{p['name']}</div>
          <div class="price">{fmt(p['price'])} تومان</div>
          <span class="stock-pill">✓ موجودی: {fmt(p['stock'])} عدد</span>
          {action}
        </article>
        """

    if not cards:
        cards='<div class="card empty">📦 هنوز محصولی اضافه نشده است.</div>'

    content=f"""
    <div class="grid">
      <div class="card stat">
        <div class="stat-icon">👤</div>
        <div><small>مشتری</small><h2>{user['username']}</h2></div>
      </div>
      <div class="card stat">
        <div class="stat-icon">💰</div>
        <div><small>موجودی حساب</small><h2 class="balance">{fmt(user['balance'])} تومان</h2></div>
      </div>
    </div>

    <div class="section-title">
      <div><h2>📦 محصولات</h2><p>محصول موردنظر را انتخاب کن.</p></div>
    </div>
    <div class="products-grid">{cards}</div>
    """
    return page("فروشگاه",content,"shop")


@app.route("/cart/add/<int:product_id>",methods=["POST"])
def add_cart(product_id):
    if session.get("role")!="customer":
        return redirect(url_for("login"))

    try:
        quantity=int(request.form.get("quantity",1))
    except ValueError:
        quantity=0

    conn=get_db()
    product=conn.execute(
        "SELECT * FROM products WHERE id=?",(product_id,)
    ).fetchone()
    conn.close()

    if not product or quantity<=0 or quantity>product["stock"]:
        flash("تعداد یا محصول نامعتبر است.","error")
        return redirect(url_for("shop"))

    cart=session.get("cart",{})
    key=str(product_id)
    new_quantity=int(cart.get(key,0))+quantity

    if new_quantity>product["stock"]:
        flash("موجودی کافی نیست.","error")
    else:
        cart[key]=new_quantity
        session["cart"]=cart
        flash("محصول به سبد خرید اضافه شد.","success")

    return redirect(url_for("shop"))


@app.route("/cart")
def cart():
    if session.get("role")!="customer":
        return redirect(url_for("login"))

    cart_data=session.get("cart",{})
    conn=get_db()
    rows=[]
    total=0

    for pid,qty in cart_data.items():
        product=conn.execute(
            "SELECT * FROM products WHERE id=?",(pid,)
        ).fetchone()
        if product:
            row_total=product["price"]*qty
            total+=row_total
            rows.append((product,qty,row_total))

    user=conn.execute(
        "SELECT * FROM users WHERE username=?",(session["username"],)
    ).fetchone()
    conn.close()

    body=""
    for product,qty,row_total in rows:
        body+=f"""
        <tr>
          <td><b>{product['name']}</b></td>
          <td>{fmt(qty)}</td>
          <td>{fmt(product['price'])} تومان</td>
          <td><b>{fmt(row_total)} تومان</b></td>
          <td>
            <form method="post" action="/cart/remove/{product['id']}">
              <button class="btn red">حذف</button>
            </form>
          </td>
        </tr>
        """

    if not rows:
        body="<tr><td colspan='5' class='empty'>🛒 سبد خرید خالی است.</td></tr>"

    payment=""
    if rows:
        if user["balance"]>=total:
            payment="""
            <form method="post" action="/checkout">
              <button class="btn green full" type="submit">💳 پرداخت و ثبت سفارش</button>
            </form>
            """
        else:
            payment=f"""
            <div class="alert error">
              موجودی کافی نیست. مبلغ کمبود: <b>{fmt(total-user['balance'])} تومان</b>
            </div>
            """

    content=f"""
    <div class="card">
      <div class="section-title" style="margin-top:0">
        <div><h2>🛒 سبد خرید</h2><p>محصولات انتخاب‌شده را بررسی کن.</p></div>
        <div class="badge">موجودی: {fmt(user['balance'])} تومان</div>
      </div>
      <div class="table-wrap">
        <table>
          <tr><th>محصول</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th><th></th></tr>
          {body}
        </table>
      </div>
      <div class="order-total">
        <span>مبلغ کل</span>
        <strong>{fmt(total)} تومان</strong>
      </div>
      <div style="margin-top:16px">{payment}</div>
    </div>
    """
    return page("سبد خرید",content,"cart")


@app.route("/cart/remove/<int:product_id>",methods=["POST"])
def remove_cart(product_id):
    cart=session.get("cart",{})
    cart.pop(str(product_id),None)
    session["cart"]=cart
    return redirect(url_for("cart"))


@app.route("/checkout",methods=["POST"])
def checkout():
    if session.get("role")!="customer":
        return redirect(url_for("login"))

    cart=session.get("cart",{})
    if not cart:
        flash("سبد خرید خالی است.","error")
        return redirect(url_for("cart"))

    conn=get_db()
    user=conn.execute(
        "SELECT * FROM users WHERE username=?",(session["username"],)
    ).fetchone()

    items=[]
    total=0

    for pid,qty in cart.items():
        product=conn.execute(
            "SELECT * FROM products WHERE id=?",(pid,)
        ).fetchone()
        if not product or qty>product["stock"]:
            conn.close()
            flash("موجودی یکی از محصولات کافی نیست.","error")
            return redirect(url_for("cart"))
        row_total=product["price"]*qty
        total+=row_total
        items.append((product,qty,row_total))

    if user["balance"]<total:
        conn.close()
        flash("موجودی حساب کافی نیست.","error")
        return redirect(url_for("cart"))

    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_code="GW-"+uuid.uuid4().hex[:8].upper()

    conn.execute(
        "UPDATE users SET balance=balance-? WHERE username=?",
        (total,session["username"])
    )
    conn.execute(
        "UPDATE store SET money=money+?,total_sales=total_sales+? WHERE id=1",
        (total,total)
    )
    cur=conn.execute(
        """INSERT INTO purchases(username,total,status,created_at,order_code)
           VALUES(?,?,?,?,?)""",
        (session["username"],total,"در حال انجام عملیات",now,order_code)
    )
    purchase_id=cur.lastrowid

    for product,qty,row_total in items:
        conn.execute(
            "UPDATE products SET stock=stock-? WHERE id=?",
            (qty,product["id"])
        )
        conn.execute(
            """INSERT INTO purchase_items
            (purchase_id,product_name,quantity,unit_price,total)
            VALUES(?,?,?,?,?)""",
            (purchase_id,product["name"],qty,product["price"],row_total)
        )

    conn.commit()
    conn.close()

    session["cart"]={}
    flash(f"سفارش ثبت شد. کد سفارش: {order_code}","success")
    return redirect(url_for("history"))


@app.route("/history")
def history():
    if session.get("role")!="customer":
        return redirect(url_for("login"))

    conn=get_db()
    purchases=conn.execute(
        "SELECT * FROM purchases WHERE username=? ORDER BY id DESC",
        (session["username"],)
    ).fetchall()

    result=""
    for p in purchases:
        items=conn.execute(
            "SELECT * FROM purchase_items WHERE purchase_id=?",
            (p["id"],)
        ).fetchall()

        item_html=""
        for i in items:
            item_html+=f"""
            <div class="order-item">
              <div class="order-item-icon">🛍️</div>
              <div class="order-item-main">
                <b>{i['product_name']}</b>
                <div class="muted">تعداد: {fmt(i['quantity'])} عدد</div>
              </div>
              <strong>{fmt(i['total'])} تومان</strong>
            </div>
            """

        status_class="pending"
        if p["status"] in ["تحویل داده شد","تکمیل شده"]:
            status_class="done"
        elif p["status"]=="لغو شده":
            status_class="cancel"

        result+=f"""
        <div class="card order-card">
          <div class="order-head">
            <div>
              <h3 style="margin:0">🧾 سفارش #{p['id']}</h3>
              <div class="muted">{p['created_at']}</div>
            </div>
            {('<div class="status-box"><span class="spinner"></span>در حال انجام عملیات</div>' if p['status']=='در حال انجام عملیات' else '<span class="badge '+status_class+'">'+p['status']+'</span>')}
          </div>

          <div class="grid" style="margin-top:15px">
            <div>
              <span class="muted">کد سفارش</span>
              <h3 style="margin:3px 0">{p['order_code']}</h3>
            </div>
            <div>
              <span class="muted">مبلغ نهایی</span>
              <h3 style="margin:3px 0">{fmt(p['total'])} تومان</h3>
            </div>
          </div>

          <div class="order-items">{item_html}</div>

          <div class="actions">
            <a class="btn" href="/invoice/{p['id']}">🧾 مشاهده فاکتور</a>
          </div>
        </div>
        """

    conn.close()

    if not result:
        result='<div class="card empty">📜 هنوز خریدی ثبت نشده است.</div>'

    return page("خریدهای من","<div class='section-title'><div><h2>🧾 خریدهای من</h2><p>جزئیات سفارش‌ها و فاکتورها.</p></div></div>"+result,"history")


@app.route("/invoice/<int:purchase_id>")
def invoice(purchase_id):
    if session.get("role") not in ["customer","admin"]:
        return redirect(url_for("login"))

    conn=get_db()
    purchase=conn.execute(
        "SELECT * FROM purchases WHERE id=?",(purchase_id,)
    ).fetchone()

    if not purchase:
        conn.close()
        flash("فاکتور پیدا نشد.","error")
        return redirect(url_for("history"))

    if session.get("role")=="customer" and purchase["username"]!=session.get("username"):
        conn.close()
        flash("دسترسی به این فاکتور مجاز نیست.","error")
        return redirect(url_for("history"))

    items=conn.execute(
        "SELECT * FROM purchase_items WHERE purchase_id=?",
        (purchase_id,)
    ).fetchall()
    conn.close()

    rows=""
    for n,item in enumerate(items,1):
        rows+=f"""
        <tr>
          <td>{n}</td>
          <td><b>{item['product_name']}</b></td>
          <td>{fmt(item['quantity'])}</td>
          <td>{fmt(item['unit_price'])} تومان</td>
          <td><b>{fmt(item['total'])} تومان</b></td>
        </tr>
        """

    content=f"""
    <div class="invoice-page">
      <div class="invoice-card">
        <div class="invoice-top">
          <div>
            <div class="invoice-logo">🛒</div>
            <div class="invoice-title">فاکتور خرید</div>
            <div class="invoice-subtitle">رسید ثبت سفارش</div>
          </div>
          <div class="invoice-code">
            <span>کد سفارش</span>
            <strong>{purchase['order_code']}</strong>
          </div>
        </div>

        <div class="invoice-info">
          <div><span>مشتری</span><b>{purchase['username']}</b></div>
          <div><span>تاریخ و ساعت</span><b>{purchase['created_at']}</b></div>
          <div><span>وضعیت</span><b>{purchase['status']}</b></div>
        </div>

        <div class="table-wrap">
          <table class="invoice-table">
            <tr>
              <th>#</th><th>نام محصول</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th>
            </tr>
            {rows}
          </table>
        </div>

        <div class="invoice-total">
          <span>مبلغ نهایی</span>
          <strong>{fmt(purchase['total'])} تومان</strong>
        </div>

        <div class="invoice-footer">
          <span>از خرید شما سپاسگزاریم 🌟</span>
          <span>کد سفارش: {purchase['order_code']}</span>
        </div>

        <div class="actions no-print">
          <button class="btn" onclick="window.print()">🖨️ چاپ فاکتور</button>
          <a class="btn light" href="{url_for('history') if session.get('role')=='customer' else url_for('admin')}">بازگشت</a>
        </div>
      </div>
    </div>
    """
    return page("فاکتور خرید",content)


@app.route("/admin")
def admin():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    conn=get_db()
    products=conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    users=conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    purchases=conn.execute("SELECT * FROM purchases ORDER BY id DESC").fetchall()
    store=conn.execute("SELECT * FROM store WHERE id=1").fetchone()
    pending=conn.execute(
        "SELECT COUNT(*) AS c FROM purchases WHERE status='در حال انجام عملیات'"
    ).fetchone()["c"]
    conn.close()

    products_html=""
    for p in products:
        products_html+=f"""
        <tr>
          <td><b>{p['name']}</b></td>
          <td>
            <form method="post" action="/admin/product/edit/{p['id']}">
              <input name="price" value="{fmt(p['price'])}">
          </td>
          <td><input name="stock" value="{p['stock']}"></td>
          <td><button class="btn" type="submit">💾 ذخیره</button></form></td>
          <td>
            <form method="post" action="/admin/product/delete/{p['id']}">
              <button class="btn red">حذف</button>
            </form>
          </td>
        </tr>
        """

    if not products_html:
        products_html="<tr><td colspan='5' class='empty'>هنوز محصولی وجود ندارد.</td></tr>"

    users_html=""
    for u in users:
        users_html+=f"""
        <tr>
          <td><b>{u['username']}</b></td>
          <td>{fmt(u['balance'])} تومان</td>
          <td>
            <form method="post" action="/admin/user/balance">
              <input type="hidden" name="username" value="{u['username']}">
              <input name="amount" placeholder="مثلاً 50000">
              <button class="btn green" name="action" value="add">➕ شارژ</button>
              <button class="btn red" name="action" value="subtract">➖ کم</button>
            </form>
          </td>
        </tr>
        """

    purchases_html=""
    admin_conn=get_db()
    for p in purchases:
        items=admin_conn.execute(
            "SELECT * FROM purchase_items WHERE purchase_id=?",(p["id"],)
        ).fetchall()

        item_names="، ".join(
            f"{i['product_name']} × {i['quantity']}" for i in items
        ) or "بدون محصول"

        status_class="pending"
        if p["status"] in ["تحویل داده شد","تکمیل شده"]:
            status_class="done"
        elif p["status"]=="لغو شده":
            status_class="cancel"

        purchases_html+=f"""
        <tr>
          <td><b>{p['order_code']}</b></td>
          <td>{p['username']}</td>
          <td>{item_names}</td>
          <td>{fmt(p['total'])} تومان</td>
          <td>{('<div class="status-box"><span class="spinner"></span>در حال انجام عملیات</div>' if p['status']=='در حال انجام عملیات' else '<span class="badge '+status_class+'">'+p['status']+'</span>')}</td>
          <td>
            <form method="post" action="/admin/purchase/status/{p['id']}">
              <select name="status">
                <option {"selected" if p["status"]=="در حال انجام عملیات" else ""}>در حال انجام عملیات</option>
                <option {"selected" if p["status"]=="دیده شد" else ""}>دیده شد</option>
                <option {"selected" if p["status"]=="در حال آماده‌سازی" else ""}>در حال آماده‌سازی</option>
                <option {"selected" if p["status"]=="ارسال شد" else ""}>ارسال شد</option>
                <option {"selected" if p["status"]=="تحویل داده شد" else ""}>تحویل داده شد</option>
                <option {"selected" if p["status"]=="لغو شده" else ""}>لغو شده</option>
              </select>
              <button class="btn orange">ذخیره</button>
            </form>
          </td>
          <td><a class="btn light" href="/invoice/{p['id']}">🧾 فاکتور</a></td>
        </tr>
        """

    admin_conn.close()
    if not purchases_html:
        purchases_html="<tr><td colspan='7' class='empty'>هنوز خریدی ثبت نشده است.</td></tr>"

    content=f"""
    <div class="admin-title">
      <div>
        <h1>⚙️ مرکز مدیریت فروشگاه</h1>
        <p>محصولات، موجودی مشتریان، سفارش‌ها و فاکتورها را از اینجا کنترل کن.</p>
      </div>
      <div style="font-size:42px">📊</div>
    </div>

    <div class="grid">
      <div class="card stat"><div class="stat-icon">💰</div><div><small>پول فروشگاه</small><h2>{fmt(store['money'])}</h2></div></div>
      <div class="card stat"><div class="stat-icon">📈</div><div><small>کل فروش</small><h2>{fmt(store['total_sales'])}</h2></div></div>
      <div class="card stat"><div class="stat-icon">👥</div><div><small>مشتریان</small><h2>{len(users)}</h2></div></div>
      <div class="card stat"><div class="stat-icon">⏳</div><div><small>در حال انجام</small><h2>{pending}</h2></div></div>
    </div>

    <div class="card">
      <h2>➕ افزودن محصول</h2>
      <form method="post" action="/admin/product/add">
        <div class="grid">
          <div><label>نام محصول</label><input name="name" required></div>
          <div><label>قیمت</label><input name="price" placeholder="50000" required></div>
          <div><label>موجودی</label><input name="stock" placeholder="20" required></div>
        </div>
        <button class="btn green">➕ افزودن محصول</button>
      </form>
    </div>

    <div class="card">
      <h2>📦 محصولات</h2>
      <div class="table-wrap">
        <table>
          <tr><th>نام</th><th>قیمت</th><th>موجودی</th><th>ویرایش</th><th>حذف</th></tr>
          {products_html}
        </table>
      </div>
    </div>

    <div class="card">
      <h2>👥 حساب مشتریان</h2>
      <div class="table-wrap">
        <table>
          <tr><th>نام کاربری</th><th>موجودی</th><th>تغییر موجودی</th></tr>
          {users_html}
        </table>
      </div>
    </div>

    <div class="card">
      <div class="section-title" style="margin-top:0">
        <div><h2>📒 دفتر سفارش‌ها</h2><p>نام محصول، تعداد، کد سفارش و وضعیت را می‌بینی.</p></div>
      </div>
      <div class="table-wrap">
        <table>
          <tr><th>کد</th><th>مشتری</th><th>محصولات</th><th>مبلغ</th><th>وضعیت</th><th>تغییر وضعیت</th><th>فاکتور</th></tr>
          {purchases_html}
        </table>
      </div>
    </div>
    """
    return page("پنل مدیریت",content,"admin")


@app.route("/admin/product/add",methods=["POST"])
def product_add():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    name=request.form.get("name","").strip()
    try:
        price=int(request.form.get("price","0").replace(",",""))
        stock=int(request.form.get("stock","0").replace(",",""))
    except ValueError:
        price,stock=0,-1

    if not name or price<=0 or stock<0:
        flash("اطلاعات محصول نامعتبر است.","error")
        return redirect(url_for("admin"))

    conn=get_db()
    try:
        conn.execute(
            "INSERT INTO products(name,price,stock) VALUES(?,?,?)",
            (name,price,stock)
        )
        conn.commit()
        flash("محصول اضافه شد.","success")
    except sqlite3.IntegrityError:
        flash("این محصول قبلاً وجود دارد.","error")
    conn.close()
    return redirect(url_for("admin"))


@app.route("/admin/product/edit/<int:product_id>",methods=["POST"])
def product_edit(product_id):
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    try:
        price=int(request.form.get("price","0").replace(",",""))
        stock=int(request.form.get("stock","0").replace(",",""))
    except ValueError:
        flash("قیمت یا موجودی نامعتبر است.","error")
        return redirect(url_for("admin"))

    if price<=0 or stock<0:
        flash("قیمت یا موجودی نامعتبر است.","error")
        return redirect(url_for("admin"))

    conn=get_db()
    conn.execute(
        "UPDATE products SET price=?,stock=? WHERE id=?",
        (price,stock,product_id)
    )
    conn.commit()
    conn.close()
    flash("محصول ویرایش شد.","success")
    return redirect(url_for("admin"))


@app.route("/admin/product/delete/<int:product_id>",methods=["POST"])
def product_delete(product_id):
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    conn=get_db()
    conn.execute("DELETE FROM products WHERE id=?",(product_id,))
    conn.commit()
    conn.close()
    flash("محصول حذف شد.","success")
    return redirect(url_for("admin"))


@app.route("/admin/user/balance",methods=["POST"])
def user_balance():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    username=request.form.get("username","")
    action=request.form.get("action")

    try:
        amount=int(request.form.get("amount","0").replace(",",""))
    except ValueError:
        amount=0

    conn=get_db()
    user=conn.execute(
        "SELECT * FROM users WHERE username=?",(username,)
    ).fetchone()

    if not user or amount<=0:
        conn.close()
        flash("حساب یا مبلغ نامعتبر است.","error")
        return redirect(url_for("admin"))

    if action=="add":
        conn.execute(
            "UPDATE users SET balance=balance+? WHERE username=?",
            (amount,username)
        )
    elif action=="subtract":
        if amount>user["balance"]:
            conn.close()
            flash("مبلغ بیشتر از موجودی مشتری است.","error")
            return redirect(url_for("admin"))
        conn.execute(
            "UPDATE users SET balance=balance-? WHERE username=?",
            (amount,username)
        )

    conn.commit()
    conn.close()
    flash("موجودی تغییر کرد.","success")
    return redirect(url_for("admin"))


@app.route("/admin/purchase/status/<int:purchase_id>",methods=["POST"])
def purchase_status(purchase_id):
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    allowed=[
        "در حال انجام عملیات","دیده شد","در حال آماده‌سازی",
        "ارسال شد","تحویل داده شد","لغو شده"
    ]
    status=request.form.get("status","در حال انجام عملیات")
    if status not in allowed:
        status="در حال انجام عملیات"

    conn=get_db()
    conn.execute(
        "UPDATE purchases SET status=? WHERE id=?",
        (status,purchase_id)
    )
    conn.commit()
    conn.close()
    flash("وضعیت سفارش تغییر کرد.","success")
    return redirect(url_for("admin"))


init_db()

if __name__=="__main__":
    print("="*42)
    print("   سوپرمارکت وب اجرا شد")
    print("   http://127.0.0.1:5000")
    print("="*42)
    app.run(host="127.0.0.1",port=5000,debug=True)
