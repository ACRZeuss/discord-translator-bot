import os
import discord
from discord import app_commands
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Token'ı çek
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot Sınıfı
class TranslateBot(discord.Client):
    def __init__(self):
        # --- DÜZELTME BURADA YAPILDI ---
        # İzinleri (Intents) burada tanımlıyoruz ki bot mesajları kesin okusun.
        intents = discord.Intents.default()
        intents.message_content = True  # Mesaj içeriğini okuma izni
        super().__init__(intents=intents)
        
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Bot hazır! Komutlar ve Etiketleme sistemi aktif.")

bot = TranslateBot()

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı. Mesajları izliyorum...')

# --- ÇEVİRİ YARDIMCISI ---
def get_translation(text, target):
    translator = GoogleTranslator(source='auto', target=target)
    return translator.translate(text)

# --- MESAJ YAKALAMA VE ETİKET KONTROLÜ ---
@bot.event
async def on_message(message):
    # Kendi mesajına cevap vermesin
    if message.author == bot.user:
        return

    # Eğer bot mesajda ETİKETLENDİYSE (Mention)
    if bot.user in message.mentions:
        
        # Ve bu mesaj bir şeye CEVAP (Reply) olarak atıldıysa
        if message.reference:
            try:
                # Orijinal mesajı çek
                channel = message.channel
                original_msg = await channel.fetch_message(message.reference.message_id)
                text_to_translate = original_msg.content

                if not text_to_translate:
                    # Sadece görsel varsa veya metin boşsa
                    return

                # Hedef dil kontrolü (Kullanıcı '@Bot en' yazdı mı?)
                content_lower = message.content.lower()
                target_lang = 'tr' # Varsayılan: Türkçe
                
                if 'en' in content_lower or 'english' in content_lower:
                    target_lang = 'en'
                elif 'de' in content_lower:
                    target_lang = 'de'
                elif 'fr' in content_lower:
                    target_lang = 'fr'
                elif 'es' in content_lower:
                    target_lang = 'es'

                # Çeviri işlemi
                translated_text = get_translation(text_to_translate, target_lang)

                # Şık bir Embed ile yanıtla
                embed = discord.Embed(color=discord.Color.gold())
                embed.set_author(name=f"Çeviri ({target_lang.upper()})", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                embed.description = f"{translated_text}"
                
                await message.reply(embed=embed)

            except Exception as e:
                print(f"Hata: {e}")
                # Kullanıcıya hata göstermiyoruz ki sohbet kirlenmesin, konsola yazıyoruz.
        else:
            # Bot etiketlendi ama cevap verilmediyse
            await message.channel.send("👋 Merhaba! Beni bir mesaja **yanıt vererek** etiketlersen senin için çevirebilirim.")

# --- SLASH KOMUTU ---
@bot.tree.command(name="translate", description="Manuel çeviri komutu.")
@app_commands.describe(target="Hedef dil (tr, en, de...)", text="Metin")
async def translate(interaction: discord.Interaction, target: str, text: str):
    await interaction.response.defer()
    res = get_translation(text, target)
    await interaction.followup.send(f"**Çeviri:** {res}")

# Token'ını buraya gir
bot.run(TOKEN)