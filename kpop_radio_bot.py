import discord
from discord.ext import commands
import yt_dlp
import random
import asyncio
import os
import requests
from keep_alive import keep_alive 

keep_alive() 

# ===== CẤU HÌNH BOT (Giữ nguyên) =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC MẶC ĐỊNH & QUEUE (CHỈ DAILYMOTION) =====
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
    "https://www.dailymotion.com/video/x1y5ufe", 
    "https://www.dailymotion.com/video/x2rlakr",
    "https://www.dailymotion.com/video/x5c6csn",
    "https://www.dailymotion.com/video/x9so4gy",
    "https://www.dailymotion.com/video/x5sk7wk",
    "https://www.dailymotion.com/video/x36mwl8",
    "https://www.dailymotion.com/video/x32lif5",
    "https://www.dailymotion.com/video/x3eyspc",
    "https://www.dailymotion.com/video/x8pk5tx",
    "https://www.dailymotion.com/video/xztew3",
    "https://www.dailymotion.com/video/x53pet7",
    "https://www.dailymotion.com/video/x7wxgc2",
    "https://www.dailymotion.com/video/x4asrb5",
    "https://www.dailymotion.com/video/x7t805s",
    "https://www.dailymotion.com/video/x8o9huy",
    "https://www.dailymotion.com/video/x7kl37j",
    "https://www.dailymotion.com/video/x7u6j5q",
    "https://www.dailymotion.com/video/x3eysq1",
    "https://www.dailymotion.com/video/x8qdpoj",
    "https://www.dailymotion.com/video/x35696o",
    "https://www.dailymotion.com/video/x3999do",
    "https://www.dailymotion.com/video/x2bojy2",
    "https://www.dailymotion.com/video/x90v7mc",
    "https://www.dailymotion.com/video/x7v1u4q",
    "https://www.dailymotion.com/video/x678e5t",
    "https://www.dailymotion.com/video/x7buirx",
    "https://www.dailymotion.com/video/x8pl2qh",
    "https://www.dailymotion.com/video/x8pxzwy",
    "https://www.dailymotion.com/video/x8ccvv4",
    "https://www.dailymotion.com/video/x8be83u",
    "https://www.dailymotion.com/video/x7ytjr3",
]

queues = {}       
current_song = {} 
IDLE_TIMEOUT = 300 
idle_timers = {}   

# ⭐️ HÀM MỚI: Hỗ trợ Playlist Dailymotion ⭐️
def extract_info_from_url(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'nocheckcertificate': True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        'extract_flat': 'in_playlist',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Đối với URL, cố gắng lấy toàn bộ playlist Dailymotion
            info = ydl.extract_info(url, download=False, process=False)
            return info
    except Exception as e:
        print(f"❌ Lỗi yt-dlp khi trích xuất info: {e}")
        return None

# (Hàm quản lý timer: cancel_idle_timer, set_idle_timer giữ nguyên)
def cancel_idle_timer(guild_id):
    if guild_id in idle_timers:
        idle_timers[guild_id].cancel()
        del idle_timers[guild_id]

async def set_idle_timer(guild_id, vc):
    cancel_idle_timer(guild_id)
    
    async def idle_timeout():
        await asyncio.sleep(IDLE_TIMEOUT)
        
        if vc and not vc.is_playing() and len(queues.get(guild_id, [])) == 0:
            if len(vc.channel.members) <= 1: 
                await vc.channel.send("👋 Bot đã rời khỏi kênh thoại do không hoạt động trong 5 phút.")
                await vc.disconnect()
                await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))

    idle_timers[guild_id] = bot.loop.create_task(idle_timeout())


# (PlayerButtons class giữ nguyên)
class PlayerButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        vc = interaction.guild.voice_client
        if vc is None or interaction.user.voice is None or interaction.user.voice.channel != vc.channel:
            await interaction.response.send_message("❌ Bạn phải ở trong kênh thoại để điều khiển bot.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bỏ qua", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="skip_button")
    async def skip_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Đã chuyển sang bài mới.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)
        
    @discord.ui.button(label="Tạm dừng / Tiếp tục", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="pause_resume_button")
    async def pause_resume_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            if vc.is_playing():
                vc.pause()
                await interaction.response.send_message("⏸️ Đã tạm dừng phát nhạc.", ephemeral=True)
            elif vc.is_paused():
                vc.resume()
                await interaction.response.send_message("▶️ Tiếp tục phát nhạc.", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Không có bài nào đang phát.", ephemeral=True)
        
    @discord.ui.button(label="Dừng & Rời", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="stop_leave_button")
    async def stop_leave_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            queues[interaction.guild.id] = []
            vc.stop()
            await vc.disconnect()
            await self.bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))
            await interaction.response.send_message("🛑 Bot đã dừng phát nhạc và rời kênh.", ephemeral=False)
        else:
            await interaction.response.send_message("⚠️ Bot không ở trong kênh thoại.", ephemeral=True)


# HÀM PHÁT NHẠC
async def play_next_song(vc, interaction=None):
    guild_id = vc.guild.id
    
    if not queues.get(guild_id):
        current_song[guild_id] = None
        await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))
        await set_idle_timer(guild_id, vc) 
        return

    cancel_idle_timer(guild_id)
    
    url = queues[guild_id].pop(0)

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "nocheckcertificate": True,
        "http_headers": {"User-Agent": "Mozilla/5.0"},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False, process=True)
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

    # AUTO-QUEUE CHECK: Tự động nạp lại danh sách khi queue còn ít bài
    if len(queues.get(guild_id, [])) <= 3:
        random_songs = random.sample(DEFAULT_KPOP_SONGS, min(5, len(DEFAULT_KPOP_SONGS)))
        queues[guild_id].extend(random_songs)
        print(f"✅ Auto-Queue: Đã thêm {len(random_songs)} bài ngẫu nhiên.")
    
    current_song[guild_id] = {
        "title": title,
        "uploader": uploader,
        "thumbnail": thumbnail,
        "url": webpage_url
    }
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name=f"{title} | {uploader}"
        )
    )

    def after_play(err):
        if err:
            print(f"❌ Lỗi khi phát nhạc: {err}")
        asyncio.run_coroutine_threadsafe(play_next_song(vc, None), bot.loop)
        
    if vc.is_playing():
        vc.stop()

    try:
        source = discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
        vc.play(
            source,
            after=after_play
        )
    except Exception as e:
        print(f"❌ Lỗi khi gọi vc.play: {e}")
        if queues[guild_id]:
            await play_next_song(vc, interaction)
        return

    # Giao diện Embed Xịn Xò hơn
    embed = discord.Embed(
        title=f"🎶 Đang phát: {title}",
        description=f"**🎤 Chủ kênh đăng tải video:** {uploader}",
        color=0xFF0099 
    )
    embed.add_field(name="🔗 Nguồn", value=f"[Xem trên Web]({webpage_url})", inline=True)
    embed.set_footer(text=f"Hàng đợi: {len(queues.get(guild_id, []))} bài | Auto-Queue Đang Bật 🔄")
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    # GỬI EMBED KÈM BUTTONS
    view = PlayerButtons(bot)
    
    if interaction:
        try:
            await interaction.followup.send(embed=embed, view=view)
        except discord.errors.NotFound:
            channel = interaction.channel
            if channel:
                await channel.send(embed=embed, view=view)
    elif vc.channel:
        await vc.channel.send(embed=embed, view=view)


# ===== SỰ KIỆN BOT (Giữ nguyên) =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")
    
    await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))


# ⭐️ LỆNH /play (Chỉ Hỗ trợ URL Dailymotion và Playlist) ⭐️
@bot.tree.command(name="play", description="Phát nhạc ngẫu nhiên hoặc thêm Playlist/URL Dailymotion 🎶")
async def play(interaction: discord.Interaction, query: str = None):
    await interaction.response.defer()

    guild = interaction.guild
    if interaction.user.voice and interaction.user.voice.channel:
        voice_channel = interaction.user.voice.channel
    else:
        voice_channel = discord.utils.get(guild.voice_channels, name="🎧│chill-room")

    if not voice_channel:
        await interaction.followup.send("❌ Vui lòng vào kênh thoại hoặc tạo kênh `🎧│chill-room`.", ephemeral=True)
        return

    vc = guild.voice_client
    if vc is None:
        try:
            vc = await voice_channel.connect()
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Không thể kết nối kênh thoại. Vui lòng thử lại.", ephemeral=True)
            return
    
    # Xử lý Query/Playlist
    if query:
        # ⚠️ CHỈ CHO PHÉP URL (BỎ LOGIC TÌM KIẾM TÊN BÀI HÁT)
        if not query.startswith("http"):
            await interaction.followup.send("❌ Vui lòng cung cấp URL Dailymotion hợp lệ (không hỗ trợ tìm kiếm tên bài).", ephemeral=True)
            return

        info = await asyncio.to_thread(extract_info_from_url, query)
        
        if not info:
            await interaction.followup.send(f"❌ Không tìm thấy thông tin cho URL `{query}`.", ephemeral=True)
            return

        # ⭐️ Logic xử lý Playlist (Queue nhiều bài) ⭐️
        if info.get('_type') == 'playlist' and 'entries' in info:
            count = 0
            for entry in info['entries']:
                if entry and 'webpage_url' in entry:
                    queues.setdefault(guild.id, []).append(entry['webpage_url'])
                    count += 1
            
            if count > 0:
                msg = f"✅ Đã thêm **{count}** bài hát từ Playlist `{info.get('title', 'Không tên')}` vào hàng đợi!"
                if not vc.is_playing() and not vc.is_paused():
                     asyncio.create_task(play_next_song(vc, interaction))
                await interaction.followup.send(msg)
                return
            else:
                await interaction.followup.send("⚠️ Playlist không chứa URL bài hát hợp lệ nào.", ephemeral=True)
                return
        
        # Logic xử lý Video Đơn
        elif 'webpage_url' in info:
            url = info['webpage_url']
            song_title = info['title']
        else:
            await interaction.followup.send(f"❌ Lỗi khi xử lý URL `{query}`.", ephemeral=True)
            return
    else:
        # Nếu không có query, chọn bài ngẫu nhiên từ danh sách mặc định
        url = random.choice(DEFAULT_KPOP_SONGS)
        song_title = "bài hát ngẫu nhiên"
        
    # Thêm bài hát đơn vào queue
    queues.setdefault(guild.id, []).append(url)
    
    # Thông báo thêm vào queue/bắt đầu phát
    if vc.is_playing() or vc.is_paused():
        await interaction.followup.send(f"✅ Đã thêm **{song_title}** vào hàng đợi.")
    else:
        await interaction.followup.send(f"🎧 Bắt đầu phát **{song_title}**...")
        asyncio.create_task(play_next_song(vc, interaction))


# (Các lệnh khác giữ nguyên)
@bot.tree.command(name="volume", description="Điều chỉnh âm lượng bot (0-100%) 🔊")
async def volume(interaction: discord.Interaction, level: int):
    vc = interaction.guild.voice_client
    if not vc or vc.source is None:
        await interaction.response.send_message("⚠️ Bot chưa phát nhạc.", ephemeral=True)
        return

    if not (0 <= level <= 100):
        await interaction.response.send_message("❌ Mức âm lượng phải nằm trong khoảng từ 0 đến 100.", ephemeral=True)
        return

    if isinstance(vc.source, discord.PCMVolumeTransformer):
        vc.source.volume = level / 100.0
    else:
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=level / 100.0)

    await interaction.response.send_message(f"🔊 Đã đặt âm lượng bot thành **{level}%**.", ephemeral=False)


@bot.tree.command(name="jump", description="Chuyển đến bài hát theo số thứ tự trong hàng đợi 🔢")
async def jump(interaction: discord.Interaction, index: int):
    vc = interaction.guild.voice_client
    guild_id = interaction.guild.id
    
    if not vc or not vc.is_playing():
        await interaction.response.send_message("⚠️ Bot chưa phát nhạc.", ephemeral=True)
        return
    
    q = queues.get(guild_id, [])
    if index < 1 or index > len(q):
        await interaction.response.send_message(f"❌ Số thứ tự không hợp lệ. Hàng đợi có {len(q)} bài (bắt đầu từ 1).", ephemeral=True)
        return
        
    del q[:index - 1] 
    vc.stop() 
    
    await interaction.response.send_message(f"🔢 Đã nhảy đến bài hát thứ **{index}** trong hàng đợi.", ephemeral=False)


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
        await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))
        await interaction.response.send_message("🛑 Đã dừng phát nhạc và xóa queue.")
    else:
        await interaction.response.send_message("⚠️ Bot chưa tham gia kênh thoại.", ephemeral=True)

@bot.tree.command(name="leave", description="Bot rời khỏi kênh thoại 🚪")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        queues[interaction.guild.id] = []
        await vc.disconnect()
        await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))
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
            description=f"🎤 **Nghệ sĩ:** {song['uploader']}\n🔗 [Xem trên Web]({song['url']})",
            color=0xFF0099
        )
        if song["thumbnail"]:
            embed.set_thumbnail(url=song["thumbnail"])
        
        view = PlayerButtons(bot)
        await interaction.response.send_message(embed=embed, view=view)
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
        title="✨ KPop Radio Bot - Hướng Dẫn Lệnh ✨",
        description="Bot chỉ chấp nhận URL Dailymotion (video hoặc playlist) hoặc phát nhạc ngẫu nhiên.",
        color=0xFF0099 
    )
    
    embed.add_field(name="▶️ Phát Nhạc & Điều Khiển", value="`/play [link Playlist/Video]`, `/pause`, `/resume`, `/skip`, `/stop`", inline=False)
    embed.add_field(name="⚙️ Quản Lý Nâng Cao", value="`/volume [0-100]`, `/jump [index]`, `/shuffle`", inline=False)
    embed.add_field(name="📜 Thông tin & Queue", value="`/nowplaying`, `/queue`", inline=False)
    embed.add_field(name="🚪 Rời Đi", value="`/leave`", inline=False)

    embed.set_footer(text="💖 Được phát triển tại Việt Nam | Dùng /play để bắt đầu!")
    await interaction.response.send_message(embed=embed)


# ===== CHẠY BOT (Giữ nguyên) =====
TOKEN = os.getenv("DISCORD_TOKEN") 

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ LỖI NGHIÊM TRỌNG: KHÔNG TÌM THẤY DISCORD_TOKEN trong biến môi trường.")

