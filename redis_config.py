import json
import os

from redis import asyncio as aioredis

redis_client = aioredis.Redis(host=os.getenv("REDIS_HOST"), port=6379)

# 곧바로 웹소켓을 이용하는것이 아닌, 웹소켓 -> 레디스 -> 웹소켓의 구조. ==> 레디스가 중계 역할을 해주어 여러 서버간에 메시지 게시 가능.


# single channel
async def publish(message):
    await redis_client.publish("main_chat", message)

# 여러 유저가 받아볼 수 있게끔 파라미터로 유저를 받아주었다. -> 원래는 받지 않고 모두에게 주는 로직을 사용했더니 같은 메시지가 여러번씩 떴었다.
async def listening(pub_sub, request, user):
    async for message in pub_sub.listen():
        if message['type'] == "message":
            await request.app['sockets'][user].send_json(json.loads(message['data'].decode("utf-8")))