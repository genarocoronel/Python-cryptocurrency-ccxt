# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange

# -----------------------------------------------------------------------------

try:
    basestring  # Python 3
except NameError:
    basestring = str  # Python 2
import base64
import hashlib
import math
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import InvalidNonce


class bitsane (Exchange):

    def describe(self):
        return self.deep_extend(super(bitsane, self).describe(), {
            'id': 'bitsane',
            'name': 'Bitsane',
            'countries': 'IE',  # Ireland
            'has': {
                'fetchCurrencies': True,
                'fetchTickers': True,
                'fetchOpenOrders': True,
                'fetchDepositAddress': True,
                'withdraw': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/41387105-d86bf4c6-6f8d-11e8-95ea-2fa943872955.jpg',
                'api': 'https://bitsane.com/api',
                'www': 'https://bitsane.com',
                'doc': 'https://bitsane.com/info-api',
                'fees': 'https://bitsane.com/fees',
            },
            'api': {
                'public': {
                    'get': [
                        'assets/currencies',
                        'assets/pairs',
                        'ticker',
                        'orderbook',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'balances',
                        'order/cancel',
                        'order/new',
                        'order/status',
                        'orders',
                        'orders/history',
                        'deposit/address',
                        'withdraw',
                        'withdrawal/status',
                        'transactions/history',
                        'vouchers',
                        'vouchers/create',
                        'vouchers/redeem',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.15 / 100,
                    'taker': 0.25 / 100,
                },
            },
            'exceptions': {
                '3': AuthenticationError,
                '4': AuthenticationError,
                '5': AuthenticationError,
                '6': InvalidNonce,
                '7': AuthenticationError,
                '8': InvalidNonce,
                '9': AuthenticationError,
                '10': AuthenticationError,
                '11': AuthenticationError,
            },
            'options': {
                'defaultCurrencyPrecision': 2,
            },
        })

    def fetch_currencies(self, params={}):
        currencies = self.publicGetAssetsCurrencies(params)
        ids = list(currencies.keys())
        result = {}
        for i in range(0, len(ids)):
            id = ids[i]
            currency = currencies[id]
            precision = self.safe_integer(currency, 'precision', self.options['defaultCurrencyPrecision'])
            code = self.common_currency_code(id)
            canWithdraw = self.safe_value(currency, 'withdrawal', True)
            canDeposit = self.safe_value(currency, 'deposit', True)
            active = True
            if not canWithdraw or not canDeposit:
                active = False
            result[code] = {
                'id': id,
                'code': code,
                'name': self.safe_string(currency, 'full_name', code),
                'active': active,
                'precision': precision,
                'funding': {
                    'withdraw': {
                        'active': canWithdraw,
                        'fee': self.safe_value(currency, 'withdrawal_fee'),
                    },
                    'deposit': {
                        'active': canDeposit,
                        'fee': self.safe_value(currency, 'deposit_fee'),
                    },
                },
                'limits': {
                    'amount': {
                        'min': self.safe_float(currency, 'minAmountTrade'),
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
                },
                'info': currency,
            }
        return result

    def fetch_markets(self):
        markets = self.publicGetAssetsPairs()
        result = []
        marketIds = list(markets.keys())
        for i in range(0, len(marketIds)):
            id = marketIds[i]
            market = markets[id]
            base = self.common_currency_code(market['base'])
            quote = self.common_currency_code(market['quote'])
            symbol = base + '/' + quote
            limits = self.safe_value(market, 'limits')
            minLimit = None
            maxLimit = None
            if limits:
                minLimit = self.safe_float(limits, 'minimum')
                maxLimit = self.safe_float(limits, 'maximum')
            precision = {
                'amount': int(market['precision']),
                'price': 8,
            }
            lot = math.pow(10, -precision['amount'])
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': market['base'],
                'quoteId': market['quote'],
                'active': True,
                'lot': lot,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': minLimit,
                        'max': maxLimit,
                    },
                    'price': {
                        'min': math.pow(10, -precision['price']),
                        'max': math.pow(10, precision['price']),
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': id,
            })
        return result

    def parse_ticker(self, ticker, market=None):
        symbol = market['symbol']
        timestamp = self.milliseconds()
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high24hr'),
            'low': self.safe_float(ticker, 'low24hr'),
            'bid': self.safe_float(ticker, 'highestBid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'lowestAsk'),
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': self.safe_float(ticker, 'percentChange'),
            'percentage': None,
            'average': None,
            'baseVolume': self.safe_float(ticker, 'baseVolume'),
            'quoteVolume': self.safe_float(ticker, 'quoteVolume'),
            'info': ticker,
        }

    def fetch_ticker(self, symbol, params={}):
        tickers = self.fetch_tickers([symbol], params)
        return tickers[symbol]

    def fetch_tickers(self, symbols=None, params={}):
        self.load_markets()
        request = {}
        if symbols:
            ids = self.market_ids(symbols)
            request['pairs'] = ','.join(ids)
        tickers = self.publicGetTicker(self.extend(request, params))
        marketIds = list(tickers.keys())
        result = {}
        for i in range(0, len(marketIds)):
            id = marketIds[i]
            market = self.safe_value(self.marketsById, id)
            if not market:
                continue
            symbol = market['symbol']
            ticker = tickers[id]
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    def fetch_order_book(self, symbol, params={}):
        self.load_markets()
        response = self.publicGetOrderbook(self.extend({
            'pair': self.market_id(symbol),
        }, params))
        return self.parse_order_book(response['result'], None, 'bids', 'asks', 'price', 'amount')

    def parse_trade(self, trade, market=None):
        symbol = market['symbol']
        timestamp = int(trade['timestamp']) * 1000
        price = float(trade['price'])
        amount = float(trade['amount'])
        cost = self.cost_to_precision(symbol, price * amount)
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': self.safe_string(trade, 'tid'),
            'order': None,
            'type': None,
            'side': None,
            'price': price,
            'amount': amount,
            'cost': float(cost),
            'fee': None,
            'info': trade,
        }

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'pair': market['id'],
        }
        if since:
            request['since'] = int(since / 1000)
        if limit:
            request['limit'] = limit
        response = self.publicGetTrades(self.extend(request, params))
        return self.parse_trades(response['result'], market, since, limit)

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privatePostBalances(params)
        result = {'info': response}
        balances = response['result']
        ids = list(balances.keys())
        for i in range(0, len(ids)):
            id = ids[i]
            balance = balances[id]
            code = id
            if id in self.currencies_by_id:
                code = self.currencies_by_id[id]['code']
            else:
                code = self.common_currency_code(code)
            account = {
                'free': float(balance['amount']),
                'used': float(balance['locked']),
                'total': float(balance['total']),
            }
            result[code] = account
        return self.parse_balance(result)

    def parse_order(self, order, market=None):
        symbol = None
        if not market:
            market = self.safe_value(self.marketsById, order['pair'])
        if market:
            symbol = market['symbol']
        timestamp = self.safe_integer(order, 'timestamp') * 1000
        price = float(order['price'])
        amount = self.safe_float(order, 'original_amount')
        filled = self.safe_float(order, 'executed_amount')
        remaining = self.safe_float(order, 'remaining_amount')
        status = 'closed'
        if order['is_cancelled']:
            status = 'canceled'
        elif order['is_live']:
            status = 'open'
        return {
            'id': self.safe_string(order, 'id'),
            'datetime': self.iso8601(timestamp),
            'timestamp': timestamp,
            'status': status,
            'symbol': symbol,
            'type': self.safe_string(order, 'type'),
            'side': self.safe_string(order, 'side'),
            'price': price,
            'cost': None,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'trades': None,
            'fee': None,
            'info': self.safe_value(order, 'info', order),
        }

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        order = {
            'pair': market['id'],
            'amount': amount,
            'type': type,
            'side': side,
        }
        if type != 'market':
            order['price'] = price
        response = self.privatePostOrderNew(self.extend(order, params))
        order['id'] = response['result']['order_id']
        order['timestamp'] = self.seconds()
        order['original_amount'] = order['amount']
        order['info'] = response
        order = self.parse_order(order, market)
        id = order['id']
        self.orders[id] = order
        return order

    def cancel_order(self, id, symbol=None, params={}):
        response = self.privatePostOrderCancel(self.extend({
            'order_id': id,
        }, params))
        return self.parse_order(response['result'])

    def fetch_order(self, id, symbol=None, params={}):
        self.load_markets()
        response = self.privatePostOrderStatus(self.extend({
            'order_id': id,
        }, params))
        return self.parse_order(response['result'])

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        response = self.privatePostOrders()
        return self.parse_orders(response['result'], None, since, limit)

    def fetch_deposit_address(self, code, params={}):
        self.load_markets()
        currency = self.currency(code)
        response = self.privatePostDepositAddress(self.extend({
            'currency': currency['id'],
        }, params))
        address = self.safe_string(response['result'], 'address')
        return {
            'currency': code,
            'address': address,
            'info': response,
        }

    def withdraw(self, code, amount, address, tag=None, params={}):
        self.load_markets()
        currency = self.currency(code)
        request = {
            'currency': currency['id'],
            'amount': amount,
            'address': address,
        }
        if tag:
            request['additional'] = tag
        response = self.privatePostWithdraw(self.extend(request, params))
        return {
            'id': response['result']['withdrawal_id'],
            'info': response,
        }

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + api + '/' + path
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            body = self.extend({
                'nonce': self.nonce(),
            }, params)
            body = base64.b64encode(self.json(body))
            headers = {
                'X-BS-APIKEY': self.apiKey,
                'X-BS-PAYLOAD': body,
                'X-BS-SIGNATURE': self.hmac(self.encode(body), self.encode(self.secret), hashlib.sha384),
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, httpCode, reason, url, method, headers, body):
        if not isinstance(body, basestring):
            return  # fallback to default error handler
        if len(body) < 2:
            return  # fallback to default error handler
        if (body[0] == '{') or (body[0] == '['):
            response = json.loads(body)
            statusCode = self.safe_string(response, 'statusCode')
            if statusCode is not None:
                if statusCode != '0':
                    feedback = self.id + ' ' + self.json(response)
                    exceptions = self.exceptions
                    if statusCode in exceptions:
                        raise exceptions[statusCode](feedback)
                    else:
                        raise ExchangeError(self.id + ' ' + self.json(response))
            return response
