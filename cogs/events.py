import main
import discord
from discord.ext import commands, tasks
# data
import random
# cogs
from cogs import users, configs, block
from cogs.utils import Utils
# afk command data
import datetime
import humanize


def setup(bot):
    bot.add_cog(Events(bot))
    # bot.add_cog(Loops(bot))


class Events(commands.Cog, name="Events"):
    """Event listeners (no commands)."""
    COG_EMOJI = "🛠️"

    def __init__(self, ctx):
        self.ctx = ctx
        self.purger.start()

    @commands.Cog.listener("on_ready")
    async def logged_in(self):
        print(f"Logged in as {self.ctx.user} (ID: {self.ctx.user.id})")
        print("------")

    @commands.Cog.listener("on_application_command_error")
    async def slash_command_error(self, ctx: discord.ApplicationContext, error):
        e = discord.Embed(description=f"`❌` {error}", color=0xFF6969)
        if isinstance(error, commands.BotMissingPermissions):
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(embed=e, ephemeral=True)
        elif isinstance(error, discord.ApplicationCommandError):
            await ctx.respond(embed=e, ephemeral=True)
        try:
            channel = self.ctx.get_channel(980964223121256529)
            e = discord.Embed(title=ctx.interaction.data.get(
                "name"), description=f"{ctx.author.mention} `❌` {error}")
            for i in ctx.interaction.data.get("options"):
                e.add_field(name=i["name"], value=i["value"])
            await channel.send(embed=e)
        except:
            pass
        raise error

    @commands.Cog.listener("on_command_error")
    async def command_error(self, ctx, error):
        e = discord.Embed(description=f"`❌` {error}", color=0xFF6969)
        if isinstance(error, commands.CommandNotFound):
            raise error
        elif isinstance(error, commands.BotMissingPermissions):
            raise error
        elif isinstance(error, commands.CommandError):
            await ctx.send(ctx.author.mention, embed=e)
        try:
            channel = self.ctx.get_channel(980964223121256529)
            msg = ctx.message.content.split(" ")
            e = discord.Embed(
                title=msg[0], description=f"{ctx.author.mention} `❌` {error}")
            msg.remove(str(msg[0]))
            c = 0
            for i in msg:
                c += 1
                e.add_field(name=f"Arg {c}", value=i)
            await channel.send(embed=e)
        except:
            pass
        raise error

    @commands.Cog.listener("on_member_join")
    async def member_data(self, member):
        afk = self.ctx.afk
        await users.UserCommands.update_data(self, afk, member)
        configs.save(self.ctx.afk_path, "w", afk)

    @commands.Cog.listener("on_guild_join")
    async def guild_add_data(self, guild):
        prefixes = self.ctx.guild_prefixes
        prefixes[str(guild.id)] = '-'
        configs.save(self.ctx.guild_prefixes_path, "w", prefixes)

        perms = self.ctx.perms
        perms[str(guild.id)] = {}
        configs.save(self.ctx.perms_path, "w", perms)

        triggers = self.ctx.triggers
        triggers[str(guild.id)] = {}
        triggers[str(guild.id)]["regex"] = {}
        triggers[str(guild.id)]["regex"]["toggle"] = False
        triggers[str(guild.id)]["regex"]["triggers"] = {}
        triggers[str(guild.id)]["match"] = {}
        triggers[str(guild.id)]["match"]["toggle"] = False
        triggers[str(guild.id)]["match"]["triggers"] = {}
        configs.save(self.ctx.triggers_path, "w", triggers)

    @commands.Cog.listener("on_guild_remove")
    async def guild_remove_data(self, guild):
        prefixes = self.ctx.guild_prefixes
        prefixes.pop(str(guild.id))
        configs.save(self.ctx.guild_prefixes_path, "w", prefixes)

        perms = self.ctx.perms
        perms.pop(str(guild.id))
        configs.save(self.ctx.perms_path, "w", perms)

        triggers = self.ctx.triggers
        triggers.pop(str(guild.id))
        configs.save(self.ctx.triggers_path, "w", triggers)

    @commands.Cog.listener("on_message")
    async def afk_check(self, message):
        # check if user is afk or members in message
        prefix = main.get_prefix(self.ctx, message)
        send = False
        afk_alert = discord.Embed(
            title=f"Members in your message are afk:")
        afk_alert.set_footer(
            text=f"Toggle: {prefix}alerts\nDMs Toggle: {prefix}dmalerts")
        if message.author.bot:
            return

        for member in message.mentions:
            if member.bot or member.id == message.author.id:
                return
            if self.ctx.afk[f'{member.id}']['AFK']:
                send = True

                # gets afk message
                reason = self.ctx.afk[f'{member.id}']['reason']

                # gets unix time
                unix_time = Utils.current_milli_time() - self.ctx.afk[f'{member.id}']['time']

                # user was afk for time.now() - time
                counter = humanize.naturaltime(datetime.datetime.now() - datetime.timedelta(seconds=unix_time // 1000))

                # add embed
                afk_alert.add_field(name=f"{member.display_name.replace('[AFK]', '')} - {counter}", value=f"\"{reason}\"", inline=True)

                # plus 1 time mentioned in afk.json
                self.ctx.afk[f'{member.id}']['mentions'] = int(self.ctx.afk[f'{member.id}']['mentions']) + 1

                # save json
                configs.save(self.ctx.afk_path, 'w', self.ctx.afk)

        if send:
            await users.UserCommands.sendafk(self, message, ["afk_alert", "afk_alert_dm"], afk_alert)
        await users.UserCommands.update_data(self, self.ctx.afk, message.author)
        # if message's author is afk continue
        if list(message.content.split(" "))[0] != f'{prefix}afk' and self.ctx.afk[f'{message.author.id}']['AFK']:
            # counter = unix now - unix since afk in format 0d 0h 0m 0s and if any of them except seconds are 0 remove them
            counter = Utils.display_time(Utils.current_milli_time() - self.ctx.afk[f'{message.author.id}']['time'])

            # get mentions
            mentionz = self.ctx.afk[f'{message.author.id}']['mentions']

            # make embed
            welcome_back = discord.Embed(
                description=f"**Welcome back {message.author.mention}!**")
            welcome_back.add_field(name="Afk for", value=counter, inline=True)
            welcome_back.add_field(
                name="Mentioned", value=f"{mentionz} time(s)", inline=True)
            welcome_back.set_footer(
                text=f"Toggle: {prefix}wbalerts\nDMs Toggle: {prefix}wbdmalerts")

            # reset afk for user
            self.ctx.afk[f'{message.author.id}']['AFK'] = False
            self.ctx.afk[f'{message.author.id}']['reason'] = 'None'
            self.ctx.afk[f'{message.author.id}']['time'] = '0'
            self.ctx.afk[f'{message.author.id}']['mentions'] = 0
            configs.save(self.ctx.afk_path, 'w', self.ctx.afk)

            # try to reset nickname
            try:
                nick = message.author.display_name.replace('[AFK]', '')
                await message.author.edit(nick=nick)
            except:
                pass
            if await block.BlockCommands.get_global_perm(self, message, "wb_alert", message.author):
                if await block.BlockCommands.get_global_perm(self, message, "wb_alert_dm", message.author):
                    await message.author.send(embed=welcome_back)
                else:
                    await message.reply(embed=welcome_back, delete_after=30)
        configs.save(self.ctx.afk_path, 'w', self.ctx.afk)

    @commands.Cog.listener("on_message")
    async def help_check(self, message):
        # check if user's message is only bot ping and reply with help, if not process commands
        if message.author.bot == False and self.ctx.user.mentioned_in(message) and len(message.content) == len(self.ctx.user.mention):
            await message.reply(embed=discord.Embed(description=f'My prefix is `{self.ctx.guild_prefixes[str(message.guild.id)]}` or {self.ctx.user.mention}, you can also use slash commands\nFor more info use the /help command!'))
        else:
            await self.ctx.process_commands(message)

    @commands.Cog.listener("on_message")
    async def word_triggers(self, message):
        if not message.author.bot and not message.channel.type == discord.ChannelType.private:
            for type in self.ctx.triggers[str(message.guild.id)]:
                if self.ctx.triggers[str(message.guild.id)][type]['toggle']:
                    await self.trigger(message, type)

    async def trigger(self, message, type: str):
        if type == "regex":
            msg = message.content.split(" ")
        else:
            msg = message.content
        try:
            for trigger, reply in self.ctx.triggers[str(message.guild.id)][type]["triggers"].items():
                multi_trigger = list(trigger.split('|'))
                for triggers in multi_trigger:
                    if triggers.casefold() in msg.casefold():
                        reply = random.choice(list(reply.split('|')))
                        await message.reply(reply)
                        break
        except:
            pass

    @tasks.loop(seconds=5)
    async def purger(self):
        rem = [False, None, None]
        for guild in self.ctx.timed_purge.items():
            for channel, timed in self.ctx.timed_purge[str(guild[0])].items():
                # sets the current time
                current_time = Utils.current_time()
                # checks list if the interval + time of last purge are lower than current time
                if timed[0] + timed[1] < current_time:
                    # sets current time in list
                    timed[1] = current_time
                    chnl = self.ctx.get_channel(int(channel))
                    if chnl is not None:
                        await chnl.purge(limit=None, check=lambda m: not m.pinned)
                        await chnl.send(embed=discord.Embed(description=f"**You ({chnl.mention}) have been purged.**").set_image(url=random.choice(["https://cdn.discordapp.com/attachments/920776187884732559/998236527714906172/PTRA_Purge.gif", "https://cdn.discordapp.com/attachments/967897893413462027/998047629139259402/3Tt5.gif", "https://c.tenor.com/giN2CZ60D70AAAAC/explosion-mushroom-cloud.gif"])).set_footer(text=f"Occurs every {Utils.display_time_s(timed[0])}"))
                    else:
                        rem = [True, str(guild[0]), str(channel)]
                    configs.save(self.ctx.timed_purge_path, "w", self.ctx.timed_purge)
        if rem[0]:
            self.ctx.timed_purge[rem[1]].pop(rem[2])
            configs.save(self.ctx.timed_purge_path, "w", self.ctx.timed_purge)

    @purger.before_loop
    async def purger_before_loop(self):
        await self.ctx.wait_until_ready()


"""
class Loops(commands.Cog):
    def __init__(self, ctx):
        self.ctx = ctx

    async def spam_start(self, ctx, id, time, text):
        await self.define_seconds(time)
        await self.spam.start(self, ctx, {time: text})

    def define_seconds(time=1):
        return time

    @commands.command(name="spam")
    async def start_spam_now(self, ctx):
        self.spam.start()

    @commands.group()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def channels(self, ctx):
        if ctx.invoked_subcommand is None:
            raise commands.CommandNotFound

    @channels.command()
    async def add(self, ctx, channel: discord.TextChannel, time, *, message):
        time_regex = re.compile("([0-9]+)(d|h|m|s)?")
        multiplier = {
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1,
            "None": 1  # if they type "30", this will be 30 seconds"
        }
        match = time_regex.match(time)

        if not match:
            raise commands.CommandError(
                "time is a required argument that is missing")

        seconds = int(match.groups()[0]) * multiplier.get(str(match.groups()[1]))

        input_spam = [channel, seconds, message]

        if await EventUtils.get_channel_bool(self, ctx, input_spam):
            await Utils.send_error(ctx, f"Channel already has repeating message.")
        else:
            await EventUtils.add_channel(self, ctx, input_spam)
            e = discord.Embed(title="Repeating message made:")
            e.add_field(name="Message", value=message)
            e.add_field(name="Repeats each", value=f"{seconds}s")
            e.add_field(name="In channel", value=channel.mention)
            await Utils.send_embed(ctx, e)
            await EventUtils.add_channel(self, ctx, input_spam)

    @channels.command()
    async def remove(self, ctx, channel: discord.TextChannel):
        spam = self.ctx.spam
        if str(channel.id) in spam[str(channel.guild.id)]:
            spam[str(channel.guild.id)].pop(str(channel.id))
            await Utils.send_embed(ctx, e=discord.Embed(description=f"Removed {channel.mention}", color=0x66FF99))
        else:
            await Utils.send_error(ctx, f"{channel.mention} isn't in data")

    @channels.command()
    async def list(self, ctx):
        channel_spam = await EventUtils.get_channels_active(self, ctx)
        e = discord.Embed(description="Active repeating messages:")
        for data in channel_spam:
            for id, value in data.items():
                e.add_field(
                    name=f"{id} - every {value[1]}s", value=f"{value[0]}")
        await Utils.send_embed(ctx, e)


class EventUtils():
    def __init__(self, ctx):
        self.ctx = ctx

    async def get_channels(guild):
        channels = []
        for channel in guild.text_channels:
            channels.append(channel)
        return channels

    async def get_channels_active(self, ctx):
        channel_list = []
        for guild in self.ctx.guilds:
            for channel in guild.text_channels:
                if await EventUtils.get_channel_bool(self, ctx, [channel]):
                    channel_spam = await EventUtils.get_channel_spam(self, ctx, channel)
                    channel_list.append(channel_spam)
        return channel_list

    async def check_channel(self, ctx, input_spam):
        spam = self.ctx.spam
        # if channel id isnt in guild
        if str(input_spam[0].id) in spam[str(input_spam[0].guild.id)]:
            return False
        else:
            await EventUtils.set_channel(self, ctx, input_spam, spam)

    async def set_channel(self, ctx, input_spam, spam):
        spam[str(input_spam[0].guild.id)][str(input_spam[0].id)] = {}
        spam[str(input_spam[0].guild.id)][str(input_spam[0].id)]["on"] = False
        spam[str(input_spam[0].guild.id)][str(input_spam[0].id)]["time"] = None
        spam[str(input_spam[0].guild.id)][str(input_spam[0].id)]["text"] = None

    async def get_channel_bool(self, ctx, input_spam):
        await EventUtils.check_channel(self, ctx, input_spam)
        spam = self.ctx.spam
        yn = spam[str(input_spam[0].guild.id)][str(input_spam[0].id)]["on"]
        return yn

    async def get_channel_spam(self, ctx, channel):
        await EventUtils.check_channel(self, ctx, [channel])
        spam = self.ctx.spam
        channel_id = spam[str(channel.guild.id)][str(channel.id)]
        channel_spam = {channel.id: [channel_id['text'], channel_id["time"]]}
        return channel_spam

    async def add_channel(self, ctx, input_spam):
        await EventUtils.check_channel(self, ctx, input_spam)
        spam = self.ctx.spam
        spam[str(input_spam[0].guild.id)][str(input_spam[0].id)]["on"] = True
        spam[str(input_spam[0].guild.id)][str(
            input_spam[0].id)]["time"] = input_spam[1]
        spam[str(input_spam[0].guild.id)][str(
            input_spam[0].id)]["text"] = input_spam[2]

    async def remove_channel(self, ctx, input_spam):
        await EventUtils.check_channel(self, ctx, input_spam)
        spam = self.ctx.spam
        spam[str(input_spam[0].guild.id)].pop(str(input_spam[0].id))
        await EventUtils.check_channel(self, ctx, input_spam)
"""
