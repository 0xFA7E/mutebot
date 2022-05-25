# pylint: disable=import-error,consider-using-with
# bot.py
import os
import datetime
from discord.ext import commands
from dotenv import load_dotenv
import discord

class MuteBot(discord.Client):

    def __init__(self, logchannel, *args, **kwargs):
 
        super().__init__(*args, **kwargs)
        self.logchannel = self.get_channel(logchannel)

    async def on_ready(self):
        for guild in self.guilds:
            logtimestamp = datetime.datetime.now().strftime('[%Y-%m-%d-%H:%M:%S] ')
            print(f'{logtimestamp} {self.user} is connected to the following guild: {guild.name}(id: {guild.id})')

    async def on_message(self, msg):
        pass


def main():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    LOGCHANID = int(os.getenv('LOG_CHANNEL_ID'))
    bot = MuteBot(logchannel=LOGCHANID,command_prefix='!', help_command=None)

    bot.run(TOKEN)


if __name__ == '__main__':
    main()