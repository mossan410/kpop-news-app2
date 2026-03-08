from flask import Flask, render_template, redirect, request, make_response
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from scrape import update_news
import atexit

app = Flask(__name__)

# -----------------
# DB取得
# -----------------
def get_news():

    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, group_name, title, link, image, favorite
        FROM news
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# -----------------
# トップページ
# -----------------
@app.route("/", methods=["GET"])
def index():

    news_list = get_news()

    group_names = sorted(list(set(n[1] for n in news_list)))

    selected_groups = request.args.getlist("group")

    if not selected_groups:

        cookie_groups = request.cookies.get("groups")

        if cookie_groups:
            selected_groups = cookie_groups.split(",")
        else:
            selected_groups = group_names

    groups = {}

    for news in news_list:

        group = news[1]

        if group in selected_groups:

            if group not in groups:
                groups[group] = []

            groups[group].append(news)

    resp = make_response(render_template(
        "index.html",
        groups=groups,
        group_names=group_names,
        selected_groups=selected_groups
    ))

    resp.set_cookie("groups", ",".join(selected_groups))

    return resp


# -----------------
# お気に入り切替
# -----------------
@app.route("/favorite/<int:news_id>")
def favorite(news_id):

    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute("SELECT favorite FROM news WHERE id=?", (news_id,))
    fav = cursor.fetchone()[0]

    new_fav = 0 if fav == 1 else 1

    cursor.execute(
        "UPDATE news SET favorite=? WHERE id=?",
        (new_fav, news_id)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# -----------------
# お気に入りページ
# -----------------
@app.route("/favorites")
def favorites():

    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, group_name, title, link, image, favorite
        FROM news
        WHERE favorite=1
        ORDER BY id DESC
    """)

    fav_news = cursor.fetchall()

    conn.close()

    return render_template(
        "favorites.html",
        news_list=fav_news
    )


# -----------------
# 手動更新
# -----------------
@app.route("/update")
def manual_update():

    update_news()
    return redirect("/")


# -----------------
# 自動更新
# -----------------
scheduler = BackgroundScheduler()
scheduler.add_job(update_news, "interval", hours=1)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":

    update_news()

    app.run(debug=True)