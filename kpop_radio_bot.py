import discord
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
    "https://www.youtube.com/watch?v=GRbF3DKd7rM",
    "https://www.youtube.com/watch?v=IwNDRDsW_UE",
    "https://www.youtube.com/watch?v=y72_r33ca88",
    "https://www.youtube.com/watch?v=4hXF67LbRPo",
    "https://www.youtube.com/watch?v=i__0VanmURE",
    "https://www.youtube.com/watch?v=yp0sRO6T-W8",
    "https://www.youtube.com/watch?v=8ykKs4gUuMg",
    "https://www.youtube.com/watch?v=uUK1TJDWHUM",
    "https://www.youtube.com/watch?v=fexlk_TlRpc",
    "https://www.youtube.com/watch?v=uLfLbtulKZc",
    "https://www.youtube.com/watch?v=Z9b0Hj-BfaM",
    "https://www.youtube.com/watch?v=3DOkxQ3HDXE",
    "https://www.youtube.com/watch?v=8Q2mth2bX10",
]

queues = {}       # {guild_id: [list of URLs]}
current_song = {} # {guild_id: song_info}

# ===== HÀM LẤY LYRICS =====
def get_lyrics(query: str):
    try:
        resp = requests.get(f"https://some-random-api.com/lyrics?title={query}")
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data.get("lyrics", "Không tìm thấy lời bài hát 😢")
            return lyrics[:1500] + "..."
    except:
        pass
    return "Không tìm thấy lời bài hát 😢"

# ===== HÀM PHÁT NHẠC =====
async def play_next_song(vc, interaction=None):
    guild_id = vc.guild.id
    if not queues.get(guild_id):
        await asyncio.sleep(1)
        return

    url = queues[guild_id].pop(0)

    cookie_file = "www.youtube.com_cookies.txt"
    if not os.path.exists(cookie_file):
        cookies_content = os.environ.get("YOUTUBE_COOKIES")
        if cookies_content:
            with open(cookie_file, "w", encoding="utf-8") as f:
                f.write(cookies_content)

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "nocheckcertificate": True,
        "cookiefile": cookie_file if os.path.exists(cookie_file) else None,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader", "Unknown Artist")
            thumbnail = info.get("thumbnail")
            webpage_url = info.get("webpage_url")
    except Exception as e:
        print(f"❌ Lỗi yt-dlp: {e}")
        if queues[guild_id]:
            await play_next_song(vc, interaction)
        return

    current_song[guild_id] = {
        "title": title,
        "uploader": uploader,
        "thumbnail": thumbnail,
        "url": webpage_url
    }

    def after_play(err):
        if err:
            print(f"❌ Lỗi khi phát nhạc: {err}")
        fut = asyncio.run_coroutine_threadsafe(play_next_song(vc, None), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"❌ Lỗi asyncio: {e}")

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
        if queues[guild_id]:
            await play_next_song(vc, interaction)
        return

    lyrics = get_lyrics(title)
    embed = discord.Embed(
        title=f"🎵 {title}",
        description=f"👩‍🎤 {uploader}\n\n📜 **Lyrics:**\n{lyrics}",
        color=0xFF69B4
    )
    embed.add_field(name="🎧 YouTube", value=f"[Xem trên YouTube]({webpage_url})", inline=False)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if interaction:
        try:
            await interaction.followup.send(embed=embed)
        except discord.errors.NotFound:
            print("⚠️ Interaction đã hết hạn, không thể gửi embed.")

# ===== SỰ KIỆN BOT =====
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
    # Gửi phản hồi ngay lập tức, tránh timeout
    await interaction.response.send_message("🎧 Đang chuẩn bị phát nhạc...")

    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name="🎧│chill-room")

    if not voice_channel:
        await interaction.followup.send("❌ Không tìm thấy kênh thoại `🎧│chill-room`!", ephemeral=True)
        return

    # Kết nối voice nếu chưa có
    vc = guild.voice_client
    if vc is None:
        vc = await voice_channel.connect()

    # Chọn bài ngẫu nhiên và thêm vào hàng chờ
    url = random.choice(KPOP_SONGS)
    queues.setdefault(guild.id, []).append(url)

    # Nếu chưa phát bài nào thì chạy phát nhạc trong background
    if not vc.is_playing():
        asyncio.create_task(play_next_song(vc, interaction))
    else:
        await interaction.followup.send("✅ Bài hát đã được thêm vào hàng đợi (queue).")

# ===== /skip =====
@bot.tree.command(name="skip", description="Chuyển sang bài tiếp theo ⏭️")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭️ Chuyển sang bài mới...")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== /pause =====
@bot.tree.command(name="pause", description="Tạm dừng nhạc ⏸️")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== /resume =====
@bot.tree.command(name="resume", description="Tiếp tục phát nhạc ▶️")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Tiếp tục phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang tạm dừng.", ephemeral=True)

# ===== /stop =====
@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        vc.stop()
        await interaction.response.send_message("🛑 Đã dừng phát nhạc và xóa queue.")
    else:
        await interaction.response.send_message("⚠️ Bot chưa tham gia kênh thoại.", ephemeral=True)

# ===== /leave =====
@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời khỏi kênh thoại.")
    else:
        await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)

# ===== /queue =====
@bot.tree.command(name="queue", description="Hiển thị danh sách bài chờ 📃")
async def queue(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if q:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(q[:10])])
        await interaction.response.send_message(f"📜 **Danh sách bài chờ:**\n{msg}")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào trong hàng đợi.", ephemeral=True)

# ===== /nowplaying =====
@bot.tree.command(name="nowplaying", description="Hiển thị bài hát đang phát 🎶")
async def nowplaying(interaction: discord.Interaction):
    song = current_song.get(interaction.guild.id)
    if song:
        embed = discord.Embed(
            title=f"🎶 Đang phát: {song['title']}",
            description=f"👩‍🎤 {song['uploader']}\n🔗 [Xem trên YouTube]({song['url']})",
            color=0xFF69B4
        )
        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

# ===== /shuffle =====
@bot.tree.command(name="shuffle", description="Trộn ngẫu nhiên danh sách bài chờ 🔀")
async def shuffle(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if len(q) > 1:
        random.shuffle(q)
        await interaction.response.send_message("🔀 Đã trộn lại thứ tự các bài trong hàng đợi!")
    else:
        await interaction.response.send_message("⚠️ Không đủ bài để trộn.", ephemeral=True)

# ===== /help =====
@bot.tree.command(name="help", description="Hiển thị hướng dẫn sử dụng bot ℹ️")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 KPop Radio Bot - Hướng dẫn lệnh",
        description=(
            "/play — Phát nhạc KPop ngẫu nhiên 🎶\n"
            "/skip — Chuyển bài ⏭️\n"
            "/pause — Tạm dừng ⏸️\n"
            "/resume — Tiếp tục ▶️\n"
            "/stop — Dừng phát ⏹️\n"
            "/queue — Xem hàng đợi 📃\n"
            "/nowplaying — Xem bài hiện tại 🎧\n"
            "/shuffle — Trộn hàng đợi 🔀\n"
            "/leave — Bot rời kênh thoại 🚪\n"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="🎀 Made with love for K-Pop fans 💖")
    await interaction.response.send_message(embed=embed)

# ===== CHẠY BOT =====
bot.run("MTQzMTUyMjQ1MDg0MzExMTQ1NA.GqldV0.o5P7gD4npliKRTHK6qgmTcF2b1Kfg5EGXKgBIE")


