from aiohttp import web


routes = web.RouteTableDef()

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
    if user not in request.app['sockets']:
        request.app['sockets'][user] = ws

    # 2. 채팅단계
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            msg_json = msg.json()
            for socket in request.app['sockets'].keys():
                await request.app['sockets'][socket].send_json(msg_json)

    # 3. 종료단계
    del request.app['sockets'][user]
    return ws

async def init():
    app = web.Application()
    app.add_routes(routes)
    app["sockets"] = dict()
    return app

if __name__ == "__main__":
    web.run_app(init())