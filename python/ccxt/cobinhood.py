# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange
from ccxt.base.errors import ExchangeError


class cobinhood (Exchange):

    def describe(self):
        return self.deep_extend(super(cobinhood, self).describe(), {
            'id': 'cobinhood',
            'name': 'COBINHOOD',
            'countries': 'TW',
            'rateLimit': 1000 / 10,
            'has': {
                'fetchTickers': True,
                'fetchOHLCV': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
            },
            'timeframes': {
                # the first two don't seem to work at all
                # '1m': '1m',
                # '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '3h': '3h',
                '6h': '6h',
                '12h': '12h',
                '1d': '1D',
                '7d': '7D',
                '14d': '14D',
                '1M': '1M',
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/35755576-dee02e5c-0878-11e8-989f-1595d80ba47f.jpg',
                'api': {
                    'web': 'https://api.cobinhood.com/v1',
                    'ws': 'wss://feed.cobinhood.com',
                },
                'test': {
                    'web': 'https://sandbox-api.cobinhood.com',
                    'ws': 'wss://sandbox-feed.cobinhood.com',
                },
                'www': 'https://cobinhood.com',
                'doc': 'https://cobinhood.github.io/api-public',
            },
            'api': {
                'system': {
                    'get': [
                        'info',
                        'time',
                        'messages',
                        'messages/{message_id}',
                    ],
                },
                'admin': {
                    'get': [
                        'system/messages',
                        'system/messages/{message_id}',
                    ],
                    'post': [
                        'system/messages',
                    ],
                    'patch': [
                        'system/messages/{message_id}',
                    ],
                    'delete': [
                        'system/messages/{message_id}',
                    ],
                },
                'public': {
                    'get': [
                        'market/currencies',
                        'market/trading_pairs',
                        'market/orderbooks/{trading_pair_id}',
                        'market/stats',
                        'market/tickers/{trading_pair_id}',
                        'market/trades/{trading_pair_id}',
                        'chart/candles/{trading_pair_id}',
                    ],
                },
                'private': {
                    'get': [
                        'trading/orders/{order_id}',
                        'trading/orders/{order_id}/trades',
                        'trading/orders',
                        'trading/order_history',
                        'trading/trades/{trade_id}',
                        'wallet/balances',
                        'wallet/ledger',
                        'wallet/deposit_addresses',
                        'wallet/withdrawal_addresses',
                        'wallet/withdrawals/{withdrawal_id}',
                        'wallet/withdrawals',
                        'wallet/deposits/{deposit_id}',
                        'wallet/deposits',
                    ],
                    'post': [
                        'trading/orders',
                        'wallet/deposit_addresses',
                        'wallet/withdrawal_addresses',
                        'wallet/withdrawals',
                    ],
                    'delete': [
                        'trading/orders/{order_id}',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.0,
                    'taker': 0.0,
                },
            },
            'precision': {
                'amount': 8,
                'price': 8,
            },
        })

    def fetch_currencies(self, params={}):
        response = self.publicGetMarketCurrencies(params)
        currencies = response['result']
        result = {}
        for i in range(0, len(currencies)):
            currency = currencies[i]
            id = currency['currency']
            code = self.common_currency_code(id)
            result[code] = {
                'id': id,
                'code': code,
                'name': currency['name'],
                'active': True,
                'status': 'ok',
                'fiat': False,
                'lot': float(currency['min_unit']),
                'precision': 8,
                'funding': {
                    'withdraw': {
                        'active': True,
                        'fee': float(currency['withdrawal_fee']),
                    },
                    'deposit': {
                        'active': True,
                        'fee': float(currency['deposit_fee']),
                    },
                },
                'info': currency,
            }
        return result

    def fetch_markets(self):
        response = self.publicGetMarketTradingPairs()
        markets = response['result']['trading_pairs']
        result = []
        for i in range(0, len(markets)):
            market = markets[i]
            id = market['id']
            base, quote = id.split('-')
            symbol = base + '/' + quote
            result.append({
                'id': id,
                'symbol': symbol,
                'base': self.common_currency_code(base),
                'quote': self.common_currency_code(quote),
                'active': True,
                'lot': float(market['quote_increment']),
                'limits': {
                    'amount': {
                        'min': float(market['base_min_size']),
                        'max': float(market['base_max_size']),
                    },
                },
                'info': market,
            })
        return result

    def parse_ticker(self, ticker, market=None):
        symbol = market['symbol']
        timestamp = None
        if 'timestamp' in ticker:
            timestamp = ticker['timestamp']
        else:
            timestamp = self.milliseconds()
        info = ticker
        # from fetchTicker
        if 'info' in ticker:
            info = ticker['info']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': float(ticker['high_24hr']),
            'low': float(ticker['low_24hr']),
            'bid': float(ticker['highest_bid']),
            'ask': float(ticker['lowest_ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': self.safe_float(ticker, 'last_price'),
            'change': self.safe_float(ticker, 'percentChanged24hr'),
            'percentage': None,
            'average': None,
            'baseVolume': float(ticker['base_volume']),
            'quoteVolume': self.safe_float(ticker, 'quote_volume'),
            'info': info,
        }

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetMarketTickersTradingPairId(self.extend({
            'trading_pair_id': market['id'],
        }, params))
        ticker = response['result']['ticker']
        ticker = {
            'last_price': ticker['last_trade_price'],
            'highest_bid': ticker['highest_bid'],
            'lowest_ask': ticker['lowest_ask'],
            'base_volume': ticker['24h_volume'],
            'high_24hr': ticker['24h_high'],
            'low_24hr': ticker['24h_low'],
            'timestamp': ticker['timestamp'],
            'info': response,
        }
        return self.parse_ticker(ticker, market)

    def fetch_tickers(self, symbols=None, params={}):
        self.load_markets()
        response = self.publicGetMarketStats(params)
        tickers = response['result']
        ids = list(tickers.keys())
        result = {}
        for i in range(0, len(ids)):
            id = ids[i]
            market = self.markets_by_id[id]
            symbol = market['symbol']
            ticker = tickers[id]
            result[symbol] = self.parse_ticker(ticker, market)
        return result

    def fetch_order_book(self, symbol, params={}):
        self.load_markets()
        response = self.publicGetMarketOrderbooksTradingPairId(self.extend({
            'trading_pair_id': self.market_id(symbol),
            'limit': 100,
        }, params))
        return self.parse_order_book(response['result']['orderbook'])

    def parse_trade(self, trade, market=None):
        symbol = None
        if market:
            symbol = market['symbol']
        timestamp = trade['timestamp']
        price = float(trade['price'])
        amount = float(trade['size'])
        cost = float(self.cost_to_precision(symbol, price * amount))
        side = trade['maker_side'] == 'sell' if 'bid' else 'buy'
        return {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': trade['id'],
            'order': None,
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
        }

    def fetch_trades(self, symbol, since=None, limit=50, params={}):
        self.load_markets()
        market = self.market(symbol)
        response = self.publicGetMarketTradesTradingPairId(self.extend({
            'trading_pair_id': market['id'],
            'limit': limit,  # default 20, but that seems too little
        }, params))
        trades = response['result']['trades']
        return self.parse_trades(trades, market, since, limit)

    def parse_ohlcv(self, ohlcv, market=None, timeframe='5m', since=None, limit=None):
        return [
            # they say that timestamps are Unix Timestamps in seconds, but in fact those are milliseconds
            ohlcv['timestamp'],
            float(ohlcv['open']),
            float(ohlcv['high']),
            float(ohlcv['low']),
            float(ohlcv['close']),
            float(ohlcv['volume']),
        ]

    def fetch_ohlcv(self, symbol, timeframe='15m', since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        query = {
            'trading_pair_id': market['id'],
            'timeframe': self.timeframes[timeframe],
            # they say in their docs that end_time defaults to current server time
            # but if you don't specify it, their range limits does not allow you to query anything
            'end_time': self.milliseconds(),
        }
        if since:
            # in their docs they say that start_time defaults to 0, but, obviously it does not
            query['start_time'] = since
        response = self.publicGetChartCandlesTradingPairId(self.extend(query, params))
        ohlcv = response['result']['candles']
        return self.parse_ohlcvs(ohlcv, market, timeframe, since, limit)

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privateGetWalletBalances(params)
        result = {'info': response}
        balances = response['result']['balances']
        for i in range(0, len(balances)):
            balance = balances[i]
            id = balance['currency']
            currency = self.common_currency_code(id)
            account = {
                'free': float(balance['total']),
                'used': float(balance['on_order']),
                'total': 0.0,
            }
            account['total'] = self.sum(account['free'], account['used'])
            result[currency] = account
        return self.parse_balance(result)

    def parse_order(self, order, market=None):
        symbol = None
        if not market:
            marketId = order['trading_pair']
            market = self.markets_by_id[marketId]
        if market:
            symbol = market['symbol']
        timestamp = order['timestamp']
        price = float(order['price'])
        amount = float(order['size'])
        filled = float(order['filled'])
        remaining = self.amount_to_precision(symbol, amount - filled)
        # new, queued, open, partially_filled, filled, cancelled
        status = order['state']
        if status == 'filled':
            status = 'closed'
        elif status == 'cancelled':
            status = 'canceled'
        else:
            status = 'open'
        side = order['side'] == 'buy' if 'bid' else 'sell'
        return {
            'id': order['id'],
            'datetime': self.iso8601(timestamp),
            'timestamp': timestamp,
            'status': status,
            'symbol': symbol,
            # market, limit, stop, stop_limit, trailing_stop, fill_or_kill
            'type': order['type'],
            'side': side,
            'price': price,
            'cost': price * amount,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'trades': None,
            'fee': None,
            'info': order,
        }

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        side = (side == 'ask' if 'sell' else 'bid')
        request = {
            'trading_pair_id': market['id'],
            # market, limit, stop, stop_limit
            'type': type,
            'side': side,
            'size': self.amount_to_precision(symbol, amount),
        }
        if type != 'market':
            request['price'] = self.price_to_precision(symbol, price)
        response = self.privatePostTradingOrders(self.extend(request, params))
        order = self.parse_order(response['result']['order'], market)
        id = order['id']
        self.orders[id] = order
        return order

    def cancel_order(self, id, symbol=None, params={}):
        response = self.privateDeleteTradingOrdersOrderId(self.extend({
            'order_id': id,
        }, params))
        return response

    def fetch_order(self, id, symbol=None, params={}):
        self.load_markets()
        response = self.privateGetTradingOrdersOrderId(self.extend({
            'order_id': str(id),
        }, params))
        return self.parse_order(response['result']['order'])

    def fetch_order_trades(self, id, symbol=None, params={}):
        self.load_markets()
        response = self.privateGetTradingOrdersOrderIdTrades(self.extend({
            'order_id': id,
        }, params))
        return self.parse_trades(response['result'])

    def create_deposit_address(self, code, params={}):
        self.load_markets()
        currency = self.currency(code)
        response = self.privatePostWalletDepositAddresses({
            'currency': currency['id'],
        })
        address = self.safe_string(response['result']['deposit_address'], 'address')
        if not address:
            raise ExchangeError(self.id + ' createDepositAddress failed: ' + self.last_http_response)
        return {
            'currency': code,
            'address': address,
            'status': 'ok',
            'info': response,
        }

    def fetch_deposit_address(self, code, params={}):
        self.load_markets()
        currency = self.currency(code)
        response = self.privateGetWalletDepositAddresses(self.extend({
            'currency': currency['id'],
        }, params))
        address = self.safe_string(response['result']['deposit_addresses'], 'address')
        if not address:
            raise ExchangeError(self.id + ' fetchDepositAddress failed: ' + self.last_http_response)
        return {
            'currency': code,
            'address': address,
            'status': 'ok',
            'info': response,
        }

    def withdraw(self, code, amount, address, params={}):
        self.load_markets()
        currency = self.currency(code)
        response = self.privatePostWalletWithdrawals(self.extend({
            'currency': currency['id'],
            'amount': amount,
            'address': address,
        }, params))
        return {
            'id': response['result']['withdrawal_id'],
            'info': response,
        }

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api']['web'] + '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        headers = {}
        if api == 'private':
            self.check_required_credentials()
            headers['device_id'] = self.apiKey
            headers['nonce'] = self.nonce()
            headers['Authorization'] = self.jwt(query, self.secret)
        if method == 'GET':
            query = self.urlencode(query)
            if len(query):
                url += '?' + query
        else:
            headers['Content-type'] = 'application/json charset=UTF-8'
            body = self.json(query)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, code, reason, url, method, headers, body):
        if code < 400 or code >= 600:
            return
        if body[0] != '{':
            raise ExchangeError(self.id + ' ' + body)
        response = self.unjson(body)
        message = self.safe_value(response['error'], 'error_code')
        raise ExchangeError(self.id + ' ' + message)
