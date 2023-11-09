from fastapi import FastAPI 
from starlette.background import BackgroundTasks
import uvicorn
from models import  SettingAdmin, SignalAdmin, SymbolAdmin, ReportView
from database import engine, Base
from database import get_db
from sqladmin import Admin
from setLogger import get_logger
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from main import Bingx


logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_db()

app = FastAPI(lifespan=lifespan)
admin = Admin(app, engine)


admin.add_view(SettingAdmin)
admin.add_view(SignalAdmin)
admin.add_view(SymbolAdmin)
admin.add_view(ReportView)


@app.get('/run')
async def run(tasks: BackgroundTasks):
    # tasks.add_task(handle_schedule)
    Bingx.bot = "Run"
    #await run_in_threadpool(handle_schedule)
    return  RedirectResponse(url="/admin/home")

@app.get('/stop')
def stop():
    Bingx.bot = "Stop"
    print("Bingx stoped. ................")
    return  RedirectResponse(url="/admin/home")

@app.get('/closeAll')
def closeAll():
    Bingx._try(method="closeAll")
    print("Close All Positions.")
    return  RedirectResponse(url="/admin/home")


@app.get('/')
def index():
    return  RedirectResponse(url="/admin/home")


if __name__ == '__main__':
	uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



