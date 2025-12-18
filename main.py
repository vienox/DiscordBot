import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import shutil
import re
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv, dotenv_values
from PIL import Image, ImageDraw, ImageFont
import math
import random
import io
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Wczytaj wartości bezpośrednio z pliku .env (ignoruj zmienne systemowe)
env_path = os.path.join(os.path.dirname(__file__), '.env')
env_values = dotenv_values(env_path)

TOKEN = env_values.get('DISCORD_TOKEN') or os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = env_values.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = env_values.get('SPOTIFY_CLIENT_SECRET')

USE_COOKIES = os.getenv('USE_COOKIES', 'false').lower() == 'true'

if USE_COOKIES:
    print("Cookies YouTube włączone")
else:
    print("Cookies YouTube wyłączone")

def find_ffmpeg():
    if shutil.which('ffmpeg'):
        return 'ffmpeg'
    
    possible_paths = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    
    try:
        import glob
        ffmpeg_dirs = glob.glob(r'C:\ffmpeg-*')
        for dir in ffmpeg_dirs:
            possible_paths.append(os.path.join(dir, 'bin', 'ffmpeg.exe'))
    except:
        pass
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return 'ffmpeg'

FFMPEG_PATH = find_ffmpeg()
print(f"Używam FFmpeg z: {FFMPEG_PATH}")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

YDL_OPTIONS = {
    'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best',
    'noplaylist': False,
    'extract_flat': 'in_playlist',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'ignoreerrors': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '320',
    }],
}

if USE_COOKIES:
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 320k -ar 48000 -ac 2'
}

music_queues = {}
giveaways = {}

def create_wheel_of_fortune_gif(usernames, winner_name):
    """Generuje GIF koła fortuny z uczestnikami"""
    width, height = 600, 600
    center_x, center_y = width // 2, height // 2
    radius = 250
    
    # Kolory dla każdego segmentu
    colors = [
        (255, 99, 71), (75, 192, 192), (255, 205, 86),
        (54, 162, 235), (153, 102, 255), (255, 159, 64),
        (199, 199, 199), (83, 102, 255), (255, 99, 132),
        (75, 255, 192)
    ]
    
    frames = []
    num_users = len(usernames)
    angle_per_segment = 360 / num_users
    winner_index = usernames.index(winner_name)
    
    spin_frames = 30
    hold_frames = 20
    total_frames = spin_frames + hold_frames
    
    for frame_num in range(total_frames):
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        if frame_num < spin_frames:
            progress = frame_num / spin_frames
            easing = 1 - (1 - progress) ** 3
        else:
            easing = 1.0
        
        target_angle = 0 - (winner_index * angle_per_segment) - (angle_per_segment / 2)
        rotation = easing * (720 + target_angle)
        for i, username in enumerate(usernames):
            start_angle = (i * angle_per_segment) + rotation
            end_angle = start_angle + angle_per_segment
            color = colors[i % len(colors)]
            
            draw.pieslice(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                start=start_angle,
                end=end_angle,
                fill=color,
                outline=(255, 255, 255),
                width=3
            )
            
            text_angle = math.radians(start_angle + angle_per_segment / 2)
            text_radius = radius * 0.7
            text_x = center_x + text_radius * math.cos(text_angle)
            text_y = center_y + text_radius * math.sin(text_angle)
            
            display_name = username[:10] + "..." if len(username) > 10 else username
            
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), display_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(
                (text_x - text_width // 2, text_y - text_height // 2),
                display_name,
                fill=(255, 255, 255),
                font=font
            )
        
        inner_radius = 40
        draw.ellipse(
            [center_x - inner_radius, center_y - inner_radius,
             center_x + inner_radius, center_y + inner_radius],
            fill=(255, 215, 0),
            outline=(255, 255, 255),
            width=3
        )
        
        if frame_num >= spin_frames:
            try:
                winner_font = ImageFont.truetype("arial.ttf", 16)
            except:
                winner_font = ImageFont.load_default()
            
            display_winner = winner_name[:12] + "..." if len(winner_name) > 12 else winner_name
            bbox = draw.textbbox((0, 0), display_winner, font=winner_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(
                (center_x - text_width // 2, center_y - text_height // 2),
                display_winner,
                fill=(0, 0, 0),
                font=winner_font
            )
        
        arrow_points = [
            (center_x + radius + 10, center_y),  
            (center_x + radius + 30, center_y - 20),  
            (center_x + radius + 30, center_y + 20)
        ]
        draw.polygon(arrow_points, fill=(255, 0, 0))
        
        status_text = "🎉 WINNER! 🎉" if frame_num >= spin_frames else "🎰 SPINNING..."
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), status_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((width - text_width) // 2, 20),
            status_text,
            fill=(255, 255, 255),
            font=title_font
        )
        
        frames.append(img)
    
    output = io.BytesIO()
    frames[0].save(
        output,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=100,  
        loop=0
    )
    output.seek(0)
    return output

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = False
        
    def add(self, song):
        self.queue.append(song)
        
    def get_next(self):
        if self.loop and self.current:
            return self.current
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        return None
        
    def clear(self):
        self.queue.clear()
        self.current = None

def get_queue(guild_id):
    if guild_id not in music_queues:
        music_queues[guild_id] = MusicQueue()
    return music_queues[guild_id]

async def cleanup_guild_state(guild):
    """Rozlacz bota i usun stan kolejki oraz zapamietane kanaly tekstowe dla serwera."""
    guild_id = guild.id
    queue = music_queues.pop(guild_id, None)
    if queue:
        queue.clear()
    if hasattr(bot, 'text_channels'):
        bot.text_channels.pop(guild_id, None)
    voice_client = guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect(force=True)

async def get_spotify_track_info(track_id):
    """Pobierz informacje o utworze ze Spotify (bez autoryzacji)"""
    url = f"https://open.spotify.com/oembed?url=spotify:track:{track_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                title_parts = data.get('title', '').split(' · ')
                if len(title_parts) >= 2:
                    return f"{title_parts[1]} {title_parts[0]}"  
                return data.get('title', '')
    return None

async def get_spotify_playlist_info(playlist_id):
    """Pobierz 25 utworów z playlisty/albumu Spotify przez API"""
    try:
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            print("Spotify: Brak kluczy API w .env")
            return None
        
        # Inicjalizuj Spotify client
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        tracks = []
        
        # Spróbuj jako playlist
        try:
            results = sp.playlist_tracks(playlist_id, limit=25)
            items = results['items']
            
            for item in items:
                track = item.get('track')
                if track:
                    artists = ', '.join([artist['name'] for artist in track['artists']])
                    title = track['name']
                    track_str = f"{artists} {title}"
                    tracks.append(track_str)
            
            if tracks:
                print(f"Spotify Playlist: Znaleziono {len(tracks)} utworów")
                return tracks[:25]
        
        except:
            # Spróbuj jako album
            try:
                results = sp.album_tracks(playlist_id, limit=25)
                items = results['items']
                
                for track in items:
                    artists = ', '.join([artist['name'] for artist in track['artists']])
                    title = track['name']
                    track_str = f"{artists} {title}"
                    tracks.append(track_str)
                
                if tracks:
                    print(f"Spotify Album: Znaleziono {len(tracks)} utworów")
                    return tracks[:25]
            except:
                pass
        
        print("Spotify: Nie znaleziono playlisty/albumu")
        return None
        
    except Exception as e:
        print(f"Błąd Spotify API: {e}")
        return None

async def play_next(guild, text_channel=None):
    queue = get_queue(guild.id)
    voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    
    if not text_channel and hasattr(bot, 'text_channels'):
        text_channel = bot.text_channels.get(guild.id)
    
    if voice_client and voice_client.is_connected():
        song = queue.get_next()
        if song:
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    
                    age_limit = info.get('age_limit', 0)
                    if age_limit >= 18:
                        if text_channel:
                            try:
                                embed = discord.Embed(
                                    description=f"🔞 **Pominięto:** {song['title']}\n⚠️ Powód: Treść 18+",
                                    color=discord.Color.orange()
                                )
                                await text_channel.send(embed=embed)
                            except:
                                pass
                        await play_next(guild, text_channel)
                        return
                    
                    url = info['url']
                    
                def after_playing(error):
                    if error:
                        print(f"Player error: {error}")
                    asyncio.run_coroutine_threadsafe(
                        play_next(guild, text_channel), bot.loop
                    )
                
                voice_client.play(
                    discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS),
                    after=after_playing
                )
                

                if text_channel:
                    try:
                        embed = discord.Embed(
                            description=f"🎵 **Teraz gra:** {song['title']}",
                            color=discord.Color.blue()
                        )
                        await text_channel.send(embed=embed)
                    except:
                        pass
                        
            except Exception as e:
                if text_channel:
                    try:
                        await text_channel.send(f"18+  {song['title'][:50]}... - szkip")
                    except:
                        pass
                await play_next(guild, text_channel)
                return
        else:
            await asyncio.sleep(300)
            if voice_client and not voice_client.is_playing() and len(queue.queue) == 0:
                await voice_client.disconnect()

@bot.event
async def on_ready():
    print(f'{bot.user} jest online!')
    try:
        synced = await bot.tree.sync()
        print(f'Zsynchronizowano {len(synced)} komend')
        for cmd in synced:
            print(f'  ✓ {cmd.name}')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

@bot.event
async def on_voice_state_update(member, before, after):
    if not bot.user or member.id != bot.user.id:
        return
    if before.channel and after.channel and before.channel != after.channel:
        text_channel = None
        if hasattr(bot, 'text_channels'):
            text_channel = bot.text_channels.get(member.guild.id)
        await cleanup_guild_state(member.guild)
        if text_channel:
            try:
                await text_channel.send("Kanal glosowy zostal zmieniony - bot rozlaczyl sie i wyczyscil kolejke.")
            except:
                pass

@bot.tree.command(name="help", description="Pokaż listę wszystkich komend")
async def help_command(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title="🎵 Pomoc - Komendy Muzycznego Bota",
            description="Oto lista wszystkich dostępnych komend:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="▶️ Podstawowe",
            value=(
                "`/join` - Bot dołącza do kanału głosowego\n"
                "`/leave` - Bot opuszcza kanał głosowy\n"
                "`/help` - Pokaż tę wiadomość"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎵 Odtwarzanie",
            value=(
                "`/play <zapytanie>` - Odtwórz utwór z YouTube/Spotify\n"
                "`/pause` - Zatrzymaj odtwarzanie\n"
                "`/resume` - Wznów odtwarzanie\n"
                "`/skip` - Pomiń obecny utwór\n"
                "`/stop` - Zatrzymaj i wyczyść kolejkę"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Kolejka",
            value=(
                "`/queue` - Pokaż kolejkę utworów\n"
                "`/clear` - Wyczyść kolejkę\n"
                "`/loop` - Włącz/wyłącz zapętlanie utworu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Przykłady użycia",
            value=(
                "`/play never gonna give you up`\n"
                "`/play https://www.youtube.com/watch?v=...`\n"
                "`/play https://www.youtube.com/playlist?list=...`\n"
                "`/play https://open.spotify.com/track/...`\n"
                "`/play https://open.spotify.com/playlist/...`\n"
                "`/play https://open.spotify.com/album/...`"
            ),
            inline=False
        )
        
        embed.set_footer(text="Bot stworzony z ❤️ | Obsługuje YouTube i Spotify")
        
        await interaction.response.send_message(embed=embed)
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="join", description="Bot dołącza do Twojego kanału głosowego")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Musisz być na kanale głosowym!", ephemeral=True)
        return
        
    channel = interaction.user.voice.channel
    
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
        await interaction.response.send_message(f"🔊 Przeniesiono do **{channel.name}**")
    else:
        await channel.connect()
        await interaction.response.send_message(f"🔊 Dołączono do **{channel.name}**")

@bot.tree.command(name="leave", description="Bot opuszcza kanał głosowy")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await cleanup_guild_state(interaction.guild)
        await interaction.response.send_message("👋 Rozłączono!")
    else:
        await interaction.response.send_message("❌ Wyrzucono z kanału głosowego", ephemeral=True)

@bot.tree.command(name="play", description="Odtwórz utwór z YouTube lub Spotify")
@app_commands.describe(zapytanie="Nazwa utworu, link YouTube lub Spotify")
async def play(interaction: discord.Interaction, zapytanie: str):
    try:
        await interaction.response.defer()
    except discord.errors.NotFound:
        pass
    
    if not interaction.user.voice:
        try:
            await interaction.followup.send("❌ Musisz być na kanale głosowym!")
        except:
            pass
        return
        
    if not interaction.guild.voice_client:
        channel = interaction.user.voice.channel
        await channel.connect()
    
    if not hasattr(bot, 'text_channels'):
        bot.text_channels = {}
    bot.text_channels[interaction.guild.id] = interaction.channel
    
    queue = get_queue(interaction.guild.id)
    
    try:
        spotify_track_pattern = r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)'
        spotify_playlist_pattern = r'https?://open\.spotify\.com/(playlist|album)/([a-zA-Z0-9]+)'
        
        track_match = re.search(spotify_track_pattern, zapytanie)
        playlist_match = re.search(spotify_playlist_pattern, zapytanie)
        
        search_queries = []
        
        if track_match:
            track_id = track_match.group(1)
            track_name = await get_spotify_track_info(track_id)
            if track_name:
                search_queries.append(track_name)
                await interaction.followup.send(f"🎵 Szukam ze Spotify: **{track_name}**")
            else:
                await interaction.followup.send("❌ Nie udało się pobrać informacji ze Spotify")
                return
                
        elif playlist_match:
            playlist_id = playlist_match.group(2)
            await interaction.followup.send("📥 Pobieram playlistę Spotify...")
            
            tracks = await get_spotify_playlist_info(playlist_id)
            if tracks:
                search_queries = tracks
                await interaction.followup.send(f"✅ Znaleziono {len(tracks)} utworów ze Spotify")
            else:
                await interaction.followup.send("❌ Nie udało się pobrać playlisty Spotify")
                return
        else:
            search_queries = [zapytanie]
        
        loop = asyncio.get_event_loop()
        
        def extract_info(query):
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if not query.startswith('http'):
                    query = f"ytsearch5:{query}"
                return ydl.extract_info(query, download=False)
        
        added_count = 0
        songs_added = []
        is_playlist = False
        is_spotify_playlist = len(search_queries) > 1 and (track_match or playlist_match)
        
        for search_query in search_queries:
            try:
                info = await loop.run_in_executor(None, extract_info, search_query)
                
                if 'entries' in info:
                    entries = [e for e in info.get('entries', []) if e]
                    if search_query.startswith('http') and ('playlist' in search_query or 'list=' in search_query):
                        is_playlist = True
                        max_songs = 50
                        total_entries = len(entries)
                        
                        await interaction.followup.send(f"📥 Ładuję playlistę: {total_entries} utworów...")
                        
                        for entry in entries[:max_songs]:  
                            song = {
                                'url': f"https://www.youtube.com/watch?v={entry.get('id') or entry.get('url')}",
                                'title': entry.get('title', 'Nieznany tytuł'),
                                'duration': entry.get('duration', 0)
                            }
                            queue.add(song)
                            songs_added.append(song)
                            added_count += 1
                        
                        if total_entries > max_songs:
                            await interaction.followup.send(
                                f"⚠️ Playlista ma {total_entries} utworów. Dodano tylko pierwsze {max_songs}."
                            )
                    else:
                        if entries:
                            entry = entries[0]
                            song = {
                                'url': f"https://www.youtube.com/watch?v={entry.get('id') or entry.get('url')}",
                                'title': entry.get('title', 'Nieznany tytuł'),
                                'duration': entry.get('duration', 0)
                            }
                            queue.add(song)
                            songs_added.append(song)
                            added_count += 1
                else:
                    song = {
                        'url': info.get('webpage_url') or info.get('url'),
                        'title': info.get('title', 'Nieznany tytuł'),
                        'duration': info.get('duration', 0)
                    }
                    queue.add(song)
                    songs_added.append(song)
                    added_count += 1
                    
            except Exception as e:
                error_short = str(e)[:100]
                print(f"Błąd dodawania: {e}")
                if not is_playlist:
                    await interaction.followup.send(f"⚠️ Błąd: {error_short}")
                continue
        
        voice_client = interaction.guild.voice_client
        was_playing = voice_client.is_playing() or voice_client.is_paused()
        
        if added_count == 1 and not is_spotify_playlist:
            if was_playing:
                await interaction.followup.send(f"✅ Dodano do kolejki: **{songs_added[0]['title']}**")
            else:
                await interaction.followup.send(f"✅ Dodano: **{songs_added[0]['title']}**")
        elif added_count > 1:
            if not is_playlist:
                await interaction.followup.send(f"✅ Dodano **{added_count}** utworów do kolejki")
        else:
            await interaction.followup.send("❌ Nie znaleziono utworu")
            return
        
        if not was_playing:
            await play_next(interaction.guild, interaction.channel)
                
    except Exception as e:
        error_msg = f"❌ Błąd: {str(e)}"
        if len(error_msg) > 2000:
            error_msg = error_msg[:1997] + "..."
        await interaction.followup.send(error_msg)
        print(f"Pełny błąd play: {e}")

@bot.tree.command(name="pause", description="Zatrzymaj odtwarzanie")
async def pause(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Zatrzymano odtwarzanie")
        else:
            await interaction.response.send_message("❌ Nic nie jest odtwarzane!", ephemeral=True)
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="resume", description="Wznów odtwarzanie")
async def resume(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Wznowiono odtwarzanie")
        else:
            await interaction.response.send_message("❌ Odtwarzanie nie jest zatrzymane!", ephemeral=True)
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="skip", description="Pomiń obecny utwór")
async def skip(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            queue = get_queue(interaction.guild.id)
            
            next_song = None
            if queue.loop and queue.current:
                next_song = queue.current
            elif queue.queue:
                next_song = queue.queue[0]
            
            guild_id = interaction.guild.id
            if not hasattr(bot, 'text_channels'):
                bot.text_channels = {}
            bot.text_channels[guild_id] = interaction.channel
            
            voice_client.stop()
            
            if next_song:
                await interaction.response.send_message(f"⏭️ Pominięto utwór")
            else:
                await interaction.response.send_message("⏭️ Pominięto utwór (to był ostatni w kolejce)")
        else:
            await interaction.response.send_message("❌ Nic nie jest odtwarzane!", ephemeral=True)
    except discord.errors.NotFound:
        if voice_client and voice_client.is_playing():
            voice_client.stop()

@bot.tree.command(name="queue", description="Pokaż kolejkę utworów")
async def queue(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)
    
    if not queue.current and not queue.queue:
        await interaction.response.send_message("📭 Kolejka jest pusta!")
        return
        
    embed = discord.Embed(title="🎵 Kolejka muzyki", color=discord.Color.blue())
    
    if queue.current:
        embed.add_field(
            name="▶️ Teraz gra:",
            value=f"**{queue.current['title']}**",
            inline=False
        )
    
    if queue.queue:
        queue_list = "\n".join([
            f"{i+1}. {song['title']}" 
            for i, song in enumerate(queue.queue[:10])
        ])
        if len(queue.queue) > 10:
            queue_list += f"\n... i jeszcze {len(queue.queue) - 10} utworów"
        embed.add_field(
            name=f"📋 Następne ({len(queue.queue)} utworów):",
            value=queue_list,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Wyczyść kolejkę muzyki")
async def clear(interaction: discord.Interaction):
    try:
        queue = get_queue(interaction.guild.id)
        queue.clear()
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        await interaction.response.send_message("🗑️ Wyczyszczono kolejkę!")
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="loop", description="Włącz/wyłącz zapętlanie obecnego utworu")
async def loop(interaction: discord.Interaction):
    try:
        queue = get_queue(interaction.guild.id)
        queue.loop = not queue.loop
        status = "włączono" if queue.loop else "wyłączono"
        await interaction.response.send_message(f"🔁 Zapętlanie {status}!")
    except discord.errors.NotFound:
        pass

@bot.tree.command(name="giveaway", description="Zacznij giveaway - ludzie wpisują /ticket aby wziąć udział")
async def giveaway(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    
    if guild_id in giveaways and giveaways[guild_id]['active']:
        await interaction.response.send_message("Losowanie już trwa! Użyj `/results` aby wylosować zwycięzcę.", ephemeral=True)
        return
    
    giveaways[guild_id] = {'users': [], 'active': True}
    
    embed = discord.Embed(
        title="🎉 GIVEAWAY ROZPOCZĘTY!",
        description="Wpisz `/ticket` aby wziąć udział w giveaway!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Uczestnicy", value="0", inline=False)
    embed.set_footer(text="Wpisz /ticket aby dołączyć")
    
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    giveaways[guild_id]['message_id'] = msg.id
    giveaways[guild_id]['channel_id'] = interaction.channel.id

@bot.tree.command(name="ticket", description="Weź udział w aktualnym giveaway")
async def ticket(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    
    if guild_id not in giveaways or not giveaways[guild_id]['active']:
        await interaction.response.send_message("❌ Nie ma aktualnego giveaway!", ephemeral=True)
        return
    
    if interaction.user.id in giveaways[guild_id]['users']:
        await interaction.response.send_message("❌ Już jesteś w giveaway!", ephemeral=True)
        return
    
    giveaways[guild_id]['users'].append(interaction.user.id)
    await interaction.response.send_message(f"✅ Dołączyłeś do giveaway! Uczestników: {len(giveaways[guild_id]['users'])}", ephemeral=True)
    try:
        channel = bot.get_channel(giveaways[guild_id]['channel_id'])
        message = await channel.fetch_message(giveaways[guild_id]['message_id'])
        
        embed = message.embeds[0]
        embed.set_field_at(0, name="Uczestnicy", value=str(len(giveaways[guild_id]['users'])), inline=False)
        await message.edit(embed=embed)
    except:
        pass

@bot.tree.command(name="results", description="Wylosuj zwycięzcę giveaway")
async def results(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    
    if guild_id not in giveaways or not giveaways[guild_id]['active']:
        await interaction.response.send_message("❌ Nie ma aktualnego giveaway!", ephemeral=True)
        return
    
    users_ids = giveaways[guild_id]['users']
    
    if not users_ids:
        await interaction.response.send_message("❌ Brak uczestników w giveaway!", ephemeral=True)
        return
    
    usernames = []
    for user_id in users_ids:
        member = interaction.guild.get_member(user_id)
        if member:
            usernames.append(member.display_name)
    
    winner_id = random.choice(users_ids)
    winner = interaction.guild.get_member(winner_id)
    winner_name = winner.display_name
    
    giveaways[guild_id]['active'] = False
    
    await interaction.response.defer()
    
    try:
        gif_bytes = await asyncio.to_thread(create_wheel_of_fortune_gif, usernames, winner_name)
        file = discord.File(gif_bytes, filename="wheel_of_fortune.gif")
        
        embed = discord.Embed(
            title="🎰 KOŁO FORTUNY!",
            description="Losowanie zwycięzcy...",
            color=discord.Color.gold()
        )
        embed.add_field(name="Liczba uczestników", value=str(len(users_ids)), inline=True)
        embed.set_image(url="attachment://wheel_of_fortune.gif")
        
        await interaction.followup.send(embed=embed, file=file)
        
        await asyncio.sleep(3)
        
        winner_embed = discord.Embed(
            title="🏆 ZWYCIĘZCA!",
            description=f"Gratulacje {winner.mention}!",
            color=discord.Color.gold()
        )
        winner_embed.add_field(name="Zwycięzca", value=winner.mention, inline=True)
        await interaction.followup.send(embed=winner_embed)
    except Exception as e:
        embed = discord.Embed(
            title="🏆 ZWYCIĘZCA GIVEAWAY!",
            description=f"Gratulacje {winner.mention}!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Liczba uczestników", value=str(len(users_ids)), inline=True)
        embed.add_field(name="Zwycięzca", value=winner.mention, inline=True)
        await interaction.followup.send(embed=embed)
        print(f"Błąd generowania GIF: {e}")
    


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Błąd: Nie znaleziono DISCORD_TOKEN w pliku .env")
        print("Utwórz plik .env i dodaj: DISCORD_TOKEN=twoj_token_tutaj")
    else:
        bot.run(TOKEN)
