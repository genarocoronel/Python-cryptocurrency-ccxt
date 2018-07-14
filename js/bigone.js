'use strict';

//  ---------------------------------------------------------------------------

const Exchange = require ('./base/Exchange');
const { ExchangeError, AuthenticationError } = require ('./base/errors');

//  ---------------------------------------------------------------------------

module.exports = class bigone extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'bigone',
            'name': 'BigONE',
            'countries': 'GB',
            'version': 'v2',
            'has': {
                'fetchTickers': true,
                'fetchOpenOrders': true,
                'fetchMyTrades': true,
                'fetchDepositAddress': true,
                'withdraw': true,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/42704835-0e48c7aa-86da-11e8-8e91-a4d1024a91b5.jpg',
                'api': 'https://big.one/api/v2/',
                'www': 'https://big.one',
                'doc': 'https://open.big.one/docs/api.html',
                'fees': 'https://help.big.one/hc/en-us/articles/115001933374-BigONE-Fee-Policy',
                'referral': 'https://b1.run/users/new?code=D3LLBVFT',
            },
            'api': {
                'public': {
                    'get': [
                        'markets',
                        // 'markets/{symbol}',
                        'markets/{symbol}/book',
                        'markets/{symbol}/trades',
                        'markets/{symbol}/ticker',
                        'orders',
                        'orders/{id}',
                        'tickers',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/{currency}',
                        'withdrawals',
                        'deposits',
                    ],
                    'post': [
                        'orders',
                        'orders/cancel',
                        'withdrawals',
                    ],
                    'delete': [
                        'orders/{id}',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'maker': 0.1 / 100,
                    'taker': 0.1 / 100,
                },
                'funding': {
                    // HARDCODING IS DEPRECATED THE FEES BELOW ARE TO BE REMOVED SOON
                    'withdraw': {
                        'BTC': 0.002,
                        'ETH': 0.01,
                        'EOS': 0.01,
                        'ZEC': 0.002,
                        'LTC': 0.01,
                        'QTUM': 0.01,
                        // 'INK': 0.01 QTUM,
                        // 'BOT': 0.01 QTUM,
                        'ETC': 0.01,
                        'GAS': 0.0,
                        'BTS': 1.0,
                        'GXS': 0.1,
                        'BITCNY': 1.0,
                    },
                },
            },
        });
    }

    async fetchMarkets () {
        let response = await this.publicGetMarkets ();
        let markets = response['data'];
        let result = [];
        for (let i = 0; i < markets.length; i++) {
            //
            //      {       uuid:   "550b34db-696e-4434-a126-196f827d9172",
            //        quoteScale:    3,
            //        quoteAsset: {   uuid: "17082d1c-0195-4fb6-8779-2cdbcb9eeb3c",
            //                      symbol: "USDT",
            //                        name: "TetherUS"                              },
            //              name:   "BTC-USDT",
            //         baseScale:    5,
            //         baseAsset: {   uuid: "0df9c3c3-255a-46d7-ab82-dedae169fba9",
            //                      symbol: "BTC",
            //                        name: "Bitcoin"                               }  } }
            //
            let market = markets[i];
            let id = market['name'];
            let baseId = market['baseAsset']['symbol'];
            let quoteId = market['quoteAsset']['symbol'];
            let base = this.commonCurrencyCode (baseId);
            let quote = this.commonCurrencyCode (quoteId);
            let symbol = base + '/' + quote;
            let precision = {
                'amount': market['baseScale'],
                'price': market['quoteScale'],
            };
            result.push ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': true,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': Math.pow (10, -precision['amount']),
                        'max': Math.pow (10, precision['amount']),
                    },
                    'price': {
                        'min': Math.pow (10, -precision['price']),
                        'max': Math.pow (10, precision['price']),
                    },
                    'cost': {
                        'min': undefined,
                        'max': undefined,
                    },
                },
                'info': market,
            });
        }
        return result;
    }

    parseTicker (ticker, market = undefined) {
        //
        //     [
        //         {
        //             "volume": "190.4925000000000000",
        //             "open": "0.0777371200000000",
        //             "market_uuid": "38dd30bf-76c2-4777-ae2a-a3222433eef3",
        //             "market_id": "ETH-BTC",
        //             "low": "0.0742925600000000",
        //             "high": "0.0789150000000000",
        //             "daily_change_perc": "-0.3789180767180466680525339760",
        //             "daily_change": "-0.0002945600000000",
        //             "close": "0.0774425600000000", // last price
        //             "bid": {
        //                 "price": "0.0764777900000000",
        //                 "amount": "6.4248000000000000"
        //             },
        //             "ask": {
        //                 "price": "0.0774425600000000",
        //                 "amount": "1.1741000000000000"
        //             }
        //         }
        //     ]
        //
        if (typeof market === 'undefined') {
            let marketId = this.safeString (ticker, 'market_id');
            if (marketId in this.markets_by_id) {
                market = this.markets_by_id[marketId];
            }
        }
        let symbol = undefined;
        if (typeof market !== 'undefined') {
            symbol = market['symbol'];
        }
        let timestamp = this.milliseconds ();
        let close = this.safeFloat (ticker, 'close');
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'high': this.safeFloat (ticker, 'high'),
            'low': this.safeFloat (ticker, 'low'),
            'bid': this.safeFloat (ticker['bid'], 'price'),
            'bidVolume': this.safeFloat (ticker['bid'], 'amount'),
            'ask': this.safeFloat (ticker['ask'], 'price'),
            'askVolume': this.safeFloat (ticker['ask'], 'amount'),
            'vwap': undefined,
            'open': this.safeFloat (ticker, 'open'),
            'close': close,
            'last': close,
            'previousDayClose': undefined,
            'change': this.safeFloat (ticker, 'daily_change'),
            'percentage': this.safeFloat (ticker, 'daily_change_perc'),
            'average': undefined,
            'baseVolume': this.safeFloat (ticker, 'volume'),
            'quoteVolume': undefined,
            'info': ticker,
        };
    }

    async fetchTicker (symbol, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.publicGetMarketsSymbolTicker (this.extend ({
            'symbol': market['id'],
        }, params));
        return this.parseTicker (response['data'], market);
    }

    async fetchTickers (symbols = undefined, params = {}) {
        await this.loadMarkets ();
        let response = await this.publicGetTickers (params);
        let tickers = response['data'];
        let result = {};
        for (let i = 0; i < tickers.length; i++) {
            let ticker = this.parseTicker (tickers[i]);
            let symbol = ticker['symbol'];
            result[symbol] = ticker;
        }
        return result;
    }

    async fetchOrderBook (symbol, params = {}) {
        await this.loadMarkets ();
        let response = await this.publicGetMarketsSymbolBook (this.extend ({
            'symbol': this.marketId (symbol),
        }, params));
        return this.parseOrderBook (response['data'], undefined, 'bids', 'asks', 'price', 'amount');
    }

    parseTrade (trade, market = undefined) {
        let timestamp = this.parse8601 (trade['created_at']);
        let price = parseFloat (trade['price']);
        let amount = parseFloat (trade['amount']);
        let symbol = market['symbol'];
        let cost = this.costToPrecision (symbol, price * amount);
        let side = trade['trade_side'] === 'ASK' ? 'sell' : 'buy';
        return {
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': symbol,
            'id': this.safeString (trade, 'trade_id'),
            'order': undefined,
            'type': 'limit',
            'side': side,
            'price': price,
            'amount': amount,
            'cost': parseFloat (cost),
            'fee': undefined,
            'info': trade,
        };
    }

    async fetchTrades (symbol, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.publicGetMarketsSymbolTrades (this.extend ({
            'symbol': market['id'],
        }, params));
        return this.parseTrades (response['data'], market, since, limit);
    }

    async fetchBalance (params = {}) {
        await this.loadMarkets ();
        let response = await this.privateGetAccounts (params);
        let result = { 'info': response };
        let balances = response['data'];
        for (let i = 0; i < balances.length; i++) {
            let balance = balances[i];
            let id = balance['account_type'];
            let currency = this.commonCurrencyCode (id);
            let account = {
                'free': parseFloat (balance['active_balance']),
                'used': parseFloat (balance['frozen_balance']),
                'total': 0.0,
            };
            account['total'] = this.sum (account['free'], account['used']);
            result[currency] = account;
        }
        return this.parseBalance (result);
    }

    parseOrder (order, market = undefined) {
        let marketId = this.safeString (order, 'order_market');
        let symbol = undefined;
        if (marketId && !market && (marketId in this.marketsById)) {
            market = this.marketsById[marketId];
        }
        if (market)
            symbol = market['symbol'];
        let timestamp = this.parse8601 (order['created_at']);
        let price = parseFloat (order['price']);
        let amount = this.safeFloat (order, 'amount');
        let filled = this.safeFloat (order, 'filled_amount');
        let remaining = amount - filled;
        let status = this.safeString (order, 'order_state');
        if (status === 'filled') {
            status = 'closed';
        }
        let side = this.safeInteger (order, 'order_side');
        if (side === 'BID') {
            side = 'buy';
        } else {
            side = 'sell';
        }
        return {
            'id': this.safeString (order, 'order_id'),
            'datetime': this.iso8601 (timestamp),
            'timestamp': timestamp,
            'status': status,
            'symbol': symbol,
            'type': order['order_type'].toLowerCase (),
            'side': side,
            'price': price,
            'cost': undefined,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'trades': undefined,
            'fee': undefined,
            'info': order,
        };
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.privatePostOrders (this.extend ({
            'order_market': market['id'],
            'order_side': (side === 'buy' ? 'BID' : 'ASK'),
            'amount': amount,
            'price': price,
        }, params));
        // TODO: what's the actual response here
        return response['data'];
    }

    async cancelOrder (id, symbol = undefined, params = {}) {
        let response = await this.privateDeleteOrdersId (this.extend ({
            'id': id,
        }, params));
        return response;
    }

    async fetchOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let response = await this.privateGetOrdersId (this.extend ({
            'id': id,
        }, params));
        return this.parseOrder (response['data']);
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        // TODO: check if it's for open orders only
        let request = {
            'market': market['id'],
        };
        if (limit)
            request['limit'] = limit;
        let response = await this.privateGetOrders (this.extend (request, params));
        return this.parseOrders (response['data'], market, since, limit);
    }

    async fetchMyTrades (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'market': market['id'],
        };
        if (limit) {
            request['limit'] = limit;
        }
        let response = await this.privateGetTrades (this.extend (request, params));
        let trades = response['data']['trade_history'];
        return this.parseTrades (trades, market, since, limit);
    }

    async fetchDepositAddress (code, params = {}) {
        await this.loadMarkets ();
        let currency = this.currency (code);
        let response = await this.privateGetAccountsCurrency (this.extend ({
            'currency': currency['id'],
        }, params));
        let address = this.safeString (response['data'], 'public_key');
        let status = address ? 'ok' : 'none';
        return {
            'currency': code,
            'address': address,
            'status': status,
            'info': response,
        };
    }

    async withdraw (code, amount, address, tag = undefined, params = {}) {
        await this.loadMarkets ();
        let currency = this.currency (code);
        let request = {
            'withdrawal_type': currency['id'],
            'address': address,
            'amount': amount,
            // 'fee': 0.0,
            // 'asset_pin': 'YOUR_ASSET_PIN',
        };
        if (tag) {
            // probably it's not the same
            request['label'] = tag;
        }
        let response = await this.privatePostWithdrawals (this.extend (request, params));
        return {
            'id': undefined,
            'info': response,
        };
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let query = this.omit (params, this.extractParams (path));
        let url = this.urls['api'] + '/' + this.implodeParams (path, params);
        if (api === 'public') {
            if (Object.keys (query).length)
                url += '?' + this.urlencode (query);
        } else {
            this.checkRequiredCredentials ();
            headers = {
                'Authorization': 'Bearer ' + this.secret,
                'Big-Device-Id': this.apiKey,
            };
            if (method === 'GET') {
                if (Object.keys (query).length)
                    url += '?' + this.urlencode (query);
            } else if (method === 'POST') {
                headers['Content-Type'] = 'application/json';
                body = this.json (query);
            }
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    async request (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let response = await this.fetch2 (path, api, method, params, headers, body);
        let error = this.safeValue (response, 'error');
        let data = this.safeValue (response, 'data');
        if (error || !data) {
            let code = this.safeInteger (error, 'code');
            let errorClasses = {
                '401': AuthenticationError,
            };
            let message = this.safeString (error, 'description', 'Error');
            let ErrorClass = this.safeString (errorClasses, code, ExchangeError);
            throw new ErrorClass (message);
        }
        return response;
    }
};
