# LoL Tracker Bot

Bot asíncrono de Discord desarrollado en Python para vincular cuentas de Riot Games y consultar estadísticas clasificatorias (Ranked) y campeones con mayor maestría en League of Legends.

## Características

- **Vinculación de cuentas:** Asocia tu Riot ID (`Nombre#TAG`) y región a tu usuario de Discord en una base de datos local SQLite.
- **Consulta de Ranked (`?rank`):** Muestra Solo/Duo y Flex (liga, división, LP, victorias, derrotas y winrate) de tu cuenta vinculada o de cualquier otro invocador al vuelo.
- **Campeón principal (`?mains`):** Consulta el campeón con mayor maestría, nivel y puntos, traduciendo el ID numérico al nombre oficial en español mediante Data Dragon de Riot.
- **Prefijo configurable:** Utiliza `?` para evitar conflictos con bots como MEE6 que emplean `!`.

## Estructura del proyecto

- `bot.py`: Inicialización del bot de Discord, comandos (`?vincular`, `?rank`, `?mains`) y traducción de IDs de campeones con Data Dragon.
- `riot_api.py`: Consultas HTTP asíncronas a la API de Riot (`account-v1`, `league-v4` por PUUID y `champion-mastery-v4`) con ruteo regional y de plataforma.
- `database.py`: Persistencia asíncrona en SQLite (`lol_bot.db`) mediante `aiosqlite`.
- `.env`: Variables de entorno locales (no se sube al repositorio).

## Requisitos e instalación

1. Clona el repositorio y entra en la carpeta del proyecto:
   ```bash
   git clone <url-de-tu-repositorio>
   cd <carpeta-del-proyecto>
   ```

2. Crea y activa un entorno virtual, e instala las dependencias:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   pip install discord.py httpx aiosqlite python-dotenv
   ```

3. Configura tu archivo `.env` en la raíz del proyecto:
   ```env
   DISCORD_TOKEN=tu_token_de_discord
   RIOT_API_KEY=tu_api_key_de_riot
   ```
   *(Asegúrate de tener activado **Message Content Intent** en el Portal de Desarrolladores de Discord).*

4. Ejecuta el bot:
   ```bash
   python bot.py
   ```

## Comandos

| Comando | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `?vincular Invocador#TAG [Región]` | Vincula tu cuenta a tu ID de Discord (región por defecto: `LAS`). | `?vincular TheRedZpecter#02752 LAN` |
| `?rank` | Muestra tus estadísticas de clasificatorias vinculadas. | `?rank` |
| `?rank Invocador#TAG [Región]` | Consulta las clasificatorias de otro invocador. | `?rank Faker#KR1 KR` |
| `?mains` | Muestra tu campeón con mayor maestría. | `?mains` |
| `?mains Invocador#TAG [Región]` | Muestra el campeón principal de otro invocador. | `?mains TheRedZpecter#02752 LAN` |

## Notas de desarrollo

- Riot actualizó `league-v4` para consultar entradas directamente por `puuid` (`/lol/league/v4/entries/by-puuid/{puuid}`) en lugar de depender de `summonerId`.
- Mantén fuera del control de versiones archivos sensibles o generados localmente como `.env`, `lol_bot.db`, `__pycache__/` y `.vs/`.
