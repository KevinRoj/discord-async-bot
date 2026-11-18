import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import httpx  # <--- ¡Asegúrate de que esta línea esté aquí arriba!
import database
import riot_api

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

# Usamos '?' como prefijo para evitar conflictos con MEE6 (!)
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    await database.init_db()
    print(f"¡Bot conectado con éxito como {bot.user} (ID: {bot.user.id})!")
    print("Base de datos SQLite inicializada correctamente.")

@bot.command(name="vincular")
async def vincular_cuenta(ctx, riot_id: str, region: str = "LAS"):
    """
    Comando para vincular la cuenta de Riot.
    Uso: ?vincular Invocador#TAG LAS
    """
    if "#" not in riot_id:
        await ctx.send("⚠️ Por favor ingresa tu Riot ID completo incluyendo el tag (Ejemplo: `Invocador#LAS`).")
        return

    game_name, tag_line = riot_id.split("#", 1)
    
    async with ctx.typing():
        resultado = await riot_api.get_riot_account(game_name, tag_line, region)

    if "error" in resultado:
        await ctx.send(f"❌ {resultado['error']}")
        return

    discord_id = str(ctx.author.id)
    await database.link_riot_account(discord_id, game_name, tag_line, region.upper())

    await ctx.send(
        f"✅ ¡Cuenta vinculada y verificada con éxito!\n"
        f"**Invocador:** `{game_name}#{tag_line}`\n"
        f"**Región:** `{region.upper()}`"
    )

@bot.command(name="rank")
async def ver_rank(ctx, *, riot_id_con_region: str = None):
    """
    Comando para ver las clasificatorias propias o de otro invocador.
    Uso propio: ?rank
    Uso ajeno: ?rank Invocador#TAG REGION  (Ejemplo: ?rank TheRedZpecter#02752 LAN)
    """
    game_name = None
    tag_line = None
    region = "LAS" # Región por defecto si buscas a alguien y no especifica, o se extrae

    # Si el usuario escribió algo después de ?rank (ej: "?rank Invocador#TAG LAN")
    if riot_id_con_region:
        # Separamos por espacios para aislar la región al final (si la ponen)
        partes = riot_id_con_region.strip().split()
        riot_id_input = partes[0]  # Tomamos la parte del "Nombre#TAG"
        
        if len(partes) > 1:
            region = partes[1].upper() # Si escribieron región (ej. LAN, NA)

        if "#" not in riot_id_input:
            await ctx.send("⚠️ Por favor ingresa el Riot ID completo incluyendo el tag (Ejemplo: `?rank Invocador#TAG LAN`).")
            return
        
        game_name, tag_line = riot_id_input.split("#", 1)
    
    else:
        # Si no escribió nada, buscamos en la base de datos al usuario de Discord actual
        discord_id = str(ctx.author.id)
        cuenta = await database.get_linked_account(discord_id)
        if not cuenta:
            await ctx.send("⚠️ No tienes ninguna cuenta vinculada ni especificaste un invocador. Usa `?vincular Invocador#TAG` o escribe `?rank RiotID#TAG Región`.")
            return

        game_name = cuenta["game_name"]
        tag_line = cuenta["tag_line"]
        region = cuenta["region"]

    async with ctx.typing():
        # Consultamos la API con los datos obtenidos (ya sea propios o de terceros)
        cuenta_riot = await riot_api.get_riot_account(game_name, tag_line, region)
        if "error" in cuenta_riot:
            await ctx.send(f"❌ {cuenta_riot['error']}")
            return
        
        puuid = cuenta_riot.get("puuid")
        rank_data = await riot_api.get_summoner_rank(puuid, region)
        
        if isinstance(rank_data, dict) and "error" in rank_data:
            await ctx.send(f"❌ {rank_data['error']}")
            return

    if not rank_data:
        await ctx.send(f"📊 El invocador `{game_name}#{tag_line}` no tiene clasificatorias registradas esta temporada.")
        return

    mensaje = f"📊 **Estadísticas de Ranked para `{game_name}#{tag_line}` ({region}):**\n"
    
    for queue in rank_data:
        queue_type = "Solo/Duo" if queue.get("queueType") == "RANKED_SOLO_5x5" else "Flex"
        tier = queue.get("tier", "UNRANKED").capitalize()
        rank = queue.get("rank", "")
        lp = queue.get("leaguePoints", 0)
        wins = queue.get("wins", 0)
        losses = queue.get("losses", 0)
        
        total_games = wins + losses
        winrate = (wins / total_games * 100) if total_games > 0 else 0

        mensaje += (
            f"\n🔹 **{queue_type}:** {tier} {rank} ({lp} LP)\n"
            f"   • Victorias: {wins} | Derrotas: {losses} | Winrate: {winrate:.1f}%\n"
        )

    await ctx.send(mensaje)

# Función auxiliar para traducir el ID numérico del campeón a su nombre real usando Data Dragon
async def get_champion_name_by_id(champion_id: int) -> str:
    # Obtenemos la última versión de los Data Dragon de Riot
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    
    async with httpx.AsyncClient() as client:
        try:
            v_res = await client.get(versions_url)
            if v_res.status_code != 200:
                return f"Desconocido (ID: {champion_id})"
            
            latest_version = v_res.json()[0]
            
            # Consultamos el listado de campeones en español (es_ES) para ese parche
            champ_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/es_ES/champion.json"
            c_res = await client.get(champ_url)
            
            if c_res.status_code == 200:
                champ_data = c_res.json()["data"]
                # El Data Dragon guarda los campeones mapeados por ID numérico en la propiedad "key"
                for champ_name, champ_info in champ_data.items():
                    if int(champ_info["key"]) == champion_id:
                        return champ_info["name"] # Devuelve el nombre oficial (ej. "Viego", "Ahri")
            
        except Exception:
            pass
            
        return f"Campeón #{champion_id}"


@bot.command(name="mains")
async def ver_main(ctx, *, riot_id_con_region: str = None):
    """
    Comando para ver el campeón con mayor maestría propio o de otro invocador.
    Uso: ?mains [Invocador#TAG REGION]
    """
    game_name = None
    tag_line = None
    region = "LAS"

    if riot_id_con_region:
        partes = riot_id_con_region.strip().split()
        riot_id_input = partes[0]
        if len(partes) > 1:
            region = partes[1].upper()

        if "#" not in riot_id_input:
            await ctx.send("⚠️ Por favor ingresa el Riot ID completo (Ejemplo: `?mains Invocador#TAG LAN`).")
            return
        
        game_name, tag_line = riot_id_input.split("#", 1)
    else:
        discord_id = str(ctx.author.id)
        cuenta = await database.get_linked_account(discord_id)
        if not cuenta:
            await ctx.send("⚠️ No tienes ninguna cuenta vinculada. Usa `?vincular Invocador#TAG` o escribe `?mains RiotID#TAG Región`.")
            return

        game_name = cuenta["game_name"]
        tag_line = cuenta["tag_line"]
        region = cuenta["region"]

    async with ctx.typing():
        cuenta_riot = await riot_api.get_riot_account(game_name, tag_line, region)
        if "error" in cuenta_riot:
            await ctx.send(f"❌ {cuenta_riot['error']}")
            return
        
        puuid = cuenta_riot.get("puuid")
        mastery_data = await riot_api.get_top_champion(puuid, region)
        
        if isinstance(mastery_data, dict) and "error" in mastery_data:
            await ctx.send(f"❌ {mastery_data['error']}")
            return

        if not mastery_data:
            await ctx.send(f"📊 El invocador `{game_name}#{tag_line}` no tiene datos de maestría registrados.")
            return

        champ_id = mastery_data.get("championId")
        champion_points = mastery_data.get("championPoints", 0)
        champion_level = mastery_data.get("championLevel", 0)
        
        # Traducimos el ID numérico a nombre usando Data Dragon
        champion_name = await get_champion_name_by_id(champ_id)

    await ctx.send(
        f"👑 **Campeón con mayor maestría para `{game_name}#{tag_line}` ({region}):**\n\n"
        f"⚔️ **{champion_name}**\n"
        f"   • Nivel de Maestría: {champion_level}\n"
        f"   • Puntos: {champion_points:,} pts"
    )

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Error: No se encontró el DISCORD_TOKEN en el archivo .env.")
    else:
        bot.run(DISCORD_TOKEN)