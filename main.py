import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import shutil
from dotenv import load_dotenv

# Załaduj token z pliku .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Znajdź FFmpeg
def find_ffmpeg():
    # Sprawdź czy ffmpeg jest w PATH
    if shutil.which('ffmpeg'):
        return 'ffmpeg'
    
    # Sprawdź typowe lokalizacje
    possible_paths = [
        r'C:\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
    ]
    
    # Szukaj folderów ffmpeg-* w C:\
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
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
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

async def play_next(guild):
    queue = get_queue(guild.id)
    voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    
    if voice_client and voice_client.is_connected():
        song = queue.get_next()
        if song:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(song['url'], download=False)
                url = info['url']
                
            voice_client.play(
                discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    play_next(guild), bot.loop
                )
            )
        else:
            await asyncio.sleep(180)  # Czekaj 3 minuty
            if voice_client and not voice_client.is_playing():
                await voice_client.disconnect()

@bot.event
async def on_ready():
    print(f'{bot.user} jest online!')
    try:
        synced = await bot.tree.sync()
        print(f'Zsynchronizowano {len(synced)} komend')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

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
        await interaction.response.send_message("❌ Bot nie jest na żadnym kanale!", ephemeral=True)

@bot.tree.command(name="play", description="Odtwórz utwór z YouTube")
@app_commands.describe(zapytanie="Nazwa utworu lub link YouTube")
async def play(interaction: discord.Interaction, zapytanie: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("❌ Musisz być na kanale głosowym!")
        return
        
    if not interaction.guild.voice_client:
        channel = interaction.user.voice.channel
        await channel.connect()
    
    queue = get_queue(interaction.guild.id)
    
    try:
        # Uruchom yt-dlp w osobnym wątku, aby nie blokować bota
        loop = asyncio.get_event_loop()
        
        def extract_info():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                query = zapytanie
                if not query.startswith('http'):
                    query = f"ytsearch1:{query}"  # Pobierz tylko pierwszy wynik
                return ydl.extract_info(query, download=False)
        
        info = await loop.run_in_executor(None, extract_info)
        
        # Obsługa playlist
        if 'entries' in info:
            entries_added = 0
            for entry in info['entries'][:10]:  # Ogranicz do 10 pierwszych utworów
                if entry:
                    song = {
                        'url': entry.get('webpage_url') or entry.get('url'),
                        'title': entry.get('title', 'Nieznany tytuł'),
                        'duration': entry.get('duration', 0)
                    }
                    queue.add(song)
                    entries_added += 1
            await interaction.followup.send(f"✅ Dodano **{entries_added}** utworów do kolejki")
        else:
            song = {
                'url': info.get('webpage_url') or info.get('url'),
                'title': info.get('title', 'Nieznany tytuł'),
                'duration': info.get('duration', 0)
            }
            queue.add(song)
            await interaction.followup.send(f"✅ Dodano do kolejki: **{song['title']}**")
        
        # Jeśli nic nie gra, zacznij odtwarzać
        voice_client = interaction.guild.voice_client
        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next(interaction.guild)
                
    except Exception as e:
        await interaction.followup.send(f"❌ Błąd: {str(e)}")

@bot.tree.command(name="pause", description="Zatrzymaj odtwarzanie")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("⏸️ Zatrzymano odtwarzanie")
    else:
        await interaction.response.send_message("❌ Nic nie jest odtwarzane!", ephemeral=True)

@bot.tree.command(name="resume", description="Wznów odtwarzanie")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("▶️ Wznowiono odtwarzanie")
    else:
        await interaction.response.send_message("❌ Odtwarzanie nie jest zatrzymane!", ephemeral=True)

@bot.tree.command(name="skip", description="Pomiń obecny utwór")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭️ Pominięto utwór")
    else:
        await interaction.response.send_message("❌ Nic nie jest odtwarzane!", ephemeral=True)

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
    queue = get_queue(interaction.guild.id)
    queue.clear()
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
    await interaction.response.send_message("🗑️ Wyczyszczono kolejkę!")

@bot.tree.command(name="loop", description="Włącz/wyłącz zapętlanie obecnego utworu")
async def loop(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)
    queue.loop = not queue.loop
    status = "włączono" if queue.loop else "wyłączono"
    await interaction.response.send_message(f"🔁 Zapętlanie {status}!")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Błąd: Nie znaleziono DISCORD_TOKEN w pliku .env")
        print("Utwórz plik .env i dodaj: DISCORD_TOKEN=twoj_token_tutaj")
    else:
        bot.run(TOKEN)
