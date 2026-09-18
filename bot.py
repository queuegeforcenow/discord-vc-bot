import os
import asyncio
import threading

import discord
from discord.ext import commands
from flask import Flask

# =========================
# Environment Variables
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

if not VOICE_CHANNEL_ID:
    raise RuntimeError("VOICE_CHANNEL_ID が設定されていません")

VOICE_CHANNEL_ID = int(VOICE_CHANNEL_ID)

# =========================
# HTTP Server
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Discord VC Bot is running!", 200


@app.route("/health")
def health():
    return "OK", 200


def run_web():
    port = int(os.getenv("PORT", "8000"))

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# Discord Bot
# =========================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


async def keep_voice_connected():
    await bot.wait_until_ready()

    while not bot.is_closed():

        try:
            voice = discord.utils.get(
                bot.voice_clients
            )

            # =========================
            # すでに接続中
            # =========================

            if voice and voice.is_connected():
                await asyncio.sleep(15)
                continue

            # =========================
            # VC取得
            # =========================

            channel = bot.get_channel(
                VOICE_CHANNEL_ID
            )

            # キャッシュに無い場合
            if channel is None:

                try:
                    channel = await bot.fetch_channel(
                        VOICE_CHANNEL_ID
                    )
                except Exception as e:
                    print(
                        f"VC取得失敗: {e}"
                    )

                    await asyncio.sleep(15)
                    continue

            # =========================
            # VC接続
            # =========================

            print(
                f"VC接続開始: {channel.name}"
            )

            await channel.connect(
                reconnect=True
            )

            print(
                f"VC接続完了: {channel.name}"
            )

        except asyncio.CancelledError:
            break

        except Exception as e:

            print(
                f"VC接続エラー: {e}"
            )

            await asyncio.sleep(10)


# =========================
# Bot Ready
# =========================

@bot.event
async def on_ready():

    print("==============================")
    print(f"ログイン成功: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"VC ID: {VOICE_CHANNEL_ID}")
    print("==============================")

    # 二重起動防止
    if not hasattr(bot, "voice_task"):

        bot.voice_task = asyncio.create_task(
            keep_voice_connected()
        )


# =========================
# 起動
# =========================

def main():

    # HTTPサーバー
    web_thread = threading.Thread(
        target=run_web,
        daemon=True
    )

    web_thread.start()

    print("Web server started")

    # Discord Bot
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
