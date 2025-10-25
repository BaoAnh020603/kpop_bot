import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import random
import asyncio
import aiohttp
import os
from keep_alive import keep_alive

keep_alive()

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC KPOP =====
KPOP_SONGS = [
    "https://www.youtube.com/watch?v=Ng01EK5ePSU",
    "https://www.youtube.com/watch?v=SKWxqYvqmmA",
    "https://www.youtube.com/watch?v=Ir4GwBhPNt0",
    "https://www.youtube.com/watch?v=Bjm920Fyo34",
    "https://www.youtube.com/watch?v=5UQzXbizT-s",
    "https://www.youtube.com/watch?v=xQk_hnuRejE",
    "https://www.youtube.com/watch?v=KBRJ3KMQZ18",
    "https://www.youtube.com/watch?v=lmvOwd2j_1Q",
    "https://www.youtube.com/watch?v=lqCM7xQozmY"
]

current_song = {}
current_info = {}

# ===== LẤY LYRICS =====
async def get_lyrics(title, artist):
    query = f"{artist} {title}".replace(" ", "%20")
    url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "❌ Không tìm thấy lời bài hát.")
                    return lyrics[:1500]  # Discord giới hạn 2000 ký tự
        except:
            pass
    return "❌ Không tìm thấy lời bài hát."

# ===== HÀM PHÁT NHẠC =====
async def play_random_kpop(vc, interaction=None):
    url = random.choice(KPOP_SONGS)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'cookiefile': 'cookies_www.youtube.com.txt'
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

    current_song[interaction.guild_id] = url
    current_info[interaction.guild_id] = (title, uploader, thumbnail)

    def after_play(error):
        if error:
            print(f"Player error: {error}")
        else:
            coro = play_random_kpop(vc)
            asyncio.run_coroutine_threadsafe(coro, bot.loop)

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

    # Gửi Embed
    embed = discord.Embed(
        title=title,
        description=f"🎤 {uploader}",
        color=0xFF69B4
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    # Lấy lyrics
    lyrics = await get_lyrics(title, uploader)
    embed.add_field(name="📜 Lyrics", value=lyrics, inline=False)

    if interaction:
        await interaction.followup.send(embed=embed)
    else:
        # Nếu phát tự động qua after_play
        channel = discord.utils.get(bot.get_all_channels(), name="general")  # hoặc đổi thành kênh bạn muốn
        if channel:
            await channel.send(embed=embed)

# ===== SỰ KIỆN ON_READY =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")

# ===== /play =====
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

    await play_random_kpop(vc, interaction)

# ===== /next =====
@bot.tree.command(name="next", description="Chuyển sang bài KPop tiếp theo ⏭️")
async def next_song(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()  # sẽ tự gọi after_play và phát bài mới
        await interaction.response.send_message("⏭️ Đang chuyển sang bài tiếp theo...")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== /stop =====
@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("🛑 Đã dừng nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== /leave =====
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
