# 🎵 Discord Music Bot

Profesjonalny bot Discord do odtwarzania muzyki z YouTube i Spotify na kanałach głosowych.

## ✨ Funkcje

- 🎵 **Odtwarzanie z YouTube** - pojedyncze utwory i playlisty (do 50 utworów)
- 🎧 **Obsługa Spotify** - automatyczne wyszukiwanie utworów ze Spotify na YouTube
- 🔊 **Wysoka jakość audio** - 320kbps bitrate, stereo
- 📋 **System kolejki** - zarządzaj kolejką utworów
- 🔁 **Zapętlanie** - zapętlaj ulubione utwory
- ⏯️ **Pełna kontrola** - pauza, wznów, pomiń
- 🚀 **Slash commands** - nowoczesny interfejs Discord
- 🛡️ **Stabilność** - obsługa błędów i automatyczne reconnect

## 📋 Wymagania

- **Python 3.8+**
- **FFmpeg** (wymagane do odtwarzania audio)
- **Discord Bot Token**

## 🚀 Szybki start (Windows)

### Automatyczna instalacja:

1. **Uruchom instalator:**
   ```cmd
   install.bat
   ```

2. **Skonfiguruj token:**
   - Otwórz plik `.env`
   - Wklej swój Discord token

3. **Uruchom bota:**
   ```cmd
   start_bot.bat
   ```

### Ręczna instalacja:

## 🔧 Instalacja krok po kroku

### 1. Zainstaluj FFmpeg

**Windows:**
```powershell
winget install ffmpeg
```

Lub pobierz z: https://ffmpeg.org/download.html

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 2. Zainstaluj biblioteki Python

```bash
pip install -r requirements.txt
```

Lub ręcznie:
```bash
pip install discord.py[voice] yt-dlp python-dotenv aiohttp
```

### 3. Utwórz bota Discord

1. Wejdź na: https://discord.com/developers/applications
2. Kliknij **"New Application"**
3. Nadaj nazwę botowi
4. Przejdź do zakładki **"Bot"**
5. Kliknij **"Add Bot"**
6. **Skopiuj token** (Reset Token → Copy)
7. **Włącz Privileged Gateway Intents:**
   - ✅ PRESENCE INTENT
   - ✅ SERVER MEMBERS INTENT  
   - ✅ MESSAGE CONTENT INTENT
8. Kliknij **"Save Changes"**

### 4. Dodaj bota na serwer

1. Przejdź do **"OAuth2" → "URL Generator"**
2. Zaznacz **Scopes:**
   - ✅ `bot`
   - ✅ `applications.commands`
3. Zaznacz **Bot Permissions:**
   - ✅ Send Messages
   - ✅ Connect
   - ✅ Speak
   - ✅ Use Voice Activity
4. Skopiuj **wygenerowany URL**
5. Otwórz w przeglądarce i dodaj na serwer

### 5. Konfiguracja

Edytuj plik `.env`:
```env
DISCORD_TOKEN=twoj_token_tutaj
```

## 🎮 Uruchamianie

**Windows (z skryptem):**
```cmd
start_bot.bat
```

**Ręcznie:**
```bash
python main.py
```

Komunikat o sukcesie:
```
Używam FFmpeg z: C:\ffmpeg\bin\ffmpeg.exe
BotName#1234 jest online!
Zsynchronizowano 9 komend
```

## 📖 Komendy

| Komenda | Opis | Przykład |
|---------|------|----------|
| `/help` | Pokaż pomoc | `/help` |
| `/join` | Dołącz do kanału głosowego | `/join` |
| `/leave` | Opuść kanał | `/leave` |
| `/play <zapytanie>` | Odtwórz muzykę | `/play never gonna give you up` |
| `/pause` | Zatrzymaj odtwarzanie | `/pause` |
| `/resume` | Wznów odtwarzanie | `/resume` |
| `/skip` | Pomiń utwór | `/skip` |
| `/queue` | Pokaż kolejkę | `/queue` |
| `/clear` | Wyczyść kolejkę | `/clear` |
| `/loop` | Zapętl utwór | `/loop` |

## 💡 Przykłady użycia

**YouTube:**
```
/play never gonna give you up
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ
/play https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG
```

**Spotify:**
```
/play https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
```
*Uwaga: Bot wyszukuje utwory Spotify na YouTube*

**Kontrola odtwarzania:**
```
/pause          # Zatrzymaj
/resume         # Wznów
/skip           # Następny utwór
/loop           # Zapętl obecny utwór
/queue          # Zobacz kolejkę
/clear          # Wyczyść wszystko
```

## 🎵 Obsługiwane źródła

- ✅ **YouTube** - filmy i playlisty (max 50 utworów)
- ✅ **Spotify** - pojedyncze utwory (konwertowane do YouTube)
- ✅ **Wyszukiwanie** - bezpośrednie wyszukiwanie po nazwie

## ⚙️ Konfiguracja zaawansowana

### Jakość audio

Bot domyślnie używa:
- **320kbps bitrate**
- **48kHz sample rate**
- **Stereo**

Możesz zmienić w `main.py`:
```python
FFMPEG_OPTIONS = {
    'options': '-vn -b:a 320k -ar 48000 -ac 2'
}
```

### Limit playlist

Domyślnie: **50 utworów**

Zmień w `main.py` (linia ~294):
```python
max_songs = 50  # Zmień na dowolną liczbę
```

## ⚠️ Rozwiązywanie problemów

### Bot nie uruchamia się

**Problem:** `ModuleNotFoundError: No module named 'discord'`
```bash
pip install -r requirements.txt
```

**Problem:** `Nie znaleziono DISCORD_TOKEN`
- Sprawdź czy plik `.env` istnieje
- Upewnij się że token jest poprawny

### Bot nie łączy się z kanałem

**Problem:** `ffmpeg was not found`
```bash
# Sprawdź FFmpeg
ffmpeg -version

# Windows - zainstaluj
winget install ffmpeg
```

**Problem:** `PrivilegedIntentsRequired`
- Włącz wszystkie 3 Intents w Developer Portal (Bot → Privileged Gateway Intents)

### Bot nie odpowiada na komendy

- Poczekaj **5-10 minut** po dodaniu (synchronizacja)
- Sprawdź czy **MESSAGE CONTENT INTENT** jest włączony
- Zrestartuj bota

### Problemy z odtwarzaniem

**Problem:** Bot się zawiesza przy playlistach
- Normalne przy dużych playlistach (ładowanie ~2-3 sekundy)
- Bot używa `extract_flat` dla szybkości

**Problem:** "Unknown interaction"
- Discord timeout (3 sekundy) - normalne przy większych playlistach
- Muzyka powinna się odtwarzać mimo błędu

**Problem:** Słaba jakość audio
- Sprawdź ustawienia Discord (User Settings → Voice & Video → Audio Quality: High)
- Bot już używa 320kbps

## 🔒 Bezpieczeństwo

- ✅ Token w pliku `.env` (nie commituj do git!)
- ✅ `.gitignore` chroni wrażliwe pliki
- ✅ Brak zapisywania muzyki na dysku
- ✅ Streaming bezpośrednio z YouTube

## 🌐 Hosting (24/7)

### Darmowe opcje:

**Railway.app (Polecane):**
1. Push kod na GitHub
2. railway.app → Deploy from GitHub
3. Dodaj zmienną `DISCORD_TOKEN`
4. Bot działa 24/7 (500h/miesiąc free)

**Render.com:**
- Darmowy tier
- Bot uśpia się po 15 min nieaktywności

**fly.io:**
- Darmowy tier wystarczający dla małych botów

### Pliki potrzebne do hostingu:
- ✅ `Procfile` - już utworzony
- ✅ `requirements.txt` - aktualne
- ✅ `.gitignore` - zabezpiecza token

## 📁 Struktura projektu

```
DiscordBot/
├── main.py              # Główny kod bota
├── .env                 # Token Discord (NIE commituj!)
├── .gitignore          # Pliki ignorowane przez git
├── requirements.txt     # Zależności Python
├── Procfile            # Konfiguracja dla hostingu
├── README.md           # Ta dokumentacja
├── start_bot.bat       # Skrypt uruchamiający (Windows)
└── install.bat         # Skrypt instalacyjny (Windows)
```

## 🤝 Wsparcie

Problemy? Sprawdź:
1. Sekcję "Rozwiązywanie problemów" powyżej
2. Logi w terminalu
3. Issues na GitHub

## 📝 Licencja

Open-source - używaj i modyfikuj swobodnie!

---

**Stworzony z ❤️ | Obsługuje YouTube i Spotify**
