from src.constants import (
    ALLOWED_SERVER_IDS,

)
import logging

logger = logging.getLogger(__name__)
from src.base import Message
from discord import Message as DiscordMessage
from typing import Optional, List
import discord

from src.constants import MAX_CHARS_PER_REPLY_MSG, INACTIVATE_THREAD_PREFIX, MAX_COMMAND_BY_USER

import datetime

# Dictionnaire pour stocker les commandes par utilisateur par semaine
commands_per_user = {}

def can_send_command(user_id):

    # Obtenir la semaine actuelle (année, numéro de semaine)
    current_week = datetime.datetime.now().isocalendar()[:2]
    
    # Vérifier si l'utilisateur a déjà des commandes enregistrées
    if user_id not in commands_per_user:
        commands_per_user[user_id] = {"week": current_week, "count": 1}
        return True
        
    user_info = commands_per_user[user_id]
    
    # Si l'utilisateur a des commandes enregistrées pour la semaine actuelle
    if user_info["week"] == current_week:
        if user_info["count"] < MAX_COMMAND_BY_USER:
            user_info["count"] += 1
            return True
        else:
            return False
    else:
        # Si les commandes enregistrées sont d'une semaine précédente, réinitialiser le compteur
        commands_per_user[user_id] = {"week": current_week, "count": 1}
        return True


def discord_message_to_message(message: DiscordMessage) -> Optional[Message]:
    if (
        message.type == discord.MessageType.thread_starter_message
        and message.reference.cached_message
        and len(message.reference.cached_message.embeds) > 0
        and len(message.reference.cached_message.embeds[0].fields) > 0
    ):
        field = message.reference.cached_message.embeds[0].fields[0]
        if field.value:
            return Message(user=field.name, text=field.value)
    else:
        if message.content:
            return Message(user=message.author.name, text=message.content)
    return None


def split_into_shorter_messages(message: str) -> List[str]:
    return [
        message[i : i + MAX_CHARS_PER_REPLY_MSG]
        for i in range(0, len(message), MAX_CHARS_PER_REPLY_MSG)
    ]


def is_last_message_stale(
    interaction_message: DiscordMessage, last_message: DiscordMessage, bot_id: str
) -> bool:
    return (
        last_message
        and last_message.id != interaction_message.id
        and last_message.author
        and last_message.author.id != bot_id
    )


async def close_thread(thread: discord.Thread):
    await thread.edit(name=INACTIVATE_THREAD_PREFIX)
    await thread.send(
        embed=discord.Embed(
            description="**Thread closed** - Context limit reached, closing...",
            color=discord.Color.blue(),
        )
    )
    await thread.edit(archived=True, locked=True)


def should_block(guild: Optional[discord.Guild]) -> bool:
    if guild is None:
        # dm's not supported
        logger.info(f"DM not supported")
        return True

    if guild.id and guild.id not in ALLOWED_SERVER_IDS:
        # not allowed in this server
        logger.info(f"Guild {guild} not allowed")
        return True
    return False
