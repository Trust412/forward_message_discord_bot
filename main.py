import asyncio
import json
import ssl
import aiohttp
import websockets
import websockets.exceptions
import zlib
import os
import logging
from datetime import datetime
from logger import logger
from dotenv import load_dotenv
import os

load_dotenv()
# Discord settings
MONITOR_USER_TOKEN =os.getenv("MONITOR_USER_TOKEN")

TARGET_USER_ID = 
DISCORD_WS_URL = "wss://gateway.discord.gg/?v=6&encoding=json"

if not os.path.exists('logs'):
    os.makedirs('logs')


async def send_payload(ws, payload):
    data = json.dumps(payload)
    if len(data.encode()) > 1048000:
        logging.warning("Payload too large, truncating...")
        payload['d'] = {k: v[:1000] if isinstance(v, str) else v 
                       for k, v in payload['d'].items()}
        data = json.dumps(payload)
    await ws.send(data)

async def send_message(sender, message):
    headers = {
        "Authorization": MONITOR_USER_TOKEN,
        "Content-Type": "application/json"
    }

    # First create a DM channel with the recipient
    print("0")
    channel_data = {
        "recipient_id": int(TARGET_USER_ID)  # Your second account's user ID
    }
    print(channel_data)
    async with aiohttp.ClientSession() as session:
        # Get or create DM channel
        async with session.post("https://discord.com/api/v10/users/@me/channels", 
                              headers=headers, 
                              json=channel_data) as response:
            dm_channel = await response.json()
            print("DM Channel Response:", dm_channel)  # This will show the full response
            
            dm_channel_id = dm_channel['id']
            print("Channel ID:", dm_channel_id)

            # Send the message
            message_data = {
                "content": f"`🔔 Message from {sender}`{message}"
            }
            print("Sending message with data:", message_data)

            async with session.post(f"https://discord.com/api/v10/channels/{dm_channel_id}/messages",
                                  headers=headers,
                                  json=message_data) as response:
                if response.status == 200:
                    print("🎆✨🧨🎆✨🧨🎆✨🧨🎆✨🧨 DM sent successfully!")


async def heartbeat(ws, interval, last_sequence):
    while True:
        await asyncio.sleep(interval)
        payload = {
            "op": 1,
            "d": last_sequence
        }
        await send_payload(ws, payload)
        logging.info("Heartbeat packet sent.")

async def identify(ws):
    identify_payload = {
        "op": 2,
        "d": {
            "token": MONITOR_USER_TOKEN,
            "properties": {
                "$os": "windows",
                "$browser": "chrome",
                "$device": "pc"
            },
            "compress": True,
            "large_threshold": 50,
            "intents": 513
        }
    }
    await send_payload(ws, identify_payload)
    logging.info("Identification sent.")

async def on_message(ws):
    last_sequence = None
    while True:
        try:
            message = await ws.recv()
            if isinstance(message, bytes):
                message = zlib.decompress(message).decode('utf-8')
            event = json.loads(message)
            logger.info("Received event: %s", event)
            op_code = event.get('op', None)

            if op_code == 10:
                interval = event['d']['heartbeat_interval'] / 1000
                asyncio.create_task(heartbeat(ws, interval, last_sequence))

            elif op_code == 0:
                last_sequence = event.get('s', None)
                event_type = event.get('t')
                
                if event_type == 'MESSAGE_CREATE':
                    # Log all message details
                    author = event['d']['author']
                    content = event['d']['content']
                    # channel_type = event['d'].get('channel_type', None)
                    sender = f"{author['global_name']} ({author['username']})"

                    message_text = ' '.join(content.split(' ')[1:])

                    await send_message(sender, message_text)

            elif op_code == 9:
                logging.info(f"Invalid session. Starting a new session...")
                await identify(ws)
               
        except Exception as e:
            logging.error(f"Error processing message: ")
            continue

async def main():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    while True:
        try:
            async with websockets.connect(DISCORD_WS_URL, ssl=ssl_context) as ws:
                await identify(ws)
                await on_message(ws)
        except websockets.exceptions.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed unexpectedly:. Reconnecting...")
            await asyncio.sleep(5)
            continue
        except Exception as e:
            logging.error(f"Unexpected error: . Reconnecting...")
            await asyncio.sleep(5)
            continue

if __name__ == "__main__":
    asyncio.run(main())