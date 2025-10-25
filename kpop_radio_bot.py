import discord
from keep_alive import keep_alive
keep_alive()
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import asyncio
import os

# ===== CẤU HÌNH BOT =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC KPOP NGẪU NHIÊN =====
KPOP_SONGS = [
    "https://www.youtube.com/watch?v=Ng01EK5ePSU&list=RDNg01EK5ePSU&start_radio=1",
    "https://www.youtube.com/watch?v=SKWxqYvqmmA&list=RDSKWxqYvqmmA&start_radio=1",
    "https://www.youtube.com/watch?v=Ir4GwBhPNt0&list=RDIr4GwBhPNt0&start_radio=1",
    # Thêm link YouTube khác nếu muốn
]

# ===== HÀM PHÁT NHẠC NGẪU NHIÊN VỚI EMBED =====
def play_random_kpop(vc, interaction=None):
    url = random.choice(KPOP_SONGS)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies_www.youtube.com.txt'  # <-- thêm cookie
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin nhạc: {e}")
            return

        audio_url = info['url']
        title = info.get('title', 'Unknown Title')
        uploader = info.get('uploader', 'Unknown Artist')
        thumbnail = info.get('thumbnail')

    def after_play(error):
        if error:
            print(f"Player error: {error}")
        else:
            play_random_kpop(vc, interaction)  # Phát bài khác ngẫu nhiên

    if vc.is_playing():
        vc.stop()
    vc.play(
        discord.FFmpegPCMAudio(
            audio_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        ),
        after=after_play
    )

    # Gửi Embed tên bài + nghệ sĩ
    if interaction:
        embed = discord.Embed(
            title=title,
            description=f"🎤 {uploader}",
            color=0xFF69B4
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        asyncio.create_task(interaction.followup.send(embed=embed))

# ===== SỰ KIỆN ON_READY =====
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

    if interaction.user.voice is None:
        await interaction.followup.send("❌ Bạn phải vào kênh thoại trước!", ephemeral=True)
        return

    voice_channel = interaction.user.voice.channel

    if interaction.guild.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = interaction.guild.voice_client

    play_random_kpop(vc, interaction)

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
