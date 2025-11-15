import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import shutil
import re
import aiohttp
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Opcja: użyj cookies jeśli USE_COOKIES=true w .env
USE_COOKIES = os.getenv('USE_COOKIES', 'false').lower() == 'true'

if USE_COOKIES:
    print("Cookies YouTube włączone")
else:
    print("Cookies YouTube wyłączone")

# Znajdź FFmpeg
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
    
    return 'ffmpeg'  # fallback

FFMPEG_PATH = find_ffmpeg()
print(f"Używam FFmpeg z: {FFMPEG_PATH}")

# Konfiguracja intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Opcje dla yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best',  # Najlepsza jakość audio
    'noplaylist': False,  # Zezwól na playlisty
    'extract_flat': 'in_playlist',  # Szybkie pobieranie playlist
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'ignoreerrors': True,
    'postprocessors': [{  # Konwersja do najlepszej jakości
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '320',
    }],
}

# Dodaj cookies tylko jeśli są włączone
if USE_COOKIES:
    YDL_OPTIONS['cookiefile'] = 'cookies.txt'

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 320k -ar 48000 -ac 2'  # 320kbps bitrate, 48kHz sample rate, stereo
}

# Kolejka muzyki dla każdego serwera
music_queues = {}

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

async def get_spotify_track_info(track_id):
    """Pobierz informacje o utworze ze Spotify (bez autoryzacji)"""
    url = f"https://open.spotify.com/oembed?url=spotify:track:{track_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Format: "Artist - Title"
                title_parts = data.get('title', '').split(' · ')
                if len(title_parts) >= 2:
                    return f"{title_parts[1]} {title_parts[0]}"  # Artist Title
                return data.get('title', '')
    return None

async def get_spotify_playlist_info(playlist_id):
    """Pobierz informacje o playliście (wymaga web scraping - uproszczona wersja)"""
    # Dla playlist używamy tylko pierwszego utworu lub informujemy użytkownika
    return None

async def play_next(guild, text_channel=None):
    queue = get_queue(guild.id)
    voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    
    # Jeśli nie przekazano kanału, spróbuj użyć zapisanego
    if not text_channel and hasattr(bot, 'text_channels'):
        text_channel = bot.text_channels.get(guild.id)
    
    if voice_client and voice_client.is_connected():
        song = queue.get_next()
        if song:
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(song['url'], download=False)
                    
                    # Sprawdź czy film jest 18+
                    age_limit = info.get('age_limit', 0)
                    if age_limit >= 18:
                        # Film 18+ - pomiń i wyświetl ostrzeżenie
                        if text_channel:
                            try:
                                embed = discord.Embed(
                                    description=f"🔞 **Pominięto:** {song['title']}\n⚠️ Powód: Treść 18+",
                                    color=discord.Color.orange()
                                )
                                await text_channel.send(embed=embed)
                            except:
                                pass
                        # Przejdź do następnego utworu
                        await play_next(guild, text_channel)
                        return
                    
                    url = info['url']
                    
                voice_client.play(
                    discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS),
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        play_next(guild, text_channel), bot.loop
                    )
                )
                
                # Wyślij wiadomość na czat o nowej piosence
                if text_channel:
                    try:
                        embed = discord.Embed(
                            description=f"🎵 **Teraz gra:** {song['title']}",
                            color=discord.Color.blue()
                        )
                        await text_channel.send(embed=embed)
                    except:
                        pass  # Ignoruj błędy wysyłania wiadomości
                        
            except Exception as e:
                # Błąd pobierania - pomiń utwór
                if text_channel:
                    try:
                        await text_channel.send(f"18+  {song['title'][:50]}... - szkip")
                    except:
                        pass
                # Spróbuj następny utwór
                await play_next(guild, text_channel)
                return
        else:
            # Kolejka pusta - czekaj 5 minut i rozłącz jeśli dalej nic nie gra
            await asyncio.sleep(300)  # 5 minut
            if voice_client and not voice_client.is_playing() and len(queue.queue) == 0:
                await voice_client.disconnect()

@bot.event
async def on_ready():
    print(f'{bot.user} jest online!')
    try:
        synced = await bot.tree.sync()
        print(f'Zsynchronizowano {len(synced)} komend')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

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
                "`/play https://open.spotify.com/track/...`"
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
        queue = get_queue(interaction.guild.id)
        queue.clear()
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Rozłączono!")
    else:
        await interaction.response.send_message("❌ Wyrzucono z kanału głosowego", ephemeral=True)

@bot.tree.command(name="play", description="Odtwórz utwór z YouTube lub Spotify")
@app_commands.describe(zapytanie="Nazwa utworu, link YouTube lub Spotify")
async def play(interaction: discord.Interaction, zapytanie: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("❌ Musisz być na kanale głosowym!")
        return
        
    if not interaction.guild.voice_client:
        channel = interaction.user.voice.channel
        await channel.connect()
    
    # Zapisz kanał tekstowy dla powiadomień
    if not hasattr(bot, 'text_channels'):
        bot.text_channels = {}
    bot.text_channels[interaction.guild.id] = interaction.channel
    
    queue = get_queue(interaction.guild.id)
    
    try:
        # Sprawdź czy to link Spotify
        spotify_track_pattern = r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)'
        spotify_playlist_pattern = r'https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)'
        
        track_match = re.search(spotify_track_pattern, zapytanie)
        playlist_match = re.search(spotify_playlist_pattern, zapytanie)
        
        search_queries = []
        
        if track_match:
            # Pobierz informacje o utworze ze Spotify
            track_id = track_match.group(1)
            track_name = await get_spotify_track_info(track_id)
            if track_name:
                search_queries.append(track_name)
                await interaction.followup.send(f"🎵 Szukam ze Spotify: **{track_name}**")
            else:
                await interaction.followup.send("❌ Nie udało się pobrać informacji ze Spotify")
                return
                
        elif playlist_match:
            await interaction.followup.send("⚠️ Playlisty Spotify nie są obsługiwane. Użyj pojedynczego utworu lub playlisty YouTube.")
            return
        else:
            # Normalny YouTube lub wyszukiwanie
            search_queries = [zapytanie]
        
        loop = asyncio.get_event_loop()
        
        def extract_info(query):
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if not query.startswith('http'):
                    query = f"ytsearch5:{query}"  # Szukaj 5 wyników i wybierz najlepszy
                return ydl.extract_info(query, download=False)
        
        added_count = 0
        songs_added = []
        is_playlist = False
        
        for search_query in search_queries:
            try:
                info = await loop.run_in_executor(None, extract_info, search_query)
                
                if 'entries' in info:
                    entries = [e for e in info.get('entries', []) if e]  # Filtruj puste
                    
                    # Sprawdź czy to wyszukiwanie czy playlista
                    if search_query.startswith('http') and ('playlist' in search_query or 'list=' in search_query):
                        # To jest playlista YouTube - dodaj wszystkie utwory (max 50)
                        is_playlist = True
                        max_songs = 50
                        total_entries = len(entries)
                        
                        # Wyślij info że ładujemy playlistę
                        if not track_match:
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
                        
                        # Jeśli playlist ma więcej niż max_songs
                        if total_entries > max_songs:
                            await interaction.followup.send(
                                f"⚠️ Playlista ma {total_entries} utworów. Dodano tylko pierwsze {max_songs}."
                            )
                    else:
                        # To jest wyszukiwanie - weź TYLKO pierwszy wynik
                        if entries:
                            entry = entries[0]  # Najlepszy wynik
                            song = {
                                'url': f"https://www.youtube.com/watch?v={entry.get('id') or entry.get('url')}",
                                'title': entry.get('title', 'Nieznany tytuł'),
                                'duration': entry.get('duration', 0)
                            }
                            queue.add(song)
                            songs_added.append(song)
                            added_count += 1
                else:
                    # Pojedynczy utwór
                    song = {
                        'url': info.get('webpage_url') or info.get('url'),
                        'title': info.get('title', 'Nieznany tytuł'),
                        'duration': info.get('duration', 0)
                    }
                    queue.add(song)
                    songs_added.append(song)
                    added_count += 1
                    
            except Exception as e:
                # Jeśli problem z konkretnym utworem, poinformuj i kontynuuj
                error_short = str(e)[:100]
                print(f"Błąd dodawania: {e}")
                if not is_playlist:  # Pokazuj błędy tylko dla pojedynczych utworów
                    await interaction.followup.send(f"⚠️ Błąd: {error_short}")
                continue
        
        # Wyślij odpowiedź
        voice_client = interaction.guild.voice_client
        was_playing = voice_client.is_playing() or voice_client.is_paused()
        
        if added_count == 1 and not is_playlist:
            if was_playing:
                # Coś już gra - tylko dodano do kolejki
                await interaction.followup.send(f"✅ Dodano do kolejki: **{songs_added[0]['title']}**")
            else:
                # Nic nie gra - zacznij grać (play_next wyświetli "Teraz gra")
                await interaction.followup.send(f"✅ Dodano: **{songs_added[0]['title']}**")
        elif added_count > 1:
            if not is_playlist or not track_match:  # Nie duplikuj wiadomości
                await interaction.followup.send(f"✅ Dodano **{added_count}** utworów do kolejki")
        else:
            await interaction.followup.send("❌ Nie znaleziono utworu")
            return
        
        # Jeśli nic nie gra, zacznij odtwarzać
        if not was_playing:
            await play_next(interaction.guild, interaction.channel)
                
    except Exception as e:
        # Pokaż pełny błąd dla debugowania
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
        pass  # Interaction wygasła, ale komenda zadziałała

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
        pass  # Interaction wygasła, ale komenda zadziałała

@bot.tree.command(name="skip", description="Pomiń obecny utwór")
async def skip(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            queue = get_queue(interaction.guild.id)
            
            # Sprawdź co będzie dalej
            next_song = None
            if queue.loop and queue.current:
                next_song = queue.current
            elif queue.queue:
                next_song = queue.queue[0]
            
            # Zapisz kanał tekstowy dla play_next
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
        # Interaction wygasła, ale utwór został pominięty
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
        pass  # Interaction wygasła, ale kolejka została wyczyszczona

@bot.tree.command(name="loop", description="Włącz/wyłącz zapętlanie obecnego utworu")
async def loop(interaction: discord.Interaction):
    try:
        queue = get_queue(interaction.guild.id)
        queue.loop = not queue.loop
        status = "włączono" if queue.loop else "wyłączono"
        await interaction.response.send_message(f"🔁 Zapętlanie {status}!")
    except discord.errors.NotFound:
        pass  # Interaction wygasła, ale zapętlanie zostało zmienione

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Błąd: Nie znaleziono DISCORD_TOKEN w pliku .env")
        print("Utwórz plik .env i dodaj: DISCORD_TOKEN=twoj_token_tutaj")
    else:
        bot.run(TOKEN)
