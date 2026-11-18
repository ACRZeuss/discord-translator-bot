import asyncio
import logging
import os
import re
import sys
from pathlib import Path

import aiohttp
import discord
from deep_translator import GoogleTranslator
from discord import app_commands
from dotenv import load_dotenv

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("translator-bot")

# Betiğin bulunduğu dizindeki .env dosyasını yükle (VPS'te farklı dizinden çalıştırılsa bile bulur)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = (os.getenv("DISCORD_TOKEN") or "").strip()
PROXY = (os.getenv("DISCORD_PROXY") or "").strip() or None

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Desteklenen popüler diller ve takma adları
LANGUAGE_ALIASES: dict[str, str] = {
    "tr": "tr",
    "turkce": "tr",
    "türkçe": "tr",
    "turkish": "tr",
    "en": "en",
    "eng": "en",
    "english": "en",
    "ingilizce": "en",
    "de": "de",
    "ger": "de",
    "german": "de",
    "almanca": "de",
    "deutsch": "de",
    "fr": "fr",
    "french": "fr",
    "fransızca": "fr",
    "fransizca": "fr",
    "es": "es",
    "spanish": "es",
    "ispanyolca": "es",
    "it": "it",
    "italian": "it",
    "italyanca": "it",
    "ru": "ru",
    "russian": "ru",
    "rusça": "ru",
    "rusca": "ru",
    "ar": "ar",
    "arabic": "ar",
    "arapça": "ar",
    "arapca": "ar",
    "pt": "pt",
    "portuguese": "pt",
    "portekizce": "pt",
    "nl": "nl",
    "dutch": "nl",
    "felemenkçe": "nl",
    "felemenkce": "nl",
    "hollandaca": "nl",
    "ja": "ja",
    "jp": "ja",
    "japanese": "ja",
    "japonca": "ja",
    "ko": "ko",
    "kr": "ko",
    "korean": "ko",
    "korece": "ko",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "chinese": "zh-CN",
    "çince": "zh-CN",
    "cince": "zh-CN",
    "pl": "pl",
    "polish": "pl",
    "lehçe": "pl",
    "lehce": "pl",
    "uk": "uk",
    "ukrainian": "uk",
    "ukraynaca": "uk",
    "el": "el",
    "greek": "el",
    "yunanca": "el",
    "az": "az",
    "azerbaijani": "az",
    "azerice": "az",
}

LANGUAGE_LABELS: dict[str, str] = {
    "tr": "Türkçe (TR)",
    "en": "İngilizce (EN)",
    "de": "Almanca (DE)",
    "fr": "Fransızca (FR)",
    "es": "İspanyolca (ES)",
    "it": "İtalyanca (IT)",
    "ru": "Rusça (RU)",
    "ar": "Arapça (AR)",
    "pt": "Portekizce (PT)",
    "nl": "Felemenkçe (NL)",
    "ja": "Japonca (JA)",
    "ko": "Korece (KO)",
    "zh-CN": "Çince (ZH)",
    "pl": "Lehçe (PL)",
    "uk": "Ukraynaca (UK)",
    "el": "Yunanca (EL)",
    "az": "Azerice (AZ)",
}

MENTION_REGEX = re.compile(r"<@!?\d+>")


def resolve_language(raw_lang: str | None, default: str = "tr") -> str:
    """Kullanıcının girdiği dil kodunu veya adını standart dil koduna çevirir."""
    if not raw_lang:
        return default
    cleaned = raw_lang.strip().lower()
    if cleaned in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[cleaned]
    return cleaned


def parse_mention_command(content: str, default_lang: str = "tr") -> tuple[str, str]:
    """
    Etiket mesajından hedef dili ve varsa satır içi çevrilecek metni ayıklar.
    Örn: '@Bot en' -> ('en', '')
    Örn: '@Bot en Merhaba dünya' -> ('en', 'Merhaba dünya')
    Örn: '@Bot' -> ('tr', '')
    """
    without_mentions = MENTION_REGEX.sub("", content).strip()
    if not without_mentions:
        return default_lang, ""

    parts = without_mentions.split(maxsplit=1)
    first_word = parts[0].lower().strip(",.:;!?")

    if first_word in LANGUAGE_ALIASES:
        target_lang = LANGUAGE_ALIASES[first_word]
        remaining_text = parts[1].strip() if len(parts) > 1 else ""
        return target_lang, remaining_text

    return default_lang, without_mentions


async def _translate_via_googleapis(session: aiohttp.ClientSession, text: str, target: str) -> str:
    """1. Katman: Google Translate GTX JSON API (VPS'lerde 429 hatasına takılmaz)."""
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "q": text,
    }
    async with session.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)
        if not data or not isinstance(data[0], list):
            raise ValueError("Geçersiz Google API yanıtı")
        translated = "".join(part[0] for part in data[0] if part and part[0])
        if not translated:
            raise ValueError("Boş çeviri yanıtı")
        return translated


async def _translate_via_clients5(session: aiohttp.ClientSession, text: str, target: str) -> str:
    """2. Katman (Yedek): Google Translate clients5 JSON API."""
    url = "https://clients5.google.com/translate_a/t"
    params = {
        "client": "dict-chrome-ex",
        "sl": "auto",
        "tl": target,
        "q": text,
    }
    async with session.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        resp.raise_for_status()
        data = await resp.json(content_type=None)
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, list) and first:
                return str(first[0])
            if isinstance(first, str):
                return first
        raise ValueError("Geçersiz clients5 API yanıtı")


def _translate_via_deep_translator(text: str, target: str) -> str:
    """3. Katman (Son Yedek): deep-translator kütüphanesi."""
    translator = GoogleTranslator(source="auto", target=target)
    return translator.translate(text)


async def translate_text(
    text: str,
    target_lang: str,
    session: aiohttp.ClientSession | None = None,
) -> tuple[str, str]:
    """
    Metni 3 katmanlı yedekli yapıyla çevirir.
    Orijinal depodaki deep-translator 'TooManyRequests (HTTP 429)' sorununu tamamen çözer.
    """
    normalized_lang = resolve_language(target_lang)
    cleaned_text = text.strip()
    if len(cleaned_text) > 4500:
        cleaned_text = cleaned_text[:4500]

    own_session = False
    if session is None:
        session = aiohttp.ClientSession()
        own_session = True

    try:
        # 1. Katman: translate.googleapis.com (GTX)
        try:
            res = await _translate_via_googleapis(session, cleaned_text, normalized_lang)
            return res, normalized_lang
        except Exception as exc1:
            logger.debug("GTX API yedek katmana geçiyor: %s", exc1)

        # 2. Katman: clients5.google.com
        try:
            res = await _translate_via_clients5(session, cleaned_text, normalized_lang)
            return res, normalized_lang
        except Exception as exc2:
            logger.debug("clients5 API yedek katmana geçiyor: %s", exc2)

        # 3. Katman: deep-translator
        res = await asyncio.to_thread(_translate_via_deep_translator, cleaned_text, normalized_lang)
        return res, normalized_lang
    finally:
        if own_session:
            await session.close()


def build_translation_embed(
    translated_text: str,
    target_lang: str,
    bot_user: discord.ClientUser | None,
) -> discord.Embed:
    """Şık bir çeviri Embed nesnesi oluşturur."""
    label = LANGUAGE_LABELS.get(target_lang, target_lang.upper())
    embed = discord.Embed(
        description=translated_text,
        color=discord.Color.gold(),
    )
    icon_url = bot_user.display_avatar.url if bot_user else None
    embed.set_author(name=f"Çeviri ({label})", icon_url=icon_url)
    return embed


class TranslateBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, proxy=PROXY)
        self.tree = app_commands.CommandTree(self)
        self.http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.http_session = aiohttp.ClientSession()
        try:
            synced = await self.tree.sync()
            logger.info("Bot hazır! %d uygulama komutu senkronize edildi.", len(synced))
        except Exception as exc:
            logger.error("Komut senkronizasyonu sırasında hata oluştu: %s", exc)

    async def close(self) -> None:
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        await super().close()


bot = TranslateBot()


@bot.event
async def on_ready() -> None:
    logger.info(
        "%s (ID: %s) olarak giriş yapıldı. Mesajlar izleniyor...",
        bot.user,
        bot.user.id if bot.user else "?",
    )


@bot.event
async def on_message(message: discord.Message) -> None:
    # Botların veya kendisinin mesajlarını yoksay
    if message.author.bot:
        return

    # Bot etiketlendiyse
    if not bot.user or bot.user not in message.mentions:
        return

    # 1. Durum: Bir mesaja YANIT (Reply) verilerek bot etiketlendiyse
    if message.reference and message.reference.message_id:
        try:
            original_msg: discord.Message | None = None
            if isinstance(message.reference.resolved, discord.Message):
                original_msg = message.reference.resolved
            else:
                original_msg = await message.channel.fetch_message(message.reference.message_id)

            text_to_translate = (original_msg.content or "").strip()
            if not text_to_translate and original_msg.embeds:
                for emb in original_msg.embeds:
                    if emb.description:
                        text_to_translate = emb.description.strip()
                        break

            if not text_to_translate:
                await message.reply(
                    "⚠️ Yanıtladığınız mesajda çevrilebilecek bir metin bulunamadı.",
                    mention_author=False,
                )
                return

            target_lang, _ = parse_mention_command(message.content, default_lang="tr")
            async with message.channel.typing():
                translated_text, normalized_lang = await translate_text(
                    text_to_translate,
                    target_lang,
                    session=bot.http_session,
                )

            embed = build_translation_embed(translated_text, normalized_lang, bot.user)
            await message.reply(embed=embed, mention_author=False)

        except discord.Forbidden:
            logger.warning("Kanalda mesaj okuma veya gönderme yetkisi yok (Kanal ID: %s)", message.channel.id)
        except Exception as exc:
            logger.error("Mesaj çevirisi sırasında hata: %s", exc)
            try:
                await message.reply(
                    "❌ Çeviri yapılırken bir hata oluştu. Lütfen dil kodunu kontrol edin (örn: `tr`, `en`, `de`, `fr`, `es`).",
                    mention_author=False,
                )
            except discord.HTTPException:
                pass
        return

    # 2. Durum: Yanıt vermeden doğrudan '@Bot en Merhaba' şeklinde metinle etiketlendiyse
    target_lang, inline_text = parse_mention_command(message.content, default_lang="tr")
    if inline_text:
        try:
            async with message.channel.typing():
                translated_text, normalized_lang = await translate_text(
                    inline_text,
                    target_lang,
                    session=bot.http_session,
                )
            embed = build_translation_embed(translated_text, normalized_lang, bot.user)
            await message.reply(embed=embed, mention_author=False)
        except Exception as exc:
            logger.error("Satır içi çeviri hatası: %s", exc)
            await message.reply(
                "❌ Çeviri yapılırken bir hata oluştu.",
                mention_author=False,
            )
    else:
        await message.reply(
            "👋 Merhaba! Beni bir mesaja **yanıt vererek** etiketlersen (örn: `@Bot` veya `@Bot en`) "
            "ya da `/translate` komutunu kullanırsan senin için çeviri yapabilirim.",
            mention_author=False,
        )


# --- SLASH KOMUTU (/translate) ---
@bot.tree.command(name="translate", description="Manuel çeviri komutu.")
@app_commands.describe(
    target="Hedef dil (tr, en, de, fr, es, ru, ar...)",
    text="Çevrilecek metin",
)
async def translate_command(interaction: discord.Interaction, target: str, text: str) -> None:
    await interaction.response.defer()
    try:
        translated_text, normalized_lang = await translate_text(
            text,
            target,
            session=bot.http_session,
        )
        embed = build_translation_embed(translated_text, normalized_lang, bot.user)
        await interaction.followup.send(embed=embed)
    except Exception as exc:
        logger.error("Slash komutu çeviri hatası: %s", exc)
        await interaction.followup.send(
            f"❌ Çeviri yapılamadı. Geçerli bir dil kodu girdiğinizden emin olun (örn: `tr`, `en`, `de`, `fr`, `es`).\nDetay: `{exc}`",
            ephemeral=True,
        )


@translate_command.autocomplete("target")
async def target_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    current_lower = current.lower().strip()
    choices: list[app_commands.Choice[str]] = []
    for code, label in LANGUAGE_LABELS.items():
        if not current_lower or current_lower in code.lower() or current_lower in label.lower():
            choices.append(app_commands.Choice(name=label, value=code))
    return choices[:25]


# --- SAĞ TIK (CONTEXT MENU) KOMUTLARI ---
@bot.tree.context_menu(name="Türkçeye Çevir")
async def context_translate_tr(interaction: discord.Interaction, message: discord.Message) -> None:
    text = (message.content or "").strip()
    if not text and message.embeds and message.embeds[0].description:
        text = message.embeds[0].description.strip()

    if not text:
        await interaction.response.send_message("⚠️ Bu mesajda çevrilebilecek bir metin yok.", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        translated_text, normalized_lang = await translate_text(
            text,
            "tr",
            session=bot.http_session,
        )
        embed = build_translation_embed(translated_text, normalized_lang, bot.user)
        await interaction.followup.send(embed=embed)
    except Exception as exc:
        logger.error("Context menu (TR) çeviri hatası: %s", exc)
        await interaction.followup.send("❌ Çeviri yapılırken bir hata oluştu.", ephemeral=True)


@bot.tree.context_menu(name="Translate to English")
async def context_translate_en(interaction: discord.Interaction, message: discord.Message) -> None:
    text = (message.content or "").strip()
    if not text and message.embeds and message.embeds[0].description:
        text = message.embeds[0].description.strip()

    if not text:
        await interaction.response.send_message("⚠️ No translatable text found in this message.", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        translated_text, normalized_lang = await translate_text(
            text,
            "en",
            session=bot.http_session,
        )
        embed = build_translation_embed(translated_text, normalized_lang, bot.user)
        await interaction.followup.send(embed=embed)
    except Exception as exc:
        logger.error("Context menu (EN) çeviri hatası: %s", exc)
        await interaction.followup.send("❌ An error occurred while translating.", ephemeral=True)


def main() -> None:
    if not TOKEN or TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.error(
            "DISCORD_TOKEN ayarlanmamış! Lütfen '%s' dosyasını açıp geçerli bir Discord Bot Token girin.",
            BASE_DIR / ".env",
        )
        sys.exit(1)

    try:
        bot.run(TOKEN, log_handler=None)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error(
            "PrivilegedIntentsRequired Hatası: Discord Developer Portal -> Bot sekmesinden "
            "'MESSAGE CONTENT INTENT' seçeneğini aktif etmeniz gerekiyor!"
        )
        sys.exit(1)
    except discord.errors.LoginFailure:
        logger.error(
            "LoginFailure Hatası: Girdiğiniz DISCORD_TOKEN geçersiz veya sıfırlanmış. "
            "Lütfen Discord Developer Portal üzerinden yeni bir token alıp .env dosyasına yapıştırın."
        )
        sys.exit(1)
    except Exception as exc:
        logger.error("Bot çalışırken beklenmeyen hata: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
