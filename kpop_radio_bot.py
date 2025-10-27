import discord
from discord.ext import commands
import yt_dlp
import random
import asyncio
import os
import requests

# ⚠️ LƯU Ý: Nếu bạn dùng Railway/Replit, hãy đảm bảo keep_alive đã được cấu hình đúng
from keep_alive import keep_alive 
keep_alive() 

# ===== CẤU HÌNH BOT =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DANH SÁCH NHẠC MẶC ĐỊNH & QUEUE =====
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
]

queues = {}       
current_song = {} 

# Hàm tìm kiếm YouTube bằng yt-dlp
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
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries'][0]
            return info
    except Exception as e:
        print(f"❌ Lỗi tìm kiếm yt-dlp: {e}")
        return None

# ===== KHAI BÁO VIEWS (NÚT BẤM TƯƠNG TÁC) =====
class PlayerButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Giới hạn tương tác: chỉ cho phép người dùng có quyền trong kênh thoại
        if interaction.user.voice is None or interaction.user.voice.channel != interaction.guild.voice_client.channel:
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
        else:
            await interaction.response.send_message("⚠️ Bot chưa tham gia kênh thoại.", ephemeral=True)
            
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


# ===== HÀM PHÁT NHẠC (ĐÃ SỬA LỖI AFTER_PLAY VÀ AUTO-QUEUE) =====
async def play_next_song(vc, interaction=None):
    guild_id = vc.guild.id
    
    if not queues.get(guild_id):
        current_song[guild_id] = None
        await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))
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

    # ⭐️ AUTO-QUEUE CHECK: Tự động nạp lại danh sách khi queue còn ít bài ⭐️
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
    
    # Cập nhật trạng thái bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name=f"{title} | {uploader}"
        )
    )

    # Cải thiện hàm after_play để xử lý chuyển bài an toàn
    def after_play(err):
        if err:
            print(f"❌ Lỗi khi phát nhạc: {err}")
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

    # ⭐️ Giao diện Embed Xịn Xò hơn
    embed = discord.Embed(
        title=f"🎶 Đang phát: {title}",
        description=f"**🎤 Chủ kênh đăng tải video:** {uploader}",
        color=0xFF0099 # Hồng K-Pop
    )
    embed.add_field(name="🔗 Nguồn", value=f"[Xem trên Web]({webpage_url})", inline=True)
    embed.set_footer(text=f"Hàng đợi: {len(queues.get(guild_id, []))} bài | Auto-Queue Đang Bật 🔄")
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    # ⭐️ GỬI EMBED KÈM BUTTONS
    view = PlayerButtons(bot)
    
    if interaction:
        try:
            # Gửi followup với view
            await interaction.followup.send(embed=embed, view=view)
        except discord.errors.NotFound:
            channel = interaction.channel
            if channel:
                await channel.send(embed=embed, view=view)
    elif vc.channel:
        # Gửi vào kênh nếu tự động chuyển bài
        await vc.channel.send(embed=embed, view=view)


# ===== SỰ KIỆN BOT =====
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")
    try:
        # Đồng bộ Slash Commands
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} slash command.")
    except Exception as e:
        print(f"❌ Lỗi khi sync slash command: {e}")
    
    # Đặt trạng thái ban đầu
    await bot.change_presence(activity=discord.Game(name="KPop Radio | Dùng /play"))


# ===== /play (Hỗ trợ Search) =====
@bot.tree.command(name="play", description="Phát nhạc KPop ngẫu nhiên hoặc tìm kiếm bài hát 🎶")
async def play(interaction: discord.Interaction, query: str = None):
    await interaction.response.defer() 

    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name="🎧│chill-room")

    if not voice_channel:
        # THÊM LOGIC JOIN ĐỘNG: Nếu người dùng đang ở trong kênh thoại nào, join kênh đó
        if interaction.user.voice and interaction.user.voice.channel:
            voice_channel = interaction.user.voice.channel
        else:
            await interaction.followup.send("❌ Không tìm thấy kênh thoại `🎧│chill-room` và bạn không ở trong kênh thoại nào!", ephemeral=True)
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
        url = random.choice(DEFAULT_KPOP_SONGS)
        song_title = "bài hát ngẫu nhiên"

    queues.setdefault(guild.id, []).append(url)

    # Thông báo thêm vào queue/bắt đầu phát
    if vc.is_playing() or vc.is_paused():
        await interaction.followup.send(f"✅ Đã thêm **{song_title}** vào hàng đợi.")
    else:
        await interaction.followup.send(f"🎧 Bắt đầu phát **{song_title}**...")
        asyncio.create_task(play_next_song(vc, interaction))


# ===== /skip, /pause, /resume, /stop, /leave (Có thể xóa nếu dùng Buttons) =====
# Giữ lại để dự phòng và đảm bảo lệnh /help khớp với nội dung đã được sync.

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
        
        view = PlayerButtons(bot) # Gửi kèm nút bấm
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
        description="Bot phát nhạc ngẫu nhiên từ Dailymotion và YouTube công khai. Luôn dùng lệnh Slash (/).",
        color=0xFF0099 
    )
    
    embed.add_field(name="▶️ Phát Nhạc & Điều Khiển", value="`/play [tên/link]`, `/pause`, `/resume`, `/skip`, `/stop`", inline=False)
    embed.add_field(name="📜 Thông tin & Queue", value="`/nowplaying`, `/queue`, `/shuffle`", inline=False)
    embed.add_field(name="🚪 Quản Lý Bot", value="`/leave`", inline=False)

    embed.set_footer(text="💖 Được phát triển tại Việt Nam | Dùng /play để bắt đầu!")
    await interaction.response.send_message(embed=embed)


# ===== CHẠY BOT (Giữ nguyên) =====
TOKEN = os.getenv("DISCORD_TOKEN") 

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ LỖI NGHIÊM TRỌNG: KHÔNG TÌM THẤY DISCORD_TOKEN trong biến môi trường.")
