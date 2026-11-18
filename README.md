# 🌐 Discord Translator Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Discord sunucularında mesajları **etiketleyerek (mention)**, **slash komutuyla (`/translate`)** veya **sağ tık uygulama menüsüyle (Apps)** saniyeler içinde istediğiniz dile çeviren hızlı, asenkron ve Docker uyumlu Discord çeviri botu.

---

## ✨ Özellikler

- 💬 **Yanıtla ve Etiketle (Reply + Mention):** Herhangi bir mesaja yanıt verip `@Bot` yazarak Türkçeye, `@Bot en`, `@Bot de` gibi dil kodu ekleyerek istediğiniz dile çeviri yapın.
- ⚡ **Satır İçi Çeviri:** Bir mesaja yanıt vermeden doğrudan `@Bot en Merhaba dünya` yazarak anında çeviri alın.
- ⌨️ **Slash Komutu (`/translate`):** Hedef dil otomatik tamamlama (Autocomplete) destekli `/translate` komutu.
- 🖱️ **Sağ Tık Menüsü (Context Menu):** Herhangi bir mesaja sağ tıklayıp **Uygulamalar (Apps) → Türkçeye Çevir** veya **Translate to English** seçeneğiyle tek tıkla çeviri.
- 🛡️ **3 Katmanlı Yedekli Çeviri Motoru:** VPS ve veri merkezi IP'lerinde sıkça karşılaşılan `HTTP 429 Too Many Requests` engeline takılmamak için `aiohttp` tabanlı 3 katmanlı (`googleapis GTX` → `clients5` → `deep-translator`) asenkron mimari.
- 🐳 **Docker & Docker Compose Desteği:** Tek komutla izole ve otomatik yeniden başlayan (`unless-stopped`) konteyner kurulumu.

---

## 🚀 Kullanım Örnekleri

| Yöntem | Örnek Kullanım | Açıklama |
| :--- | :--- | :--- |
| **Yanıtla + Etiketle (Varsayılan)** | *(Mesaja Yanıtla)* `@Bot` | Yanıtlanan mesajı otomatik algılayıp **Türkçeye** çevirir. |
| **Yanıtla + Hedef Dil** | *(Mesaja Yanıtla)* `@Bot en` veya `@Bot almanca` | Yanıtlanan mesajı belirtilen hedef dile çevirir. |
| **Doğrudan Etiketle** | `@Bot fr Merhaba, nasılsın?` | Yazılan metni doğrudan Fransızcaya çevirir. |
| **Slash Komutu** | `/translate target:İngilizce (EN) text:Merhaba` | Otomatik tamamlamalı menü ile manuel çeviri yapar. |
| **Sağ Tık (Apps)** | `Mesaja Sağ Tık` → `Apps` → `Türkçeye Çevir` | Hiçbir şey yazmadan mesajı tek tıkla çevirir. |

---

## 🌍 Desteklenen Popüler Diller ve Kısaltmalar

Bot, aşağıdaki popüler dilleri hem kod hem de Türkçe/İngilizce isimleriyle tanır (ayrıca Google Translate tarafından desteklenen tüm ISO dil kodlarını kullanabilirsiniz):

| Dil | Kullanabileceğiniz Kodlar / İsimler |
| :--- | :--- |
| 🇹🇷 **Türkçe** | `tr`, `türkçe`, `turkce`, `turkish` *(Varsayılan)* |
| 🇬🇧 **İngilizce** | `en`, `eng`, `ingilizce`, `english` |
| 🇩🇪 **Almanca** | `de`, `ger`, `almanca`, `german`, `deutsch` |
| 🇫🇷 **Fransızca** | `fr`, `fransızca`, `fransizca`, `french` |
| 🇪🇸 **İspanyolca** | `es`, `ispanyolca`, `spanish` |
| 🇮🇹 **İtalyanca** | `it`, `italyanca`, `italian` |
| 🇷🇺 **Rusça** | `ru`, `rusça`, `rusca`, `russian` |
| 🇸🇦 **Arapça** | `ar`, `arapça`, `arapca`, `arabic` |
| 🇵🇹 **Portekizce** | `pt`, `portekizce`, `portuguese` |
| 🇳🇱 **Felemenkçe** | `nl`, `felemenkçe`, `hollandaca`, `dutch` |
| 🇯🇵 **Japonca** | `ja`, `jp`, `japonca`, `japanese` |
| 🇰🇷 **Korece** | `ko`, `kr`, `korece`, `korean` |
| 🇨🇳 **Çince** | `zh`, `zh-cn`, `çince`, `chinese` |
| 🇦🇿 **Azerice** | `az`, `azerice`, `azerbaijani` |
| 🇵🇱 **Lehçe** | `pl`, `lehçe`, `polish` |
| 🇺🇦 **Ukraynaca** | `uk`, `ukraynaca`, `ukrainian` |
| 🇬🇷 **Yunanca** | `el`, `yunanca`, `greek` |

---

## ⚙️ Discord Developer Portal Kurulumu

Botu çalıştırmadan önce [Discord Developer Portal](https://discord.com/developers/applications) üzerinden bir uygulama oluşturup şu ayarları yapın:

1. **New Application** butonuna tıklayarak botunuzu oluşturun.
2. Sol menüden **Bot** sekmesine gidin:
   - **Reset Token** butonuna tıklayarak bot token'ınızı kopyalayın (`.env` dosyasında kullanacaksınız).
   - **Authorization Flow** altındaki `Requires OAuth2 Code Grant` seçeneğinin **KAPALI** olduğundan emin olun.
   - **Privileged Gateway Intents** altındaki **`Message Content Intent`** seçeneğini **AÇIK** konuma getirin ve **Save Changes**'e tıklayın.
3. Sol menüden **OAuth2** sekmesine gidin:
   - **OAuth2 URL Generator** altından `bot` ve `applications.commands` kutucuklarını işaretleyin.
   - **Bot Permissions** altından şunları seçin:
     - `View Channels`
     - `Send Messages`
     - `Send Messages in Threads`
     - `Embed Links`
     - `Read Message History`
   - En altta oluşan **Generated URL** bağlantısını tarayıcıda açarak botu sunucunuza davet edin.

---

## 📦 Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın ve `.env` Dosyasını Hazırlayın

```bash
git clone https://github.com/ACRZeuss/discord-translator-bot.git
cd discord-translator-bot
cp .env.example .env
```

`.env` dosyasını açıp Discord Bot Token'ınızı yapıştırın:

```env
DISCORD_TOKEN=BOT_TOKENINIZI_BURAYA_YAZIN
```

---

### 🐳 Yöntem A: Docker Compose ile Çalıştırma (VPS İçin Önerilen)

```bash
# İmajı derleyip arka planda başlatır
docker compose up -d --build

# Logları canlı olarak izlemek için
docker compose logs -f

# Botu durdurmak için
docker compose down
```

---

### 🐍 Yöntem B: Python Sanal Ortamı (venv) ile Çalıştırma

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](./LICENSE) altında lisanslanmıştır.
