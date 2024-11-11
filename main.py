import discord
import asyncio

# Replace with your user token
USER_TOKEN = 'YOUR_USER_TOKEN'

# Replace with the user ID of the account you want to monitor
MONITOR_USER_ID = YOUR_MONITOR_USER_ID

# Replace with the user ID of the account you want to send messages to
TARGET_USER_ID = YOUR_TARGET_USER_ID

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print('Monitoring messages...')

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Check if the message is from the monitored user
        if message.author.id == MONITOR_USER_ID:
            target_user = await self.fetch_user(TARGET_USER_ID)
            if target_user:
                await target_user.send(f'From {message.author}: {message.content}')

# Create an instance of the client and run it
intents = discord.Intents.default()
intents.messages = True  # Enable message intents
client = MyClient(intents=intents)
client.run(USER_TOKEN)
