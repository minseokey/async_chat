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


async def init():
    app = web.Application()
    app.add_routes(routes)
    app["sockets"] = dict()
    return app

if __name__ == "__main__":
    web.run_app(init())