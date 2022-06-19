from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import sqlite3
from random import choice, shuffle

app = FastAPI()
db = sqlite3.connect("data3__.db")

cur = db.cursor()
MEMES_COUNT = cur.execute("SELECT COUNT(*) FROM memes").fetchone()[0]


async def check_id(id: int) -> bool:
    return 0 < id < MEMES_COUNT


async def get_random_id(most_recommended: dict = None) -> int:
    not_weighted = [i for i in range(1, MEMES_COUNT+1)]

    if most_recommended is not None:
        weighted = not_weighted + [most_recommended["id"]] * \
            int(most_recommended["score"] / (1 / MEMES_COUNT))
        shuffle(weighted)

        return choice(weighted)
    return choice(not_weighted)


@app.get("/")
async def root(id: int = None):
    if id is None:
        params = {"id": 27, "score": 0.65}
        meme_id = await get_random_id(params)
    else:
        meme_id = id

    if not await check_id(meme_id):
        return {"message": "Incorrect id"}

    res = cur.execute(f"SELECT * FROM memes WHERE id={meme_id}").fetchone()
    out = {"id": res[0], "url": res[4], "name": res[2].strip(), "likes": res[5],
           "skips": res[6]}

    return out


@app.get("/like/{meme_id}")
async def like(meme_id: int):
    if not await check_id(meme_id):
        return {"message": "Incorrect id"}
    cur.execute(f"UPDATE memes SET likes = likes + 1 WHERE id = {meme_id}")

    res = cur.execute(f"SELECT * FROM memes WHERE id={meme_id}").fetchone()
    cur.execute(f"INSERT INTO logs (id, url, date, likes, skips, isLiked) VALUES (?, ?, ?, ?, ?, 1)",
                (meme_id, res[4], datetime.now(), res[5], res[6]))

    db.commit()

    return {"message": f"Id {meme_id} successfully liked"}


@app.get("/skip/{meme_id}")
async def skip(meme_id: int):
    if not await check_id(meme_id):
        return {"message": "Incorrect id"}
    cur.execute(f"UPDATE memes SET skips = skips + 1 WHERE id = {meme_id}")

    res = cur.execute(f"SELECT * FROM memes WHERE id={meme_id}").fetchone()
    cur.execute(f"INSERT INTO logs (id, url, date, likes, skips, isLiked) VALUES (?, ?, ?, ?, ?, 0)",
                (meme_id, res[4], datetime.now(), res[5], res[6]))
    db.commit()

    return {"message": f"Id {meme_id} successfully skiped"}


@app.get("/task10", response_class=PlainTextResponse)
async def task10():
    out = ""
    res = cur.execute(
        "SELECT * FROM memes WHERE id BETWEEN 1 AND 64").fetchall()

    for (id, _, name, _, url, likes, _, _, _) in res:
        out += f"[ {id} ] : {url}, Автор: {name}, {likes} ❤️\n"

    return out.rstrip()


@app.get("/stats/{pretty}")
async def stats(pretty: bool, secret: str = None):
    if secret != "1337pa$$word":
        return {"message": "Not autorized"}

    req_top_five = cur.execute(
        "SELECT * FROM memes ORDER BY likes DESC LIMIT 5").fetchall()

    last_five_actions = cur.execute(
        "SELECT * FROM logs ORDER BY date DESC LIMIT 5").fetchall()

    if pretty:
        out = "Топ-5 мемов:\n"
        for (id, _, name, _, url, likes, _, _, _) in req_top_five:
            out += f"[ {id} ] : {url}, Автор: {name}, {likes} ❤️\n"

        out += "\nПоследние пять действий:\n"
        for (id, url, date, likes, skips, isLiked) in last_five_actions:
            print((id, url, date, likes, skips, isLiked))
            out += f"[ {id}, {date} ] : {url}, {likes} лайк(-ов), {skips} скип(-ов), Тип - {'Лайк' if isLiked else 'Скип'}\n"

        return PlainTextResponse(content=out)

    return {"top": req_top_five, "history": last_five_actions}
