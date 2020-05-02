import pandas as pd
from kiteconnect import KiteConnect

from pyalgotrading.broker.broker_connection_base import BrokerConnectionBase
from pyalgotrading.constants import *

ORDER_TRANSACTION_TYPE_MAP = {BrokerOrderTransactionTypeConstants.BROKER_ORDER_TRANSACTION_TYPE_BUY: 'BUY',
                              BrokerOrderTransactionTypeConstants.BROKER_ORDER_TRANSACTION_TYPE_SELL: 'SELL'}

ORDER_TYPE_MAP = {BrokerOrderTypeConstants.BROKER_ORDER_TYPE_REGULAR: 'regular',
                  BrokerOrderTypeConstants.BROKER_ORDER_TYPE_BRACKET: 'bo',
                  BrokerOrderTypeConstants.BROKER_ORDER_TYPE_COVER: 'co'}

ORDER_CODE_MAP = {BrokerOrderCodeConstants.BROKER_ORDER_CODE_INTRADAY: 'MIS',
                  BrokerOrderCodeConstants.BROKER_ORDER_CODE_DELIVERY: 'CNC'}

ORDER_VARIETY_MAP = {BrokerOrderVarietyConstants.BROKER_ORDER_VARIETY_MARKET: 'MARKET',
                     BrokerOrderVarietyConstants.BROKER_ORDER_VARIETY_LIMIT: 'LIMIT',
                     BrokerOrderVarietyConstants.BROKER_ORDER_VARIETY_STOPLOSS_LIMIT: 'SL',
                     BrokerOrderVarietyConstants.BROKER_ORDER_VARIETY_STOPLOSS_MARKET: 'SL-M'}


class BrokerConnectionZerodha(BrokerConnectionBase):

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.api = KiteConnect(api_key=self.api_key)
        print(self.api.login_url())

        self.all_instruments = None

    def set_access_token(self, request_token):
        data = self.api.generate_session(request_token, api_secret=self.api_secret)
        self.api.set_access_token(data["access_token"])

    def get_all_instruments(self):
        self.all_instruments = pd.DataFrame(self.api.instruments())
        return self.all_instruments

    def get_instrument(self, segment, tradingsymbol):
        if self.all_instruments is None:
            self.all_instruments = self.get_all_instruments()
        return self.all_instruments[(self.all_instruments.segment == segment) & (self.all_instruments.tradingsymbol == tradingsymbol)].iloc[0]

    def get_quote(self, segment, tradingsymbol):
        instrument = f'{segment}:{tradingsymbol}'
        quote = self.api.quote([instrument])[instrument]
        return quote

    def get_market_depth(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        buy_market_depth = pd.DataFrame(quote['depth']['buy'])
        sell_market_depth = pd.DataFrame(quote['depth']['sell'])
        return buy_market_depth, sell_market_depth

    def get_circuit_limits(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        lower_circuit_limit = quote['lower_circuit_limit']
        upper_circuit_limit = quote['upper_circuit_limit']
        return lower_circuit_limit, upper_circuit_limit

    def get_ltp(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        ltp = quote['last_price']
        return ltp

    def get_ltt(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        ltt = quote['last_trade_time']
        return ltt

    def get_ltq(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        ltq = quote['last_quantity']
        return ltq

    def get_total_buy_quantity_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        total_buy_quantity_day = quote['buy_quantity']
        return total_buy_quantity_day

    def get_total_sell_quantity_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        total_sell_quantity_day = quote['sell_quantity']
        return total_sell_quantity_day

    def get_total_volume_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        total_volume_day = quote['volume']
        return total_volume_day

    def get_open_price_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        open_price_day = quote['ohlc']['open']
        return open_price_day

    def get_high_price_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        high_price_day = quote['ohlc']['high']
        return high_price_day

    def get_low_price_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        low_price_day = quote['ohlc']['low']
        return low_price_day

    def get_close_price_last_day(self, segment, tradingsymbol):
        quote = self.get_quote(segment, tradingsymbol)
        close_price_day = quote['ohlc']['close']
        return close_price_day

    def get_historical_data(self, instrument, candle_interval, start_date, end_date):
        return pd.DataFrame(self.api.historical_data(instrument['instrument_token'], from_date=start_date, to_date=end_date, interval=candle_interval)) \
            .reindex(['date', 'open', 'high', 'low', 'close', 'volume'], axis="columns").rename(columns={'date': 'timestamp'})

    def get_funds(self, segment):
        return self.api.margins(segment=segment)['net']

    def get_profile(self):
        return self.api.profile()

    def place_order(self, instrument, order_transaction_type, order_type, order_code, order_variety, quantity, price=None, trigger_price=None, stoploss=None, target=None, trailing_stoploss=None):
        _variety = ORDER_TYPE_MAP[order_type]  # what we call as 'Order Type', Zerodha calls it as 'variety'
        _transaction_type = ORDER_TRANSACTION_TYPE_MAP[order_transaction_type]
        _product = ORDER_CODE_MAP[order_code]  # what we call as 'Order Code', Zerodha calls it as 'product'
        _order_type = ORDER_VARIETY_MAP[order_variety]  # What we call as 'Order Variety', Zerodha calls it as 'order_type'
        return self.api.place_order(variety=_variety, exchange=instrument.exchange, tradingsymbol=instrument.tradingsymbol, transaction_type=_transaction_type, quantity=quantity, product=_product, order_type=_order_type, price=price,
                                    trigger_price=trigger_price, squareoff=target, stoploss=stoploss, trailing_stoploss=trailing_stoploss)

    def get_order_status(self, order_id):
        return self.api.order_history(order_id)[-1]['status']

    def cancel_order(self, order_id, order_type):
        _variety = ORDER_TYPE_MAP[order_type]  # What we call as 'Order Type', Zerodha calls it as 'variety'
        return self.api.cancel_order(variety=_variety, order_id=order_id)