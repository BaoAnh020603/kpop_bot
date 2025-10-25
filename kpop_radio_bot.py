import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import random
import asyncio
import os
import aiohttp
from keep_alive import keep_alive

# ====== CẤU HÌNH BOT ======
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Tên kênh thoại mà bot sẽ tự động vào
VOICE_CHANNEL_NAME = "🎧│chill-room"

# Danh sách bài KPop
KPOP_SONGS = [
    "https://www.youtube.com/watch?v=Ng01EK5ePSU&list=RDNg01EK5ePSU&start_radio=1",
    "https://www.youtube.com/watch?v=SKWxqYvqmmA&list=RDSKWxqYvqmmA&start_radio=1",
    "https://www.youtube.com/watch?v=Ir4GwBhPNt0&list=RDIr4GwBhPNt0&start_radio=1",
    "https://www.youtube.com/watch?v=Bjm920Fyo34&list=RDBjm920Fyo34&start_radio=1",
    "https://www.youtube.com/watch?v=5UQzXbizT-s&list=RD5UQzXbizT-s&start_radio=1",
    "https://www.youtube.com/watch?v=xQk_hnuRejE&list=RDxQk_hnuRejE&start_radio=1",
    "https://www.youtube.com/watch?v=KBRJ3KMQZ18&list=RDKBRJ3KMQZ18&start_radio=1",
    "https://www.youtube.com/watch?v=lmvOwd2j_1Q&list=RDlmvOwd2j_1Q&start_radio=1",
    "https://www.youtube.com/watch?v=lqCM7xQozmY&list=RDlqCM7xQozmY&start_radio=1",
]

# ====== HÀM LẤY LYRICS ======
async def get_lyrics(title, artist):
    """Lấy lyrics từ API lyrics.ovh"""
    query_artist = artist.split(' feat')[0]
    api_url = f"https://api.lyrics.ovh/v1/{query_artist}/{title}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                lyrics = data.get("lyrics", None)
                if lyrics:
                    return lyrics[:1500] + "..." if len(lyrics) > 1500 else lyrics
            return "❌ Không tìm thấy lời bài hát."

# ====== HÀM PHÁT NHẠC NGẪU NHIÊN ======
async def play_random_kpop(vc, interaction=None):
    url = random.choice(KPOP_SONGS)
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies_www.youtube.com.txt'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"❌ Lỗi khi lấy thông tin nhạc: {e}")
        await interaction.followup.send("⚠️ Không thể tải bài hát này, thử lại nhé!", ephemeral=True)
        return

    audio_url = info['url']
    title = info.get('title', 'Unknown Title')
    uploader = info.get('uploader', 'Unknown Artist')
    thumbnail = info.get('thumbnail')

    # Dừng nhạc cũ (nếu đang phát)
    if vc.is_playing():
        vc.stop()

    # Phát bài mới
    def after_play(error):
        if error:
            print(f"Player error: {error}")
        else:
            asyncio.run_coroutine_threadsafe(play_random_kpop(vc, interaction), bot.loop)

    vc.play(
        discord.FFmpegPCMAudio(
            audio_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        ),
        after=after_play
    )

    # Lấy lyrics
    lyrics = await get_lyrics(title, uploader)

    # Gửi embed thông tin bài hát
    embed = discord.Embed(
        title=f"🎶 Đang phát: {title}",
        description=f"🎤 {uploader}\n\n📜 **Lyrics:**\n{lyrics}",
        color=0xFF69B4
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    await interaction.followup.send(embed=embed)

# ====== SỰ KIỆN ON_READY ======
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")

# ====== LỆNH /play ======
@bot.tree.command(name="play", description="Phát nhạc KPop ngẫu nhiên 🎶")
async def play(interaction: discord.Interaction):
    await interaction.response.defer()

    # Tìm kênh thoại chill-room
    voice_channel = discord.utils.get(interaction.guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if voice_channel is None:
        await interaction.followup.send(f"⚠️ Không tìm thấy kênh thoại **{VOICE_CHANNEL_NAME}**!", ephemeral=True)
        return

    # Nếu bot chưa kết nối
    if interaction.guild.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = interaction.guild.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)

    await play_random_kpop(vc, interaction)

# ====== LỆNH /next ======
@bot.tree.command(name="next", description="Phát bài KPop tiếp theo 🔁")
async def next_song(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_connected():
        await interaction.response.defer()
        await play_random_kpop(vc, interaction)
    else:
        await interaction.response.send_message("⚠️ Bot chưa vào kênh thoại!", ephemeral=True)

# ====== LỆNH /stop ======
@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("🛑 Đã dừng nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ====== LỆNH /leave ======
@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời khỏi kênh thoại.")
    else:
        await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)

# ====== CHẠY BOT ======
keep_alive()
bot.run(os.environ["DISCORD_TOKEN"])
