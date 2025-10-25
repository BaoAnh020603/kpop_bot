import discord
from keep_alive import keep_alive
keep_alive()
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import asyncio

# ===== CẤU HÌNH BOT =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC KPOP NGẪU NHIÊN =====
KPOP_SONGS = [
    "https://www.youtube.com/watch?v=pcKR0LPwoYs&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=1",
    "https://www.youtube.com/watch?v=6GC8JF2FOgA&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=2",
    "https://www.youtube.com/watch?v=fTc5tuEn6_U&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=3",
    "https://www.youtube.com/watch?v=XyzaMpAVm3s&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=4",
    "https://www.youtube.com/watch?v=YmC53o2_gWk&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=5",
    "https://www.youtube.com/watch?v=SdHQkkRc-hc&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=6",
    "https://www.youtube.com/watch?v=W0cs6ciCt_k&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=7",
    "https://www.youtube.com/watch?v=O0StKlRHVeE&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=8",
    "https://www.youtube.com/watch?v=JvjWy4saR08&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=9",
    "https://www.youtube.com/watch?v=N5ShoQimivM&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=10",
    "https://www.youtube.com/watch?v=aE0eV2YR51k&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=11",
    "https://www.youtube.com/watch?v=A1aRHQ6EnXE&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=12",
    "https://www.youtube.com/watch?v=ToASX6axGuw&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=13",
    "https://www.youtube.com/watch?v=FFmdTU4Cpr8&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=14",
    "https://www.youtube.com/watch?v=qMWXVc3WAYs&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=16",
    "https://www.youtube.com/watch?v=uLfLbtulKZc&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=17",
    "https://www.youtube.com/watch?v=Z9b0Hj-BfaM&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=18",
    "https://www.youtube.com/watch?v=3DOkxQ3HDXE&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=19",
    "https://www.youtube.com/watch?v=8Q2mth2bX10&list=PL39Vgo021gjfHis9mCiE7XOApWaMlUxXY&index=20",
    # Thêm link YouTube khác
]

# ===== HÀM PHÁT NHẠC NGẪU NHIÊN VỚI EMBED =====
def play_random_kpop(vc, interaction=None):
    url = random.choice(KPOP_SONGS)

  ydl_opts = {
    "format": "bestaudio",
    "cookiefile": "cookies.txt",
    "quiet": True,
    "noplaylist": True,
}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        title = info.get('title', 'Unknown Title')
        uploader = info.get('uploader', 'Unknown Artist')
        thumbnail = info.get('thumbnail')

    def after_play(error):
        if error:
            print(f"Player error: {error}")
        else:
            play_random_kpop(vc, interaction)  # Phát bài khác ngẫu nhiên

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
import os
bot.run(os.environ["DISCORD_TOKEN"])
