import json
import os

from redis import asyncio as aioredis

redis_client = aioredis.Redis(host=os.getenv("REDIS_HOST"), port=6379)

# 곧바로 웹소켓을 이용하는것이 아닌, 웹소켓 -> 레디스 -> 웹소켓의 구조.


# single channel
async def publish(message):
    await redis_client.publish("main_chat", message)


# 하나의 프로세스에 여러 소켓들이 매달려 있을수도 있다.
async def listening(pub_sub, request, user):
    async for message in pub_sub.listen():
        if message['type'] == "message":
            await request.app['sockets'][user].send_json(json.loads(message['data'].decode("utf-8")))