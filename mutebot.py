# pylint: disable=import-error,consider-using-with
# bot.py
import os
from datetime import datetime, timedelta
import json
import random
from decimal import Decimal as dec
from discord.ext import commands
from dotenv import load_dotenv
from numpy import interp
import discord

def position(now=None):
    """Credits to Sean B. Palmer, inamidst.com for the snippet"""
    if now is None: 
        now = datetime.now()

    diff = now - datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))

    return round(float(lunations % dec(1)), 3)

def load_targets(configfile):
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
        return {}

class Victim():
    """Class for a target, records message intervals and determines if it should be muted/unmuted"""

    #pylint: disable=too-many-instance-attributes
    #eight instance attributes is relevant for us
    def __init__(self, user_id, perma=False, interval_limit=5, base_rate=10, mute_duration=10):
        self.is_muted = False
        self.id = user_id
        self.mute_time = None
        self.mute_duration = mute_duration
        self.message_intervals = []
        self.interval_limit = interval_limit
        self.last_message_time = None
        self.base_rate = base_rate
        #flag if this user is config hardcoded
        self.perma = perma
        #print(f"New victim loaded {self.id}")

   # def __repr__(self):
    #    return f'{self.id}'

    def spoke(self):
        """Register that a target has written a message"""

        #we check if enough time has elapsed to unmute the target
        self.unmute_check()
        #calculate message intervals so we can build a rate collection
        if self.last_message_time is None:
            self.last_message_time = datetime.now()
            return
        message_time = datetime.now()
        delta = message_time - self.last_message_time
        self.message_intervals.append(delta.total_seconds())
        #limit the stored message intervals to certain amount of recent messages
        while len(self.message_intervals) > self.interval_limit:
            self.message_intervals.pop(0)
        self.last_message_time = message_time
        #check if we should be muted now
        self.should_mute()
    
    def should_mute(self):
        """Calculates if the target should be muted"""

        if len(self.message_intervals) < 2:
            #not enough data yet
            return

        #this whole algorithm is cursed. All you need to know is if the victim types faster than their avg they get closer to the full base rate
        #slower and they can subtract the base rate to nothing. The moon's phase makes this weird
        intervals = [interp(x, [min(self.message_intervals), max(self.message_intervals)], [0,100]) for x in self.message_intervals]
        clamped_avg = sum(intervals) / len(intervals)
        #moon_phase = position(datetime(2022,7,14))
        #print("Chance for today")
        moon_phase = position()
        mod_rate = self.base_rate * moon_phase
        #print(f'{self.base_rate}, {moon_phase}, {mod_rate}')

        last_message = interp(intervals[-1], [min(intervals),max(intervals)], [0,clamped_avg])
        chance = self.base_rate - interp(last_message, [0,clamped_avg], [0,mod_rate])
        rng = random.uniform(0.0,100.0)
        if rng <= chance:
            #we mute!
            print("Muting!")
            self.mute()


    def mute(self):
        """Mute the target for the duration specified""" 
        self.is_muted = True
        self.mute_time = datetime.now() + timedelta(0,self.mute_duration)
        #print(self.mute_time)

    def unmute_check(self):
        """Unmute the target if enough time has elapsed"""
        if not self.is_muted:
            return
        if datetime.now() >= self.mute_time:
            self.is_muted = False

class MuteBot(discord.Client):
    """The discord bot shell. Loads the config, creates victims, and carries out message deletion"""

    def __init__(self, *args, configfile='config.json', logchannel=None, **kwargs):

        self.configfile = configfile
        self.targets = load_targets(self.configfile)
        victims = {user : Victim(user, perma=True) for user in self.targets["users"]}
        self.targets["users"] = victims

        super().__init__(*args, **kwargs)
        if logchannel:
            self.logchannel = self.get_channel(logchannel)


    async def on_ready(self):
        """Discord client startup"""
        for guild in self.guilds:
            logtimestamp = datetime.now().strftime('[%Y-%m-%d-%H:%M:%S] ')
            print(f'{logtimestamp} {self.user} is connected to the following guild: {guild.name}(id: {guild.id})')


    def is_target(self, user):
        """Checks if a user is in our target list"""
        for role in self.targets['roles']:
            if role in [user_role.id for user_role in user.roles]:
                if user.id not in self.targets["users"]:
                    print("Adding user")
                    self.targets["users"][user.id] = Victim(user.id)
                return True
        if user.id not in self.targets['users'].keys():
            return False
        
        if not self.targets['users'][user.id].perma:
            #not a hardcoded user and no longer has role, remove
            self.targets['users'].pop(user.id)
            return False
        return True


    async def on_message(self, msg):
        """Discord bot message hook"""

        if not self.is_target(msg.author):
            return
        print(f"target user found: {msg.author.display_name}")
        victim = self.targets["users"][msg.author.id]
        victim.spoke()
        if victim.is_muted:
            print(f'Deleting message: {msg}')
            await msg.delete()


def main():
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    #logchanid = int(os.getenv('LOG_CHANNEL_ID'))
    bot = MuteBot(command_prefix='!', help_command=None)

    bot.run(token)


if __name__ == '__main__':
    main()