import requests
import xml.etree.ElementTree as ET
import sqlite3
from datetime import datetime

groups = [
"NMIXX",
"IVE",
"NewJeans",
"LE_SSERAFIM",
"aespa",
"BLACKPINK"
]


def update_news():

    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT,
        title TEXT,
        link TEXT UNIQUE,
        image TEXT,
        favorite INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    for group in groups:

        url = f"https://news.google.com/rss/search?q={group}&hl=ja&gl=JP&ceid=JP:ja"

        try:
            response = requests.get(url, timeout=10)
        except:
            continue

        root = ET.fromstring(response.content)

        for item in root.findall(".//item")[:10]:

            title = item.find("title").text
            link = item.find("link").text

            media = item.find("{http://search.yahoo.com/mrss/}thumbnail")
            image = media.attrib["url"] if media is not None else ""

            try:

                cursor.execute("""
                INSERT INTO news
                (group_name, title, link, image, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    group,
                    title,
                    link,
                    image,
                    datetime.now()
                ))

            except sqlite3.IntegrityError:
                pass

    conn.commit()
    conn.close()