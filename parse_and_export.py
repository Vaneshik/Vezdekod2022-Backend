import sqlite3
import vk_api
from datetime import datetime


def init_database() -> sqlite3.Connection:
    sqlite3_db = sqlite3.connect('data2.db')

    query = '''
    CREATE TABLE memes (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name TEXT,
        url text NOT NULL UNIQUE,
        short_url text NOT NULL UNIQUE,
        likes INTEGER NOT NULL,
        skips INTEGER, 
        date timestamp NOT NULL,
        likes_changed INTEGER);
    '''

    cur = sqlite3_db.cursor()
    cur.execute(query)
    sqlite3_db.commit()
    cur.close()

    return sqlite3_db


def get_api(login: str, password: str) -> vk_api.vk_api.VkApiMethod:
    vk_session = vk_api.VkApi(login, password)
    vk_session.auth()

    return vk_session.get_api()


def get_pool(vk: vk_api.vk_api.VkApiMethod, owner_album: list) -> list:
    out = []

    for owner, album in owner_album:
        out += vk.photos.get(owner_id=owner, album_id=album,
                             extended=1, count=500)["items"]

    return out


def parse_data(vk: vk_api.vk_api.VkApiMethod, pool: list) -> list:
    out = []

    for photo_obj in pool:
        temp = {"url": "", "short_url": "",
                "likes": 0, "user_id": 0, "name": "", "date": ""}

        sizes = photo_obj["sizes"]

        url_best_size = [i for i in sizes if i["type"] == "x"][0]["url"]
        short_url = vk.utils.getShortLink(url=url_best_size)["short_url"]

        if photo_obj["user_id"] != 100:
            user_info = vk.users.get(user_ids=photo_obj["user_id"])[0]
            name = f'{user_info["first_name"]} {user_info["last_name"]}'
        else:
            name = "localhost"
            photo_obj["user_id"] = 46453123

        temp["url"] = url_best_size
        temp["short_url"] = short_url
        temp["likes"] = photo_obj["likes"]["count"]
        temp["user_id"] = photo_obj["user_id"]
        temp["name"] = name
        temp["date"] = datetime.now()

        print(temp)
        out.append(temp)

    return out


def export_in_db(db: sqlite3.Connection, data: list) -> None:
    cur = db.cursor()

    for item in data:
        query = f"""
        INSERT INTO memes (url, short_url, likes, user_id, name, skips, date)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        """

        cur.execute(query, (item['url'], item['short_url'],
                    item['likes'], item['user_id'], item['name'], item["date"]))

    db.commit()
    cur.close()


def main():
    sqlite3_db = init_database()

    vk = get_api("login", "password")  # INSERT YOUR TOKEN

    owner_album = [
        (-197700721, 284717200),
        (-46453123, 166262020),
    ]

    memes_pool = get_pool(vk, owner_album)
    to_export = parse_data(vk, memes_pool)

    export_in_db(sqlite3_db, to_export)

    print("Готово!")


if __name__ == "__main__":
    main()
