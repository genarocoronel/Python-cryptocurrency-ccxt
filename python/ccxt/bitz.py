# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection
from ccxt.base.errors import InvalidNonce


class bitz (Exchange):

    def describe(self):
        return self.deep_extend(super(bitz, self).describe(), {
            'id': 'bitz',
            'name': 'Bit-Z',
            'countries': 'HK',
            'rateLimit': 1000,
            'version': 'v1',
            'has': {
                'fetchTickers': True,
                'fetchOHLCV': True,
                'fetchOpenOrders': True,
            },
            'timeframes': {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '1d': '1d',
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/35862606-4f554f14-0b5d-11e8-957d-35058c504b6f.jpg',
                'api': 'https://www.bit-z.com/api_v1',
                'www': 'https://www.bit-z.com',
                'doc': 'https://www.bit-z.com/api.html',
                'fees': 'https://www.bit-z.com/about/fee',
            },
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'tickerall',
                        'depth',
                        'orders',
                        'kline',
                    ],
                },
                'private': {
                    'post': [
                        'balances',
                        'tradeAdd',
                        'tradeCancel',
                        'openOrders',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.001,
                    'taker': 0.001,
                },
                'funding': {
                    'withdraw': {
                        'BTC': '0.5%',
                        'DKKT': '0.5%',
                        'ETH': 0.01,
                        'USDT': '0.5%',
                        'LTC': '0.5%',
                        'FCT': '0.5%',
                        'LSK': '0.5%',
                        'HXI': '0.8%',
                        'ZEC': '0.5%',
                        'DOGE': '0.5%',
                        'MZC': '0.5%',
                        'ETC': '0.5%',
                        'GXS': '0.5%',
                        'XPM': '0.5%',
                        'PPC': '0.5%',
                        'BLK': '0.5%',
                        'XAS': '0.5%',
                        'HSR': '0.5%',
                        'NULS': 5.0,
                        'VOISE': 350.0,
                        'PAY': 1.5,
                        'EOS': 0.6,
                        'YBCT': 35.0,
                        'OMG': 0.3,
                        'OTN': 0.4,
                        'BTX': '0.5%',
                        'QTUM': '0.5%',
                        'DASH': '0.5%',
                        'GAME': '0.5%',
                        'BCH': '0.5%',
                        'GNT': 9.0,
                        'SSS': 1500.0,
                        'ARK': '0.5%',
                        'PART': '0.5%',
                        'LEO': '0.5%',
                        'DGB': '0.5%',
                        'ZSC': 130.0,
                        'VIU': 350.0,
                        'BTG': '0.5%',
                        'ARN': 10.0,
                        'VTC': '0.5%',
                        'BCD': '0.5%',
                        'TRX': 200.0,
                        'HWC': '0.5%',
                        'UNIT': '0.5%',
                        'OXY': '0.5%',
                        'MCO': 0.3500,
                        'SBTC': '0.5%',
                        'BCX': '0.5%',
                        'ETF': '0.5%',
                        'PYLNT': 0.4000,
                        'XRB': '0.5%',
                        'ETP': '0.5%',
                    },
                },
            },
            'precision': {
                'amount': 8,
                'price': 8,
            },
            'options': {
                'lastNonceTimestamp': 0,
            },
        })

    def fetch_markets(self):
        response = self.publicGetTickerall()
        markets = response['data']
        ids = list(markets.keys())
        result = []
        for i in range(0, len(ids)):
            id = ids[i]
            market = markets[id]
            baseId, quoteId = id.split('_')
            base = baseId.upper()
            quote = quoteId.upper()
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            symbol = base + '/' + quote
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': True,
                'info': market,
            })
        return result

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privatePostBalances(params)
        data = response['data']
        balances = self.omit(data, 'uid')
        result = {'info': response}
        keys = list(balances.keys())
        for i in range(0, len(keys)):
            currency = keys[i]
            balance = float(balances[currency])
            if currency in self.currencies_by_id:
                currency = self.currencies_by_id[currency]['code']
            else:
                currency = currency.upper()
            account = self.account()
            account['free'] = balance
            account['used'] = None
            account['total'] = balance
            result[currency] = account
        return self.parse_balance(result)

    def parse_ticker(self, ticker, market=None):
        timestamp = ticker['date'] * 1000
        symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': float(ticker['high']),
            'low': float(ticker['low']),
            'bid': float(ticker['buy']),
            'ask': float(ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float(ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float(ticker['vol']),
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetTicker(self.extend({
            'coin': market['id'],
        }, params))
        return self.parse_ticker(response['data'], market)

    def fetch_tickers(self, symbols=None, params={}):
        self.load_markets()
        response = self.publicGetTickerall(params)
        tickers = response['data']
        result = {}
        ids = list(tickers.keys())
        for i in range(0, len(ids)):
            id = ids[i]
            market = self.markets_by_id[id]
            symbol = market['symbol']
            result[symbol] = self.parse_ticker(tickers[id], market)
        return result

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        response = self.publicGetDepth(self.extend({
            'coin': self.market_id(symbol),
        }, params))
        orderbook = response['data']
        timestamp = orderbook['date'] * 1000
        return self.parse_order_book(orderbook, timestamp)

    def parse_trade(self, trade, market=None):
        hkt = self.sum(self.milliseconds(), 28800000)
        utcDate = self.iso8601(hkt)
        utcDate = utcDate.split('T')
        utcDate = utcDate[0] + ' ' + trade['t'] + '+08'
        timestamp = self.parse8601(utcDate)
        price = float(trade['p'])
        amount = float(trade['n'])
        symbol = market['symbol']
        cost = self.price_to_precision(symbol, amount * price)
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': None,
            'order': None,
            'type': 'limit',
            'side': trade['s'],
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
            'info': trade,
        }

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetOrders(self.extend({
            'coin': market['id'],
        }, params))
        trades = response['data']['d']
        return self.parse_trades(trades, market, since, limit)

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetKline(self.extend({
            'coin': market['id'],
            'type': self.timeframes[timeframe],
        }, params))
        ohlcv = json.loads(response['data']['datas']['data'])
        return self.parse_ohlcvs(ohlcv, market, timeframe, since, limit)

    def parse_order(self, order, market=None):
        symbol = None
        if market is not None:
            symbol = market['symbol']
        side = self.safe_string(order, 'side')
        if side is None:
            side = self.safe_string(order, 'type')
            if side is not None:
                side = 'buy' if (side == 'in') else 'sell'
        return {
            'id': order['id'],
            'datetime': None,
            'timestamp': None,
            'status': 'open',
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': order['price'],
            'cost': None,
            'amount': order['number'],
            'filled': None,
            'remaining': None,
            'trades': None,
            'fee': None,
            'info': order,
        }

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        orderType = 'in' if (side == 'buy') else 'out'
        request = {
            'coin': market['id'],
            'type': orderType,
            'price': self.price_to_precision(symbol, price),
            'number': self.amount_to_string(symbol, amount),
            'tradepwd': self.password,
        }
        response = self.privatePostTradeAdd(self.extend(request, params))
        id = response['data']['id']
        order = self.parse_order({
            'id': id,
            'price': price,
            'number': amount,
            'side': side,
        }, market)
        self.orders[id] = order
        return order

    def cancel_order(self, id, symbol=None, params={}):
        self.load_markets()
        response = self.privatePostTradeCancel(self.extend({
            'id': id,
        }, params))
        return response

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.privatePostOpenOrders(self.extend({
            'coin': market['id'],
        }, params))
        return self.parse_orders(response['data'], market)

    def nonce(self):
        currentTimestamp = self.seconds()
        if currentTimestamp > self.options['lastNonceTimestamp']:
            self.options['lastNonceTimestamp'] = currentTimestamp
            self.options['lastNonce'] = 100000
        self.options['lastNonce'] += 1
        return self.options['lastNonce']

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + path
        query = None
        if api == 'public':
            query = self.urlencode(params)
            if len(query):
                url += '?' + query
        else:
            self.check_required_credentials()
            body = self.urlencode(self.keysort(self.extend({
                'api_key': self.apiKey,
                'timestamp': self.seconds(),
                'nonce': self.nonce(),
            }, params)))
            body += '&sign=' + self.hash(self.encode(body + self.secret))
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        code = self.safe_string(response, 'code')
        if code != '0':
            ErrorClass = self.safe_value({
                '103': AuthenticationError,
                '104': AuthenticationError,
                '200': AuthenticationError,
                '202': AuthenticationError,
                '401': AuthenticationError,
                '406': AuthenticationError,
                '203': InvalidNonce,
                '201': OrderNotFound,
                '408': InsufficientFunds,
                '106': DDoSProtection,
            }, code, ExchangeError)
            message = self.safe_string(response, 'msg', 'Error')
            raise ErrorClass(message)
        return response
