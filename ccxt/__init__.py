# coding=utf-8

# Python 2 & 3
import base64
import calendar
import collections
import datetime
import functools
import hashlib
import hmac
import json
import math
import re
import sys
import time

try: 
    import urllib.parse   as _urlencode  # Python 3
    import urllib.request as _urllib
except ImportError: 
    import urllib  as _urlencode         # Python 2
    import urllib2 as _urllib

class Market (object):

    id        = None
    rateLimit = 2000
    timeout   = 10
    verbose   = False
    products  = None
    tickers   = None

    def __init__ (self, config = {}):

        for key in config:
            setattr (self, key, config[key])

        if self.api:
            for apiType, methods in self.api.iteritems ():
                for method, urls in methods.iteritems ():                    
                    for url in urls:
                        url = url.strip ()
                        splitPath = re.compile ('[^a-zA-Z0-9]').split (url)

                        uppercaseMethod  = method.upper ()
                        lowercaseMethod  = method.lower ()
                        camelcaseMethod  = lowercaseMethod.capitalize ()
                        camelcaseSuffix  = ''.join ([ Market.capitalize (x) for x in splitPath ])
                        lowercasePath    = [ x.strip ().lower () for x in splitPath ]
                        underscoreSuffix = '_'.join ([ k for k in lowercasePath if len (k) ])

                        if camelcaseSuffix.find (camelcaseMethod) == 0:
                            camelcaseSuffix = camelcaseSuffix[len (camelcaseMethod):]

                        if underscoreSuffix.find (lowercaseMethod) == 0:
                            underscoreSuffix = underscoreSuffix[len (lowercaseMethod):]

                        camelcase  = apiType + camelcaseMethod + Market.capitalize (camelcaseSuffix)
                        underscore = apiType + '_' + lowercaseMethod + '_' + underscoreSuffix.lower ()

                        f = functools.partial (self.request, url, apiType, uppercaseMethod)
                        setattr (self, camelcase,  f)
                        setattr (self, underscore, f)


    # return (fetch ((self.cors ? self.cors : '') + url, options)
    #     .then (response => (typeof response === 'string') ? response : response.text ())
    #     .then (response => {
    #         try {
    #             return JSON.parse (response)
    #         } catch (e) {
    #             cloudflareProtection = response.match (/cloudflare/i) ? 'DDoS protection by Cloudflare' : ''
    #             if (self.verbose)
    #                 console.log (self.id, response, cloudflareProtection, e)
    #             throw e
    #         }
    #     }))

    
    def fetch (self, url, method = 'GET', headers = None, data = None):
        """Perform a HTTP request and return decoded JSON data"""
        version = '.'.join (map (str, sys.version_info[:3]))
        userAgent = 'ccxt/0.1.0 (+https://github.com/kroitor/ccxt) Python/' + version
        headers = headers or {}
        headers.update ({ 'User-Agent': userAgent })
        if self.verbose:
            print (url, method, headers, data)
        request = _urllib.Request (url, data, headers)
        request.get_method = lambda: method
        response = None
        try:
            handler = _urllib.HTTPHandler if url.startswith ('http://') else _urllib.HTTPSHandler
            opener = _urllib.build_opener (handler)
            response = opener.open (request, timeout = self.timeout).read ()
            return json.loads (response)
        except _urllib.HTTPError as e:
            try: 
                text = e.fp.read ()
                m = re.search ('(cloudflare)', text, flags = re.IGNORECASE)
                if re.search ('(cloudflare)', text, flags = re.IGNORECASE):
                    error = 'DDoS protection by Cloudflare'
                    print (self.id, method, url, e.code, e.msg, error)
                else:
                    print (self.id, method, url, e.code, e.msg, json.loads (text))
            except Exception as unused:
                print (self.id, method, url, e.code, e.msg, text)
            raise

    # import httplib
    # connection =  httplib.HTTPConnection('1.2.3.4:1234')
    # body_content = 'BODY CONTENT GOES HERE'
    # connection.request('PUT', '/url/path/to/put/to', body_content)
    # result = connection.getresponse()
    # # Now result.status and result.reason contains interesting stuff

    @staticmethod
    def capitalize (string): # first character only, rest characters unchanged
        if len (string) > 1:
            return "%s%s" % (string[0].upper (), string[1:])
        return string.upper ()

    @staticmethod 
    def keysort (dictionary):
        return collections.OrderedDict (sorted (dictionary.items (), key = lambda t: t[0]))

    @staticmethod
    def extend (*args):
        result = {}
        if args is not None:
            for arg in args:
                result.update (arg)
        return result

    @staticmethod
    def index_by (l, key):
        result = {}
        for x in l:
            result[x[key]] = x
        return result

    @staticmethod
    def indexBy (l, key):
        return Market.index_by (l, key)

    @staticmethod
    def commonCurrencyCode (currency):
        return 'BTC' if currency == 'XBT' else currency

    @staticmethod
    def extract_params (string):
        return re.findall (r'{([a-zA-Z0-9_]+?)}', string)

    @staticmethod
    def implode_params (string, params):
        for key in params:
            string = string.replace ('{' + key + '}', str (params[key]))
        return string

    @staticmethod
    def extractParams (string):
        return Market.extract_params (string)

    @staticmethod
    def implodeParams (string, params):
        return Market.implode_params (string, params)

    @staticmethod
    def omit (d, *args):
        result = d.copy ()
        for arg in args:
            if type (arg) is list:
                for key in arg:
                    if key in result: del result[key]
            else:
                if arg in result: del result[arg]
        return result

    @staticmethod
    def s ():
        return Market.seconds ()
    
    @staticmethod
    def sec ():
        return Market.seconds ()
    
    @staticmethod
    def ms ():
        return Market.milliseconds ()
    
    @staticmethod
    def msec ():
        return Market.milliseconds ()
    
    @staticmethod
    def us ():
        return Market.microseconds ()
    
    @staticmethod
    def usec ():
        return Market.microseconds ()
    
    @staticmethod
    def seconds ():
        return int (time.time ())
    
    @staticmethod
    def milliseconds ():
        return int (time.time () * 1000)
    
    @staticmethod
    def microseconds ():
        return int (time.time () * 1000000)

    @staticmethod
    def iso8601 (timestamp):
        return (datetime
            .datetime
            .utcfromtimestamp (int (round (timestamp / 1000)))
            .strftime ('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')

    @staticmethod
    def parse8601 (timestamp):
        yyyy = '([0-9]{4})-?'
        mm   = '([0-9]{2})-?'
        dd   = '([0-9]{2})(?:T|[\s])?'
        h    = '([0-9]{2}):?'
        m    = '([0-9]{2}):?'
        s    = '([0-9]{2})'
        ms   = '(\.[0-9]{3})?'
        tz = '(?:(\+|\-)([0-9]{2})\:?([0-9]{2})|Z)?'
        regex = r'' + yyyy + mm + dd + h + m + s + ms + tz
        match = re.search (regex, timestamp, re.IGNORECASE)
        yyyy, mm, dd, h, m, s, ms, sign, hours, minutes = match.groups ()
        ms = ms or '.000'
        sign = sign or ''
        sign = int (sign + '1')
        hours = int (hours or 0) * sign
        minutes = int (minutes or 0) * sign
        offset = datetime.timedelta (hours = hours, minutes = minutes)
        string = yyyy + mm + dd + h + m + s + ms + 'Z'
        dt = datetime.datetime.strptime (string, "%Y%m%d%H%M%S.%fZ")
        dt = dt + offset
        return calendar.timegm (dt.utctimetuple ()) * 1000

    @staticmethod
    def hash (request, hash = 'md5', digest = 'hex'):
        h = hashlib.new (hash, request)
        if digest == 'hex':
            return h.hexdigest ()
        elif digest == 'base64':
            return base64.b64encode (h.digest ())
        return h.digest ()

    @staticmethod
    def hmac (request, secret, hash = hashlib.sha256, digest = 'hex'):
        h = hmac.new (secret, request, hash)
        if digest == 'hex':
            return h.hexdigest ()
        elif digest == 'base64':
            return base64.b64encode (h.digest ())
        return h.digest ()

    @staticmethod
    def base64urlencode (s):
        return base64.urlsafe_b64encode (s).replace ('=', '')

    @staticmethod
    def jwt (request, secret, hash = hashlib.sha256, alg = 'HS256'):
        encodedHeader = Market.base64urlencode (json.dumps ({ 'alg': alg, 'typ': 'JWT' }, separators = (',', ':')))
        encodedData = Market.base64urlencode (json.dumps (request, separators = (',', ':')))
        token = encodedHeader + '.' + encodedData
        signature = Market.base64urlencode (Market.hmac (token, secret, hash, 'binary'))
        return token + '.' + signature

    def nonce (self): return Market.seconds ()

    def load_products (self, reload = False):
        if not reload:
            if self.products:
                return self.products
        self.products = Market.indexBy (self.fetchProducts (), 'symbol')
        return self.products

    def loadProducts  (self, reload = False):
        return self.load_products  ()
    
    def fetchProducts (self):
        return self.fetch_products ()

    def product (self, product):
        isString = type (product) in [ str, unicode ]
        if isString and self.products and (product in self.products):
            return self.products [product]
        return product

    def product_id (self, product):
        p = self.product (product)
        return p['id'] if type (p) is dict else product

    def productId  (self, product):
        return self.product_id (product)

    def symbol (self, product):
        p = self.product (product)
        return p['symbol'] if type (p) is dict else product

    # def parse_ticker (self, ticker, product, replacements = {}):
    #     print (ticker)
    #     t = {}
    #     t.update (ticker)
    #     if replacements: t = self.update (self.lowerkeys (t), replacements)
    #     p = self.product (product)
    #     result = {}
    #     synonyms = {
    #         'high':  [ 'high', 'max', 'h', '24hhigh' ],
    #         'low':   [ 'low',  'min', 'l', '24hlow'  ],
    #         'bid':   [ 'bid',  'buy', 'buy_price' ],
    #         'ask':   [ 'ask',  'sell', 'sell_price' ],
    #         'vwap':  [ 'vwap' ],
    #         'open':  [ 'open' ],
    #         'close': [ 'close' ],
    #         'first': [ 'first' ],
    #         'change': [ 'change' ],
    #         'percentage': [ 'percentage' ],
    #         'last':  [ 'last', 'last_price', 'last_trade', 'last_traded_price', 'lastprice', 'll' ],
    #         'average': [ 'average', 'avg', 'av', 'mid' ],
    #         'baseVolume': [ 'vol_cur' ],
    #         'quoteVolume': [ 'volume', 'vol', 'v', 'a', 'volume_24h', 'volume_24hours', 'rolling_24_hour_volume', '24hvolume' ],
    #     }
    #     for synonym in synonyms:
    #         value = self.first_of (t, synonyms[synonym])
    #         value = float (value) if value else value
    #         result[synonym] = value       
    #     timestamp = self.first_of (t, [
    #         'time',
    #         'timestamp',
    #         'server_time',
    #         'created',
    #         'created_at',
    #         'updated',
    #     ])
    #     timestamp = self.parse_time (timestamp)
    #     return self.extend (result, {
    #         'timestamp': timestamp,
    #         'datetime':  datetime.datetime.utcfromtimestamp (timestamp).isoformat (),
    #         'details':   ticker,
    #         'volume':    dict ([
    #             (p['base'],  result['baseVolume']),
    #             (p['quote'], result['quoteVolume']),
    #         ]),
    #     })

    def fetchBalance (self):
        return self.fetch_balance ()
    
    def fetchOrderBook (self, product): 
        return self.fetch_order_book (product)
    
    def fetchTicker (self, product):
        return self.fetch_ticker (product)
    
    def fetchTrades (self, product): 
        return self.fetch_trades (product)

    def buy (self, product, amount, price = None, params = {}):
        return self.order (product, 'buy', amount, price, params)

    def sell (self, product, amount, price = None, params = {}):
        return self.order (product, 'sell', amount, price, params)

    def trade (self, product, side, amount, price = None, params = {}):
        return self.order (product, side, amount, price, params)

    def order (self, product, side, amount, price = None, params = {}):
        type = 'limit' if price else 'market'
        return self.create_order (product, type, side, amount, price, params)

    def create_buy_order (self, product, type, amount, price = None, params = {}):
        return self.create_order (product, type, 'buy',  amount, price, params)

    def create_sell_order (self, product, type, amount, price = None, params = {}):
        return self.create_order (product, type, 'sell', amount, price, params)

    def create_limit_buy_order (self, product, amount, price, params = {}):
        return self.createLimitOrder (product, 'buy',  amount, price, params)

    def create_limit_sell_order (self, product, amount, price, params = {}):
        return self.createLimitOrder (product, 'sell', amount, price, params)

    def create_market_buy_order (self, product, amount, params = {}):
        return self.create_market_order (product, 'buy',  amount, params)

    def create_market_sell_order (self, product, amount, params = {}):
        return self.create_market_order (product, 'sell', amount, params)

    def create_limit_order (self, product, side, amount, price, params = {}):
        return self.create_order (product, 'limit', side, amount, price, params)

    def create_market_order (self, product, side, amount, params = {}):
        return self.create_order (product, 'market', side, amount, None, params)

    def createBuyOrder (self, product, type, amount, price = None, params = {}):
        return self.create_buy_order  (product, type, amount, price, params)

    def createSellOrder (self, product, type, amount, price = None, params = {}):
        return self.create_sell_order (product, type, amount, price, params)

    def createLimitBuyOrder (self, product, amount, price, params = {}):
        return self.create_limit_buy_order  (product, amount, price, params)

    def createLimitSellOrder (self, product, amount, price, params = {}):
        return self.create_limit_sell_order (product, amount, price, params)

    def createMarketBuyOrder (self, product, amount, params = {}): 
        return self.create_market_buy_order  (product, amount, params)

    def createMarketSellOrder (self, product, amount, params = {}):
        return self.create_market_sell_order (product, amount, params)

    def createLimitOrder (self, product, side, amount, price, params = {}):
        return self.create_limit_order (product, side, amount, price, params)

    def createMarketOrder (self, product, side, amount, params = {}):
        return self.create_market_order (product, side, amount, params)

#==============================================================================

class _1broker (Market):

    def __init__ (self, config = {}):
        params = {
            'id': '_1broker',
            'name': '1Broker',
            'countries': 'US',
            'rateLimit': 2000,
            'version': 'v2',
            'urls': {
                'api': 'https://1broker.com/api',        
                'www': 'https://1broker.com',
                'doc': 'https://1broker.com/?c=en/content/api-documentation',
            },
            'api': {
                'private': {
                    'get': [
                        'market/bars',
                        'market/categories',
                        'market/details',
                        'market/list',
                        'market/quotes',
                        'market/ticks',
                        'order/cancel',
                        'order/create',
                        'order/open',
                        'position/close',
                        'position/close_cancel',
                        'position/edit',
                        'position/history',
                        'position/open',
                        'position/shared/get',
                        'social/profile_statistics',
                        'social/profile_trades',
                        'user/bitcoin_deposit_address',
                        'user/details',
                        'user/overview',
                        'user/quota_status',
                        'user/transaction_log',
                    ],
                },
            },
        }
        params.update (config)
        super (_1broker, self).__init__ (params)

    def fetchCategories (self):
        categories = self.privateGetMarketCategories ()
        return categories['response']

    def fetch_products (self):
        categories = self.fetchCategories ()
        result = []
        for c in range (0, len (categories)):
            category = categories[c]
            products = self.privateGetMarketList ({ 
                'category': category.lower (),
            })
            for p in range (0, len (products['response'])):
                product = products['response'][p]
                if (category == 'FOREX') or (category == 'CRYPTO'):
                    id = product['symbol']
                    symbol = product['name']
                    base, quote = symbol.split ('/')
                    result.append ({
                        'id': id,
                        'symbol': symbol,
                        'base': base,
                        'quote': quote,
                        'info': product,
                    })
                else:
                    id = product['symbol']
                    symbol = product['symbol']
                    name = product['name']
                    type = product['type'].lower ()
                    result.push ({
                        'id': id,
                        'symbol': symbol,
                        'name': name,
                        'type': type,
                        'info': product,
                    })
        return result

    def fetch_balance (self):
        return self.privateGetUserOverview ()

    def fetch_order_book (self, product):
        return self.privateGetMarketQuotes ({
            'symbols': self.product_id (product),
        })

    def fetch_ticker (self, product):
        return self.privateGetMarketBars ({
            'symbol': self.product_id (product),
            'resolution': 60,
            'limit': 1,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'margin': amount,
            'direction': 'short' if (side == 'sell') else 'long',
            'leverage': 1,
            'type': side,
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['type'] += '_market'
        return self.privateGetOrderCreate (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path + '.php'
        query = self.extend ({ 'token': (self.apiKey or self.token) }, params)
        url += '?' + _urlencode.urlencode (query)
        return self.fetch (url, method)

#------------------------------------------------------------------------------

class cryptocapital (Market):

    def __init__ (self, config = {}):
        params = {
            'comment': 'Crypto Capital API',
            'api': {
                'public': {
                    'get': [
                        'stats',
                        'historical-prices',
                        'order-book',
                        'transactions',
                    ],
                },
                'private': {            
                    'post': [
                        'balances-and-info',
                        'open-orders',
                        'user-transactions',
                        'btc-deposit-address/get',
                        'btc-deposit-address/new',
                        'deposits/get',
                        'withdrawals/get',
                        'orders/new',
                        'orders/edit',
                        'orders/cancel',
                        'orders/status',
                        'withdrawals/new',
                    ],
                },
            },
        }
        params.update (config)
        super (cryptocapital, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalancesAndInfo ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBook ({
            'currency': self.product_id (product),
        })

    def fetch_ticker (self, product):
        response = self.publicGetStats ({
            'currency': self.product_id (product),
        })
        ticker = response['stats']
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': float (ticker['daily_change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['total_btc_traded']),
        }

    def fetch_trades (self, product):
        return self.publicGetTransactions ({
            'currency': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'side': side,
            'type': type,
            'currency': self.product_id (product),
            'amount': amount,
        }
        if type == 'limit':
            order['limit_price'] = price
        return self.privatePostOrdersNew (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            query = self.extend ({
                'api_key': self.apiKey,
                'nonce': self.nonce (),
            }, params)
            query['signature'] = self.hmac (json.dumps (query), self.secret)
            body = json.dumps (query)
            headers = { 'Content-Type': 'application/json' }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class _1btcxe (cryptocapital):

    def __init__ (self, config = {}):
        params = {
            'id': '_1btcxe',
            'name': '1BTCXE',
            'countries': 'PA', # Panama
            'comment': 'Crypto Capital API',
            'urls': { 
                'api': 'https://1btcxe.com/api',
                'www': 'https://1btcxe.com',
                'doc': 'https://1btcxe.com/api-docs.php',
            },    
            'products': {
                'BTC/USD': { 'id': 'USD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD', },
                'BTC/EUR': { 'id': 'EUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR', },
                'BTC/CNY': { 'id': 'CNY', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY', },
                'BTC/RUB': { 'id': 'RUB', 'symbol': 'BTC/RUB', 'base': 'BTC', 'quote': 'RUB', },
                'BTC/CHF': { 'id': 'CHF', 'symbol': 'BTC/CHF', 'base': 'BTC', 'quote': 'CHF', },
                'BTC/JPY': { 'id': 'JPY', 'symbol': 'BTC/JPY', 'base': 'BTC', 'quote': 'JPY', },
                'BTC/GBP': { 'id': 'GBP', 'symbol': 'BTC/GBP', 'base': 'BTC', 'quote': 'GBP', },
                'BTC/CAD': { 'id': 'CAD', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD', },
                'BTC/AUD': { 'id': 'AUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD', },
                'BTC/AED': { 'id': 'AED', 'symbol': 'BTC/AED', 'base': 'BTC', 'quote': 'AED', },
                'BTC/BGN': { 'id': 'BGN', 'symbol': 'BTC/BGN', 'base': 'BTC', 'quote': 'BGN', },
                'BTC/CZK': { 'id': 'CZK', 'symbol': 'BTC/CZK', 'base': 'BTC', 'quote': 'CZK', },
                'BTC/DKK': { 'id': 'DKK', 'symbol': 'BTC/DKK', 'base': 'BTC', 'quote': 'DKK', },
                'BTC/HKD': { 'id': 'HKD', 'symbol': 'BTC/HKD', 'base': 'BTC', 'quote': 'HKD', },
                'BTC/HRK': { 'id': 'HRK', 'symbol': 'BTC/HRK', 'base': 'BTC', 'quote': 'HRK', },
                'BTC/HUF': { 'id': 'HUF', 'symbol': 'BTC/HUF', 'base': 'BTC', 'quote': 'HUF', },
                'BTC/ILS': { 'id': 'ILS', 'symbol': 'BTC/ILS', 'base': 'BTC', 'quote': 'ILS', },
                'BTC/INR': { 'id': 'INR', 'symbol': 'BTC/INR', 'base': 'BTC', 'quote': 'INR', },
                'BTC/MUR': { 'id': 'MUR', 'symbol': 'BTC/MUR', 'base': 'BTC', 'quote': 'MUR', },
                'BTC/MXN': { 'id': 'MXN', 'symbol': 'BTC/MXN', 'base': 'BTC', 'quote': 'MXN', },
                'BTC/NOK': { 'id': 'NOK', 'symbol': 'BTC/NOK', 'base': 'BTC', 'quote': 'NOK', },
                'BTC/NZD': { 'id': 'NZD', 'symbol': 'BTC/NZD', 'base': 'BTC', 'quote': 'NZD', },
                'BTC/PLN': { 'id': 'PLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN', },
                'BTC/RON': { 'id': 'RON', 'symbol': 'BTC/RON', 'base': 'BTC', 'quote': 'RON', },
                'BTC/SEK': { 'id': 'SEK', 'symbol': 'BTC/SEK', 'base': 'BTC', 'quote': 'SEK', },
                'BTC/SGD': { 'id': 'SGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD', },
                'BTC/THB': { 'id': 'THB', 'symbol': 'BTC/THB', 'base': 'BTC', 'quote': 'THB', },
                'BTC/TRY': { 'id': 'TRY', 'symbol': 'BTC/TRY', 'base': 'BTC', 'quote': 'TRY', },
                'BTC/ZAR': { 'id': 'ZAR', 'symbol': 'BTC/ZAR', 'base': 'BTC', 'quote': 'ZAR', },
            },
        }
        params.update (config)
        super (_1btcxe, self).__init__ (params)

#------------------------------------------------------------------------------

class bit2c (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bit2c',
            'name': 'Bit2C',
            'countries': 'IL', # Israel
            'rateLimit': 3000,
            'urls': {
                'api': 'https://www.bit2c.co.il',
                'www': 'https://www.bit2c.co.il',
                'doc': [
                    'https://www.bit2c.co.il/home/api',
                    'https://github.com/OferE/bit2c',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'Exchanges/{pair}/Ticker',
                        'Exchanges/{pair}/orderbook',
                        'Exchanges/{pair}/trades',
                    ],
                },
                'private': {
                    'post': [
                        'Account/Balance',
                        'Account/Balance/v2',
                        'Merchant/CreateCheckout',
                        'Order/AccountHistory',
                        'Order/AddCoinFundsRequest',
                        'Order/AddFund',
                        'Order/AddOrder',
                        'Order/AddOrderMarketPriceBuy',
                        'Order/AddOrderMarketPriceSell',
                        'Order/CancelOrder',
                        'Order/MyOrders',
                        'Payment/GetMyId',
                        'Payment/Send',
                    ],
                },
            },
            'products': {
                'BTC/NIS': { 'id': 'BtcNis', 'symbol': 'BTC/NIS', 'base': 'BTC', 'quote': 'NIS' },
                'LTC/BTC': { 'id': 'LtcBtc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'LTC/NIS': { 'id': 'LtcNis', 'symbol': 'LTC/NIS', 'base': 'LTC', 'quote': 'NIS' },
            },
        }
        params.update (config)
        super (bit2c, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostAccountBalanceV2 ()

    def fetch_order_book (self, product):
        return self.publicGetExchangesPairOrderbook ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetExchangesPairTicker ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['h']),
            'low': float (ticker['l']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['ll']),
            'change': None,
            'percentage': None,
            'average': float (ticker['av']),
            'baseVolume': None,
            'quoteVolume': float (ticker['a']),
        }

    def fetch_trades (self, product):
        return self.publicGetExchangesPairTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePostOrderAddOrder'
        order = {
            'Amount': amount,
            'Pair': self.product_id (product),
        }
        if type == 'market':
            method += 'MarketPrice' + self.capitalize (side)
        else:
            order['Price'] = price
            order['Total'] = amount * price
            order['IsBid'] = (side == 'buy')
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        if type == 'public':
            url += '.json'
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'key': self.apiKey,
                'sign': self.hmac (body, self.secret, hashlib.sha512, 'base64'),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitbay (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitbay',
            'name': 'BitBay',
            'countries': [ 'PL', 'EU', ], # Poland
            'rateLimit': 1000,
            'urls': {
                'www': 'https://bitbay.net',
                'api': {
                    'public': 'https://bitbay.net/API/Public',
                    'private': 'https://bitbay.net/API/Trading/tradingApi.php',
                },
                'doc': [
                    'https://bitbay.net/public-api',
                    'https://bitbay.net/account/tab-api',
                    'https://github.com/BitBayNet/API',
                ], 
            },
            'api': {
                'public': {
                    'get': [
                        '{id}/all',
                        '{id}/market',
                        '{id}/orderbook',
                        '{id}/ticker',
                        '{id}/trades',
                    ],
                },
                'private': {
                    'post': [
                        'info',
                        'trade',
                        'cancel',
                        'orderbook',
                        'orders',
                        'transfer',
                        'withdraw',
                        'history',
                        'transactions',
                    ],
                },
            },
            'products': {  
                'BTC/USD': { 'id': 'BTCUSD', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/EUR': { 'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'BTC/PLN': { 'id': 'BTCPLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN' },
                'LTC/USD': { 'id': 'LTCUSD', 'symbol': 'LTC/USD', 'base': 'LTC', 'quote': 'USD' },
                'LTC/EUR': { 'id': 'LTCEUR', 'symbol': 'LTC/EUR', 'base': 'LTC', 'quote': 'EUR' },
                'LTC/PLN': { 'id': 'LTCPLN', 'symbol': 'LTC/PLN', 'base': 'LTC', 'quote': 'PLN' },
                'LTC/BTC': { 'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'ETH/USD': { 'id': 'ETHUSD', 'symbol': 'ETH/USD', 'base': 'ETH', 'quote': 'USD' },
                'ETH/EUR': { 'id': 'ETHEUR', 'symbol': 'ETH/EUR', 'base': 'ETH', 'quote': 'EUR' },
                'ETH/PLN': { 'id': 'ETHPLN', 'symbol': 'ETH/PLN', 'base': 'ETH', 'quote': 'PLN' },
                'ETH/BTC': { 'id': 'ETHBTC', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC' },
                'LSK/USD': { 'id': 'LSKUSD', 'symbol': 'LSK/USD', 'base': 'LSK', 'quote': 'USD' },
                'LSK/EUR': { 'id': 'LSKEUR', 'symbol': 'LSK/EUR', 'base': 'LSK', 'quote': 'EUR' },
                'LSK/PLN': { 'id': 'LSKPLN', 'symbol': 'LSK/PLN', 'base': 'LSK', 'quote': 'PLN' },
                'LSK/BTC': { 'id': 'LSKBTC', 'symbol': 'LSK/BTC', 'base': 'LSK', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (bitbay, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostInfo ()

    def fetch_order_book (self, product):
        return self.publicGetIdOrderbook ({
            'id': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetIdTicker ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['average']),
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetIdTrades ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        return self.privatePostTrade (self.extend ({
            'type': side,
            'currency': p['base'],
            'amount': amount,
            'payment_currency': p['quote'],
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path, params) + '.json'
        else:
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'moment': self.nonce (),
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'API-Key': self.apiKey,
                'API-Hash': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitcoincoid (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitcoincoid',
            'name': 'Bitcoin.co.id',
            'countries': 'ID', # Indonesia
            'urls': {
                'api': {
                    'public': 'https://vip.bitcoin.co.id/api',
                    'private': 'https://vip.bitcoin.co.id/tapi',
                },
                'www': 'https://www.bitcoin.co.id',
                'doc': [
                    'https://vip.bitcoin.co.id/trade_api',
                    'https://vip.bitcoin.co.id/downloads/BITCOINCOID-API-DOCUMENTATION.pdf',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        '{pair}/ticker',
                        '{pair}/trades',
                        '{pair}/depth',
                    ],
                },
                'private': {
                    'post': [
                        'getInfo',
                        'transHistory',
                        'trade',
                        'tradeHistory',
                        'openOrders',
                        'cancelOrder',
                    ],
                },
            },
            'products': {
                'BTC/IDR':  { 'id': 'btc_idr', 'symbol': 'BTC/IDR', 'base': 'BTC', 'quote': 'IDR', 'baseId': 'btc', 'quoteId': 'idr' },
                'BTS/BTC':  { 'id': 'bts_btc', 'symbol': 'BTS/BTC', 'base': 'BTS', 'quote': 'BTC', 'baseId': 'bts', 'quoteId': 'btc' },
                'DASH/BTC': { 'id': 'drk_btc', 'symbol': 'DASH/BTC', 'base': 'DASH', 'quote': 'BTC', 'baseId': 'drk', 'quoteId': 'btc' },
                'DOGE/BTC': { 'id': 'doge_btc', 'symbol': 'DOGE/BTC', 'base': 'DOGE', 'quote': 'BTC', 'baseId': 'doge', 'quoteId': 'btc' },
                'ETH/BTC':  { 'id': 'eth_btc', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC', 'baseId': 'eth', 'quoteId': 'btc' },
                'LTC/BTC':  { 'id': 'ltc_btc', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'baseId': 'ltc', 'quoteId': 'btc' },
                'NXT/BTC':  { 'id': 'nxt_btc', 'symbol': 'NXT/BTC', 'base': 'NXT', 'quote': 'BTC', 'baseId': 'nxt', 'quoteId': 'btc' },
                'STR/BTC':  { 'id': 'str_btc', 'symbol': 'STR/BTC', 'base': 'STR', 'quote': 'BTC', 'baseId': 'str', 'quoteId': 'btc' },
                'NEM/BTC':  { 'id': 'nem_btc', 'symbol': 'NEM/BTC', 'base': 'NEM', 'quote': 'BTC', 'baseId': 'nem', 'quoteId': 'btc' },
                'XRP/BTC':  { 'id': 'xrp_btc', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC', 'baseId': 'xrp', 'quoteId': 'btc' },
            },
        }
        params.update (config)
        super (bitcoincoid, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostGetInfo ()

    def fetch_order_book (self, product):
        return self.publicGetPairDepth ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        pair = self.product (product)
        response = self.publicGetPairTicker ({
            'pair': pair['id'],
        })
        ticker = response['ticker']
        timestamp = float (ticker['server_time']) * 1000
        baseVolume = 'vol_' + pair['baseId'].lower ()
        quoteVolume = 'vol_' + pair['quoteId'].lower ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['average']),
            'baseVolume': float (ticker[baseVolume]),
            'quoteVolume': float (ticker[quoteVolume]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetPairTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        order = {
            'pair': p['id'],
            'type': side,
            'price': price,
        }
        base = p['base'].lower ()
        order[base] = amount
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path, params)
        else:
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'nonce': self.nonce (),
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitfinex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitfinex',
            'name': 'Bitfinex',
            'countries': 'US',
            'version': 'v1',
            'rateLimit': 2000,
            'urls': {
                'api': 'https://api.bitfinex.com',
                'www': 'https://www.bitfinex.com',
                'doc': [
                    'https://bitfinex.readme.io/v1/docs',
                    'https://bitfinex.readme.io/v2/docs',
                    'https://github.com/bitfinexcom/bitfinex-api-node',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'book/{symbol}',
                        'candles/{symbol}',
                        'lendbook/{currency}',
                        'lends/{currency}',
                        'pubticker/{symbol}',
                        'stats/{symbol}',
                        'symbols',
                        'symbols_details',
                        'today',
                        'trades/{symbol}',                
                    ],
                },
                'private': {
                    'post': [
                        'account_infos',
                        'balances',
                        'basket_manage',
                        'credits',
                        'deposit/new',
                        'funding/close',
                        'history',
                        'history/movements',
                        'key_info',
                        'margin_infos',
                        'mytrades',
                        'offer/cancel',
                        'offer/new',
                        'offer/status',
                        'offers',
                        'order/cancel',
                        'order/cancel/all',
                        'order/cancel/multi',
                        'order/cancel/replace',
                        'order/new',
                        'order/new/multi',
                        'order/status',
                        'orders',
                        'position/claim',
                        'positions',
                        'summary',
                        'taken_funds',
                        'total_taken_funds',
                        'transfer',
                        'unused_taken_funds',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (bitfinex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetSymbolsDetails ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['pair'].upper ()
            base = id[0:3]
            quote = id[3:6]
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalances ()

    def fetch_order_book (self, product):
        return self.publicGetBookSymbol ({ 
            'symbol': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetPubtickerSymbol ({
            'symbol': self.product_id (product),
        })
        timestamp = float (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': None,
            'percentage': None,
            'average': float (ticker['mid']),
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradesSymbol ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostOrderNew (self.extend ({
            'symbol': self.product_id (product),
            'amount': amount.toString (),
            'price': price.toString (),
            'side': side,
            'type': 'exchange ' + type,
            'ocoorder': false,
            'buy_price_oco': 0,
            'sell_price_oco': 0,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        request = '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        url = self.urls['api'] + request
        if type == 'public':            
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({
                'nonce': nonce.toString (),
                'request': request,
            }, query)
            payload = base64.b64encode (json.dumps (query))
            headers = {
                'X-BFX-APIKEY': self.apiKey,
                'X-BFX-PAYLOAD': payload,
                'X-BFX-SIGNATURE': self.hmac (payload, self.secret, hashlib.sha384),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitlish (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitlish',
            'name': 'bitlish',
            'countries': [ 'UK', 'EU', 'RU', ],
            'rateLimit': 2000,    
            'version': 'v1',
            'urls': {
                'api': 'https://bitlish.com/api',
                'www': 'https://bitlish.com',
                'doc': 'https://bitlish.com/api',
            },
            'api': {
                'public': {
                    'get': [
                        'instruments',
                        'ohlcv',
                        'pairs',
                        'tickers',
                        'trades_depth',
                        'trades_history',
                    ],
                },
                'private': {
                    'post': [
                        'accounts_operations',
                        'balance',
                        'cancel_trade',
                        'cancel_trades_by_ids',
                        'cancel_all_trades',
                        'create_bcode',
                        'create_template_wallet',
                        'create_trade',
                        'deposit',
                        'list_accounts_operations_from_ts',
                        'list_active_trades',
                        'list_bcodes',
                        'list_my_matches_from_ts',
                        'list_my_trades',
                        'list_my_trads_from_ts',
                        'list_payment_methods',
                        'list_payments',
                        'redeem_code',
                        'resign',
                        'signin',
                        'signout',
                        'trade_details',
                        'trade_options',
                        'withdraw',
                        'withdraw_by_id',
                    ],
                },
            },
        }
        params.update (config)
        super (bitlish, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairs ()
        result = []
        keys = products.keys ()
        for p in range (0, len (keys)):
            product = products[keys[p]]
            id = product['id']
            symbol = product['name']
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetTickers ()
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['max']),
            'low': float (ticker['min']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': None,
            'close': None,
            'first': float (ticker['first']),
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_order_book (self, product):
        return self.publicGetTradesDepth ({
            'pair_id': self.product_id (product),
        })

    def fetch_trades (self, product):
        return self.publicGetTradesHistory ({
            'pair_id': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalance ()

    def sign_in (self):
        return self.privatePostSignin ({
            'login': self.login,
            'passwd': self.password,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair_id': self.product_id (product),
            'dir': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostCreateTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            body = json.dumps (self.extend ({ 'token': self.apiKey }, params))
            headers = { 'Content-Type': 'application/json' }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitmarket (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitmarket',
            'name': 'BitMarket',
            'countries': [ 'PL', 'EU', ],
            'rateLimit': 3000,
            'urls': {
                'api': {
                    'public': 'https://www.bitmarket.net',
                    'private': 'https://www.bitmarket.pl/api2/', # last slash is critical
                },
                'www': [
                    'https://www.bitmarket.pl',
                    'https://www.bitmarket.net',
                ],
                'doc': [
                    'https://www.bitmarket.net/docs.php?file=api_public.html',
                    'https://www.bitmarket.net/docs.php?file=api_private.html',
                    'https://github.com/bitmarket-net/api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'json/{market}/ticker',
                        'json/{market}/orderbook',
                        'json/{market}/trades',
                        'json/ctransfer',
                        'graphs/{market}/90m',
                        'graphs/{market}/6h',
                        'graphs/{market}/1d',
                        'graphs/{market}/7d',
                        'graphs/{market}/1m',
                        'graphs/{market}/3m',
                        'graphs/{market}/6m',
                        'graphs/{market}/1y',
                    ],
                },
                'private': {
                    'post': [
                        'info',
                        'trade',
                        'cancel',
                        'orders',
                        'trades',
                        'history',
                        'withdrawals',
                        'tradingdesk',
                        'tradingdeskStatus',
                        'tradingdeskConfirm',
                        'cryptotradingdesk',
                        'cryptotradingdeskStatus',
                        'cryptotradingdeskConfirm',
                        'withdraw',
                        'withdrawFiat',
                        'withdrawPLNPP',
                        'withdrawFiatFast',
                        'deposit',
                        'transfer',
                        'transfers',
                        'marginList',
                        'marginOpen',
                        'marginClose',
                        'marginCancel',
                        'marginModify',
                        'marginBalanceAdd',
                        'marginBalanceRemove',
                        'swapList',
                        'swapOpen',
                        'swapClose',
                    ],
                },
            },
            'products': {
                'BTC/PLN': { 'id': 'BTCPLN', 'symbol': 'BTC/PLN', 'base': 'BTC', 'quote': 'PLN' },
                'BTC/EUR': { 'id': 'BTCEUR', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
                'LTC/PLN': { 'id': 'LTCPLN', 'symbol': 'LTC/PLN', 'base': 'LTC', 'quote': 'PLN' },
                'LTC/BTC': { 'id': 'LTCBTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC' },
                'LMX/BTC': { 'id': 'LiteMineXBTC', 'symbol': 'LMX/BTC', 'base': 'LMX', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (bitmarket, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostInfo ()

    def fetch_order_book (self, product):
        return self.publicGetJsonMarketOrderbook ({
            'market': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetJsonMarketTicker ({
            'market': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetJsonMarketTrades ({
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTrade (self.extend ({
            'market': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'public':
            url += '/' + self.implode_params (path + '.json', params)
        else:
            nonce = self.nonce ()
            query = self.extend ({
                'tonce': nonce,
                'method': path,
            }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'API-Key': self.apiKey,
                'API-Hash': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitmex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitmex',
            'name': 'BitMEX',
            'countries': 'SC', # Seychelles
            'version': 'v1',
            'rateLimit': 2000,
            'urls': {
                'api': 'https://www.bitmex.com',
                'www': 'https://www.bitmex.com',
                'doc': [
                    'https://www.bitmex.com/app/apiOverview',
                    'https://github.com/BitMEX/api-connectors/tree/master/official-http',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'announcement',
                        'announcement/urgent',
                        'funding',
                        'instrument',
                        'instrument/active',
                        'instrument/activeAndIndices',
                        'instrument/activeIntervals',
                        'instrument/compositeIndex',
                        'instrument/indices',
                        'insurance',
                        'leaderboard',
                        'liquidation',
                        'orderBook',
                        'orderBook/L2',
                        'quote',
                        'quote/bucketed',
                        'schema',
                        'schema/websocketHelp',
                        'settlement',
                        'stats',
                        'stats/history',
                        'trade',
                        'trade/bucketed',
                    ],
                },
                'private': {
                    'get': [
                        'apiKey',
                        'chat',
                        'chat/channels',
                        'chat/connected',
                        'execution',
                        'execution/tradeHistory',
                        'notification',
                        'order',
                        'position',
                        'user',
                        'user/affiliateStatus',
                        'user/checkReferralCode',
                        'user/commission',
                        'user/depositAddress',
                        'user/margin',
                        'user/minWithdrawalFee',
                        'user/wallet',
                        'user/walletHistory',
                        'user/walletSummary',
                    ],
                    'post': [
                        'apiKey',
                        'apiKey/disable',
                        'apiKey/enable',
                        'chat',
                        'order',
                        'order/bulk',
                        'order/cancelAllAfter',
                        'order/closePosition',
                        'position/isolate',
                        'position/leverage',
                        'position/riskLimit',
                        'position/transferMargin',
                        'user/cancelWithdrawal',
                        'user/confirmEmail',
                        'user/confirmEnableTFA',
                        'user/confirmWithdrawal',
                        'user/disableTFA',
                        'user/logout',
                        'user/logoutAll',
                        'user/preferences',
                        'user/requestEnableTFA',
                        'user/requestWithdrawal',
                    ],
                    'put': [
                        'order',
                        'order/bulk',
                        'user',
                    ],
                    'delete': [
                        'apiKey',
                        'order',
                        'order/all',
                    ],
                }
            },
        }
        params.update (config)
        super (bitmex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetInstrumentActive ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['symbol']
            base = product['underlying']
            quote = product['quoteCurrency']
            isFuturesContract = id != (base + quote)
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            symbol = id if isFuturesContract else (base + '/' + quote)
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetUserMargin ({ 'currency': 'all' })

    def fetch_order_book (self, product):
        return self.publicGetOrderBookL2 ({
            'symbol': self.product_id (product),
        })

    def fetch_ticker (self, product):
        request = {
            'symbol': self.product_id (product),
            'binSize': '1d',
            'partial': True,
            'count': 1,
            'reverse': True,            
        }
        quotes = self.publicGetQuoteBucketed (request)
        quotesLength = len (quotes)
        quote = quotes[quotesLength - 1]
        tickers = self.publicGetTradeBucketed (request)
        ticker = tickers[0]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (quote['bidPrice']),
            'ask': float (quote['askPrice']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': float (ticker['close']),
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['homeNotional']),
            'quoteVolume': float (ticker['foreignNotional']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrade ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'side': self.capitalize (side),
            'orderQty': amount,
            'ordType': self.capitalize (type),
        }
        if type == 'limit':
            order['rate'] = price
        return self.privatePostOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        query = '/api/' + self.version + '/' + path
        if params:
            query += '?' + _urlencode.urlencode (params)
        url = self.urls['api'] + query
        if type == 'private':
            nonce = self.nonce ()
            if method == 'POST':
                if params:
                    body = json.dumps (params)
            request = ''.join ([ method, query, nonce.toString (), body or ''])
            headers = {
                'Content-Type': 'application/json',
                'api-nonce': nonce,
                'api-key': self.apiKey,
                'api-signature': self.hmac (request, self.secret),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bitso (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bitso',
            'name': 'Bitso',
            'countries': 'MX', # Mexico
            'rateLimit': 2000, # 30 requests per minute
            'version': 'v3',
            'urls': {
                'api': 'https://api.bitso.com',
                'www': 'https://bitso.com',
                'doc': 'https://bitso.com/api_info',
            },
            'api': {
                'public': {
                    'get': [
                        'available_books',
                        'ticker',
                        'order_book',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'account_status',
                        'balance',
                        'fees',
                        'fundings',
                        'fundings/{fid}',
                        'funding_destination',
                        'kyc_documents',
                        'ledger',
                        'ledger/trades',
                        'ledger/fees',
                        'ledger/fundings',
                        'ledger/withdrawals',
                        'mx_bank_codes',
                        'open_orders',
                        'order_trades/{oid}',
                        'orders/{oid}',
                        'user_trades',
                        'user_trades/{tid}',
                        'withdrawals/',
                        'withdrawals/{wid}',
                    ],
                    'post': [
                        'bitcoin_withdrawal',
                        'debit_card_withdrawal',
                        'ether_withdrawal',
                        'orders',
                        'phone_number',
                        'phone_verification',
                        'phone_withdrawal',
                        'spei_withdrawal',
                    ],
                    'delete': [
                        'orders/{oid}',
                        'orders/all',
                    ],
                }
            },
        }
        params.update (config)
        super (bitso, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetAvailableBooks ()
        result = []
        for p in range (0, len (products['payload'])):
            product = products['payload'][p]
            id = product['book']
            symbol = id.upper ().replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBook ({
            'book': self.product_id (product),
        })

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'book': self.product_id (product),
        })
        ticker = response['payload']
        timestamp = self.parse8601 (ticker['created_at'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'book': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'book': self.product_id (product),
            'side': side,
            'type': type,
            'major': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostOrders (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        query = '/' + self.version + '/' + self.implode_params (path, params)
        url = self.urls['api'] + query
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            if params:
                body = json.dumps (params)
            nonce = self.nonce ().toString ()
            request = ''.join ([ nonce, method, query, body or '' ])
            signature = self.hmac (request, self.secret)
            auth = self.apiKey + ':' + nonce + ':' + signature
            headers = { 'Authorization': "Bitso " + auth }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bittrex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bittrex',
            'name': 'Bittrex',
            'countries': 'US',
            'version': 'v1.1',
            'rateLimit': 2000,
            'urls': {
                'api': 'https://bittrex.com/api',
                'www': 'https://bittrex.com',
                'doc': [ 
                    'https://bittrex.com/Home/Api',
                    'https://www.npmjs.org/package/node.bittrex.api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'currencies',
                        'markethistory',
                        'markets',
                        'marketsummaries',
                        'marketsummary',
                        'orderbook',
                        'ticker',            
                    ],
                },
                'account': {
                    'get': [
                        'balance',
                        'balances',
                        'depositaddress',
                        'deposithistory',
                        'order',
                        'orderhistory',
                        'withdrawalhistory',
                        'withdraw',
                    ],
                },
                'market': {
                    'get': [
                        'buylimit',
                        'buymarket',
                        'cancel',
                        'openorders',
                        'selllimit',
                        'sellmarket',
                    ],
                },
            },
        }
        params.update (config)
        super (bittrex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetMarkets ()
        result = []
        for p in range (0, len (products['result'])):
            product = products['result'][p]
            id = product['MarketName']
            base = product['BaseCurrency']
            quote = product['MarketCurrency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.accountGetBalances ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 50,
        })

    def fetch_ticker (self, product):
        response = self.publicGetMarketsummary ({
            'market': self.product_id (product),
        })
        ticker = response['result'][0]
        timestamp = self.parse8601 (ticker['TimeStamp'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['High']),
            'low': float (ticker['Low']),
            'bid': float (ticker['Bid']),
            'ask': float (ticker['Ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['Last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['Volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetMarkethistory ({ 
            'market': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'marketGet' + self.capitalize (side) + type
        order = {
            'market': self.product_id (product),
            'quantity': amount,
        }
        if type == 'limit':
            order['rate'] = price
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/'
        if type == 'public':
            url += type + '/' + method.lower () + path
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            url += type + '/'
            if ((type == 'account') and (path != 'withdraw')) or (path == 'openorders'):
                url += method.lower ()
            url += path + '?' + _urlencode.urlencode (self.extend ({
                'nonce': nonce,
                'apikey': self.apiKey,
            }, params))
            headers = { 'apisign': self.hmac (url, self.secret, hashlib.sha512) }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class btcx (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'btcx',
            'name': 'BTCX',
            'countries': [ 'IS', 'US', 'EU', ],
            'rateLimit': 3000, # support in english is very poor, unable to tell rate limits
            'version': 'v1',
            'urls': {
                'api': 'https://btc-x.is/api',
                'www': 'https://btc-x.is',
                'doc': 'https://btc-x.is/custom/api-document.html',
            },
            'api': {
                'public': {
                    'get': [
                        'depth/{id}/{limit}',
                        'ticker/{id}',         
                        'trade/{id}/{limit}',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'cancel',
                        'history',
                        'order',
                        'redeem',
                        'trade',
                        'withdraw',
                    ],
                },
            },
            'products': {
                'BTC/USD': { 'id': 'btc/usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'BTC/EUR': { 'id': 'btc/eur', 'symbol': 'BTC/EUR', 'base': 'BTC', 'quote': 'EUR' },
            },
        }
        params.update (config)
        super (btcx, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        p = self.product (product)
        return self.publicGetDepthIdLimit ({ 
            'id': self.product_id (product),
            'limit': 1000,
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerId ({
            'id': self.product_id (product),
        })
        timestamp = ticker['time'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradeIdLimit ({
            'id': self.product_id (product),
            'limit': 100,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTrade (self.extend ({
            'type': side.upper (),
            'market': self.product_id (product),
            'amount': amount,
            'price': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/'
        if type == 'public':
            url += self.implode_params (path, params)
        else:
            nonce = self.nonce ()
            url += type
            body = _urlencode.urlencode (self.extend ({
                'Method': path.upper (),
                'Nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Signature': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class bxinth (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'bxinth',
            'name': 'BX.in.th',
            'countries': 'TH', # Thailand
            'rateLimit': 2000,
            'urls': {
                'api': 'https://bx.in.th/api',
                'www': 'https://bx.in.th',
                'doc': 'https://bx.in.th/info/api',
            },
            'api': {
                'public': {
                    'get': [
                        '', # ticker
                        'options',
                        'optionbook',
                        'orderbook',
                        'pairing',
                        'trade',
                        'tradehistory',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'biller',
                        'billgroup',
                        'billpay',
                        'cancel',
                        'deposit',
                        'getorders',
                        'history',
                        'option-issue',
                        'option-bid',
                        'option-sell',
                        'option-myissue',
                        'option-mybid',
                        'option-myoptions',
                        'option-exercise',
                        'option-cancel',
                        'option-history',
                        'order',
                        'withdrawal',
                        'withdrawal-history',
                    ],
                },
            },
        }
        params.update (config)
        super (bxinth, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairing ()
        keys = products.keys ()
        result = []
        for p in range (0, len (keys)):
            product = products[keys[p]]
            id = product['pairing_id']
            base = product['primary_currency']
            quote = product['secondary_currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ({
            'pairing': self.product_id (product),
        })

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGet ({ 'pairing': p['id'] })
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['orderbook']['bids']['highbid']),
            'ask': float (ticker['orderbook']['asks']['highbid']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_price']),
            'change': float (ticker['change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume_24hours']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrade ({
            'pairing': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostOrder (self.extend ({
            'pairing': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path + '/'
        if params:
            url += '?' + _urlencode.urlencode (params)
        if type == 'private':
            nonce = self.nonce ()
            signature = self.hash (self.apiKey + nonce + self.secret, hashlib.sha256)
            body = _urlencode.urlencode (self.extend ({
                'key': self.apiKey,
                'nonce': nonce,
                'signature': signature,
                # twofa: self.twofa,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class ccex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'ccex',
            'name': 'C-CEX',
            'countries': [ 'DE', 'EU', ],
            'rateLimit': 2000,
            'urls': {
                'api': {
                    'tickers': 'https://c-cex.com/t',
                    'public': 'https://c-cex.com/t/api_pub.html',
                    'private': 'https://c-cex.com/t/api.html',
                },
                'www': 'https://c-cex.com',
                'doc': 'https://c-cex.com/?id=api',
            },
            'api': {
                'tickers': {
                    'get': [
                        'coinnames',
                        '{market}',
                        'pairs',
                        'prices',
                        'volume_{coin}',
                    ],
                },
                'public': {
                    'get': [                
                        'balancedistribution',
                        'markethistory',
                        'markets',
                        'marketsummaries',
                        'orderbook',
                    ],
                },
                'private': {            
                    'get': [
                        'buylimit',
                        'cancel',
                        'getbalance',
                        'getbalances',                
                        'getopenorders',
                        'getorder',
                        'getorderhistory',
                        'mytrades',
                        'selllimit',
                    ],
                },
            },
        }
        params.update (config)
        super (ccex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetMarkets ()
        result = []
        for p in range (0, len (products['result'])):
            product = products['result'][p]
            id = product['MarketName']
            base = product['MarketCurrency']
            quote = product['BaseCurrency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalances ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 100,
        })

    def fetch_ticker (self, product):
        response = self.tickersGetMarket ({
            'market': self.product_id (product).lower (),
        })
        ticker = response['ticker']
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['lastprice']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': None,
            'quoteVolume': float (ticker['buysupport']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetMarkethistory ({
            'market': self.product_id (product),
            'type': 'both',
            'depth': 100,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privateGet' + self.capitalize (side) + type
        return getattr (self, method) (self.extend ({
            'market': self.product_id (product),
            'quantity': amount,
            'rate': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        if type == 'private':
            nonce = self.nonce ().toString ()
            query = self.keysort (self.extend ({
                'a': path,
                'apikey': self.apiKey,
                'nonce': nonce,
            }, params))
            url += '?' + _urlencode.urlencode (query)
            headers = { 'apisign': self.hmac (url, self.secret, hashlib.sha512) }
        elif type == 'public':
            url += '?' + _urlencode.urlencode (self.extend ({
                'a': 'get' + path,
            }, params))
        else:
            url += '/' + self.implode_params (path, params) + '.json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class cex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'cex',
            'name': 'CEX.IO',
            'countries': [ 'UK', 'EU', 'CY', 'RU', ],
            'rateLimit': 2000,
            'urls': {
                'api': 'https://cex.io/api',
                'www': 'https://cex.io',
                'doc': 'https://cex.io/cex-api',
            },
            'api': {
                'public': {
                    'get': [
                        'currency_limits',
                        'last_price/{pair}',
                        'last_prices/{currencies}',
                        'ohlcv/hd/{yyyymmdd}/{pair}',
                        'order_book/{pair}',
                        'ticker/{pair}',
                        'tickers/{currencies}',
                        'trade_history/{pair}',
                    ],
                    'post': [
                        'convert/{pair}',
                        'price_stats/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'active_orders_status/',
                        'archived_orders/{pair}',
                        'balance/',
                        'cancel_order/',
                        'cancel_orders/{pair}',
                        'cancel_replace_order/{pair}',
                        'close_position/{pair}',
                        'get_address/',
                        'get_myfee/',
                        'get_order/',
                        'get_order_tx/',
                        'open_orders/{pair}',
                        'open_orders/',
                        'open_position/{pair}',
                        'open_positions/{pair}',
                        'place_order/{pair}',
                        'place_order/{pair}',
                    ],
                }
            },
        }
        params.update (config)
        super (cex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetCurrencyLimits ()
        result = []
        for p in range (0, len (products['data']['pairs'])):
            product = products['data']['pairs'][p]
            id = product['symbol1'] + '/' + product['symbol2']
            symbol = id
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBookPair ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerPair ({
            'pair': self.product_id (product),
        })
        timestamp = int (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': float (ticker['change']),
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTradeHistoryPair ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair': self.product_id (product),
            'type': side,
            'amount': amount,            
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['order_type'] = type
        return self.privatePostPlaceOrderPair (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':   
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ().toString ()
            body = _urlencode.urlencode (self.extend ({
                'key': self.apiKey,
                'signature': self.hmac (nonce + self.uid + self.apiKey, self.secret).upper (),
                'nonce': nonce,
            }, query))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class coincheck (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'coincheck',
            'name': 'coincheck',
            'countries': [ 'JP', 'ID', ],
            'rateLimit': 2000,
            'urls': {
                'api': 'https://coincheck.com/api',
                'www': 'https://coincheck.com',
                'doc': 'https://coincheck.com/documents/exchange/api',
            },
            'api': {
                'public': {
                    'get': [
                        'exchange/orders/rate',
                        'order_books',
                        'rate/{pair}',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/balance',
                        'accounts/leverage_balance',
                        'bank_accounts',
                        'deposit_money',
                        'exchange/orders/opens',
                        'exchange/orders/transactions',
                        'exchange/orders/transactions_pagination',
                        'exchange/leverage/positions',
                        'lending/borrows/matches',
                        'send_money',
                        'withdraws',
                    ],            
                    'post': [
                        'bank_accounts',
                        'deposit_money/{id}/fast',
                        'exchange/orders',
                        'exchange/transfers/to_leverage',
                        'exchange/transfers/from_leverage',
                        'lending/borrows',
                        'lending/borrows/{id}/repay',
                        'send_money',
                        'withdraws',
                    ],
                    'delete': [
                        'bank_accounts/{id}',
                        'exchange/orders/{id}',
                        'withdraws/{id}',
                    ],
                },
            },
            'products': {
                'BTC/JPY':  { 'id': 'btc_jpy',  'symbol': 'BTC/JPY',  'base': 'BTC',  'quote': 'JPY' }, # the only real pair
                'ETH/JPY':  { 'id': 'eth_jpy',  'symbol': 'ETH/JPY',  'base': 'ETH',  'quote': 'JPY' },
                'ETC/JPY':  { 'id': 'etc_jpy',  'symbol': 'ETC/JPY',  'base': 'ETC',  'quote': 'JPY' },
                'DAO/JPY':  { 'id': 'dao_jpy',  'symbol': 'DAO/JPY',  'base': 'DAO',  'quote': 'JPY' },
                'LSK/JPY':  { 'id': 'lsk_jpy',  'symbol': 'LSK/JPY',  'base': 'LSK',  'quote': 'JPY' },
                'FCT/JPY':  { 'id': 'fct_jpy',  'symbol': 'FCT/JPY',  'base': 'FCT',  'quote': 'JPY' },
                'XMR/JPY':  { 'id': 'xmr_jpy',  'symbol': 'XMR/JPY',  'base': 'XMR',  'quote': 'JPY' },
                'REP/JPY':  { 'id': 'rep_jpy',  'symbol': 'REP/JPY',  'base': 'REP',  'quote': 'JPY' },
                'XRP/JPY':  { 'id': 'xrp_jpy',  'symbol': 'XRP/JPY',  'base': 'XRP',  'quote': 'JPY' },
                'ZEC/JPY':  { 'id': 'zec_jpy',  'symbol': 'ZEC/JPY',  'base': 'ZEC',  'quote': 'JPY' },
                'XEM/JPY':  { 'id': 'xem_jpy',  'symbol': 'XEM/JPY',  'base': 'XEM',  'quote': 'JPY' },
                'LTC/JPY':  { 'id': 'ltc_jpy',  'symbol': 'LTC/JPY',  'base': 'LTC',  'quote': 'JPY' },
                'DASH/JPY': { 'id': 'dash_jpy', 'symbol': 'DASH/JPY', 'base': 'DASH', 'quote': 'JPY' },
                'ETH/BTC':  { 'id': 'eth_btc',  'symbol': 'ETH/BTC',  'base': 'ETH',  'quote': 'BTC' },
                'ETC/BTC':  { 'id': 'etc_btc',  'symbol': 'ETC/BTC',  'base': 'ETC',  'quote': 'BTC' },
                'LSK/BTC':  { 'id': 'lsk_btc',  'symbol': 'LSK/BTC',  'base': 'LSK',  'quote': 'BTC' },
                'FCT/BTC':  { 'id': 'fct_btc',  'symbol': 'FCT/BTC',  'base': 'FCT',  'quote': 'BTC' },
                'XMR/BTC':  { 'id': 'xmr_btc',  'symbol': 'XMR/BTC',  'base': 'XMR',  'quote': 'BTC' },
                'REP/BTC':  { 'id': 'rep_btc',  'symbol': 'REP/BTC',  'base': 'REP',  'quote': 'BTC' },
                'XRP/BTC':  { 'id': 'xrp_btc',  'symbol': 'XRP/BTC',  'base': 'XRP',  'quote': 'BTC' },
                'ZEC/BTC':  { 'id': 'zec_btc',  'symbol': 'ZEC/BTC',  'base': 'ZEC',  'quote': 'BTC' },
                'XEM/BTC':  { 'id': 'xem_btc',  'symbol': 'XEM/BTC',  'base': 'XEM',  'quote': 'BTC' },
                'LTC/BTC':  { 'id': 'ltc_btc',  'symbol': 'LTC/BTC',  'base': 'LTC',  'quote': 'BTC' },
                'DASH/BTC': { 'id': 'dash_btc', 'symbol': 'DASH/BTC', 'base': 'DASH', 'quote': 'BTC' },
            },
        }
        params.update (config)
        super (coincheck, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetAccountsBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBooks ()

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ()
        timestamp = ticker['timestamp'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        prefix = ''
        order = {
            'pair': self.product_id (product),
        }
        if type == 'market':
            order_type = type + '_' + side
            order['order_type'] = order_type
            prefix = (order_type + '_') if (side == buy) else ''
            order[prefix + 'amount'] = amount
        else:
            order['order_type'] = side
            order['rate'] = price
            order['amount'] = amount
        return self.privatePostExchangeOrders (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ().toString ()
            if query:
                body = _urlencode.urlencode (self.keysort (query))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'ACCESS-KEY': self.apiKey,
                'ACCESS-NONCE': nonce,
                'ACCESS-SIGNATURE': self.hmac (nonce + url + (body or ''), self.secret)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class coinsecure (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'coinsecure',
            'name': 'Coinsecure',
            'countries': 'IN', # India
            'rateLimit': 1000,
            'version': 'v1',
            'urls': {
                'api': 'https://api.coinsecure.in',
                'www': 'https://coinsecure.in',
                'doc': [
                    'https://api.coinsecure.in',
                    'https://github.com/coinsecure/plugins',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'bitcoin/search/confirmation/{txid}',
                        'exchange/ask/low',
                        'exchange/ask/orders',
                        'exchange/bid/high',
                        'exchange/bid/orders',
                        'exchange/lastTrade',
                        'exchange/max24Hr',
                        'exchange/min24Hr',
                        'exchange/ticker',
                        'exchange/trades',
                    ],
                },
                'private': {
                    'get': [
                        'mfa/authy/call',
                        'mfa/authy/sms',            
                        'netki/search/{netkiName}',
                        'user/bank/otp/{number}',
                        'user/kyc/otp/{number}',
                        'user/profile/phone/otp/{number}',
                        'user/wallet/coin/address/{id}',
                        'user/wallet/coin/deposit/confirmed/all',
                        'user/wallet/coin/deposit/confirmed/{id}',
                        'user/wallet/coin/deposit/unconfirmed/all',
                        'user/wallet/coin/deposit/unconfirmed/{id}',
                        'user/wallet/coin/wallets',
                        'user/exchange/bank/fiat/accounts',
                        'user/exchange/bank/fiat/balance/available',
                        'user/exchange/bank/fiat/balance/pending',
                        'user/exchange/bank/fiat/balance/total',
                        'user/exchange/bank/fiat/deposit/cancelled',
                        'user/exchange/bank/fiat/deposit/unverified',
                        'user/exchange/bank/fiat/deposit/verified',
                        'user/exchange/bank/fiat/withdraw/cancelled',
                        'user/exchange/bank/fiat/withdraw/completed',
                        'user/exchange/bank/fiat/withdraw/unverified',
                        'user/exchange/bank/fiat/withdraw/verified',
                        'user/exchange/ask/cancelled',
                        'user/exchange/ask/completed',
                        'user/exchange/ask/pending',
                        'user/exchange/bid/cancelled',
                        'user/exchange/bid/completed',
                        'user/exchange/bid/pending',
                        'user/exchange/bank/coin/addresses',
                        'user/exchange/bank/coin/balance/available',
                        'user/exchange/bank/coin/balance/pending',
                        'user/exchange/bank/coin/balance/total',
                        'user/exchange/bank/coin/deposit/cancelled',
                        'user/exchange/bank/coin/deposit/unverified',
                        'user/exchange/bank/coin/deposit/verified',
                        'user/exchange/bank/coin/withdraw/cancelled',
                        'user/exchange/bank/coin/withdraw/completed',
                        'user/exchange/bank/coin/withdraw/unverified',
                        'user/exchange/bank/coin/withdraw/verified',
                        'user/exchange/bank/summary',
                        'user/exchange/coin/fee',
                        'user/exchange/fiat/fee',
                        'user/exchange/kycs',
                        'user/exchange/referral/coin/paid',
                        'user/exchange/referral/coin/successful',
                        'user/exchange/referral/fiat/paid',
                        'user/exchange/referrals',
                        'user/exchange/trade/summary',
                        'user/login/token/{token}',
                        'user/summary',
                        'user/wallet/summary',
                        'wallet/coin/withdraw/cancelled',
                        'wallet/coin/withdraw/completed',
                        'wallet/coin/withdraw/unverified',
                        'wallet/coin/withdraw/verified',
                    ],
                    'post': [
                        'login',
                        'login/initiate',
                        'login/password/forgot',
                        'mfa/authy/initiate',
                        'mfa/ga/initiate',
                        'signup',
                        'user/netki/update',
                        'user/profile/image/update',
                        'user/exchange/bank/coin/withdraw/initiate',
                        'user/exchange/bank/coin/withdraw/newVerifycode',
                        'user/exchange/bank/fiat/withdraw/initiate',
                        'user/exchange/bank/fiat/withdraw/newVerifycode',
                        'user/password/change',
                        'user/password/reset',
                        'user/wallet/coin/withdraw/initiate',
                        'wallet/coin/withdraw/newVerifycode',
                    ],
                    'put': [
                        'signup/verify/{token}',
                        'user/exchange/kyc',
                        'user/exchange/bank/fiat/deposit/new',
                        'user/exchange/ask/new',
                        'user/exchange/bid/new',
                        'user/exchange/instant/buy',
                        'user/exchange/instant/sell',
                        'user/exchange/bank/coin/withdraw/verify',
                        'user/exchange/bank/fiat/account/new',
                        'user/exchange/bank/fiat/withdraw/verify',
                        'user/mfa/authy/initiate/enable',
                        'user/mfa/ga/initiate/enable',
                        'user/netki/create',
                        'user/profile/phone/new',
                        'user/wallet/coin/address/new',
                        'user/wallet/coin/new',
                        'user/wallet/coin/withdraw/sendToExchange',
                        'user/wallet/coin/withdraw/verify',
                    ],
                    'delete': [
                        'user/gcm/{code}',
                        'user/logout',
                        'user/exchange/bank/coin/withdraw/unverified/cancel/{withdrawID}',
                        'user/exchange/bank/fiat/deposit/cancel/{depositID}',
                        'user/exchange/ask/cancel/{orderID}',
                        'user/exchange/bid/cancel/{orderID}',
                        'user/exchange/bank/fiat/withdraw/unverified/cancel/{withdrawID}',
                        'user/mfa/authy/disable/{code}',
                        'user/mfa/ga/disable/{code}',
                        'user/profile/phone/delete',
                        'user/profile/image/delete/{netkiName}',
                        'user/wallet/coin/withdraw/unverified/cancel/{withdrawID}',
                    ],
                },
            },
            'products': {
                'BTC/INR': { 'id': 'BTC/INR', 'symbol': 'BTC/INR', 'base': 'BTC', 'quote': 'INR' },
            },
        }
        params.update (config)
        super (coinsecure, self).__init__ (params)

    def fetch_balance (self):
        return self.privateGetUserExchangeBankSummary ()

    def fetch_order_book (self, product):
        return self.publicGetExchangeAskOrders ()

    def fetch_ticker (self, product):
        response = self.publicGetExchangeTicker ()
        ticker = response['message']
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['lastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['coinvolume']),
            'quoteVolume': float (ticker['fiatvolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetExchangeTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePutUserExchange'
        order = {}
        if type == 'market':       
            method += 'Instant' + self.capitalize (side)
            if side == 'buy':
                order['maxFiat'] = amount
            else:
                order['maxVol'] = amount
        else:
            direction = 'Bid' if (side == 'buy') else 'Ask'
            method += direction + 'New'
            order['rate'] = price
            order['vol'] = amount
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'private':
            headers = { 'Authorization': self.apiKey }
            if query:
                body = json.dumps (query)
                headers['Content-Type'] = 'application/json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class exmo (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'exmo',
            'name': 'EXMO',
            'countries': [ 'ES', 'RU', ], # Spain, Russia
            'rateLimit': 1000, # once every 350 ms ≈ 180 requests per minute ≈ 3 requests per second
            'version': 'v1',
            'urls': {
                'api': 'https://api.exmo.com',
                'www': 'https://exmo.me',
                'doc': [
                    'https://exmo.me/ru/api_doc',
                    'https://github.com/exmo-dev/exmo_api_lib/tree/master/nodejs',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'currency',
                        'order_book',
                        'pair_settings',
                        'ticker',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'user_info',
                        'order_create',
                        'order_cancel',
                        'user_open_orders',
                        'user_trades',
                        'user_cancelled_orders',
                        'order_trades',
                        'required_amount',
                        'deposit_address',
                        'withdraw_crypt',
                        'withdraw_get_txid',
                        'excode_create',
                        'excode_load',
                        'wallet_history',
                    ],
                },
            },
        }
        params.update (config)
        super (exmo, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetPairSettings ()
        keys = products.keys ()
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products[id]
            symbol = id.replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostUserInfo ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBook ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        response = self.publicGetTicker ()
        p = self.product (product)
        ticker = response[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy_price']),
            'ask': float (ticker['sell_price']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last_trade']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker['vol_curr']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        prefix = ''
        if type =='market':
            prefix = 'market_'
        order = {
            'pair': self.product_id (product),
            'quantity': amount,
            'price': price or 0,
            'type': prefix + side,
        }
        return self.privatePostOrderCreate (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({ 'nonce': nonce }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class fyb (Market):

    def __init__ (self, config = {}):
        params = {
            'rateLimit': 2000,
            'api': {
                'public': {
                    'get': [
                        'ticker',
                        'tickerdetailed',
                        'orderbook',
                        'trades',
                    ],
                },
                'private': {
                    'post': [
                        'test',
                        'getaccinfo',
                        'getpendingorders',
                        'getorderhistory',
                        'cancelpendingorder',
                        'placeorder',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (fyb, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostGetaccinfo ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ()

    def fetch_ticker (self, product):
        ticker = self.publicGetTickerdetailed ()
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostPlaceorder (self.extend ({
            'qty': amount,
            'price': price,
            'type': side[0].upper ()
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + path
        if type == 'public':           
            url += '.json'
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({ 'timestamp': nonce }, params))
            headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'key': self.apiKey,
                'sig': self.hmac (body, self.secret, hashlib.sha1)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class fybse (fyb):

    def __init__ (self, config = {}):
        params = {
            'id': 'fybse',
            'name': 'FYB-SE',
            'countries': 'SE', # Sweden
            'urls': {
                'api': 'https://www.fybse.se/api/SEK',
                'www': 'https://www.fybse.se',
                'doc': 'http://docs.fyb.apiary.io',
            },
            'products': {
                'BTC/SEK': { 'id': 'SEK', 'symbol': 'BTC/SEK', 'base': 'BTC', 'quote': 'SEK' },
            },
        }
        params.update (config)
        super (fybse, self).__init__ (params)

#------------------------------------------------------------------------------

class fybsg (fyb):

    def __init__ (self, config = {}):
        params = {
            'id': 'fybsg',
            'name': 'FYB-SG',
            'countries': 'SG', # Singapore
            'urls': {
                'api': 'https://www.fybsg.com/api/SGD',
                'www': 'https://www.fybsg.com',
                'doc': 'http://docs.fyb.apiary.io',
            },
            'products': {
                'BTC/SGD': { 'id': 'SGD', 'symbol': 'BTC/SGD', 'base': 'BTC', 'quote': 'SGD' },
            },
        }
        params.update (config)
        super (fybsg, self).__init__ (params)

#------------------------------------------------------------------------------

class hitbtc (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'hitbtc',
            'name': 'HitBTC',
            'countries': 'HK', # Hong Kong
            'rateLimit': 2000,
            'version': '1',
            'urls': {
                'api': 'http://api.hitbtc.com',
                'www': 'https://hitbtc.com',
                'doc': [
                    'https://hitbtc.com/api',
                    'http://hitbtc-com.github.io/hitbtc-api',
                    'http://jsfiddle.net/bmknight/RqbYB',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        '{symbol}/orderbook',
                        '{symbol}/ticker',
                        '{symbol}/trades',
                        '{symbol}/trades/recent',
                        'symbols',
                        'ticker',
                        'time,'
                    ],
                },
                'trading': {
                    'get': [
                        'balance',
                        'orders/active',
                        'orders/recent',
                        'order',
                        'trades/by/order',
                        'trades',
                    ],
                    'post': [
                        'new_order',
                        'cancel_order',
                        'cancel_orders',
                    ],
                },
                'payment': {
                    'get': [
                        'balance',
                        'address/{currency}',
                        'transactions',
                        'transactions/{transaction}',
                    ],
                    'post': [
                        'transfer_to_trading',
                        'transfer_to_main',
                        'address/{currency}',
                        'payout',
                    ],
                }
            },
        }
        params.update (config)
        super (hitbtc, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetSymbols ()
        result = []
        for p in range (0, len (products['symbols'])):
            product = products['symbols'][p]
            id = product['symbol']
            base = product['commodity']
            quote = product['currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tradingGetBalance ()

    def fetch_order_book (self, product):
        return self.publicGetSymbolOrderbook ({
            'symbol': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetSymbolTicker ({
            'symbol': self.product_id (product),
        })
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume']),
            'quoteVolume': float (ticker['volume_quote']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetSymbolTrades ({
            'symbol': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'clientOrderId': self.nonce (),
            'symbol': self.product_id (product),
            'side': side,
            'quantity': amount,
            'type': type,            
        }
        if type == 'limit':
            order['price'] = price
        return self.tradingPostNewOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/api/' + self.version + '/' + type + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'nonce': nonce, 'apikey': self.apiKey }, query)
            if method == 'POST':
                if query:
                    body = _urlencode.urlencode (query)
            if query:
                url += '?' + _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Signature': self.hmac (url + (body or ''), self.secret, hashlib.sha512).lower (),
            }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class huobi (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'huobi',
            'name': 'Huobi',
            'countries': 'CN',
            'rateLimit': 5000,
            'version': 'v3',
            'urls': {
                'api': 'http://api.huobi.com',
                'www': 'https://www.huobi.com',
                'doc': 'https://github.com/huobiapi/API_Docs_en/wiki',
            },
            'api': {
                'staticmarket': {
                    'get': [
                        '{id}_kline_{period}',
                        'ticker_{id}',
                        'depth_{id}',
                        'depth_{id}_{length}',
                        'detail_{id}',
                    ],
                },
                'usdmarket': {
                    'get': [
                        '{id}_kline_{period}',
                        'ticker_{id}',
                        'depth_{id}',
                        'depth_{id}_{length}',
                        'detail_{id}',
                    ],
                },
                'trade': {
                    'post': [
                        'get_account_info',
                        'get_orders',
                        'order_info',
                        'buy',
                        'sell',
                        'buy_market',
                        'sell_market',
                        'cancel_order',
                        'get_new_deal_orders',
                        'get_order_id_by_trade_id',
                        'withdraw_coin',
                        'cancel_withdraw_coin',
                        'get_withdraw_coin_result',
                        'transfer',
                        'loan',
                        'repayment',
                        'get_loan_available',
                        'get_loans',
                    ],            
                },
            },
            'products': {
                'BTC/CNY': { 'id': 'btc', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY', 'type': 'staticmarket', 'coinType': 1, },
                'LTC/CNY': { 'id': 'ltc', 'symbol': 'LTC/CNY', 'base': 'LTC', 'quote': 'CNY', 'type': 'staticmarket', 'coinType': 2, },
                'BTC/USD': { 'id': 'btc', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD', 'type': 'usdmarket',    'coinType': 1, },
            },
        }
        params.update (config)
        super (huobi, self).__init__ (params)

    def fetch_balance (self):
        return self.tradePostGetAccountInfo ()

    def fetch_order_book (self, product):
        p = self.product (product)
        method = p['type'] + 'GetDepthId'
        return getattr (self, method) ({ 'id': p['id'] })

    def fetch_ticker (self, product):
        p = self.product (product)
        method = p['type'] + 'GetTickerId'
        response = getattr (self, method) ({ 'id': p['id'] })
        ticker = response['ticker']
        timestamp = int (response['time']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        p = self.product (product)
        method = p['type'] + 'GetDetailId'
        return getattr (self, method) ({ 'id': p['id'] })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        method = 'tradePost' + self.capitalize (side)
        order = {
            'coin_type': p['coinType'],
            'amount': amount,
            'market': p['quote'].lower (),
        }
        if type == 'limit':
            order['price'] = price
        else:
            method += self.capitalize (type)
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'trade', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api']
        if type == 'trade':
            url += '/api' + self.version
            query = self.keysort (self.extend ({
                'method': path,
                'access_key': self.apiKey,
                'created': self.nonce (),
            }, params))
            queryString = _urlencode.urlencode (self.omit (query, 'market'))
            # secret key must be at the end of query to be signed
            queryString += '&secret_key=' + self.secret
            query['sign'] = self.hash (queryString)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        else:
            url += '/' + type + '/' + self.implode_params (path, params) + '_json.js'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class jubi (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'jubi',
            'name': 'jubi.com',
            'countries': 'CN',
            'rateLimit': 2000,
            'version': 'v1',
            'urls': {
                'api': 'https://www.jubi.com/api',
                'www': 'https://www.jubi.com',
                'doc': 'https://www.jubi.com/help/api.html',
            },
            'api': {
                'public': {
                    'get': [
                        'depth',
                        'orders',
                        'ticker',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'trade_add',
                        'trade_cancel',
                        'trade_list',
                        'trade_view',
                        'wallet',
                    ],
                },
            },
            'products': {
                'BTC/CNY':  { 'id': 'btc',  'symbol': 'BTC/CNY',  'base': 'BTC',  'quote': 'CNY' },
                'ETH/CNY':  { 'id': 'eth',  'symbol': 'ETH/CNY',  'base': 'ETH',  'quote': 'CNY' },
                'ANS/CNY':  { 'id': 'ans',  'symbol': 'ANS/CNY',  'base': 'ANS',  'quote': 'CNY' },
                'BLK/CNY':  { 'id': 'blk',  'symbol': 'BLK/CNY',  'base': 'BLK',  'quote': 'CNY' },
                'DNC/CNY':  { 'id': 'dnc',  'symbol': 'DNC/CNY',  'base': 'DNC',  'quote': 'CNY' },
                'DOGE/CNY': { 'id': 'doge', 'symbol': 'DOGE/CNY', 'base': 'DOGE', 'quote': 'CNY' },
                'EAC/CNY':  { 'id': 'eac',  'symbol': 'EAC/CNY',  'base': 'EAC',  'quote': 'CNY' },
                'ETC/CNY':  { 'id': 'etc',  'symbol': 'ETC/CNY',  'base': 'ETC',  'quote': 'CNY' },
                'FZ/CNY':   { 'id': 'fz',   'symbol': 'FZ/CNY',   'base': 'FZ',   'quote': 'CNY' },
                'GOOC/CNY': { 'id': 'gooc', 'symbol': 'GOOC/CNY', 'base': 'GOOC', 'quote': 'CNY' },
                'GAME/CNY': { 'id': 'game', 'symbol': 'GAME/CNY', 'base': 'GAME', 'quote': 'CNY' },
                'HLB/CNY':  { 'id': 'hlb',  'symbol': 'HLB/CNY',  'base': 'HLB',  'quote': 'CNY' },
                'IFC/CNY':  { 'id': 'ifc',  'symbol': 'IFC/CNY',  'base': 'IFC',  'quote': 'CNY' },
                'JBC/CNY':  { 'id': 'jbc',  'symbol': 'JBC/CNY',  'base': 'JBC',  'quote': 'CNY' },
                'KTC/CNY':  { 'id': 'ktc',  'symbol': 'KTC/CNY',  'base': 'KTC',  'quote': 'CNY' },
                'LKC/CNY':  { 'id': 'lkc',  'symbol': 'LKC/CNY',  'base': 'LKC',  'quote': 'CNY' },
                'LSK/CNY':  { 'id': 'lsk',  'symbol': 'LSK/CNY',  'base': 'LSK',  'quote': 'CNY' },
                'LTC/CNY':  { 'id': 'ltc',  'symbol': 'LTC/CNY',  'base': 'LTC',  'quote': 'CNY' },
                'MAX/CNY':  { 'id': 'max',  'symbol': 'MAX/CNY',  'base': 'MAX',  'quote': 'CNY' },
                'MET/CNY':  { 'id': 'met',  'symbol': 'MET/CNY',  'base': 'MET',  'quote': 'CNY' },
                'MRYC/CNY': { 'id': 'mryc', 'symbol': 'MRYC/CNY', 'base': 'MRYC', 'quote': 'CNY' },        
                'MTC/CNY':  { 'id': 'mtc',  'symbol': 'MTC/CNY',  'base': 'MTC',  'quote': 'CNY' },
                'NXT/CNY':  { 'id': 'nxt',  'symbol': 'NXT/CNY',  'base': 'NXT',  'quote': 'CNY' },
                'PEB/CNY':  { 'id': 'peb',  'symbol': 'PEB/CNY',  'base': 'PEB',  'quote': 'CNY' },
                'PGC/CNY':  { 'id': 'pgc',  'symbol': 'PGC/CNY',  'base': 'PGC',  'quote': 'CNY' },
                'PLC/CNY':  { 'id': 'plc',  'symbol': 'PLC/CNY',  'base': 'PLC',  'quote': 'CNY' },
                'PPC/CNY':  { 'id': 'ppc',  'symbol': 'PPC/CNY',  'base': 'PPC',  'quote': 'CNY' },
                'QEC/CNY':  { 'id': 'qec',  'symbol': 'QEC/CNY',  'base': 'QEC',  'quote': 'CNY' },
                'RIO/CNY':  { 'id': 'rio',  'symbol': 'RIO/CNY',  'base': 'RIO',  'quote': 'CNY' },
                'RSS/CNY':  { 'id': 'rss',  'symbol': 'RSS/CNY',  'base': 'RSS',  'quote': 'CNY' },
                'SKT/CNY':  { 'id': 'skt',  'symbol': 'SKT/CNY',  'base': 'SKT',  'quote': 'CNY' },
                'TFC/CNY':  { 'id': 'tfc',  'symbol': 'TFC/CNY',  'base': 'TFC',  'quote': 'CNY' },
                'VRC/CNY':  { 'id': 'vrc',  'symbol': 'VRC/CNY',  'base': 'VRC',  'quote': 'CNY' },
                'VTC/CNY':  { 'id': 'vtc',  'symbol': 'VTC/CNY',  'base': 'VTC',  'quote': 'CNY' },
                'WDC/CNY':  { 'id': 'wdc',  'symbol': 'WDC/CNY',  'base': 'WDC',  'quote': 'CNY' },
                'XAS/CNY':  { 'id': 'xas',  'symbol': 'XAS/CNY',  'base': 'XAS',  'quote': 'CNY' },
                'XPM/CNY':  { 'id': 'xpm',  'symbol': 'XPM/CNY',  'base': 'XPM',  'quote': 'CNY' },
                'XRP/CNY':  { 'id': 'xrp',  'symbol': 'XRP/CNY',  'base': 'XRP',  'quote': 'CNY' },
                'XSGS/CNY': { 'id': 'xsgs', 'symbol': 'XSGS/CNY', 'base': 'XSGS', 'quote': 'CNY' },
                'YTC/CNY':  { 'id': 'ytc',  'symbol': 'YTC/CNY',  'base': 'YTC',  'quote': 'CNY' },
                'ZET/CNY':  { 'id': 'zet',  'symbol': 'ZET/CNY',  'base': 'ZET',  'quote': 'CNY' },
                'ZCC/CNY':  { 'id': 'zcc',  'symbol': 'ZCC/CNY',  'base': 'ZCC',  'quote': 'CNY' },        
            },
        }
        params.update (config)
        super (jubi, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        return self.publicGetDepth ({
            'coin': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({ 
            'coin': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['vol']),
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetOrders ({
            'coin': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        return self.privatePostTradeAdd (self.extend ({
            'amount': amount,
            'price': price,
            'type': side,
            'coin': self.product_id (product),
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':  
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ().toString ()
            query = self.extend ({
                'key': self.apiKey,
                'nonce': nonce,
            }, params)
            query['signature'] = self.hmac (_urlencode.urlencode (query), self.hash (self.secret))
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class kraken (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'kraken',
            'name': 'Kraken',
            'countries': 'US',
            'version': '0',
            'rateLimit': 3000,
            'urls': {
                'api': 'https://api.kraken.com',
                'www': 'https://www.kraken.com',
                'doc': [
                    'https://www.kraken.com/en-us/help/api',
                    'https://github.com/nothingisdead/npm-kraken-api',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'Assets',
                        'AssetPairs',
                        'Depth',
                        'OHLC',
                        'Spread',
                        'Ticker',
                        'Time',
                        'Trades',
                    ],
                },
                'private': {
                    'post': [
                        'AddOrder',
                        'Balance',
                        'CancelOrder',
                        'ClosedOrders',
                        'DepositAddresses',
                        'DepositMethods',
                        'DepositStatus',
                        'Ledgers',
                        'OpenOrders',
                        'OpenPositions', 
                        'QueryLedgers', 
                        'QueryOrders', 
                        'QueryTrades',
                        'TradeBalance',
                        'TradesHistory',
                        'TradeVolume',
                        'Withdraw',
                        'WithdrawCancel', 
                        'WithdrawInfo',                 
                        'WithdrawStatus',
                    ],
                },
            },
        }
        params.update (config)
        super (kraken, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetAssetPairs ()
        keys = products['result'].keys ()
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products['result'][id]
            base = product['base']
            quote = product['quote']
            if (base[0] == 'X') or (base[0] == 'Z'):
                base = base[1:]
            if (quote[0] == 'X') or (quote[0] == 'Z'):
                quote = quote[1:]
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            darkpool = id.find ('.d') >= 0
            symbol = product['altname'] if darkpool else (base + '/' + quote)
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_order_book (self, product):
        return self.publicGetDepth  ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        p = self.product (product)
        response = self.publicGetTicker ({
            'pair': p['id'],
        })
        ticker = response['result'][p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['h'][1]),
            'low': float (ticker['l'][1]),
            'bid': float (ticker['b'][0]),
            'ask': float (ticker['a'][0]),
            'vwap': float (ticker['p'][1]),
            'open': float (ticker['o']),
            'close': None,
            'first': None,
            'last': float (ticker['c'][0]),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['v'][1]),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostBalance ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'pair': self.product_id (product),
            'type': side,
            'ordertype': type,
            'volume': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostAddOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/' + self.version + '/' + type + '/' + path
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ().toString ()
            query = self.extend ({ 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            query = url + self.hash (nonce + body, hashlib.sha256, 'binary')
            secret = base64.b64decode (self.secret)
            headers = {
                'API-Key': self.apiKey,
                'API-Sign': self.hmac (query, secret, hashlib.sha512, 'base64'),
                'Content-type': 'application/x-www-form-urlencoded',
            }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class luno (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'luno',
            'name': 'luno',
            'countries': [ 'UK', 'SG', 'ZA', ],
            'rateLimit': 5000,
            'version': '1',
            'urls': {
                'api': 'https://api.mybitx.com/api',
                'www': 'https://www.luno.com',
                'doc': [
                    'https://npmjs.org/package/bitx',
                    'https://github.com/bausmeier/node-bitx',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'orderbook',
                        'ticker',
                        'tickers',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'accounts/{id}/pending',
                        'accounts/{id}/transactions',
                        'balance',
                        'fee_info',
                        'funding_address',
                        'listorders',
                        'listtrades',
                        'orders/{id}',
                        'quotes/{id}',
                        'withdrawals',
                        'withdrawals/{id}',
                    ],
                    'post': [
                        'accounts',
                        'postorder',
                        'marketorder',
                        'stoporder',
                        'funding_address',
                        'withdrawals',
                        'send',
                        'quotes',
                        'oauth2/grant',
                    ],
                    'put': [
                        'quotes/{id}',
                    ],
                    'delete': [
                        'quotes/{id}',
                        'withdrawals/{id}',
                    ],
                },
            },
        }
        params.update (config)
        super (luno, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetTickers ()
        result = []
        for p in range (0, len (products['tickers'])):
            product = products['tickers'][p]
            id = product['pair']
            base = id[0:3]
            quote = id[3:6]
            base = self.commonCurrencyCode (base)
            quote = self.commonCurrencyCode (quote)
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({
            'pair': self.product_id (product),
        })
        timestamp = ticker['timestamp']
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': None,
            'low': None,
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_trade']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['rolling_24_hour_volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'pair': self.product_id (product)
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost'
        order = { 'pair': self.product_id (product) }
        if type == 'market':
            method += 'Marketorder'
            order['type'] = side.upper ()
            if side == 'buy':
                order['counter_volume'] = amount
            else:
                order['base_volume'] = amount            
        else:
            method += 'Order'
            order['volume'] = amount
            order['price'] = price
            if side == 'buy':
                order['type'] = 'BID'
            else:
                order['type'] = 'ASK'
        return getattr (self, method) (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if query:
            url += '?' + _urlencode.urlencode (query)
        if type == 'private':
            auth = base64.b64encode (self.apiKey + ':' + self.secret)
            headers = { 'Authorization': 'Basic ' + auth }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class okcoin (Market):

    def __init__ (self, config = {}):
        params = {
            'version': 'v1',
            'rateLimit': 2000, # up to 3000 requests per 5 minutes ≈ 600 requests per minute ≈ 10 requests per second ≈ 100 ms
            'api': {
                'public': {
                    'get': [
                        'depth',
                        'exchange_rate',
                        'future_depth',
                        'future_estimated_price',
                        'future_hold_amount',
                        'future_index',
                        'future_kline',
                        'future_price_limit',
                        'future_ticker',
                        'future_trades',
                        'kline',
                        'otcs',
                        'ticker',
                        'trades',    
                    ],
                },
                'private': {
                    'post': [
                        'account_records',
                        'batch_trade',
                        'borrow_money',
                        'borrow_order_info',
                        'borrows_info',
                        'cancel_borrow',
                        'cancel_order',
                        'cancel_otc_order',
                        'cancel_withdraw',
                        'future_batch_trade',
                        'future_cancel',
                        'future_devolve',
                        'future_explosive',
                        'future_order_info',
                        'future_orders_info',
                        'future_position',
                        'future_position_4fix',
                        'future_trade',
                        'future_trades_history',
                        'future_userinfo',
                        'future_userinfo_4fix',
                        'lend_depth',
                        'order_fee',
                        'order_history',
                        'order_info',
                        'orders_info',
                        'otc_order_history',
                        'otc_order_info',
                        'repayment',
                        'submit_otc_order',
                        'trade',
                        'trade_history',
                        'trade_otc_order',
                        'withdraw',
                        'withdraw_info',
                        'unrepayments_info',
                        'userinfo',
                    ],
                },
            },
        }
        params.update (config)
        super (okcoin, self).__init__ (params)

    def fetch_order_book (self, product):
        return self.publicGetDepth ({
            'symbol': self.product_id (product),
        })

    def fetch_ticker (self, product):
        response = self.publicGetTicker ({
            'symbol': self.product_id (product),
        })
        ticker = response['ticker']
        timestamp = int (response['date']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTrades ({
            'symbol': self.product_id (product),
        })

    def fetch_balance (self):
        return self.privatePostUserinfo ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'symbol': self.product_id (product),
            'type': side,
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        else:
            order['type'] += '_market'
        return self.privatePostTrade (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/api/' + self.version + '/' + path + '.do'   
        if type == 'public':
            if params:
                url += '?' + _urlencode.urlencode (params)
        else:
            query = self.keysort (self.extend ({
                'api_key': self.apiKey,
            }, params))
            # secret key must be at the end of query
            queryString = _urlencode.urlencode (query) + '&secret_key=' + self.secret
            query['sign'] = self.hash (queryString).upper ()
            body = _urlencode.urlencode (query)
            headers = { 'Content-type': 'application/x-www-form-urlencoded' }
        url = self.urls['api'] + url
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class okcoincny (okcoin):

    def __init__ (self, config = {}):
        params = {
            'id': 'okcoincny',
            'name': 'OKCoin CNY',
            'countries': 'CN',
            'urls': {
                'api': 'https://www.okcoin.cn',
                'www': 'https://www.okcoin.cn',
                'doc': 'https://www.okcoin.cn/rest_getStarted.html',
            },
            'products': {
                'BTC/CNY': { 'id': 'btc_cny', 'symbol': 'BTC/CNY', 'base': 'BTC', 'quote': 'CNY' },
                'LTC/CNY': { 'id': 'ltc_cny', 'symbol': 'LTC/CNY', 'base': 'LTC', 'quote': 'CNY' },
            },
        }
        params.update (config)
        super (okcoincny, self).__init__ (params)

#------------------------------------------------------------------------------

class okcoinusd (okcoin):

    def __init__ (self, config = {}):
        params = {
            'id': 'okcoinusd',
            'name': 'OKCoin USD',
            'countries': [ 'CN', 'US' ],
            'urls': {
                'api': 'https://www.okcoin.com',
                'www': 'https://www.okcoin.com',
                'doc': [
                    'https://www.okcoin.com/rest_getStarted.html',
                    'https://www.npmjs.com/package/okcoin.com',
                ],
            },
            'products': {
                'BTC/USD': { 'id': 'btc_usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'LTC/USD': { 'id': 'ltc_usd', 'symbol': 'LTC/USD', 'base': 'LTC', 'quote': 'USD' },
            },
        }
        params.update (config)
        super (okcoinusd, self).__init__ (params)

#------------------------------------------------------------------------------

class poloniex (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'poloniex',
            'name': 'Poloniex',
            'countries': 'US',
            'rateLimit': 1000, # 6 calls per second
            'urls': {
                'api': {
                    'public': 'https://poloniex.com/public',
                    'private': 'https://poloniex.com/tradingApi',
                },
                'www': 'https://poloniex.com',
                'doc': [
                    'https://poloniex.com/support/api/',
                    'http://pastebin.com/dMX7mZE0',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'return24hVolume',
                        'returnChartData',
                        'returnCurrencies',
                        'returnLoanOrders',
                        'returnOrderBook',
                        'returnTicker',
                        'returnTradeHistory',
                    ],
                },
                'private': {
                    'post': [
                        'buy',
                        'cancelLoanOffer',
                        'cancelOrder',
                        'closeMarginPosition',
                        'createLoanOffer',
                        'generateNewAddress',
                        'getMarginPosition',
                        'marginBuy',
                        'marginSell',
                        'moveOrder',
                        'returnActiveLoans',
                        'returnAvailableAccountBalances',
                        'returnBalances',
                        'returnCompleteBalances',
                        'returnDepositAddresses',
                        'returnDepositsWithdrawals',
                        'returnFeeInfo',
                        'returnLendingHistory',
                        'returnMarginAccountSummary',
                        'returnOpenLoanOffers',
                        'returnOpenOrders',
                        'returnOrderTrades',
                        'returnTradableBalances',
                        'returnTradeHistory',
                        'sell',
                        'toggleAutoRenew',
                        'transferBalance',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (poloniex, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetReturnTicker ()
        keys = products.keys ()
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products[id]
            symbol = id.replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostReturnCompleteBalances ({
            'account': 'all',
        })

    def fetch_order_book (self, product):
        return self.publicGetReturnOrderBook ({
            'currencyPair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.publicGetReturnTicker ()
        ticker = tickers[p['id']]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high24hr']),
            'low': float (ticker['low24hr']),
            'bid': float (ticker['highestBid']),
            'ask': float (ticker['lowestAsk']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': float (ticker['percentChange']),
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['baseVolume']),
            'quoteVolume': float (ticker['quoteVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetReturnTradeHistory ({
            'currencyPair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side)
        return getattr (self, method) (self.extend ({
            'currencyPair': self.product_id (product),
            'rate': price,
            'amount': amount,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({
            'orderNumber': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        query = self.extend ({ 'command': path }, params)
        if type == 'public':
            url += '?' + _urlencode.urlencode (query)
        else:
            query['nonce'] = self.nonce ()
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class quadrigacx (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'quadrigacx',
            'name': 'QuadrigaCX',
            'countries': 'CA',
            'rateLimit': 2000,
            'version': 'v2',
            'urls': {
                'api': 'https://api.quadrigacx.com',
                'www': 'https://www.quadrigacx.com',
                'doc': 'https://www.quadrigacx.com/api_info',
            },
            'api': {
                'public': {
                    'get': [
                        'order_book',
                        'ticker',                
                        'transactions',
                    ],
                },
                'private': {
                    'post': [
                        'balance',
                        'bitcoin_deposit_address',
                        'bitcoin_withdrawal',
                        'buy',
                        'cancel_order',
                        'ether_deposit_address',
                        'ether_withdrawal',
                        'lookup_order',
                        'open_orders',
                        'sell',
                        'user_transactions',
                    ],
                },
            },
            'products': {
                'BTC/CAD': { 'id': 'btc_cad', 'symbol': 'BTC/CAD', 'base': 'BTC', 'quote': 'CAD' },
                'BTC/USD': { 'id': 'btc_usd', 'symbol': 'BTC/USD', 'base': 'BTC', 'quote': 'USD' },
                'ETH/BTC': { 'id': 'eth_btc', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC' },
                'ETH/CAD': { 'id': 'eth_cad', 'symbol': 'ETH/CAD', 'base': 'ETH', 'quote': 'CAD' },
            },
        }
        params.update (config)
        super (quadrigacx, self).__init__ (params)

    def fetch_balance (self):
        return self.privatePostBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderBook ({
            'book': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetTicker ({
            'book': self.product_id (product),
        })
        timestamp = int (ticker['timestamp']) * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactions ({
            'book': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        method = 'privatePost' + self.capitalize (side) 
        order = {
            'amount': amount,
            'book': self.product_id (product),
        }
        if type == 'limit':
            order['price'] = price
        return getattr (self, method) (self.extend (order, params))

    def cancel_order (self, id, params = {}):
        return self.privatePostCancelOrder (self.extend ({ id }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if type == 'public':
            url += '?' + _urlencode.urlencode (params)
        else:
            nonce = self.nonce ()
            request = ''.join ([ nonce, self.uid, self.apiKey ])
            signature = self.hmac (request, self.secret)
            query = self.extend ({ 
                'key': self.apiKey,
                'nonce': nonce,
                'signature': signature,
            }, params)
            body = json.dumps (query)
            headers = {
                'Content-Type': 'application/json',
                'Content-Length': len (body),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class quoine (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'quoine',
            'name': 'QUOINE',
            'countries': [ 'JP', 'SG', 'VN' ],
            'version': '2',
            'rateLimit': 2000,
            'urls': {
                'api': 'https://api.quoine.com',
                'www': 'https://www.quoine.com',
                'doc': 'https://developers.quoine.com',
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
                        'crypto_accounts',
                        'executions/me',
                        'fiat_accounts',
                        'loan_bids',
                        'loans',
                        'orders',
                        'orders/{id}',
                        'orders/{id}/trades',
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
        }
        params.update (config)
        super (quoine, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetProducts ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['id']
            base = product['base_currency']
            quote = product['quoted_currency']
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetAccountsBalance ()

    def fetch_order_book (self, product):
        return self.publicGetProductsIdPriceLevels ({
            'id': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetProductsId ({
            'id': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high_market_ask']),
            'low': float (ticker['low_market_bid']),
            'bid': float (ticker['market_bid']),
            'ask': float (ticker['market_ask']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last_traded_price']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume_24h']),
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetExecutions ({
            'product_id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'order_type': type,
            'product_id': self.product_id (product),
            'side': side,
            'quantity': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostOrders (self.extend ({
            'order': order,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.privatePutOrdersIdCancel (self.extend ({
            'id': id,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        headers = {
            'X-Quoine-API-Version': self.version,
            'Content-type': 'application/json',
        }
        if type == 'public':
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            request = {
                'path': url, 
                'nonce': nonce, 
                'token_id': self.apiKey,
                'iat': int (math.floor (nonce / 1000)), # issued at
            }
            if query:
                body = json.dumps (query)
            headers['X-Quoine-Auth'] = self.jwt (request, self.secret)
        return self.fetch (self.urls['api'] + url, method, headers, body)

#------------------------------------------------------------------------------

class therock (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'therock',
            'name': 'TheRockTrading',
            'countries': 'MT',
            'rateLimit': 1000,
            'version': 'v1',
            'urls': {
                'api': 'https://api.therocktrading.com',
                'www': 'https://therocktrading.com',
                'doc': 'https://api.therocktrading.com/doc/',
            },
            'api': {
                'public': {
                    'get': [
                        'funds/{id}/orderbook',
                        'funds/{id}/ticker',
                        'funds/{id}/trades',
                        'funds/tickers',
                    ],
                },
                'private': {
                    'get': [
                        'balances',
                        'balances/{id}',
                        'discounts',
                        'discounts/{id}',
                        'funds',
                        'funds/{id}',
                        'funds/{id}/trades',
                        'funds/{fund_id}/orders',
                        'funds/{fund_id}/orders/{id}',                
                        'funds/{fund_id}/position_balances',
                        'funds/{fund_id}/positions',
                        'funds/{fund_id}/positions/{id}',
                        'transactions',
                        'transactions/{id}',
                        'withdraw_limits/{id}',
                        'withdraw_limits',
                    ],
                    'post': [
                        'atms/withdraw',
                        'funds/{fund_id}/orders',
                    ],
                    'delete': [
                        'funds/{fund_id}/orders/{id}',
                        'funds/{fund_id}/orders/remove_all',
                    ],
                },
            },
        }
        params.update (config)
        super (therock, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetFundsTickers ()
        result = []
        for p in range (0, len (products['tickers'])):
            product = products['tickers'][p]
            id = product['fund_id']
            base = id[0:3]
            quote = id[3:6]
            symbol = base + '/' + quote
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privateGetBalances ()

    def fetch_order_book (self, product):
        return self.publicGetFundsIdOrderbook ({
            'id': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.publicGetFundsIdTicker ({
            'id': self.product_id (product),
        })
        timestamp = self.parse8601 (ticker['date'])
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': None,
            'open': float (ticker['open']),
            'close': float (ticker['close']),
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['volume_traded']),
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetFundsIdTrades ({
            'id': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.privatePostFundsFundIdOrders (self.extend ({
            'fund_id': self.product_id (product),
            'side': side,
            'amount': amount,
            'price': price,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + self.version + '/' + self.implode_params (path, params)
        query = self.omit (params, self.extract_params (path))
        if type == 'private':
            nonce = self.nonce ().toString ()
            headers = {
                'X-TRT-KEY': self.apiKey,
                'X-TRT-NONCE': nonce,
                'X-TRT-SIGN': self.hmac (nonce + url, self.secret, hashlib.sha512),
            }
            if query:
                body = json.dumps (query)
                headers['Content-Type'] = 'application/json'
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class vaultoro (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'vaultoro',
            'name': 'Vaultoro',
            'countries': 'CH',
            'rateLimit': 1000,
            'version': '1',
            'urls': {
                'api': 'https://api.vaultoro.com',
                'www': 'https://www.vaultoro.com',
                'doc': 'https://api.vaultoro.com',
            },
            'api': {
                'public': {
                    'get': [
                        'bidandask',
                        'buyorders',
                        'latest',
                        'latesttrades',
                        'markets',
                        'orderbook',
                        'sellorders',
                        'transactions/day',
                        'transactions/hour',
                        'transactions/month',
                    ],
                },
                'private': {
                    'get': [
                        'balance',
                        'mytrades',
                        'orders',
                    ],
                    'post': [
                        'buy/{symbol}/{type}',
                        'cancel/{orderid',
                        'sell/{symbol}/{type}',
                        'withdraw',
                    ],
                },
            },
        }
        params.update (config)
        super (vaultoro, self).__init__ (params)

    def fetch_products (self):
        result = []
        products = self.publicGetMarkets ()
        product = products['data']
        base = product['BaseCurrency']
        quote = product['MarketCurrency']
        symbol = base + '/' + quote
        baseId = base
        quoteId = quote
        id = product['MarketName']
        result.append ({
            'id': id,
            'symbol': symbol,
            'base': base,
            'quote': quote,
            'baseId': baseId,
            'quoteId': quoteId,
            'info': product,
        })
        return result

    def fetch_balance (self):
        return self.privateGetBalance ()

    def fetch_order_book (self, product):
        return self.publicGetOrderbook ()

    def fetch_ticker (self, product):
        quote = self.publicGetBidandask ()
        bidsLength = len (quote['bids'])
        bid = quote['bids'][bidsLength - 1]
        ask = quote['asks'][0]
        response = self.publicGetMarkets ()
        ticker = response['data']
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['24hHigh']),
            'low': float (ticker['24hLow']),
            'bid': bid[0],
            'ask': ask[0],
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['lastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['24hVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetTransactionsDay ()

    def create_order (self, product, type, side, amount, price = None, params = {}):
        p = self.product (product)
        method = 'privatePost' + self.capitalize (side) + 'SymbolType'
        return getattr (self, method) (self.extend ({
            'symbol': p['quoteId'].lower (),
            'type': type,
            'gld': amount,
            'price': price or 1,
        }, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/'
        if type == 'public':
            url += path
        else:
            nonce = self.nonce ()
            url += self.version + '/' + self.implode_params (path, params)
            query = self.extend ({
                'nonce': nonce,
                'apikey': self.apiKey,
            }, self.omit (params, self.extract_params (path)))
            url += '?' + _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/json',
                'X-Signature': self.hmac (url, self.secret)
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class virwox (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'virwox',
            'name': 'VirWoX',
            'countries': 'AT',
            'rateLimit': 1000,
            'urls': {
                'api': {
                    'public': 'http://api.virwox.com/api/json.php',
                    'private': 'https://www.virwox.com/api/trading.php',
                },
                'www': 'https://www.virwox.com',
                'doc': 'https://www.virwox.com/developers.php',
            },
            'api': {
                'public': {
                    'get': [
                        'getInstruments',
                        'getBestPrices',
                        'getMarketDepth',
                        'estimateMarketOrder',
                        'getTradedPriceVolume',
                        'getRawTradeData',
                        'getStatistics',
                        'getTerminalList',
                        'getGridList',
                        'getGridStatistics',
                    ],
                    'post': [
                        'getInstruments',
                        'getBestPrices',
                        'getMarketDepth',
                        'estimateMarketOrder',
                        'getTradedPriceVolume',
                        'getRawTradeData',
                        'getStatistics',
                        'getTerminalList',
                        'getGridList',
                        'getGridStatistics',
                    ],
                },
                'private': {
                    'get': [
                        'cancelOrder',
                        'getBalances',
                        'getCommissionDiscount',
                        'getOrders',
                        'getTransactions',
                        'placeOrder',
                    ],
                    'post': [
                        'cancelOrder',
                        'getBalances',
                        'getCommissionDiscount',
                        'getOrders',
                        'getTransactions',
                        'placeOrder',
                    ],
                },
            },
        }
        params.update (config)
        super (virwox, self).__init__ (params)

    def fetch_products (self):
        products = self.publicGetInstruments ()
        keys = products['result'].keys ()
        result = []
        for p in range (0, len (keys)):
            product = products['result'][keys[p]]
            id = product['instrumentID']
            symbol = product['symbol']
            base = product['longCurrency']
            quote = product['shortCurrency']
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.privatePostGetBalances ()

    def fetchBestPrices (self, product):
        return self.publicPostGetBestPrices ({
            'symbols': [ self.symbol (product) ],
        })

    def fetch_order_book (self, product):
        return self.publicPostGetMarketDepth ({
            'symbols': [ self.symbol (product) ],
            'buyDepth': 100,
            'sellDepth': 100,
        })

    def fetch_ticker (self, product):
        end = self.milliseconds ()
        start = end - 86400000
        response = self.publicGetTradedPriceVolume ({
            'instrument': self.symbol (product),
            'endDate': self.yyyymmddhhmmss (end),
            'startDate': self.yyyymmddhhmmss (start),
            'HLOC': 1,
        })
        tickers = response['result']['priceVolumeList']
        keys = tickers.keys ()
        length = len (keys)
        lastKey = keys[length - 1]
        ticker = tickers[lastKey]
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': None,
            'ask': None,
            'vwap': None,
            'open': float (ticker['open']),
            'close': float (ticker['close']),
            'first': None,
            'last': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float (ticker['longVolume']),
            'quoteVolume': float (ticker['shortVolume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.publicGetRawTradeData ({
            'instrument': self.symbol (product),
            'timespan': 3600,
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        order = {
            'instrument': self.symbol (product),
            'orderType': side.upper (),
            'amount': amount,
        }
        if type == 'limit':
            order['price'] = price
        return self.privatePostPlaceOrder (self.extend (order, params))

    def request (self, path, type = 'public', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'][type]
        auth = {}
        if type == 'public':
            auth['key'] = self.apiKey
            auth['user'] = self.login
            auth['pass'] = self.password
        nonce = self.nonce ()
        if method == 'GET':
            url += '?' + _urlencode.urlencode (self.extend ({ 
                'method': path, 
                'id': nonce,
            }, auth, params))
        else:
            headers = { 'Content-type': 'application/json' }
            body = json.dumps ({ 
                'method': path, 
                'params': self.extend (auth, params),
                'id': nonce,
            })
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class yobit (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'yobit',
            'name': 'YoBit',
            'countries': 'RU',
            'rateLimit': 2000, # responses are cached every 2 seconds
            'version': '3',
            'urls': {
                'api': 'https://yobit.net',
                'www': 'https://www.yobit.net',
                'doc': 'https://www.yobit.net/en/api/',
            },
            'api': {
                'api': {
                    'get': [
                        'depth/{pairs}',
                        'info',
                        'ticker/{pairs}',
                        'trades/{pairs}',
                    ],
                },
                'tapi': {
                    'post': [
                        'ActiveOrders',
                        'CancelOrder',
                        'GetDepositAddress',
                        'getInfo',
                        'OrderInfo',
                        'Trade',                
                        'TradeHistory',
                        'WithdrawCoinsToAddress',
                    ],
                },
            },
        }
        params.update (config)
        super (yobit, self).__init__ (params)

    def fetch_products (self):
        products = self.apiGetInfo ()
        keys = products['pairs'].keys ()
        result = []
        for p in range (0, len (keys)):
            id = keys[p]
            product = products['pairs'][id]
            symbol = id.upper ().replace ('_', '/')
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tapiPostGetInfo ()

    def fetch_order_book (self, product):
        return self.apiGetDepthPairs ({
            'pairs': self.product_id (product),
        })

    def fetch_ticker (self, product):
        p = self.product (product)
        tickers = self.apiGetTickerPairs ({
            'pairs': p['id'],
        })
        ticker = tickers[p['id']]
        timestamp = ticker['updated'] * 1000
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['buy']),
            'ask': float (ticker['sell']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': float (ticker['avg']),
            'baseVolume': float (ticker['vol_cur']),
            'quoteVolume': float (ticker['vol']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.apiGetTradesPairs ({
            'pairs': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.tapiPostTrade (self.extend ({
            'pair': self.product_id (product),
            'type': side,
            'amount': amount,
            'rate': price,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.tapiPostCancelOrder (self.extend ({
            'order_id': id,
        }, params))

    def request (self, path, type = 'api', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + type
        if type == 'api':
            url += '/' + self.version + '/' + self.implode_params (path, params)
            query = self.omit (params, self.extract_params (path))
            if query:
                url += '?' + _urlencode.urlencode (query)
        else:
            nonce = self.nonce ()
            query = self.extend ({ 'method': path, 'nonce': nonce }, params)
            body = _urlencode.urlencode (query)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'key': self.apiKey,
                'sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)

#------------------------------------------------------------------------------

class zaif (Market):

    def __init__ (self, config = {}):
        params = {
            'id': 'zaif',
            'name': 'Zaif',
            'countries': 'JP',
            'rateLimit': 3000,
            'version': '1',
            'urls': {
                'api': 'https://api.zaif.jp',
                'www': 'https://zaif.jp',
                'doc': [
                    'https://corp.zaif.jp/api-docs',
                    'https://corp.zaif.jp/api-docs/api_links',
                    'https://www.npmjs.com/package/zaif.jp',
                    'https://github.com/you21979/node-zaif',
                ],
            },
            'api': {
                'api': {
                    'get': [
                        'depth/{pair}',
                        'currencies/{pair}',
                        'currencies/all',
                        'currency_pairs/{pair}',
                        'currency_pairs/all',
                        'last_price/{pair}',
                        'ticker/{pair}',
                        'trades/{pair}',
                    ],
                },
                'tapi': {
                    'post': [
                        'active_orders',
                        'cancel_order',
                        'deposit_history',
                        'get_id_info',
                        'get_info',
                        'get_info2',
                        'get_personal_info',
                        'trade',
                        'trade_history',
                        'withdraw',
                        'withdraw_history',
                    ],
                },
                'ecapi': {
                    'post': [
                        'createInvoice',
                        'getInvoice',
                        'getInvoiceIdsByOrderNumber',
                        'cancelInvoice',
                    ],
                },
            },
        }
        params.update (config)
        super (zaif, self).__init__ (params)

    def fetch_products (self):
        products = self.apiGetCurrencyPairsAll ()
        result = []
        for p in range (0, len (products)):
            product = products[p]
            id = product['currency_pair']
            symbol = product['name']
            base, quote = symbol.split ('/')
            result.append ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': product,
            })
        return result

    def fetch_balance (self):
        return self.tapiPostGetInfo ()

    def fetch_order_book (self, product):
        return self.apiGetDepthPair  ({
            'pair': self.product_id (product),
        })

    def fetch_ticker (self, product):
        ticker = self.apiGetTickerPair ({
            'pair': self.product_id (product),
        })
        timestamp = self.milliseconds ()
        return {
            'timestamp': timestamp,
            'datetime': self.iso8601 (timestamp),
            'high': float (ticker['high']),
            'low': float (ticker['low']),
            'bid': float (ticker['bid']),
            'ask': float (ticker['ask']),
            'vwap': float (ticker['vwap']),
            'open': None,
            'close': None,
            'first': None,
            'last': float (ticker['last']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': None,
            'quoteVolume': float (ticker['volume']),
            'info': ticker,
        }

    def fetch_trades (self, product):
        return self.apiGetTradesPair ({
            'pair': self.product_id (product),
        })

    def create_order (self, product, type, side, amount, price = None, params = {}):
        if type == 'market':
            raise Exception (self.id + ' allows limit orders only')
        return self.tapiPostTrade (self.extend ({
            'currency_pair': self.product_id (product),
            'action': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
            'price': price,
        }, params))

    def cancel_order (self, id, params = {}):
        return self.tapiPostCancelOrder (self.extend ({
            'order_id': id,
        }, params))

    def request (self, path, type = 'api', method = 'GET', params = {}, headers = None, body = None):
        url = self.urls['api'] + '/' + type
        if type == 'api':
            url += '/' + self.version + '/' + self.implode_params (path, params)
        else:
            nonce = self.nonce ()
            body = _urlencode.urlencode (self.extend ({
                'method': path,
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': len (body),
                'Key': self.apiKey,
                'Sign': self.hmac (body, self.secret, hashlib.sha512),
            }
        return self.fetch (url, method, headers, body)
