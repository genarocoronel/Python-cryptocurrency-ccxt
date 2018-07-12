# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange
import math
import json
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import InsufficientFunds
from ccxt.base.errors import InvalidOrder
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import InvalidNonce


class qryptos (Exchange):

    def describe(self):
        return self.deep_extend(super(qryptos, self).describe(), {
            'id': 'qryptos',
            'name': 'QRYPTOS',
            'countries': ['CN', 'TW'],
            'version': '2',
            'rateLimit': 1000,
            'has': {
                'CORS': False,
                'fetchTickers': True,
                'fetchOrder': True,
                'fetchOrders': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'fetchMyTrades': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/30953915-b1611dc0-a436-11e7-8947-c95bd5a42086.jpg',
                'api': 'https://api.qryptos.com',
                'www': 'https://www.qryptos.com',
                'doc': [
                    'https://developers.quoine.com',
                    'https://developers.quoine.com/v2',
                ],
                'fees': 'https://qryptos.zendesk.com/hc/en-us/articles/115007858167-Fees',
            },
            'api': {
                'public': {
                    'get': [
                        'products',
                        'products/{id}',
                        'products/{id}/price_levels',
                        'executions',
                        'ir_ladders/{currency}',
                    ],
                },
                'private': {
                    'get': [
                        'accounts/balance',
                        'accounts/main_asset',
                        'crypto_accounts',
                        'executions/me',
                        'fiat_accounts',
                        'loan_bids',
                        'loans',
                        'orders',
                        'orders/{id}',
                        'orders/{id}/trades',
                        'orders/{id}/executions',
                        'trades',
                        'trades/{id}/loans',
                        'trading_accounts',
                        'trading_accounts/{id}',
                    ],
                    'post': [
                        'fiat_accounts',
                        'loan_bids',
                        'orders',
                    ],
                    'put': [
                        'loan_bids/{id}/close',
                        'loans/{id}',
                        'orders/{id}',
                        'orders/{id}/cancel',
                        'trades/{id}',
                        'trades/{id}/close',
                        'trades/close_all',
                        'trading_accounts/{id}',
                    ],
                },
            },
            'skipJsonOnStatusCodes': [401],
            'exceptions': {
                'messages': {
                    'API Authentication failed': AuthenticationError,
                    'Nonce is too small': InvalidNonce,
                    'Order not found': OrderNotFound,
                    'user': {
                        'not_enough_free_balance': InsufficientFunds,
                    },
                    'price': {
                        'must_be_positive': InvalidOrder,
                    },
                    'quantity': {
                        'less_than_order_size': InvalidOrder,
                    },
                },
            },
            'commonCurrencies': {
                'WIN': 'WCOIN',
            },
        })

    async def fetch_markets(self):
        markets = await self.publicGetProducts()
        result = []
        for p in range(0, len(markets)):
            market = markets[p]
            id = str(market['id'])
            baseId = market['base_currency']
            quoteId = market['quoted_currency']
            base = self.common_currency_code(baseId)
            quote = self.common_currency_code(quoteId)
            symbol = base + '/' + quote
            maker = self.safe_float(market, 'maker_fee')
            taker = self.safe_float(market, 'taker_fee')
            active = not market['disabled']
            minAmount = None
            minPrice = None
            if base == 'BTC':
                minAmount = 0.001
            elif base == 'ETH':
                minAmount = 0.01
            if quote == 'BTC':
                minPrice = 0.00000001
            elif quote == 'ETH' or quote == 'USD' or quote == 'JPY':
                minPrice = 0.00001
            limits = {
                'amount': {'min': minAmount},
                'price': {'min': minPrice},
                'cost': {'min': None},
            }
            if minPrice is not None:
                if minAmount is not None:
                    limits['cost']['min'] = minPrice * minAmount
            precision = {
                'amount': None,
                'price': None,
            }
            if minAmount is not None:
                precision['amount'] = -math.log10(minAmount)
            if minPrice is not None:
                precision['price'] = -math.log10(minPrice)
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'maker': maker,
                'taker': taker,
                'limits': limits,
                'precision': precision,
                'active': active,
                'info': market,
            })
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        balances = await self.privateGetAccountsBalance(params)
        result = {'info': balances}
        for b in range(0, len(balances)):
            balance = balances[b]
            currencyId = balance['currency']
            code = currencyId
            if currencyId in self.currencies_by_id:
                code = self.currencies_by_id[currencyId]['code']
            total = float(balance['balance'])
            account = {
                'free': total,
                'used': 0.0,
                'total': total,
            }
            result[code] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        orderbook = await self.publicGetProductsIdPriceLevels(self.extend({
            'id': self.market_id(symbol),
        }, params))
        return self.parse_order_book(orderbook, None, 'buy_price_levels', 'sell_price_levels')

    def parse_ticker(self, ticker, market=None):
        timestamp = self.milliseconds()
        last = None
        if 'last_traded_price' in ticker:
            if ticker['last_traded_price']:
                length = len(ticker['last_traded_price'])
                if length > 0:
                    last = self.safe_float(ticker, 'last_traded_price')
        symbol = None
        if market is None:
            marketId = self.safe_string(ticker, 'id')
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
            else:
                baseId = self.safe_string(ticker, 'base_currency')
                quoteId = self.safe_string(ticker, 'quoted_currency')
                base = self.common_currency_code(baseId)
                quote = self.common_currency_code(quoteId)
                if symbol in self.markets:
                    market = self.markets[symbol]
                else:
                    symbol = base + '/' + quote
        if market is not None:
            symbol = market['symbol']
        change = None
        percentage = None
        average = None
        open = self.safe_float(ticker, 'last_price_24h')
        if open is not None and last is not None:
            change = last - open
            average = self.sum(last, open) / 2
            if open > 0:
                percentage = change / open * 100
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high_market_ask'),
            'low': self.safe_float(ticker, 'low_market_bid'),
            'bid': self.safe_float(ticker, 'market_bid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'market_ask'),
            'askVolume': None,
            'vwap': None,
            'open': open,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': change,
            'percentage': percentage,
            'average': average,
            'baseVolume': self.safe_float(ticker, 'volume_24h'),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_tickers(self, symbols=None, params={}):
        await self.load_markets()
        tickers = await self.publicGetProducts(params)
        result = {}
        for t in range(0, len(tickers)):
            ticker = tickers[t]
            base = ticker['base_currency']
            quote = ticker['quoted_currency']
            symbol = base + '/' + quote
            market = self.markets[symbol]
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        ticker = await self.publicGetProductsId(self.extend({
            'id': market['id'],
        }, params))
        return self.parse_ticker(ticker, market)

    def parse_trade(self, trade, market):
        # {            id:  12345,
        #         quantity: "6.789",
        #            price: "98765.4321",
        #       taker_side: "sell",
        #       created_at:  1512345678,
        #          my_side: "buy"           }
        timestamp = trade['created_at'] * 1000
        # 'taker_side' gets filled for both fetchTrades and fetchMyTrades
        takerSide = self.safe_string(trade, 'taker_side')
        # 'my_side' gets filled for fetchMyTrades only and may differ from 'taker_side'
        mySide = self.safe_string(trade, 'my_side')
        side = mySide if (mySide is not None) else takerSide
        takerOrMaker = None
        if mySide is not None:
            takerOrMaker = 'taker' if (takerSide == mySide) else 'maker'
        return {
            'info': trade,
            'id': str(trade['id']),
            'order': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': side,
            'takerOrMaker': takerOrMaker,
            'price': self.safe_float(trade, 'price'),
            'amount': self.safe_float(trade, 'quantity'),
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
        }
        if limit is not None:
            request['limit'] = limit
        response = await self.publicGetExecutions(self.extend(request, params))
        return self.parse_trades(response['models'], market, since, limit)

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
        }
        if limit is not None:
            request['limit'] = limit
        response = await self.privateGetExecutionsMe(self.extend(request, params))
        return self.parse_trades(response['models'], market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        order = {
            'order_type': type,
            'product_id': self.market_id(symbol),
            'side': side,
            'quantity': amount,
        }
        if type == 'limit':
            order['price'] = price
        response = await self.privatePostOrders(self.extend(order, params))
        return self.parse_order(response)

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        result = await self.privatePutOrdersIdCancel(self.extend({
            'id': id,
        }, params))
        order = self.parse_order(result)
        if order['status'] == 'closed':
            raise OrderNotFound(self.id + ' ' + self.json(order))
        return order

    def parse_order(self, order, market=None):
        timestamp = order['created_at'] * 1000
        marketId = self.safe_string(order, 'product_id')
        if marketId is not None:
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
        status = None
        if 'status' in order:
            if order['status'] == 'live':
                status = 'open'
            elif order['status'] == 'filled':
                status = 'closed'
            elif order['status'] == 'cancelled':  # 'll' intended
                status = 'canceled'
        amount = self.safe_float(order, 'quantity')
        filled = self.safe_float(order, 'filled_quantity')
        price = self.safe_float(order, 'price')
        symbol = None
        if market is not None:
            symbol = market['symbol']
        return {
            'id': str(order['id']),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'type': order['order_type'],
            'status': status,
            'symbol': symbol,
            'side': order['side'],
            'price': price,
            'amount': amount,
            'filled': filled,
            'remaining': amount - filled,
            'trades': None,
            'fee': {
                'currency': None,
                'cost': self.safe_float(order, 'order_fee'),
            },
            'info': order,
        }

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        order = await self.privateGetOrdersId(self.extend({
            'id': id,
        }, params))
        return self.parse_order(order)

    async def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = None
        request = {}
        if symbol is not None:
            market = self.market(symbol)
            request['product_id'] = market['id']
        status = self.safe_value(params, 'status')
        if status:
            params = self.omit(params, 'status')
            if status == 'open':
                request['status'] = 'live'
            elif status == 'closed':
                request['status'] = 'filled'
            elif status == 'canceled':
                request['status'] = 'cancelled'
        if limit is not None:
            request['limit'] = limit
        result = await self.privateGetOrders(self.extend(request, params))
        orders = result['models']
        return self.parse_orders(orders, market, since, limit)

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders(symbol, since, limit, self.extend({'status': 'open'}, params))

    def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders(symbol, since, limit, self.extend({'status': 'closed'}, params))

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        headers = {
            'X-Quoine-API-Version': self.version,
            'Content-Type': 'application/json',
        }
        if api == 'public':
            if query:
                url += '?' + self.urlencode(query)
        else:
            self.check_required_credentials()
            if method == 'GET':
                if query:
                    url += '?' + self.urlencode(query)
            elif query:
                body = self.json(query)
            nonce = self.nonce()
            request = {
                'path': url,
                'nonce': nonce,
                'token_id': self.apiKey,
                'iat': int(math.floor(nonce / 1000)),  # issued at
            }
            headers['X-Quoine-Auth'] = self.jwt(request, self.secret)
        url = self.urls['api'] + url
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, code, reason, url, method, headers, body, response=None):
        if code >= 200 and code <= 299:
            return
        messages = self.exceptions['messages']
        if code == 401:
            # expected non-json response
            if body in messages:
                raise messages[body](self.id + ' ' + body)
            else:
                return
        if response is None:
            if (body[0] == '{') or (body[0] == '['):
                response = json.loads(body)
            else:
                return
        feedback = self.id + ' ' + self.json(response)
        if code == 404:
            # {"message": "Order not found"}
            message = self.safe_string(response, 'message')
            if message in messages:
                raise messages[message](feedback)
        elif code == 422:
            # array of error messages is returned in 'user' or 'quantity' property of 'errors' object, e.g.:
            # {"errors": {"user": ["not_enough_free_balance"]}}
            # {"errors": {"quantity": ["less_than_order_size"]}}
            if 'errors' in response:
                errors = response['errors']
                errorTypes = ['user', 'quantity', 'price']
                for i in range(0, len(errorTypes)):
                    errorType = errorTypes[i]
                    if errorType in errors:
                        errorMessages = errors[errorType]
                        for j in range(0, len(errorMessages)):
                            message = errorMessages[j]
                            if message in messages[errorType]:
                                raise messages[errorType][message](feedback)
