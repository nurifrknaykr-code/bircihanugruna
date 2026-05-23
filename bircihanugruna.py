import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
import g4f
from discord import app_commands
import asyncio  # Temizle komutu için gerekli

# --- AYARLAR ---
TOKEN = 'MTQ2OTA3MTA4NjAxOTY3ODM1Nw.GdX2Yc.LrqpzqYe-sYy1MSlJvOtrA5XsG6nUCX7cmANYE' 
YOUTUBE_API_KEY = 'AIzaSyAkgD850wiq9O8tKFm-rAXa4OvxO7RwLJQ'
CHANNEL_ID = 'UCcfOsQKtxJHlzS6f0Hz9Now'

GUILD_ID = 1469058783282991287
KURALLAR_KANAL_ID = 1469059399732563988
GELEN_KANAL_ID = 1469063234207223981
GIDEN_KANAL_ID = 1469063262657314868
SAHIBIN_ID = 1163545676131610704
OTO_ROL_ID = 1469061013704802538 

YASAKLI_KELIMELER = ["lune", "ecrin", "ecos", "salak", "gerizekalı", "lunecraft"]
bot_durumu = "AKTIF"

# --- BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # Üye girişlerini görmek için bu ŞART
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        if not update_status.is_running():
            update_status.start()

bot = MyBot()

# --- YOUTUBE FONKSİYONLARI ---
async def get_channel_data():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.channels().list(part="statistics,snippet", id=CHANNEL_ID)
        response = request.execute()
        return response["items"][0]
    except:
        return None

async def refresh_subs():
    data = await get_channel_data()
    if data:
        subs = data["statistics"]["subscriberCount"]
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name=f"Abone: {subs}")
        )
        return subs
    return None

@tasks.loop(minutes=10)
async def update_status():
    await bot.wait_until_ready()
    if bot_durumu == "AKTIF":
        await refresh_subs()

# --- ETKİNLİKLER ---

@bot.event
async def on_ready():
    print(f"✅ {bot.user} olarak giriş yapıldı ve sistem hazır!")

@bot.event
async def on_member_join(member):
    """Yeni üye katıldığında çalışır"""
    # 1. Otomatik Rol Verme 
    guild = member.guild 
    rol = guild.get_role(OTO_ROL_ID)
    
    if rol:
        try:
            await member.add_roles(rol)
            print(f"✅ {member.name} kullanıcısına rol verildi.")
        except Exception as e:
            print(f"❌ Rol verilirken hata oluştu: {e}")
    else:
        print("❌ Belirtilen OTO_ROL_ID bulunamadı.")
 
    # 2. Hoş geldin mesajı
    kanal = bot.get_channel(GELEN_KANAL_ID)
    if kanal:
        await kanal.send(f"Hoş geldin {member.mention} 🎉    Sunucumuza katıldığın için mutluyuz!")

@bot.event
async def on_member_remove(member):
    kanal = bot.get_channel(GIDEN_KANAL_ID)
    if kanal:
        await kanal.send(f"📤 **{member.name}** sunucudan ayrıldı. Görüşürüz!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Yasaklı Kelime Kontrolü
    if any(k in message.content.lower() for k in YASAKLI_KELIMELER):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, bu kelimeyi kullanmak yasaktır!", delete_after=5)
        return

    # Bot Etiketlendiğinde AI Cevabı
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                soru = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
                if not soru:
                    await message.reply("Efendim? Bir şey mi soracaktın? 😄")
                    return

                cevap = await g4f.ChatCompletion.create_async(
                    model=g4f.models.default,
                    messages=[
                        {"role": "system", "content": "Samimi, kısa, arkadaş gibi konuş."},
                        {"role": "user", "content": soru}
                    ]
                )
                await message.reply(cevap)
            except:
                await message.reply("Şu an kafam biraz karışık, sonra tekrar sorar mısın? 😅")

    await bot.process_commands(message)

# --- KOMUTLAR ---

@bot.command()
async def temizle(ctx, limit: int = 100):
    if ctx.author.id != SAHIBIN_ID:
        return await ctx.reply("Bu komutu sadece sahibim kullanabilir.")
    
    deleted = await ctx.channel.purge(limit=limit)
    await ctx.send(f"✅ {len(deleted)} mesaj temizlendi.", delete_after=5)

@bot.tree.command(name="abone", description="YouTube abone sayısını gösterir")
async def abone(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await get_channel_data()
    if data:
        subs = data["statistics"]["subscriberCount"]
        await interaction.followup.send(f"📊 **Mevcut Abone Sayımız:** `{subs}`")
    else:
        await interaction.followup.send("Veriler şu an çekilemiyor.")

# Botu çalıştır
bot.run(TOKEN)
