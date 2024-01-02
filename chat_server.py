import ipaddress
import logging
import os
from aiohttp import web
import redis_config
import socket

routes = web.RouteTableDef()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


@routes.get("/config")
async def socket_port(request):
    websocket_port = os.getenv("WEBSOCKET_PORT", 8080)
    logging.info("now port is {}".format(websocket_port))
    return web.json_response({"wport": websocket_port})


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
    await ws.prepare(request)  # 웹소켓 대기

    # 1. 연결단계
    user = await ws.receive_str()  # -> 클라이언트에게 유저 이름을 받는다.
    if user not in request.app['sockets'].keys():  # -> 같은 소켓내의 중복을 방지한다.
        request.app['sockets'][user] = ws  # -> 그렇다면 app["socket"] 에 만들어둔 딕셔너리에 이 웹소켓 객체를 매핑
        pubsub = redis_config.redis_client.pubsub()  # 레디스 pubsub 객체 만들고
        await pubsub.subscribe("main_chat")  # 단일 채팅방 구독
        logging.info(
            "room info : {}".format(await redis_config.redis_client.execute_command("PUBSUB", "NUMSUB", "main_chat")))
    else:
        logging.error("not allowed same name")
        return ws

    # 2. 채팅단계
    # 2-1. 별도의 task 를 비동기적으로 대기시킨다. -> 레디스에서 새로운 소식이 넘어오면 웹소켓으로 받는코드 (sub)
    request.app.loop.create_task(redis_config.listening(pubsub, request, user))

    # 2-2. 소켓을 통해 메시지를 받는다 -> 만약 타입이 텍스트가 아닌 에러? => 종료
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            msg = msg.json()
            jsonable_str = str(msg).replace("'", "\"")
            await redis_config.publish(jsonable_str)  # 받은 데이터 json 으로 바꿔서 pub
        else:
            logging.error("ws connection closed with exception {}".format(ws.exception()))
            return ws

    # 3. 종료단계
    del request.app['sockets'][user]  # 소켓에서 사용자 제거
    logging.info(  # 직접 redis 의 Numsub명령어로 몇명의 구독자가 남았는지 확인한다.
        "room info : {}".format(await redis_config.redis_client.execute_command("PUBSUB", "NUMSUB", "main_chat")))
    await pubsub.unsubscribe()  # 구독취소
    return ws


async def init():
    app = web.Application()
    app.add_routes(routes)
    app["sockets"] = dict()
    return app


if __name__ == "__main__":
    web.run_app(init())
