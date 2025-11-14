# 🎵 Discord Music Bot

Bot Discord do odtwarzania muzyki z YouTube na kanałach głosowych.

## 📋 Wymagania

- Python 3.8 lub nowszy
- FFmpeg (wymagane do odtwarzania audio)

## 🔧 Instalacja

### 1. Zainstaluj FFmpeg

**Windows:**
- Pobierz z: https://ffmpeg.org/download.html
- Rozpakuj i dodaj do zmiennej PATH
- Lub użyj: `winget install ffmpeg`

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 2. Zainstaluj zależności Python

Biblioteki zostały już zainstalowane. Jeśli potrzebujesz reinstalacji:
```bash
pip install discord.py[voice] yt-dlp python-dotenv
```

### 3. Utwórz bota Discord

1. Idź na: https://discord.com/developers/applications
2. Kliknij "New Application"
3. Nadaj nazwę botowi
4. Przejdź do zakładki "Bot"
5. Kliknij "Add Bot"
6. Skopiuj token (kliknij "Reset Token" jeśli trzeba)
7. Włącz następujące intencje (Privileged Gateway Intents):
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT
   - ✅ PRESENCE INTENT

### 4. Dodaj bota do serwera

1. Przejdź do zakładki "OAuth2" → "URL Generator"
2. Zaznacz:
   - **Scopes:** `bot`, `applications.commands`
   - **Bot Permissions:** 
     - Send Messages
     - Connect
     - Speak
     - Use Voice Activity
3. Skopiuj wygenerowany URL i otwórz w przeglądarce
4. Wybierz serwer i autoryzuj bota

### 5. Skonfiguruj token

Otwórz plik `.env` i wklej swój token:
```
DISCORD_TOKEN=tutaj_wklej_swoj_token
```

## 🚀 Uruchamianie

```bash
python main.py
```

Jeśli wszystko działa poprawnie, zobaczysz:
```
NazwaBota#1234 jest online!
Zsynchronizowano X komend
```

## 📖 Komendy

Wszystkie komendy używają slash commands (`/`):

| Komenda | Opis |
|---------|------|
| `/join` | Bot dołącza do Twojego kanału głosowego |
| `/leave` | Bot opuszcza kanał głosowy |
| `/play <zapytanie>` | Odtwórz utwór (nazwa lub link YouTube) |
| `/pause` | Zatrzymaj odtwarzanie |
| `/resume` | Wznów odtwarzanie |
| `/skip` | Pomiń obecny utwór |
| `/queue` | Pokaż kolejkę utworów |
| `/clear` | Wyczyść kolejkę muzyki |
| `/loop` | Włącz/wyłącz zapętlanie utworu |

## 💡 Przykłady użycia

```
/join
/play never gonna give you up
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ
/play https://www.youtube.com/playlist?list=...
/pause
/resume
/skip
/queue
/loop
/clear
/leave
```

## 🛠️ Funkcje

- ✅ Odtwarzanie muzyki z YouTube (pojedyncze utwory i playlisty)
- ✅ Kolejka utworów
- ✅ Pauza/wznowienie
- ✅ Pomijanie utworów
- ✅ Zapętlanie utworu
- ✅ Automatyczne rozłączanie po 3 minutach bezczynności
- ✅ Slash commands (nowoczesne komendy Discord)

## ⚠️ Rozwiązywanie problemów

### Bot nie łączy się z kanałem głosowym
- Sprawdź czy FFmpeg jest zainstalowany: `ffmpeg -version`
- Upewnij się, że bot ma uprawnienia do połączenia z kanałem

### "❌ Błąd: Nie znaleziono DISCORD_TOKEN"
- Sprawdź czy plik `.env` istnieje
- Upewnij się, że token jest poprawnie wklejony

### Bot nie odpowiada na komendy
- Poczekaj 5-10 minut po dodaniu bota (synchronizacja komend)
- Sprawdź czy MESSAGE CONTENT INTENT jest włączony
- Użyj `/` aby zobaczyć dostępne komendy

### Błędy podczas odtwarzania
- Sprawdź połączenie internetowe
- Niektóre filmy mogą być zablokowane w Twoim regionie
- Spróbuj zaktualizować yt-dlp: `pip install --upgrade yt-dlp`

## 📝 Licencja

Projekt open-source - możesz go swobodnie modyfikować i używać!

## 🤝 Wsparcie

Jeśli napotkasz problemy:
1. Sprawdź sekcję "Rozwiązywanie problemów"
2. Upewnij się, że wszystkie wymagania są spełnione
3. Sprawdź logi w terminalu po uruchomieniu bota
