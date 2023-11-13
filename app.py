from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
import uvicorn, requests
from models import  SettingAdmin, SignalAdmin, SymbolAdmin, ReportView, AllSymbols, AllSymbolAdmin
from database import engine, Base
from database import get_db
from sqladmin import Admin
from setLogger import get_logger
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from main import Bingx, main_job
from utils import get_user_params
import threading


logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_db()
    from Bingx_websocket_spot import start_bingx_ws
    threading.Thread(target=start_bingx_ws).start()
    yield
    Bingx.ws = False

app = FastAPI(lifespan=lifespan)
admin = Admin(app, engine)


admin.add_view(SettingAdmin)
admin.add_view(SignalAdmin)
admin.add_view(SymbolAdmin)
admin.add_view(AllSymbolAdmin)
admin.add_view(ReportView)


@app.get('/run')
async def run(tasks: BackgroundTasks, db:Session =Depends(get_db)):
    get_user_params(db)

    tasks.add_task(main_job)
    Bingx.bot = "Run"
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

# @app.get('/ws')
# async def ws(tasks: BackgroundTasks):
#     from Bingx_websocket_spot import start_bingx_ws
#     tasks.add_task(start_bingx_ws)
#     print("ws done.")


@app.get('/')
def index():
    return  RedirectResponse(url="/admin/home")

@app.get('/load-symbols')
def load_symbols(db: Session = Depends(get_db)):
    symbols_list = Bingx.loadSymbols()
    if not symbols_list: return None
    for sym in symbols_list:
        symbol_db = AllSymbols()
        symbol_db.symbol = sym
        db.add(symbol_db)
        db.commit()
        db.close()
    print('All Symbols Add.')


if __name__ == '__main__':
	uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



