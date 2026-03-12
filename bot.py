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

MODEL_NAME = "gpt-5-mini"

HISTORY_CHANCE = 0.15

ALLOWED_CHANNELS = [
    "🖖promenade",
    "🖖quarks-bar",
    "🖖habitat-ring",
    "🖖holo-suite"
]

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
    "Computer: Supplementary historical record available. Prior to Federation administration, this station was known as Terok Nor under Cardassian control.",
    "Computer: Supplementary historical record available. Terok Nor served as a Cardassian ore-processing station during the occupation of Bajor.",
    "Computer: Supplementary historical record available. The station was abandoned by Cardassian forces before being assumed by the Bajoran Provisional Government.",
    "Computer: Supplementary historical record available. Following Cardassian withdrawal, the station was jointly administered by Bajor and the Federation.",
    "Computer: Supplementary historical record available. The Promenade once served primarily Cardassian administrative and commercial functions."
]

SYSTEM_PROMPT = """
You are the computer system of Deep Space Nine.

Behavior rules:

- Speak like a Star Trek station computer.
- Responses must begin with "Computer:".
- Keep answers concise and formal.
- Prefer 1–3 sentences.
- Do not use slang or humor.
- Do not mention AI or being a chatbot.
- If the request asks for restricted or classified information,
  respond with a short refusal such as:
  "Computer: Higher security clearance is required."
- If the request is vague, ask the user to clarify.
"""

# =============================
# AI CLIENT
# =============================

client = OpenAI(api_key=OPENAI_API_KEY)

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


def add_history_note(text: str) -> str:

    if random.random() < HISTORY_CHANCE:
        return text + "\n\n" + random.choice(TEROK_NOR_HISTORY)

    return text


def query_ds9_ai(question: str, channel_name: str) -> str:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are the computer system of Deep Space Nine. "
                    "Answer briefly, formally, and in-universe. "
                    "Always begin your answer with 'Computer:'. "
                    "Keep replies to 1 to 3 sentences."
                )
            },
            {
                "role": "user",
                "content": f"Current terminal location: {channel_name}\nUser query: {question}"
            }
        ],
        max_output_tokens=120
    )

    text = response.output_text.strip()

    if not text:
        raise Exception("OpenAI returned empty output.")

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
            f"Computer access is not available at this terminal. Debug channel name: {channel.name}",
            ephemeral=True
        )
        return

    try:
        reply = query_ds9_ai(question, channel_name)
        reply = add_history_note(reply)
        await interaction.followup.send(reply)
    except Exception as e:
        print("AI error:", e)
        await interaction.followup.send(
            f"Computer debug: {e}",
            ephemeral=True
        )

# =============================
# START BOT
# =============================

bot.run(DISCORD_BOT_TOKEN)
