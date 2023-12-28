from aiohttp import web
import logging
import redis_config

routes = web.RouteTableDef()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


@routes.get("/")
async def index(request):
    f = open('./templates/index.html')
    return web.Response(text=f.read(), content_type="text/html")


@routes.get("/chat")
async def chat(request):
    f = open('./templates/chat.html')
    return web.Response(text=f.read(), content_type="text/html")


@routes.get("/ws")
async def websoket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 1. 연결단계
    user = await ws.receive_str()
    if user not in request.app['sockets'].keys():
        request.app['sockets'][user] = ws
        pubsub = redis_config.redis_client.pubsub()
        await pubsub.subscribe("main_chat")
        logging.info(
            "room info : {}".format(await redis_config.redis_client.execute_command("PUBSUB", "NUMSUB", "main_chat")))
    else:
        logging.error("not allowed same name")
        return ws

    # 2. 채팅단계
    request.app.loop.create_task(redis_config.listening(pubsub, request, user))

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            msg = msg.json()
            jsonable_str = str(msg).replace("'", "\"")
            await redis_config.publish(jsonable_str)
        else:
            logging.error("ws connection closed with exception {}".format(ws.exception()))
            return ws

    # 3. 종료단계
    del request.app['sockets'][user]
    logging.info(
        "room info : {}".format(await redis_config.redis_client.execute_command("PUBSUB", "NUMSUB", "main_chat")))
    await pubsub.unsubscribe()
    return ws


async def init():
    app = web.Application()
    app.add_routes(routes)
    app["sockets"] = dict()
    return app


if __name__ == "__main__":
    web.run_app(init())