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