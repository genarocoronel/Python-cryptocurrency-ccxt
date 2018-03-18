# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange
import hashlib
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import PermissionDenied
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection
from ccxt.base.errors import ExchangeNotAvailable


class bibox (Exchange):

    def describe(self):
        return self.deep_extend(super(bibox, self).describe(), {
            'id': 'bibox',
            'name': 'Bibox',
            'countries': ['CN', 'US', 'KR'],
            'version': 'v1',
            'has': {
                'CORS': False,
                'publicAPI': False,
                'fetchBalance': True,
                'fetchCurrencies': True,
                'fetchDepositAddress': True,
                'fetchTickers': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'fetchMyTrades': True,
                'fetchOHLCV': True,
                'withdraw': True,
            },
            'timeframes': {
                '1m': '1min',
                '5m': '5min',
                '15m': '15min',
                '30m': '30min',
                '1h': '1hour',
                '8h': '12hour',
                '1d': 'day',
                '1w': 'week',
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/34902611-2be8bf1a-f830-11e7-91a2-11b2f292e750.jpg',
                'api': 'https://api.bibox.com',
                'www': 'https://www.bibox.com',
                'doc': [
                    'https://github.com/Biboxcom/api_reference/wiki/home_en',
                    'https://github.com/Biboxcom/api_reference/wiki/api_reference',
                ],
                'fees': 'https://bibox.zendesk.com/hc/en-us/articles/115004417013-Fee-Structure-on-Bibox',
            },
            'api': {
                'public': {
                    'post': [
                        # TODO: rework for full endpoint/cmd paths here
                        'mdata',
                    ],
                    'get': [
                        'mdata',
                    ],
                },
                'private': {
                    'post': [
                        'user',
                        'orderpending',
                        'transfer',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': False,
                    'percentage': True,
                    'taker': 0.001,
                    'maker': 0.0,
                },
                'funding': {
                    'tierBased': False,
                    'percentage': False,
                    'withdraw': {},
                    'deposit': {},
                },
            },
        })

    async def fetch_markets(self, params={}):
        response = await self.publicGetMdata(self.extend({
            'cmd': 'marketAll',
        }, params))
        markets = response['result']
        result = []
        for i in range(0, len(markets)):
            market = markets[i]
            base = market['coin_symbol']
            quote = market['currency_symbol']
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            symbol = base + '/' + quote
            id = base + '_' + quote
            precision = {
                'amount': 8,
                'price': 8,
            }
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'active': None,
                'info': market,
                'lot': math.pow(10, -precision['amount']),
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': math.pow(10, -precision['amount']),
                        'max': None,
                    },
                    'price': {
                        'min': None,
                        'max': None,
                    },
                },
            })
        return result

    def parse_ticker(self, ticker, market=None):
        timestamp = self.safe_integer(ticker, 'timestamp', self.seconds())
        symbol = None
        if market:
            symbol = market['symbol']
        else:
            symbol = ticker['coin_symbol'] + '/' + ticker['currency_symbol']
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'buy'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'sell'),
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': self.safe_string(ticker, 'percent'),
            'average': None,
            'baseVolume': self.safe_float(ticker, 'vol24H'),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetMdata(self.extend({
            'cmd': 'ticker',
            'pair': market['id'],
        }, params))
        return self.parse_ticker(response['result'], market)

    def parse_tickers(self, rawTickers, symbols=None):
        tickers = []
        for i in range(0, len(rawTickers)):
            tickers.append(self.parse_ticker(rawTickers[i]))
        return self.filter_by_array(tickers, 'symbol', symbols)

    async def fetch_tickers(self, symbols=None, params={}):
        response = await self.publicGetMdata(self.extend({
            'cmd': 'marketAll',
        }, params))
        return self.parse_tickers(response['result'], symbols)

    def parse_trade(self, trade, market=None):
        timestamp = trade['time']
        side = self.safe_integer(trade, 'side')
        side = self.safe_integer(trade, 'order_side', side)
        side = 'buy' if (side == 1) else 'sell'
        if market is None:
            marketId = self.safe_string(trade, 'pair')
            if marketId is not None:
                if marketId in self.markets_by_id:
                    market = self.markets_by_id[marketId]
        symbol = market['symbol'] if (market is not None) else None
        fee = None
        if 'fee' in trade:
            fee = {
                'cost': self.safe_float(trade, 'fee'),
                'currency': None,
            }
        return {
            'id': None,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': float(trade['price']),
            'amount': float(trade['amount']),
            'fee': fee,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        size = limit if (limit) else 200
        response = await self.publicGetMdata(self.extend({
            'cmd': 'deals',
            'pair': market['id'],
            'size': size,
        }, params))
        return self.parse_trades(response['result'], market, since, limit)

    async def fetch_order_book(self, symbol, limit=200, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'cmd': 'depth',
            'pair': market['id'],
        }
        request['size'] = limit  # default = 200 ?
        response = await self.publicGetMdata(self.extend(request, params))
        return self.parse_order_book(response['result'], self.safe_float(response['result'], 'update_time'), 'bids', 'asks', 'price', 'volume')

    def parse_ohlcv(self, ohlcv, market=None, timeframe='1m', since=None, limit=None):
        return [
            ohlcv['time'],
            ohlcv['open'],
            ohlcv['high'],
            ohlcv['low'],
            ohlcv['close'],
            ohlcv['vol'],
        ]

    async def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=1000, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetMdata(self.extend({
            'cmd': 'kline',
            'pair': market['id'],
            'period': self.timeframes[timeframe],
            'size': limit,
        }, params))
        return self.parse_ohlcvs(response['result'], market, timeframe, since, limit)

    async def fetch_currencies(self, params={}):
        response = await self.privatePostTransfer({
            'cmd': 'transfer/coinList',
            'body': {},
        })
        currencies = response['result']
        result = {}
        for i in range(0, len(currencies)):
            currency = currencies[i]
            id = currency['symbol']
            code = self.common_currency_code(id)
            precision = 8
            deposit = currency['enable_deposit']
            withdraw = currency['enable_withdraw']
            active = (deposit and withdraw)
            result[code] = {
                'id': id,
                'code': code,
                'info': currency,
                'name': currency['name'],
                'active': active,
                'status': 'ok',
                'fee': None,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': math.pow(10, -precision),
                        'max': math.pow(10, precision),
                    },
                    'price': {
                        'min': math.pow(10, -precision),
                        'max': math.pow(10, precision),
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                    'withdraw': {
                        'min': None,
                        'max': math.pow(10, precision),
                    },
                },
            }
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privatePostTransfer({
            'cmd': 'transfer/assets',
            'body': self.extend({
                'select': 1,
            }, params),
        })
        balances = response['result']
        result = {'info': balances}
        indexed = None
        if 'assets_list' in balances:
            indexed = self.index_by(balances['assets_list'], 'coin_symbol')
        else:
            indexed = {}
        keys = list(indexed.keys())
        for i in range(0, len(keys)):
            id = keys[i]
            currency = self.common_currency_code(id)
            account = self.account()
            balance = indexed[id]
            used = float(balance['freeze'])
            free = float(balance['balance'])
            total = self.sum(free, used)
            account['free'] = free
            account['used'] = used
            account['total'] = total
            result[currency] = account
        return self.parse_balance(result)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        orderType = 2 if (type == 'limit') else 1
        orderSide = 1 if (side == 'buy') else 2
        response = await self.privatePostOrderpending({
            'cmd': 'orderpending/trade',
            'body': self.extend({
                'pair': market['id'],
                'account_type': 0,
                'order_type': orderType,
                'order_side': orderSide,
                'pay_bix': 0,
                'amount': amount,
                'price': price,
            }, params),
        })
        return {
            'info': response,
            'id': self.safe_string(response, 'result'),
        }

    async def cancel_order(self, id, symbol=None, params={}):
        response = await self.privatePostOrderpending({
            'cmd': 'orderpending/cancelTrade',
            'body': self.extend({
                'orders_id': id,
            }, params),
        })
        return response

    def parse_order(self, order, market=None):
        symbol = None
        if market:
            symbol = market['symbol']
        else:
            symbol = order['coin_symbol'] + '/' + order['currency_symbol']
        type = 'market' if (order['order_type'] == 1) else 'limit'
        timestamp = order['createdAt']
        price = order['price']
        filled = self.safe_float(order, 'deal_amount')
        amount = self.safe_float(order, 'amount')
        cost = self.safe_float(order, 'money')
        remaining = None
        if filled is not None:
            if amount is not None:
                remaining = amount - filled
            if cost is None:
                cost = price * filled
        side = 'buy' if (order['order_side'] == 1) else 'sell'
        status = self.safe_string(order, 'status')
        if status is not None:
            status = self.parse_order_status(status)
        result = {
            'info': order,
            'id': self.safe_string(order, 'id'),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'type': type,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost if cost else float(price) * filled,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': self.safe_float(order, 'fee'),
        }
        return result

    def parse_order_status(self, status):
        statuses = {
            # original comments from bibox:
            '1': 'pending',  # pending
            '2': 'open',  # part completed
            '3': 'closed',  # completed
            '4': 'canceled',  # part canceled
            '5': 'canceled',  # canceled
            '6': 'canceled',  # canceling
        }
        return self.safe_string(statuses, status, status.lower())

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        market = None
        pair = None
        if symbol is not None:
            await self.load_markets()
            market = self.market(symbol)
            pair = market['id']
        size = limit if (limit) else 200
        response = await self.privatePostOrderpending({
            'cmd': 'orderpending/orderPendingList',
            'body': self.extend({
                'pair': pair,
                'account_type': 0,  # 0 - regular, 1 - margin
                'page': 1,
                'size': size,
            }, params),
        })
        orders = self.safe_value(response['result'], 'items', [])
        return self.parse_orders(orders, market, since, limit)

    async def fetch_closed_orders(self, symbol=None, since=None, limit=200, params={}):
        if symbol is None:
            raise ExchangeError(self.id + ' fetchClosedOrders requires a symbol argument')
        await self.load_markets()
        market = self.market(symbol)
        response = await self.privatePostOrderpending({
            'cmd': 'orderpending/pendingHistoryList',
            'body': self.extend({
                'pair': market['id'],
                'account_type': 0,  # 0 - regular, 1 - margin
                'page': 1,
                'size': limit,
            }, params),
        })
        orders = self.safe_value(response['result'], 'items', [])
        return self.parse_orders(orders, market, since, limit)

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        if not symbol:
            raise ExchangeError(self.id + ' fetchMyTrades requires a symbol argument')
        await self.load_markets()
        market = self.market(symbol)
        size = limit if (limit) else 200
        response = await self.privatePostOrderpending({
            'cmd': 'orderpending/orderHistoryList',
            'body': self.extend({
                'pair': market['id'],
                'account_type': 0,  # 0 - regular, 1 - margin
                'page': 1,
                'size': size,
            }, params),
        })
        trades = self.safe_value(response['result'], 'items', [])
        return self.parse_trades(trades, market, since, limit)

    async def fetch_deposit_address(self, code, params={}):
        await self.load_markets()
        currency = self.currency(code)
        response = await self.privatePostTransfer({
            'cmd': 'transfer/transferIn',
            'body': self.extend({
                'coin_symbol': currency['id'],
            }, params),
        })
        address = self.safe_string(response, 'result')
        result = {
            'info': response,
            'address': address,
        }
        return result

    async def withdraw(self, code, amount, address, tag=None, params={}):
        self.check_address(address)
        await self.load_markets()
        currency = self.currency(code)
        if self.password is None:
            if not('trade_pwd' in list(params.keys())):
                raise ExchangeError(self.id + ' withdraw() requires self.password set on the exchange instance or a trade_pwd parameter')
        if not('totp_code' in list(params.keys())):
            raise ExchangeError(self.id + ' withdraw() requires a totp_code parameter for 2FA authentication')
        body = {
            'trade_pwd': self.password,
            'coin_symbol': currency['id'],
            'amount': amount,
            'addr': address,
        }
        if tag is not None:
            body['address_remark'] = tag
        response = await self.privatePostTransfer({
            'cmd': 'transfer/transferOut',
            'body': self.extend(body, params),
        })
        return {
            'info': response,
            'id': None,
        }

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        cmds = self.json([params])
        if api == 'public':
            if method != 'GET':
                body = {'cmds': cmds}
            elif params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            body = {
                'cmds': cmds,
                'apikey': self.apiKey,
                'sign': self.hmac(self.encode(cmds), self.encode(self.secret), hashlib.md5),
            }
        if body is not None:
            body = self.json(body, {'convertArraysToObjects': True})
        headers = {'Content-Type': 'application/json'}
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        message = self.id + ' ' + self.json(response)
        if 'error' in response:
            if 'code' in response['error']:
                code = response['error']['code']
                if code == '2033':
                    # \u64cd\u4f5c\u5931\u8d25\uff01\u8ba2\u5355\u5df2\u5b8c\u6210\u6216\u5df2\u64a4\u9500
                    # operation failednot  Orders have been completed or revoked
                    # e.g. trying to cancel a filled order
                    raise OrderNotFound(message)
                elif code == '2068':
                    # \u4e0b\u5355\u6570\u91cf\u4e0d\u80fd\u4f4e\u4e8e
                    # The number of orders can not be less than
                    raise InvalidOrder(message)
                elif code == '3012':
                    raise AuthenticationError(message)  # invalid apiKey
                elif code == '3024':
                    raise PermissionDenied(message)  # insufficient apiKey permissions
                elif code == '3025':
                    raise AuthenticationError(message)  # signature failed
                elif code == '4000':
                    # \u5f53\u524d\u7f51\u7edc\u8fde\u63a5\u4e0d\u7a33\u5b9a\uff0c\u8bf7\u7a0d\u5019\u91cd\u8bd5
                    # The current network connection is unstable. Please try again later
                    raise ExchangeNotAvailable(message)
                elif code == '4003':
                    raise DDoSProtection(message)  # server is busy, try again later
            raise ExchangeError(message)
        if not('result' in list(response.keys())):
            raise ExchangeError(message)
        if method == 'GET':
            return response
        else:
            return response['result'][0]
