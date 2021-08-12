import json
import requests
import sqlite3
import time
import ipaddress
import sys
from telegram import Bot

games = {
    "gmod": "https://api.facepunch.com/api/public/manifest/?public_key=RWsOQQrO860EaGY3qPsSsBQSev3gNO0KrcF3kv4Rl5frjE9OuUKQgAsRutxMZ4aU",
    "rust": "https://api.facepunch.com/api/public/manifest/?public_key=j0VF6sNnzn9rwt9qTZtI02zTYK8PRdN1"
}

if len(sys.argv) != 2:
    print("program GAME")
    sys.exit()

if sys.argv[1] not in games:
    print("Unknown game")
    sys.exit()

game = sys.argv[1]

subnets = [
    ipaddress.ip_network("43.250.192.0/24"),
    ipaddress.ip_network("43.250.193.0/24"),
]

channel_chat_id = "CHAT_ID_START_WITH_MINUS"
bot_token = "BOT_TOKEN"
tgbot = Bot(token=bot_token)

sqlite3_conn = sqlite3.connect('blc.db')
db_cursor = sqlite3_conn.cursor()
db_cursor.execute("CREATE TABLE IF NOT EXISTS ips (ip integer, game text, created_at integer)")
sqlite3_conn.commit()


response = requests.get(games[game])

if (response.status_code == 200):
    manifest = json.loads(response.text)
    banneds = manifest["Servers"]["Banned"]
    new_banneds = []

    sql = "SELECT ip FROM ips WHERE game = ?"
    db_cursor.execute(sql, [(game)])
    rows = db_cursor.fetchall()
    current_banneds = []

    for row in rows:
        current_banneds.append(row[0])

    for banned in banneds:
        try:
            if banned[len(banned)-1] == "*":
                banned = banned[:-1] + "0"
            
            ipaddr = ipaddress.IPv4Address(banned)
            
            if (int(ipaddr) not in current_banneds):
                new_banneds.append([int(ipaddr), game, time.time()])
                for subnet in subnets:
                    if ipaddr in subnet:
                        if ipaddr == subnet.network_address:
                            tg_message = "Banned subnet: {subnet}\nGame: {game}".format(subnet = str(subnet), game = game)
                        else:
                            tg_message = "Banned address: {ip}\nSubnet: {subnet}\nGame: {game}".format(ip = str(ipaddr), subnet = str(subnet), game = game)
                        tgbot.send_message(chat_id = channel_chat_id, text = tg_message)
        except:
            continue

    if new_banneds:
        print("New banned ips count: " + str(len(new_banneds)))
        db_cursor.executemany("INSERT INTO ips (ip, game, created_at) VALUES (?, ?, ?)", new_banneds)
        sqlite3_conn.commit()

    else:
        print("No new banned IPs")
else:
    print("Response code {code}".format(code = response.status_code))