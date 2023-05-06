#logging code
class DiscordChannelHandler(logging.Handler):
    def __init__(self, channel_id):
        super().__init__()
        self.channel_id = channel_id

    async def send_log(self, message):
        channel = bot.get_channel(self.channel_id)
        if channel:
            await channel.send(message)

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.ensure_future(self.send_log(log_entry))


import discord
from discord.ext import commands, tasks
from collections import deque
from datetime import datetime, timedelta
import aiohttp
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Set a threshold for the maximum number of requests per second
REQUESTS_PER_SECOND = 10

# Define a dictionary to keep track of requests by IP address
request_counts = {}

#raid variables
JOIN_LOG = deque(maxlen=10)  # Adjust this value based on the desired join event tracking
TIME_THRESHOLD = timedelta(seconds=10)  # Adjust this value based on the desired time threshold
JOIN_LIMIT = 5  # Adjust this value based on the desired user join limit

#meme variables
POST_INTERVAL_MINUTES = 20  # Set the desired interval between meme posts (in minutes)
MEME_CHANNEL_ID = 1103151667098157177  # Set the ID of the channel where memes will be posted

#logging variables
log_channel_id = 1103157649136177153  # Replace with your desired channel ID
logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = DiscordChannelHandler(log_channel_id)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

#application variables

# Channel IDs and Role IDs
APPLICATION_CHANNEL_ID = 1234567890
SUBMISSION_CHANNEL_ID = 9876543210
RESULTS_CHANNEL_ID = 1029384756
APPLICANT_ROLE_ID = 1928374650

# Application questions
questions = [
    "What is your name?",
    "How old are you?",
    "Why do you want to join our community?",
]

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    post_meme.start() # This is part of the meme code


##Defense Section

#DDos Protection

@bot.event
async def on_message(message):
    # Get the IP address of the user who sent the message
    ip_address = message.author.ip

    # Check if the IP address has exceeded the threshold for requests per second
    if ip_address in request_counts and request_counts[ip_address] > REQUESTS_PER_SECOND:
        # If the IP address has exceeded the threshold, delete the message and ban the user
        await message.delete()
        await message.author.ban(reason='Excessive requests')
    else:
        # If the IP address has not exceeded the threshold, increment the request count
        request_counts[ip_address] = request_counts.get(ip_address, 0) + 1

    # Allow the message to be processed as usual
    await bot.process_commands(message)
    
# Lockdown code

async def lockdown(guild, lock):
    everyone_role = guild.default_role
    perms = everyone_role.permissions
    perms.update(send_messages=not lock)
    await everyone_role.edit(permissions=perms)

@bot.event
async def on_member_join(member):
    current_time = datetime.utcnow()
    JOIN_LOG.append(current_time)

    # Check if the number of joins exceeds the limit within the time threshold
    if len(JOIN_LOG) == JOIN_LOG.maxlen and JOIN_LOG[-1] - JOIN_LOG[0] <= TIME_THRESHOLD:
        await lockdown(member.guild, True)  # Lockdown the server
        print(f"Lockdown triggered in {member.guild.name}")
        
@bot.command(description='Unlock')
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    await lockdown(ctx.guild, False)  # Unlock the server
    print(f"Lockdown lifted in {ctx.guild.name}")
    
#Admin protecion code
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        print(f"Unauthorized command usage detected by {ctx.author}. Shutting down the bot
        logger.error(f"Admin command error, bot shutting down. Command: '{ctx.command}', Error: {error}")
        await bot.logout()
    else
        logger.error(f"Error in command '{ctx.command}', Error: {error}")
        
        
# XP Code

# Cool bois code goes here

# Meme code (oof)

async def get_meme():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://meme-api.herokuapp.com/gimme') as response:
            if response.status == 200:
                json_response = await response.json()
                return json_response['url']
    return None

@tasks.loop(minutes=POST_INTERVAL_MINUTES)
async def post_meme():
    channel = bot.get_channel(MEME_CHANNEL_ID)
    meme_url = await get_meme()
    if meme_url:
        await channel.send(meme_url)
        
#Application code
@bot.command()
async def apply(ctx):
    if ctx.channel.id != APPLICATION_CHANNEL_ID:
        return

    def check(m):
        return m.author == ctx.author and m.channel.id == APPLICATION_CHANNEL_ID

    application = {}
    applicant_role = ctx.guild.get_role(APPLICANT_ROLE_ID)

    await ctx.author.add_roles(applicant_role)
    await ctx.send(embed=discord.Embed(title="Welcome to the application process!", description="Please answer the following questions:", color=discord.Color.green()))

    for question in questions:
        embed_question = discord.Embed(description=question, color=discord.Color.green())
        await ctx.send(embed=embed_question)
        try:
            answer = await bot.wait_for("message", timeout=300, check=check)
            application[question] = answer.content
        except asyncio.TimeoutError:
            await ctx.author.remove_roles(applicant_role)
            await ctx.send(embed=discord.Embed(title="Timeout", description="You took too long to answer. The application process has been canceled.", color=discord.Color.red()))
            return

    # Send the application to the submission channel
    submission_channel = bot.get_channel(SUBMISSION_CHANNEL_ID)
    formatted_application = "\n".join([f"{k}: {v}" for k, v in application.items()])
    embed_submission = discord.Embed(title=f"New application from {ctx.author.name}", description=formatted_application, color=discord.Color.green())
    await submission_channel.send(embed=embed_submission)

    # Send the result to the results channel
    results_channel = bot.get_channel(RESULTS_CHANNEL_ID)
    embed_result = discord.Embed(title="Application Completed", description=f"{ctx.author.mention} has completed the application process.", color=discord.Color.green())
    await results_channel.send(embed=embed_result)

    # Remove the applicant role
    await ctx.author.remove_roles(applicant_role)
    await ctx.send(embed=discord.Embed(title="Application Submitted", description="Thank you for completing the application. Our team will review your submission.", color=discord.Color.green()))        

bot.run(MTEwMzEyOTI4MTM4ODg3MTc5MQ.GsHNwB.vd6YBmo44yHeUoX2KMrQX6Ce9JsnMVRwvJp-jM)

#Might be missing bot events