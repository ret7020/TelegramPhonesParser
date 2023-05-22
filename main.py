from config import *
import sqlite3
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import datetime
import tqdm


def process_group(target, sqlite_connection, cursor):
    try:
        all_participants = client.get_participants(target, aggressive=True)
    except:
        return

    for user in tqdm.tqdm(all_participants):
        if user.id not in black_list_users:
            if user.phone:
                can_append = True
                this_phone = cursor.execute(
                    "SELECT * FROM `users` WHERE `phone` == ?", (user.phone, )).fetchall()
                for row in this_phone:
                    tg_id, name, phone, username = row[1], row[2], row[3], row[4]
                    if tg_id == user.id and name == f"{user.first_name} {user.last_name if user.last_name else ''}" and phone == user.phone and username == user.username:
                        can_append = False
                if can_append:
                    cursor.execute("INSERT INTO `users` (`telegram_id`, `name`, `phone`, `username`, `create_date`) VALUES (?, ?, ?, ?, ?)", (
                        user.id,
                        f"{user.first_name} {user.last_name if user.last_name else ''}",
                        user.phone,
                        user.username,
                        datetime.datetime.now()
                    ))
                    sqlite_connection.commit()


last_date = None
chunk_size = 200
groups = []

# Channel parse error
sqlite_connection = sqlite3.connect('db')
cursor = sqlite_connection.cursor()

with TelegramClient("test", api_id, api_hash) as client:
    result = client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    groups.extend(result.chats)

    target = None
    if not auto_parse:  # Manual group parse
        for g in groups:
            print(f"{g.title} - {g.id}")

        index = int(input("Choose a group to scrape members from: "))
        for g in groups:
            if g.id == index:
                target = g
                break

        if not target:
            print("Can't find such group")
            exit(1)
        process_group(target, sqlite_connection, cursor)
    else:  # Auto parse all groups
        for group in tqdm.tqdm(groups):
            process_group(group.id, sqlite_connection, cursor)


cursor.close()
sqlite_connection.close()
