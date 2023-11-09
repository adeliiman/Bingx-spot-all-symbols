
from sqlalchemy import Column,Integer,Numeric,String, DateTime, Boolean, Float
from database import Base
from sqladmin import Admin, ModelView
from sqladmin import BaseView, expose
import wtforms



class Setting(Base):
    __tablename__ = "setting"
    id = Column(Integer,primary_key=True)  
    timeframe = Column(String)


class SettingAdmin(ModelView, model=Setting):
    #form_columns = [User.name]
    column_list = [Setting.id, Setting.timeframe]
    name = "Setting"
    name_plural = "Setting"
    icon = "fa-solid fa-user"
    form_args = dict(timeframe=dict(default="15min", choices=["15min", "1min", "5min", "1hour", "4hour"]), 
                     )
    form_overrides =  dict(timeframe=wtforms.SelectField)

    async def on_model_change(self, data, model, is_created):
        # Perform some other action
        #print(data)
        pass

    async def on_model_delete(self, model):
        # Perform some other action
        pass



class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer,primary_key=True,index=True)
    symbol = Column(String)
    side = Column(String)
    peak2 = Column(Float)
    level0 = Column(Float)
    level1 = Column(Float)
    level2 = Column(Float)
    level3 = Column(Float)
    SLPrice = Column(Float)
    vol1 = Column(Float)
    vol2 = Column(Float)
    vol3 = Column(Float)
    time = Column(String)
    status = Column(String)


class SignalAdmin(ModelView, model=Signal):
    column_list = [Signal.id, Signal.symbol, Signal.side, Signal.time, Signal.level0, Signal.level1, Signal.level2, Signal.level3, 
                   Signal.SLPrice, Signal.status, Signal.peak2]
    column_searchable_list = [Signal.symbol, Signal.side, Signal.time]
    #icon = "fa-chart-line"
    icon = "fas fa-chart-line"
    column_sortable_list = [Signal.id, Signal.time]
    column_formatters = {Signal.level0 : lambda m, a: round(m.level0,4),
                         Signal.level1 : lambda m, a: round(m.level1,4),
                         Signal.level2 : lambda m, a: round(m.level2,4),
                         Signal.level3 : lambda m, a: round(m.level3,4),
                         Signal.SLPrice : lambda m, a:round(m.SLPrice,4)}
    
    async def on_model_change(self, data, model, is_created):
        # Perform some other action
        #print(data)
        pass

class Symbols(Base):
    __tablename__ = "symbols"
    id = Column(Integer,primary_key=True)
    symbol = Column(String)
    fibo1 = Column(Float, default=1.1)
    fibo2 = Column(Float, default=1.5)
    fibo3 = Column(Float, default=1.75)
    slLevel = Column(Float, default=2)
    vol1 = Column(Integer, default=1)
    vol2 = Column(Integer, default=2)
    vol3 = Column(Integer, default=7)
    leverage = Column(Integer, default=10)
    marginMode = Column(String)
    test = Column(String)


class SymbolAdmin(ModelView, model=Symbols):
    column_list = [Symbols.id, Symbols.symbol, Symbols.fibo1, Symbols.fibo2, Symbols.fibo3, Symbols.slLevel,
                   Symbols.vol1, Symbols.vol2, Symbols.vol3, Symbols.leverage, Symbols.marginMode, Symbols.test]
    name = "Symbol"
    name_plural = "Symbol"
    icon = "fa-sharp fa-solid fa-bitcoin-sign"
    form_overrides = dict(symbol=wtforms.StringField, marginMode=wtforms.SelectField)
    form_args = dict(symbol=dict(validators=[wtforms.validators.regexp('.+[A-Z]-USDT')], label="symbol(BTC-USDT)"),
                     marginMode=dict(choices=["Isolated", "Cross"]))
    async def on_model_change(self, data, model, is_created):
        print(is_created)
        from database import SessionLocal
        db = SessionLocal()
        symbol = db.query(Symbols).order_by(Symbols.id.desc()).first()
        symbol.test = "iman"
        db.commit()




class ReportView(BaseView):
    name = "Home"
    icon = "fas fa-house-user"

    @expose("/home", methods=["GET"])
    def report_page(self, request):
        from main import Bingx
        return self.templates.TemplateResponse("base1.html", context={"request":request, "status":Bingx.bot})




class AllSymbols(Base):
    __tablename__ = "all_symbols"
    id = Column(Integer,primary_key=True)
    symbol = Column(String)

class AllSymbolAdmin(ModelView, model=AllSymbols):
    column_list = [AllSymbols.id, AllSymbols.symbol]
    column_searchable_list = [AllSymbols.symbol]
    column_sortable_list = [AllSymbols.symbol]
    name = "symbol"
    name_plural = "All Symbols"
    icon = "fa-sharp fa-solid fa-bitcoin-sign"
    