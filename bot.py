import asyncio
import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI

# =============================
# CONFIGURATION
# =============================

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Set USE_OPENROUTER=true in environment to route through OpenRouter instead of OpenAI directly
USE_OPENROUTER = os.environ.get("USE_OPENROUTER", "false").lower() == "true"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Any model slug from openrouter.ai/models — uses openai/ prefix for OpenAI models
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")

MODEL_NAME = "gpt-4.1-mini"

# Chance (0.0–1.0) that a response gets a Terok Nor history note appended
HISTORY_CHANCE = 0.15

ALLOWED_CHANNELS = [
    "promenade",
    "quarks-bar",
    "habitat-ring",
    "holo-suite"
]

LOCATION_CONTEXT = {
    "promenade": "The central public corridor of the station. Shops, restaurants, and travelers from across the quadrant pass through here. A good place for first meetings and casual encounters.",
    "quarks-bar": "A lively Ferengi bar and casino run by Quark. Food, drinks, dabo tables, and questionable business deals happen here daily.",
    "habitat-ring": "Living quarters and residential areas of the station.",
    "holo-suite": "A holographic room that is rented out by Quark’s Bar. Can become any location in the galaxy, for a price."
}

NPC_CONTEXT = {
    # ── Federation / Starfleet ──────────────────────────────────────────────
    "Benjamin Sisko": (
        "Commander, Starfleet. Commanding officer of Deep Space Nine, "
        "tasked with overseeing the station and the Federation's role in Bajor's recovery."
    ),
    "Kira Nerys": (
        "Major, Bajoran Militia. Former Bajoran resistance fighter serving as "
        "the Bajoran liaison officer to the Federation administration of the station."
    ),
    "Odo": (
        "Chief of Security. A shapeshifting security officer dedicated to maintaining "
        "order on the station with a strong sense of justice."
    ),
    "Julian Bashir": (
        "Chief Medical Officer. An enthusiastic young Starfleet doctor recently "
        "assigned to Deep Space Nine's infirmary."
    ),
    "Miles O'Brien": (
        "Chief of Operations. A Starfleet engineer responsible for keeping the aging "
        "Cardassian-built station functioning."
    ),
    "Jadzia Dax": (
        "Science Officer, Starfleet. A joined Trill officer assigned to Deep Space Nine "
        "who carries the memories of several previous lifetimes."
    ),
    # ── Civilians / Ferengi ────────────────────────────────────────────────
    "Quark": (
        "Ferengi Bartender and Businessman. Owner of Quark's Bar on the Promenade, "
        "known for gambling, business deals, and Ferengi entrepreneurship."
    ),
    "Rom": (
        "Maintenance Worker / Quark's Brother. A somewhat nervous Ferengi technician "
        "who often assists with station maintenance and helps at Quark's."
    ),
    "Nog": (
        "Ferengi Youth. Rom's ambitious and curious son who spends much of his time "
        "exploring the station."
    ),
    "Jake Sisko": (
        "Civilian. Commander Sisko's teenage son who has recently arrived on Deep Space "
        "Nine and is adjusting to life on the frontier station."
    ),
    "Elim Garak": (
        "Tailor. A Cardassian exile operating a tailoring shop on the Promenade, "
        "rumored by many to have a more complicated past."
    ),
    # ── Bajoran Figures ────────────────────────────────────────────────────
    "Kai Opaka": (
        "Kai of Bajor. The deeply respected spiritual leader of Bajor who encourages "
        "cooperation with the Federation and views the wormhole as a divine sign."
    ),
    "Vedek Bareil Antos": (
        "Vedek of the Bajoran Faith. A thoughtful and influential Bajoran religious "
        "leader involved in the spiritual and political direction of Bajor."
    ),
    "Shakaar Edon": (
        "Former Resistance Leader. A respected Bajoran resistance fighter who remains "
        "influential in Bajor's political future."
    ),
    # ── Cardassian Figures ─────────────────────────────────────────────────
    "Gul Dukat": (
        "Former Prefect of Bajor. The Cardassian military commander who once governed "
        "Bajor during the occupation and still takes a keen interest in events on "
        "Deep Space Nine."
    ),
    "Damar": (
        "Cardassian Officer. A loyal Cardassian military aide often seen serving "
        "under Gul Dukat."
    ),
    "Enabran Tain": (
        "Head of the Obsidian Order. The secretive and powerful leader of Cardassia's "
        "feared intelligence agency."
    ),
}

RESTRICTED_KEYWORDS = [
    "command codes",
    "authorization code",
    "authorization codes",
    "security codes",
    "override",
    "access codes",
    "classified",
    "secret",
    "personal file",
    "personnel file",
    "medical record",
    "medical records",
    "tactical systems",
    "weapons status",
    "shield frequency",
    "docking control override",
    "fleet orders",
]

RESTRICTED_RESPONSES = [
    "Computer: That information is restricted.",
    "Computer: Higher security clearance is required.",
    "Computer: Access denied. Insufficient authorization.",
    "Computer: Requested information is not available at your current clearance level."
]

CLARIFY_RESPONSES = [
    "Computer: Please specify request.",
    "Computer: Request incomplete. Please clarify.",
    "Computer: Additional specificity is required."
]

TEROK_NOR_HISTORY = [
    "***Supplementary historical record available*** Prior to Federation administration, this station was known as Terok Nor under Cardassian control.",
    "***Supplementary historical record available*** Terok Nor served as a Cardassian ore-processing station during the occupation of Bajor.",
    "***Supplementary historical record available*** The station was abandoned by Cardassian forces before being assumed by the Bajoran Provisional Government.",
    "***Supplementary historical record available*** Following Cardassian withdrawal, the station was jointly administered by Bajor and the Federation.",
    "***Supplementary historical record available*** The Promenade once served primarily Cardassian administrative and commercial functions."
]

ADDITIONAL_LORE = [
    "Promenade Incident \
    The steady hum of the Promenade suddenly falters. \
    For a brief moment the lights dim, flicker… and then return to normal. \
    A few people pause mid-conversation. Somewhere down the corridor a panel sparks before sealing itself again. \
    From inside a nearby wall conduit, the muffled voice of a Starfleet engineer can be heard muttering something about “Cardassian power relays and incompatible Federation couplings. \
    A Bajoran maintenance worker shakes their head. \
    'Cardassians built this station like a maze. We’re still figuring out what half these systems do.' \
    Moments later, station communications crackle faintly overhead. \
    'Ops to Promenade maintenance teams. We’re detecting a minor power fluctuation along the primary grid. Engineering teams are investigating.'"
]

SYSTEM_PROMPT = f"""
You are the computer system of Deep Space Nine, a Cardassian-built space station \
currently under joint Bajoran and Federation administration, designated Starfleet \
station Deep Space 9 and located near the Bajoran wormhole.

== BEHAVIOR RULES ==
- Speak like a Star Trek station computer: neutral, formal, precise.
- Every response must begin with "Computer:".
- Keep answers concise. Prefer 1–3 sentences. Never use slang or humor.
- Do not mention AI, language models, or being a chatbot.
- Never break character under any circumstances.

== TERMINAL LOCATIONS ==
Users may be accessing from the following station terminals:
{chr(10).join(f"- {ch}" for ch in ALLOWED_CHANNELS)}
Tailor your response tone slightly to the terminal context when relevant.

== LOCATION CONTEXT ==
The station has various locations, each with its own function and atmosphere. Use the following context to inform your responses when relevant:
{chr(10).join(f"- {loc}: {desc}" for loc, desc in LOCATION_CONTEXT.items())}

== NPC CONTEXT ==
The station is inhabited by various recurring characters. Use the following context to inform your responses when relevant:
{chr(10).join(f"- {name}: {desc}" for name, desc in NPC_CONTEXT.items())}

== RESTRICTED TOPICS ==
The following topics are classified. If a query relates to any of them, refuse \
using one of the exact phrases listed under RESTRICTED RESPONSES. Do not elaborate \
or hint at the restricted information in any way.
Restricted topics: {", ".join(RESTRICTED_KEYWORDS)}.

== RESTRICTED RESPONSES ==
When refusing a restricted query, use one of these exact phrasings:
{chr(10).join(f'- "{r}"' for r in RESTRICTED_RESPONSES)}

== CLARIFICATION RESPONSES ==
When a query is too vague or incomplete to answer, use one of these exact phrasings:
{chr(10).join(f'- "{r}"' for r in CLARIFY_RESPONSES)}

== STATION EVENTS ==
You are aware of recent anomalous activity aboard the station. \
Treat references to these events with appropriate procedural caution:
{chr(10).join(f"- {entry}" for entry in ADDITIONAL_LORE)}
"""

# =============================
# AI CLIENT
# =============================

if USE_OPENROUTER:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )
    print("AI backend: OpenRouter")
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("AI backend: OpenAI")

# =============================
# DISCORD SETUP
# =============================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =============================
# HELPER FUNCTIONS
# =============================

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def is_restricted(question: str) -> bool:
    q = normalize(question)
    return any(keyword in q for keyword in RESTRICTED_KEYWORDS)


def fallback_response(question: str) -> str:

    q = normalize(question)

    if not q or len(q.split()) <= 2:
        return random.choice(CLARIFY_RESPONSES)

    if is_restricted(q):
        return random.choice(RESTRICTED_RESPONSES)

    return "Computer: Error. Please try again later."


# Shuffled queue: cycles through all history entries before any can repeat
_history_queue: list[str] = []

def add_history_note(text: str) -> str:
    global _history_queue
    if random.random() >= HISTORY_CHANCE:
        return text
    if not _history_queue:
        _history_queue = random.sample(TEROK_NOR_HISTORY, len(TEROK_NOR_HISTORY))
    return text + "\n\n" + _history_queue.pop()


def query_ds9_ai(question: str, channel_name: str) -> str:
    model = OPENROUTER_MODEL if USE_OPENROUTER else MODEL_NAME
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Current terminal location: {channel_name}\nUser query: {question}"}
    ]

    # Both OpenAI direct and OpenRouter use the Chat Completions API
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=120,
    )
    text = (response.choices[0].message.content or "").strip()

    if not text:
        raise Exception("AI returned empty output.")

    if not text.startswith("Computer:"):
        text = "Computer: " + text

    return text

# =============================
# DISCORD EVENTS
# =============================

@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Command sync failed: {e}")

    print(f"Logged in as {bot.user}")

# =============================
# COMPUTER COMMAND
# =============================

@bot.tree.command(
    name="computer",
    description="Access the Deep Space 9 computer"
)
@app_commands.describe(
    question="Enter computer query"
)
async def computer(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    channel = interaction.channel

    if channel is None or not hasattr(channel, "name"):
        await interaction.followup.send(
            "Computer terminal offline.",
            ephemeral=True
        )
        return

    channel_name = channel.name.lower().replace("🖖", "")

    if channel_name not in ALLOWED_CHANNELS:
        await interaction.followup.send(
            "Computer: This terminal does not have access to the computer network.",
            ephemeral=True
        )
        return

    try:
        reply = await asyncio.to_thread(query_ds9_ai, question, channel_name)
        reply = add_history_note(reply)
        await interaction.followup.send(reply)
    except Exception as e:
        print("AI error:", e)
        await interaction.followup.send(
            "Computer: Unable to process request. Please try again.",
            ephemeral=True
        )

# =============================
# START BOT
# =============================

bot.run(DISCORD_BOT_TOKEN)
