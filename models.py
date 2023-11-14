
from sqlalchemy import Column,Integer,Numeric,String, DateTime, Boolean, Float
from database import Base
from sqladmin import Admin, ModelView
from sqladmin import BaseView, expose
import wtforms



class Setting(Base):
    __tablename__ = "setting"
    id = Column(Integer,primary_key=True)  
    timeframe = Column(String)
    trade_value = Column(Integer)
    ma1 = Column(Integer)
    ma2 = Column(Integer)
    ma3 = Column(Integer)
    ma4 = Column(Integer)
    chandelier_length = Column(Integer)
    chandelier_multi = Column(Integer)
    use_all_symbols = Column(String)


class SettingAdmin(ModelView, model=Setting):
    #form_columns = [User.name]
    column_list = [Setting.id, Setting.timeframe, Setting.trade_value, Setting.ma1, Setting.ma2, Setting.ma3, Setting.ma4,
                    Setting.chandelier_length, Setting.chandelier_multi, Setting.use_all_symbols]
    name = "user setting"
    name_plural = "Setting"
    icon = "fa-solid fa-user"
    form_args = dict(timeframe=dict(default="15min", choices=["1min", "15min", "5min", "30min", "1hour", "4hour"]), 
                     use_all_symbols=dict(default="user_symbols", choices=["user_symbols", "All_symbols"]))
    form_overrides =  dict(timeframe=wtforms.SelectField, use_all_symbols=wtforms.SelectField)

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
    price = Column(Float)
    qty = Column(Float)
    time = Column(String)


class SignalAdmin(ModelView, model=Signal):
    column_list = [Signal.id, Signal.symbol, Signal.side, Signal.time, Signal.qty]
    column_searchable_list = [Signal.symbol, Signal.side, Signal.time, Signal.qty]
    #icon = "fa-chart-line"
    icon = "fas fa-chart-line"
    column_sortable_list = [Signal.id, Signal.time, Signal.qty]
    # column_formatters = {Signal.level0 : lambda m, a: round(m.level0,4),
    #                      Signal.level1 : lambda m, a: round(m.level1,4),
    #                      Signal.level2 : lambda m, a: round(m.level2,4),
    #                      Signal.level3 : lambda m, a: round(m.level3,4),
    #                      Signal.SLPrice : lambda m, a:round(m.SLPrice,4)}
    
    async def on_model_change(self, data, model, is_created):
        # Perform some other action
        #print(data)
        pass

class Symbols(Base):
    __tablename__ = "symbols"
    id = Column(Integer,primary_key=True)
    symbol = Column(String)

class SymbolAdmin(ModelView, model=Symbols):
    column_list = [Symbols.id, Symbols.symbol]
    name = "Symbol"
    sname_plural = "user Symbol"
    icon = "fa-sharp fa-solid fa-bitcoin-sign"
    form_overrides = dict(symbol=wtforms.StringField, marginMode=wtforms.SelectField)
    form_args = dict(symbol=dict(validators=[wtforms.validators.regexp('.+[A-Z]-USDT')], label="symbol(BTC-USDT)"),
                     marginMode=dict(choices=["Isolated", "Cross"]))
    async def on_model_change(self, data, model, is_created):
        pass


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
    