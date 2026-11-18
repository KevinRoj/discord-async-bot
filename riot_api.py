import os
import httpx
from dotenv import load_dotenv

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")

REGIONAL_ROUTING = {
    "LAS": "americas",
    "LAN": "americas",
    "NA": "americas",
    "BR": "americas",
    "EUW": "europe",
    "EUNE": "europe",
    "KR": "asia",
    "JP": "asia"
}

PLATFORM_ROUTING = {
    "LAS": "la2",
    "LAN": "la1",
    "NA": "na1",
    "BR": "br1",
    "EUW": "euw1",
    "EUNE": "eun1",
    "KR": "kr",
    "JP": "jp1"
}

async def get_riot_account(game_name: str, tag_line: str, region: str = "LAS"):
    """Obtiene el PUUID y los datos de cuenta de Riot usando Riot ID."""
    routing = REGIONAL_ROUTING.get(region.upper(), "americas")
    url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "No se encontró una cuenta con ese Riot ID."}
            elif response.status_code == 403:
                return {"error": "La API Key de Riot ha expirado o no es válida."}
            else:
                return {"error": f"Error en la API de Riot (Código: {response.status_code})"}
        except httpx.RequestError:
            return {"error": "No se pudo conectar con los servidores de Riot Games."}

async def get_summoner_rank(puuid: str, region: str = "LAS"):
    """Obtiene las estadísticas clasificatorias directamente usando el PUUID del invocador."""
    platform = PLATFORM_ROUTING.get(region.upper(), "la2")
    rank_url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            rank_response = await client.get(rank_url, headers=headers)

            if rank_response.status_code == 200:
                return rank_response.json()
            elif rank_response.status_code == 403:
                return {"error": "La API Key de Riot ha expirado o no tiene permisos para league-v4."}
            else:
                return {"error": f"No se pudieron obtener las clasificatorias (Código HTTP: {rank_response.status_code})."}
        except httpx.RequestError:
            return {"error": "No se pudo conectar con los servidores de Riot Games."}

async def get_top_champion(puuid: str, region: str = "LAS"):
    """
    Obtiene el campeón con mayor maestría de un invocador usando su PUUID.
    """
    platform = PLATFORM_ROUTING.get(region.upper(), "la2")
    # Endpoint de maestría por PUUID (obtiene los campeones con más maestría)
    mastery_url = f"https://{platform}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=1"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(mastery_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data[0] # Retorna el primer elemento (el de mayor maestría)
                return None
            elif response.status_code == 403:
                return {"error": "La API Key de Riot ha expirado o no tiene permisos para champion-mastery."}
            else:
                return {"error": f"No se pudo obtener la maestría (Código HTTP: {response.status_code})."}
        except httpx.RequestError:
            return {"error": "No se pudo conectar con los servidores de Riot Games."}