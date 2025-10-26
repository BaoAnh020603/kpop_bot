import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import asyncio
import os
import requests
from keep_alive import keep_alive

keep_alive()

# ===== CẤU HÌNH BOT =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC KPOP NGẪU NHIÊN =====
KPOP_SONGS = [
    "https://www.youtube.com/watch?v=Ng01EK5ePSU",
    "https://www.youtube.com/watch?v=SKWxqYvqmmA",
    "https://www.youtube.com/watch?v=Ir4GwBhPNt0",
    "https://www.youtube.com/watch?v=Bjm920Fyo34",
    "https://www.youtube.com/watch?v=5UQzXbizT-s",
    "https://www.youtube.com/watch?v=xQk_hnuRejE",
    "https://www.youtube.com/watch?v=KBRJ3KMQZ18",
    "https://www.youtube.com/watch?v=lmvOwd2j_1Q",
    "https://www.youtube.com/watch?v=lqCM7xQozmY",
]

# ===== HÀM LẤY LYRICS =====
def get_lyrics(query: str):
    try:
        resp = requests.get(f"https://some-random-api.com/lyrics?title={query}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("lyrics")[:1500] + "..."  # Giới hạn độ dài
    except Exception:
        pass
    return "Không tìm thấy lời bài hát 😢"

# ===== HÀM PHÁT NHẠC =====
def play_kpop(vc, interaction=None):
    url = random.choice(KPOP_SONGS)

    # Tạo file cookies tạm từ ENV VAR nếu chưa có
    cookie_file = "www.youtube.com_cookies.txt"
    if not os.path.exists(cookie_file):
        cookies_content = os.environ.get("YOUTUBE_COOKIES")
        if not cookies_content:
            if interaction:
                asyncio.create_task(interaction.followup.send("❌ Biến môi trường YOUTUBE_COOKIES chưa được thiết lập!"))
            return
        with open(cookie_file, "w", encoding="utf-8") as f:
            f.write(cookies_content)

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": cookie_file,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Referer": "https://www.youtube.com"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader", "Unknown Artist")
            thumbnail = info.get("thumbnail")
    except Exception as e:
        print(f"❌ Lỗi khi lấy thông tin nhạc ({url}): {e}")
        # Thử bài khác
        play_kpop(vc, interaction)
        return

    def after_play(err):
        if err:
            print(f"❌ Lỗi phát nhạc: {err}")
        play_kpop(vc, interaction)

    if vc.is_playing():
        vc.stop()

    try:
        vc.play(
            discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            ),
            after=after_play
        )
    except Exception as e:
        print(f"❌ Lỗi khi phát nhạc: {e}")
        play_kpop(vc, interaction)
        return

    # Embed nhạc + lyrics
    lyrics = get_lyrics(title)
    embed = discord.Embed(
        title=f"🎵 {title}",
        description=f"👩‍🎤 {uploader}\n\n📜 **Lyrics:**\n{lyrics}",
        color=0xFF69B4
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if interaction:
        asyncio.create_task(interaction.followup.send(embed=embed))

# ===== SỰ KIỆN BOT =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")

# ===== LỆNH /play =====
@bot.tree.command(name="play", description="Phát nhạc KPop ngẫu nhiên 🎶")
async def play(interaction: discord.Interaction):
    await interaction.response.defer()
    guild = interaction.guild

    voice_channel = discord.utils.get(guild.voice_channels, name="🎧│chill-room")
    if not voice_channel:
        await interaction.followup.send("❌ Không tìm thấy kênh thoại '🎧│chill-room'!", ephemeral=True)
        return

    vc = guild.voice_client
    if vc is None:
        vc = await voice_channel.connect()

    play_kpop(vc, interaction)

# ===== LỆNH /next =====
@bot.tree.command(name="next", description="Chuyển sang bài tiếp theo ⏭️")
async def next_song(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.followup.send("⏭️ Đang chuyển sang bài mới...")
    else:
        await interaction.followup.send("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== LỆNH /pause =====
@bot.tree.command(name="pause", description="Tạm dừng nhạc ⏸️")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== LỆNH /resume =====
@bot.tree.command(name="resume", description="Tiếp tục phát nhạc ▶️")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Tiếp tục phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang tạm dừng.", ephemeral=True)

# ===== LỆNH /stop =====
@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("🛑 Đã dừng nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== LỆNH /leave =====
@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời khỏi kênh thoại.")
    else:
        await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)

# ===== CHẠY BOT =====
bot.run(os.environ["DISCORD_TOKEN"])
