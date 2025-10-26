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

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": "www.youtube.com_cookies"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin nhạc: {e}")
            return

        audio_url = info["url"]
        title = info.get("title", "Unknown Title")
        uploader = info.get("uploader", "Unknown Artist")
        thumbnail = info.get("thumbnail")

    def after_play(err):
        if err:
            print(f"Lỗi phát nhạc: {err}")
        else:
            play_kpop(vc, interaction)  # tự phát bài khác

    if vc.is_playing():
        vc.stop()

    vc.play(
        discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        after=after_play
    )

    # === Embed bài nhạc + lyrics ===
    lyrics = get_lyrics(title)
    embed = discord.Embed(
        title=f"🎵 {title}",
        description=f"👩‍🎤 {uploader}\n\n📜 **Lyrics:**\n{lyrics}",
        color=0xFF69B4
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    asyncio.create_task(interaction.followup.send(embed=embed))

# ===== SỰ KIỆN =====
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

    # Lấy kênh thoại chill-room
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
