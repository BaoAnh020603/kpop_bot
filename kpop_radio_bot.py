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

# ===== DANH SÁCH NHẠC MẶC ĐỊNH & QUEUE =====
# Sử dụng Dailymotion và YouTube M/V công khai để tránh lỗi xác thực
DEFAULT_KPOP_SONGS = [
    "https://www.dailymotion.com/video/x7zuocf",
    "https://www.dailymotion.com/video/x8psjs7",
    "https://www.dailymotion.com/video/x7t3ao4",
    "https://www.dailymotion.com/video/x425w0w",
    "https://www.dailymotion.com/video/x3zwk2r",
    "https://www.dailymotion.com/video/x683djo",
    "https://www.dailymotion.com/video/x7bugyp",
    "https://www.dailymotion.com/video/x8pl2nq",
    "https://www.dailymotion.com/video/x4qz046",
    "https://www.dailymotion.com/video/x8p3p6w",
    "https://www.dailymotion.com/video/x42wf0z",
    "https://www.dailymotion.com/video/x2wto4r",
    "https://www.dailymotion.com/video/x9miaw0",
    "https://www.dailymotion.com/video/x74e7xl",
    "https://www.dailymotion.com/video/x2mpj5b",
    "https://www.dailymotion.com/video/x3cbksb",
    "https://www.dailymotion.com/video/x8ucqke",
    "https://www.dailymotion.com/video/x8aauvk",
    "https://www.dailymotion.com/video/x1y5ufe", #
]

queues = {}       # {guild_id: [list of URLs]}
current_song = {} # {guild_id: song_info}

# Hàm tìm kiếm YouTube bằng yt-dlp (cho /play tên bài hát)
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'nocheckcertificate': True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Tìm kiếm và lấy info của video đầu tiên
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries'][0]
            return info
    except Exception as e:
        print(f"❌ Lỗi tìm kiếm yt-dlp: {e}")
        return None

# ===== HÀM LẤY LYRICS =====
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

# ===== HÀM PHÁT NHẠC (ĐÃ SỬA LỖI AFTER_PLAY) =====
async def play_next_song(vc, interaction=None):
    guild_id = vc.guild.id
    
    if not queues.get(guild_id):
        current_song[guild_id] = None
        await asyncio.sleep(1)
        return

    url = queues[guild_id].pop(0)

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
    
    # ⭐️ Cập nhật trạng thái bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name=f"{title} | {uploader}"
        )
    )

    # ⭐️ SỬA LỖI: Cải thiện hàm after_play để xử lý chuyển bài an toàn
    def after_play(err):
        if err:
            print(f"❌ Lỗi khi phát nhạc: {err}")
        
        # Chạy coroutine trong event loop chính để chuyển bài
        asyncio.run_coroutine_threadsafe(play_next_song(vc, None), bot.loop)
        
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
    
    # ⭐️ Giao diện Embed Xịn Xò hơn
    embed = discord.Embed(
        title=f"🎶 Đang phát: {title}",
        description=f"**🎤 Nghệ sĩ:** {uploader}",
        color=0xFF0099 # Hồng K-Pop
    )
    embed.add_field(name="📜 Lyrics (Trích đoạn)", value=lyrics, inline=False)
    embed.add_field(name="🔗 Nguồn", value=f"[Xem trên Web]({webpage_url})", inline=True)
    embed.set_footer(text=f"Đã thêm vào hàng đợi: {len(queues.get(guild_id, []))} bài")
    
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


# ===== SỰ KIỆN BOT =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")
    
    # Đặt trạng thái ban đầu
    await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))


# ===== /play (Hỗ trợ Search) =====
@bot.tree.command(name="play", description="Phát nhạc KPop ngẫu nhiên hoặc tìm kiếm bài hát 🎶")
async def play(interaction: discord.Interaction, query: str = None):
    await interaction.response.defer() # Dùng defer để có thêm thời gian xử lý

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
    
    # Xử lý Query
    if query:
        # Nếu là URL, dùng trực tiếp; nếu là tên, tìm kiếm
        if query.startswith("http"):
            url = query
            song_title = "URL đã cung cấp"
        else:
            info = await asyncio.to_thread(search_youtube, query)
            if not info or 'webpage_url' not in info:
                await interaction.followup.send(f"❌ Không tìm thấy bài hát cho từ khóa: `{query}`.", ephemeral=True)
                return
            url = info['webpage_url']
            song_title = info['title']
    else:
        # Nếu không có query, chọn bài ngẫu nhiên từ danh sách mặc định
        url = random.choice(DEFAULT_KPOP_SONGS)
        song_title = "bài hát ngẫu nhiên"

    queues.setdefault(guild.id, []).append(url)

    # Thông báo thêm vào queue/bắt đầu phát
    if vc.is_playing() or vc.is_paused():
        await interaction.followup.send(f"✅ Đã thêm **{song_title}** vào hàng đợi.")
    else:
        await interaction.followup.send(f"🎧 Bắt đầu phát **{song_title}**...")
        asyncio.create_task(play_next_song(vc, interaction))


# ===== /lyrics (Lấy lời bài hát đang phát) =====
@bot.tree.command(name="lyrics", description="Hiển thị lời bài hát đang phát 📜")
async def lyrics(interaction: discord.Interaction):
    song = current_song.get(interaction.guild.id)
    if not song:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát để xem lời.", ephemeral=True)
        return

    await interaction.response.defer()
    
    # Lấy lyrics qua thread
    lyrics_text = await asyncio.to_thread(get_lyrics, song['title'])
    
    embed = discord.Embed(
        title=f"📜 Lời bài hát: {song['title']}",
        description=f"**🎤 {song['uploader']}**\n\n{lyrics_text}",
        color=0xFF0099
    )
    await interaction.followup.send(embed=embed)


# ===== /skip, /pause, /resume, /stop, /leave, /queue, /nowplaying, /shuffle (Giữ nguyên) =====
@bot.tree.command(name="skip", description="Chuyển sang bài tiếp theo ⏭️")
# ... (Nội dung hàm /skip) ...
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭️ Chuyển sang bài mới...")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="pause", description="Tạm dừng nhạc ⏸️")
# ... (Nội dung hàm /pause) ...
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="resume", description="Tiếp tục phát nhạc ▶️")
# ... (Nội dung hàm /resume) ...
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Tiếp tục phát nhạc.")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang tạm dừng.", ephemeral=True)

@bot.tree.command(name="stop", description="Dừng phát nhạc ⏹️")
# ... (Nội dung hàm /stop) ...
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        vc.stop() 
        await interaction.response.send_message("🛑 Đã dừng phát nhạc và xóa queue.")
    else:
        await interaction.response.send_message("⚠️ Bot chưa tham gia kênh thoại.", ephemeral=True)

@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
# ... (Nội dung hàm /leave) ...
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        await vc.disconnect()
        await interaction.response.send_message("👋 Bot đã rời khỏi kênh thoại.")
    else:
        await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)

@bot.tree.command(name="queue", description="Hiển thị danh sách bài chờ 📃")
# ... (Nội dung hàm /queue) ...
async def queue(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if q:
        msg = "\n".join([f"**{i+1}.** {url}" for i, url in enumerate(q[:10])])
        await interaction.response.send_message(f"📜 **Danh sách bài chờ ({len(q)} bài):**\n{msg}")
    else:
        await interaction.response.send_message("⚠️ Không có bài nào trong hàng đợi.", ephemeral=True)

@bot.tree.command(name="nowplaying", description="Hiển thị bài hát đang phát 🎶")
# ... (Nội dung hàm /nowplaying) ...
async def nowplaying(interaction: discord.Interaction):
    song = current_song.get(interaction.guild.id)
    if song:
        embed = discord.Embed(
            title=f"🎶 Đang phát: {song['title']}",
            description=f"🎤 **Nghệ sĩ:** {song['uploader']}\n🔗 [Xem trên Web]({song['url']})",
            color=0xFF0099
        )
        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)

@bot.tree.command(name="shuffle", description="Trộn ngẫu nhiên danh sách bài chờ 🔀")
# ... (Nội dung hàm /shuffle) ...
async def shuffle(interaction: discord.Interaction):
    q = queues.get(interaction.guild.id, [])
    if len(q) > 1:
        random.shuffle(q)
        await interaction.response.send_message("🔀 Đã trộn lại thứ tự các bài trong hàng đợi!")
    else:
        await interaction.response.send_message("⚠️ Không đủ bài để trộn.", ephemeral=True)

# ===== /help (Giao diện mới) =====
@bot.tree.command(name="help", description="Hiển thị hướng dẫn sử dụng bot ℹ️")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ KPop Radio Bot - Hướng Dẫn Lệnh ✨",
        description="Bot phát nhạc ngẫu nhiên từ Dailymotion và YouTube công khai. Luôn dùng lệnh Slash (/).",
        color=0xFF0099 
    )
    
    embed.add_field(name="▶️ Phát Nhạc & Điều Khiển", value="`/play [tên/link]`, `/pause`, `/resume`, `/skip`, `/stop`", inline=False)
    embed.add_field(name="📜 Thông tin & Queue", value="`/nowplaying`, `/queue`, `/lyrics`, `/shuffle`", inline=False)
    embed.add_field(name="🚪 Quản Lý Bot", value="`/leave`", inline=False)

    embed.set_footer(text="💖 Được phát triển tại Việt Nam | Dùng /play để bắt đầu!")
    await interaction.response.send_message(embed=embed)


# ===== CHẠY BOT (Giữ nguyên) =====
TOKEN = os.getenv("DISCORD_TOKEN") 

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ LỖI NGHIÊM TRỌNG: KHÔNG TÌM THẤY DISCORD_TOKEN trong biến môi trường.")
