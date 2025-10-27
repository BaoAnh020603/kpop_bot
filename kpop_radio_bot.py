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
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC (SỬ DỤNG DAILYMOTION/YT CÔNG KHAI) =====
# ⭐️ ĐÃ SỬA: Chuyển sang URL Dailymotion để tránh lỗi xác thực YouTube
KPOP_SONGS = [
    "https://www.dailymotion.com/video/x7zuocf", 
]

queues = {}       
current_song = {} 

# ===== HÀM LẤY LYRICS (Giữ nguyên) =====
def get_lyrics(query: str):
    try:
        resp = requests.get(f"https://some-random-api.com/lyrics?title={query}")
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data.get("lyrics", "Không tìm thấy lời bài hát 😢")
            if len(lyrics) > 1500:
                return lyrics[:1500] + "..."
            return lyrics
    except:
        pass
    return "Không tìm thấy lời bài hát 😢"

# ===== HÀM PHÁT NHẠC (ĐÃ XÓA LOGIC COOKIE) =====
async def play_next_song(vc, interaction=None):
    guild_id = vc.guild.id
    
    if not queues.get(guild_id):
        await asyncio.sleep(1)
        return

    url = queues[guild_id].pop(0)

    # ⭐️ ĐÃ SỬA: Loại bỏ logic cookies_content vì không dùng YouTube nữa
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get("url")
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader", "Unknown Artist")
            thumbnail = info.get("thumbnail")
            webpage_url = info.get("webpage_url")
            
            if not audio_url:
                 raise Exception("Không tìm thấy URL audio.")

    except Exception as e:
        print(f"❌ Lỗi yt-dlp khi xử lý {url}: {e}")
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
            print(f"❌ Lỗi asyncio khi chuyển bài: {e}")

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
        print(f"❌ Lỗi khi gọi vc.play: {e}")
        if queues[guild_id]:
            await play_next_song(vc, interaction)
        return

    lyrics = get_lyrics(title)
    embed = discord.Embed(
        title=f"🎵 Đang phát: {title}",
        description=f"👩‍🎤 **{uploader}**\n\n📜 **Lyrics (Trích đoạn):**\n{lyrics}",
        color=0xFF69B4 
    )
    embed.add_field(name="🎧 Dailymotion/YouTube", value=f"[Xem trên Web]({webpage_url})", inline=False)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if interaction:
        try:
            await interaction.followup.send(embed=embed)
        except discord.errors.NotFound:
            channel = interaction.channel
            if channel:
                await channel.send(embed=embed)
    elif vc.channel:
        await vc.channel.send(embed=embed)


# ===== CÁC LỆNH KHÁC (GIỮ NGUYÊN) =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")

@bot.tree.command(name="play", description="Phát nhạc KPop ngẫu nhiên 🎶")
async def play(interaction: discord.Interaction):
    await interaction.response.send_message("🎧 Đang chuẩn bị phát nhạc...", ephemeral=True)
    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name="🎧│chill-room")

    if not voice_channel:
        await interaction.followup.send("❌ Không tìm thấy kênh thoại `🎧│chill-room`!", ephemeral=True)
        return

    vc = guild.voice_client
    if vc is None:
        try:
            vc = await voice_channel.connect()
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Không thể kết nối kênh thoại. Vui lòng thử lại.", ephemeral=True)
            return

    url = random.choice(KPOP_SONGS)
    queues.setdefault(guild.id, []).append(url)

    if vc.is_playing() or vc.is_paused():
        await interaction.followup.send("✅ Bài hát ngẫu nhiên đã được thêm vào hàng đợi (queue).", ephemeral=False)
    else:
        asyncio.create_task(play_next_song(vc, interaction))

@bot.tree.command(name="skip", description="Chuyển sang bài tiếp theo ⏭️")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭️ Chuyển sang bài mới...")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="pause", description="Tạm dừng nhạc ⏸️")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="resume", description="Tiếp tục phát nhạc ▶️")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Tiếp tục phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang tạm dừng.", ephemeral=True)

@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        vc.stop() 
        await interaction.response.send_message("🛑 Đã dừng phát nhạc và xóa queue.")
    else:
        await interaction.response.send_message("⚠️ Bot chưa tham gia kênh thoại.", ephemeral=True)

@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời khỏi kênh thoại.")
    else:
        await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)

@bot.tree.command(name="queue", description="Hiển thị danh sách bài chờ 📃")
async def queue(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if q:
        msg = "\n".join([f"**{i+1}.** {url}" for i, url in enumerate(q[:10])])
        await interaction.response.send_message(f"📜 **Danh sách bài chờ ({len(q)} bài):**\n{msg}")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào trong hàng đợi.", ephemeral=True)

@bot.tree.command(name="nowplaying", description="Hiển thị bài hát đang phát 🎶")
async def nowplaying(interaction: discord.Interaction):
    song = current_song.get(interaction.guild.id)
    if song:
        embed = discord.Embed(
            title=f"🎶 Đang phát: {song['title']}",
            description=f"👩‍🎤 {song['uploader']}\n🔗 [Xem trên Dailymotion/YouTube]({song['url']})",
            color=0xFF69B4
        )
        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="shuffle", description="Trộn ngẫu nhiên danh sách bài chờ 🔀")
async def shuffle(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if len(q) > 1:
        random.shuffle(q)
        await interaction.response.send_message("🔀 Đã trộn lại thứ tự các bài trong hàng đợi!")
    else:
        await interaction.response.send_message("⚠️ Không đủ bài để trộn.", ephemeral=True)

@bot.tree.command(name="help", description="Hiển thị hướng dẫn sử dụng bot ℹ️")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 KPop Radio Bot - Hướng dẫn lệnh",
        description=(
            "**Cài đặt:** Bot sẽ tự động kết nối vào kênh thoại có tên `🎧│chill-room`\n\n"
            "**/play** — Phát nhạc KPop ngẫu nhiên 🎶\n"
            "**/skip** — Chuyển bài ⏭️\n"
            "**/pause** — Tạm dừng ⏸️\n"
            "**/resume** — Tiếp tục ▶️\n"
            "**/stop** — Dừng phát ⏹️\n"
            "**/queue** — Xem hàng đợi 📃\n"
            "**/nowplaying** — Xem bài hiện tại 🎧\n"
            "**/shuffle** — Trộn hàng đợi 🔀\n"
            "**/leave** — Bot rời kênh thoại 🚪\n"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="🎀 Made with love for K-Pop fans 💖")
    await interaction.response.send_message(embed=embed)

# ===== CHẠY BOT =====
TOKEN = os.getenv("DISCORD_TOKEN") 

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ LỖI NGHIÊM TRỌNG: KHÔNG TÌM THẤY DISCORD_TOKEN trong biến môi trường.")
