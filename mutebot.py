# pylint: disable=import-error,consider-using-with
# bot.py
import os
from datetime import datetime
import json
from discord.ext import commands
from dotenv import load_dotenv
from decimal import Decimal as dec
import discord


def position(now=None):
    """Credits to Sean B. Palmer, inamidst.com for the snippet"""
    if now is None: 
        now = datetime.now()

    diff = now - datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))

    return round(float(lunations % dec(1)),3)

class Victim():
    def __init__(self, user_id, interval_limit=20):
        self.is_muted = False
        self.id = user_id
        self.mute_time = None
        self.mute_duration = None
        self.message_intervals = []
        self.interval_limit = interval_limit
        self.last_message_time = None
        #print(f"New victim loaded {self.id}")

   # def __repr__(self):
    #    return f'{self.id}'

    def spoke(self):
        """Register that a target has written a message"""
        if self.last_message_time is None:
            self.last_message_time = datetime.now()
            return
        message_time = datetime.now()
        delta = message_time - self.last_message_time
        self.message_intervals.append(delta.total_seconds())
        #limit the stored message intervals to certain amount of recent messages
        while len(self.message_intervals) >= self.interval_limit:
            self.message_intervals.pop(0)
        self.last_message_time = message_time
        self.should_mute()
    
    def should_mute(self):
        #getting the avg interval time
        avg = sum(self.message_intervals) / len(self.message_intervals)
        if avg > 100:
            inverse_rate = 100
        inverse_rate = 100 - avg
        moon_phase = position()

        print(inverse_rate * moon_phase)





class MuteBot(discord.Client):

    def __init__(self,logchannel, configfile='config.json', *args, **kwargs):

        self.configfile = configfile
        self.targets = self.load_targets(self.configfile)
        victims = {user : Victim(user) for user in self.targets["users"]}
        self.targets["users"] = victims       
 
        super().__init__(*args, **kwargs)
        self.logchannel = self.get_channel(logchannel)

    def load_targets(self, configfile):
        """Load initial targets using discord ID's stored in a JSON file,
        can be user IDs or Role IDs."""
        #we probably dont actually NEED it to be a json file, but makes it nice if we expand later
        if not os.path.exists(configfile):
            targets =  {'users':[], 'roles':[]}
            with open(configfile, "w+", encoding="utf8") as fp:
                fp.write(json.dumps(targets))
            return targets

        try:
            with open(configfile, "r+", encoding="utf8") as fp:
                targets = json.load(fp)
                #validate we loaded good json, can delete if we dont like it later
                if 'users' not in targets.keys() or 'roles' not in targets.keys():
                    raise ValueError("Found JSON but not kind we like")
                return targets
        except Exception as e:
            print(e)


    async def on_ready(self):
        for guild in self.guilds:
            logtimestamp = datetime.now().strftime('[%Y-%m-%d-%H:%M:%S] ')
            print(f'{logtimestamp} {self.user} is connected to the following guild: {guild.name}(id: {guild.id})')


    def is_target(self, user):
        for role in self.targets['roles']:
            if role in [user_role.id for user_role in user.roles]:
                return True
        return user.id in self.targets['users'].keys()


    async def on_message(self, msg):

        if not self.is_target(msg.author):
            return
        print(f"target user found: {msg.author.display_name}")


def main():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    LOGCHANID = int(os.getenv('LOG_CHANNEL_ID'))
    bot = MuteBot(logchannel=LOGCHANID,command_prefix='!', help_command=None)

    bot.run(TOKEN)


if __name__ == '__main__':
    main()