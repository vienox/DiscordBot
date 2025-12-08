# 🎵 Discord Music Bot

Bot Discord do odtwarzania muzyki z YouTube i Spotify.

## Funkcje

- Odtwarzanie z YouTube (pojedyncze utwory i playlisty)
- Obsługa linków Spotify
- Jakość audio 320kbps
- System kolejki
- Zapętlanie utworów
- Kontrola odtwarzania (pause/resume/skip)

## Wymagania

- Python 3.8+
- FFmpeg
- Discord Bot Token

## Instalacja

### Windows (automatyczna):

```cmd
install.bat
```

Edytuj `.env` i wklej token Discord, potem:

```cmd
start_bot.bat
```

### Ręczna instalacja:

**1. Zainstaluj FFmpeg:**
```powershell
winget install ffmpeg
```

**2. Zainstaluj biblioteki:**
```bash
pip install -r requirements.txt
```

**3. Stwórz bota Discord:**
- https://discord.com/developers/applications
- New Application → Bot → Copy Token
- Włącz wszystkie 3 Privileged Gateway Intents
- OAuth2 → URL Generator → zaznacz `bot` i `applications.commands`
- Bot Permissions: Send Messages, Connect, Speak

**4. Konfiguracja:**

Stwórz plik `.env`:
```env
DISCORD_TOKEN=twoj_token_tutaj
USE_COOKIES=false
```

**5. Uruchom:**
```bash
python main.py
```

## Komendy

| Komenda | Opis |
|---------|------|
| `/help` | Pomoc |
| `/join` | Dołącz do kanału |
| `/leave` | Opuść kanał |
| `/play <query>` | Odtwórz muzykę |
| `/pause` | Pauza |
| `/resume` | Wznów |
| `/skip` | Pomiń |
| `/queue` | Pokaż kolejkę |
| `/clear` | Wyczyść kolejkę |
| `/loop` | Zapętl utwór |

## Przykłady

```
/play never gonna give you up
/play https://youtube.com/watch?v=...
/play https://youtube.com/playlist?list=...
/play https://open.spotify.com/track/...
```

## Rozwiązywanie problemów

**Bot nie uruchamia się:**
```bash
pip install -r requirements.txt
```

**Brak FFmpeg:**
```bash
ffmpeg -version
winget install ffmpeg  # Windows
```

**Brak komend Discord:**
- Włącz wszystkie Privileged Gateway Intents w Developer Portal
- Poczekaj 5-10 minut na synchronizację

**Problemy z YouTube:**
- Wyeksportuj cookies YouTube
- Zapisz jako `cookies.txt` w folderze projektu
- W `.env` ustaw `USE_COOKIES=true`

## Hosting 24/7

**Railway.app (zalecane):**
1. Push na GitHub
2. railway.app → Deploy from GitHub
3. Dodaj zmienną środowiskową `DISCORD_TOKEN`
4. Opcjonalnie: `YOUTUBE_COOKIES` (zawartość pliku cookies.txt)

**Inne opcje:** Render.com, fly.io

## Struktura

```
DiscordBot/
├── main.py              # Kod bota
├── .env                 # Token (NIE commituj!)
├── .gitignore          
├── requirements.txt     
├── Procfile            # Hosting config
├── README.md           
├── start_bot.bat       # Windows launcher
└── install.bat         # Windows installer
```

## Bezpieczeństwo

- Token w `.env` chroniony przez `.gitignore`
- Brak zapisywania plików muzycznych
- Streaming bezpośrednio z YouTube

---

Made with ❤️
