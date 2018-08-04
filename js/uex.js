'use strict';

//  ---------------------------------------------------------------------------

const Exchange = require ('./base/Exchange');
const { ExchangeError, ExchangeNotAvailable, AuthenticationError, InvalidOrder, InsufficientFunds, OrderNotFound, DDoSProtection, PermissionDenied, AddressPending } = require ('./base/errors');

//  ---------------------------------------------------------------------------

module.exports = class bittrex extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'uex',
            'name': 'UEX',
            'countries': [ 'SG', 'US' ],
            'version': 'v1.0.3',
            'rateLimit': 1500,
            'certified': true,
            // new metainfo interface
            'has': {
                'CORS': true,
                'createMarketOrder': false,
                'fetchDepositAddress': true,
                'fetchClosedOrders': true,
                'fetchMyTrades': false,
                'fetchOHLCV': true,
                'fetchOrder': true,
                'fetchOpenOrders': true,
                'fetchTickers': true,
                'withdraw': true,
            },
            'timeframes': {
                '1m': 'oneMin',
                '5m': 'fiveMin',
                '30m': 'thirtyMin',
                '1h': 'hour',
                '1d': 'day',
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766352-cf0b3c26-5ed5-11e7-82b7-f3826b7a97d8.jpg',
                'api': 'https://open-api.uex.com/open/api',
                'www': 'https://www.uex.com',
                'doc': 'https://download.uex.com/doc/UEX-API-English-1.0.3.pdf',
                'fees': 'https://www.uex.com/footer/ufees.html',
                'referral': 'https://www.uex.com/signup.html?code=VAGQLL',
            },
            'api': {
                'public': {
                    'get': [
                        'common/symbols',
                        'get_records', // ohlcvs
                        'get_ticker',
                        'get_trades',
                        'market_dept',
                    ],
                },
                'private': {
                    'get': [
                        'user/account',
                        'market', // Docs: Get the latest transaction price of each currency pair (??)
                        'order_info',
                        'new_order', // open orders
                        'all_order',
                        'all_trade',
                    ],
                    'post': [
                        'create_order',
                        'cancel_order',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': false,
                    'percentage': true,
                    'maker': 0.0025,
                    'taker': 0.0025,
                },
                'funding': {
                    'tierBased': false,
                    'percentage': false,
                    'withdraw': {
                        'BTC': 0.001,
                        'LTC': 0.01,
                        'DOGE': 2,
                        'VTC': 0.02,
                        'PPC': 0.02,
                        'FTC': 0.2,
                        'RDD': 2,
                        'NXT': 2,
                        'DASH': 0.002,
                        'POT': 0.002,
                    },
                    'deposit': {
                        'BTC': 0,
                        'LTC': 0,
                        'DOGE': 0,
                        'VTC': 0,
                        'PPC': 0,
                        'FTC': 0,
                        'RDD': 0,
                        'NXT': 0,
                        'DASH': 0,
                        'POT': 0,
                    },
                },
            },
            'exceptions': {
                // // 'Call to Cancel was throttled. Try again in 60 seconds.': DDoSProtection,
                // // 'Call to GetBalances was throttled. Try again in 60 seconds.': DDoSProtection,
                // 'APISIGN_NOT_PROVIDED': AuthenticationError,
                // 'INVALID_SIGNATURE': AuthenticationError,
                // 'INVALID_CURRENCY': ExchangeError,
                // 'INVALID_PERMISSION': AuthenticationError,
                // 'INSUFFICIENT_FUNDS': InsufficientFunds,
                // 'QUANTITY_NOT_PROVIDED': InvalidOrder,
                // 'MIN_TRADE_REQUIREMENT_NOT_MET': InvalidOrder,
                // 'ORDER_NOT_OPEN': OrderNotFound,
                // 'INVALID_ORDER': InvalidOrder,
                // 'UUID_INVALID': OrderNotFound,
                // 'RATE_NOT_PROVIDED': InvalidOrder, // createLimitBuyOrder ('ETH/BTC', 1, 0)
                // 'WHITELIST_VIOLATION_IP': PermissionDenied,
            },
        });
    }

    async fetchMarkets () {
        let response = await this.publicGetCommonSymbols ();
        //
        //     { code:   "0",
        //        msg:   "suc",
        //       data: [ {           symbol: "btcusdt",
        //                       count_coin: "usdt",
        //                 amount_precision:  3,
        //                        base_coin: "btc",
        //                  price_precision:  2         },
        //               {           symbol: "ethusdt",
        //                       count_coin: "usdt",
        //                 amount_precision:  3,
        //                        base_coin: "eth",
        //                  price_precision:  2         },
        //               {           symbol: "ethbtc",
        //                       count_coin: "btc",
        //                 amount_precision:  3,
        //                        base_coin: "eth",
        //                  price_precision:  6        },
        //
        let result = [];
        let markets = response['data'];
        for (let i = 0; i < markets.length; i++) {
            let market = markets[i];
            let id = market['symbol'];
            let baseId = market['base_coin'];
            let quoteId = market['count_coin'];
            let base = baseId.toUpperCase ();
            let quote = quoteId.toUpperCase ();
            base = this.commonCurrencyCode (base);
            quote = this.commonCurrencyCode (quote);
            let symbol = base + '/' + quote;
            let precision = {
                'amount': market['amount_precision'],
                'price': market['price_precision'],
            };
            let active = true;
            result.push ({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'info': market,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': undefined,
                        'max': undefined,
                    },
                    'price': {
                        'min': undefined,
                        'max': undefined,
                    },
                    'cost': {
                        'min': undefined,
                        'max': undefined,
                    },
                },
            });
        }
        return result;
    }

    async fetchBalance (params = {}) {
        await this.loadMarkets ();
        let response = await this.privateGetUserAccount (params);
        let log = require ('ololog').unlimited;
        log (response);
        process.exit ();
        let balances = response['result'];
        let result = { 'info': balances };
        let indexed = this.indexBy (balances, 'Currency');
        let keys = Object.keys (indexed);
        for (let i = 0; i < keys.length; i++) {
            let id = keys[i];
            let currency = this.commonCurrencyCode (id);
            let account = this.account ();
            let balance = indexed[id];
            let free = parseFloat (balance['Available']);
            let total = parseFloat (balance['Balance']);
            let used = total - free;
            account['free'] = free;
            account['used'] = used;
            account['total'] = total;
            result[currency] = account;
        }
        return this.parseBalance (result);
    }

    async fetchOrderBook (symbol, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let response = await this.publicGetOrderbook (this.extend ({
            'market': this.marketId (symbol),
            'type': 'both',
        }, params));
        let orderbook = response['result'];
        if ('type' in params) {
            if (params['type'] === 'buy') {
                orderbook = {
                    'buy': response['result'],
                    'sell': [],
                };
            } else if (params['type'] === 'sell') {
                orderbook = {
                    'buy': [],
                    'sell': response['result'],
                };
            }
        }
        return this.parseOrderBook (orderbook, undefined, 'buy', 'sell', 'Rate', 'Quantity');
    }

    parseTicker (ticker, market = undefined) {
        let timestamp = this.safeString (ticker, 'TimeStamp');
        let iso8601 = undefined;
        if (typeof timestamp === 'string') {
            if (timestamp.length > 0) {
                timestamp = this.parse8601 (timestamp);
                iso8601 = this.iso8601 (timestamp);
            }
        }
        let symbol = undefined;
        if (market)
            symbol = market['symbol'];
        let previous = this.safeFloat (ticker, 'PrevDay');
        let last = this.safeFloat (ticker, 'Last');
        let change = undefined;
        let percentage = undefined;
        if (typeof last !== 'undefined')
            if (typeof previous !== 'undefined') {
                change = last - previous;
                if (previous > 0)
                    percentage = (change / previous) * 100;
            }
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': iso8601,
            'high': this.safeFloat (ticker, 'High'),
            'low': this.safeFloat (ticker, 'Low'),
            'bid': this.safeFloat (ticker, 'Bid'),
            'bidVolume': undefined,
            'ask': this.safeFloat (ticker, 'Ask'),
            'askVolume': undefined,
            'vwap': undefined,
            'open': previous,
            'close': last,
            'last': last,
            'previousClose': undefined,
            'change': change,
            'percentage': percentage,
            'average': undefined,
            'baseVolume': this.safeFloat (ticker, 'Volume'),
            'quoteVolume': this.safeFloat (ticker, 'BaseVolume'),
            'info': ticker,
        };
    }

    async fetchTickers (symbols = undefined, params = {}) {
        await this.loadMarkets ();
        let response = await this.publicGetMarketsummaries (params);
        let tickers = response['result'];
        let result = {};
        for (let t = 0; t < tickers.length; t++) {
            let ticker = tickers[t];
            let id = ticker['MarketName'];
            let market = undefined;
            let symbol = id;
            if (id in this.markets_by_id) {
                market = this.markets_by_id[id];
                symbol = market['symbol'];
            } else {
                symbol = this.parseSymbol (id);
            }
            result[symbol] = this.parseTicker (ticker, market);
        }
        return result;
    }

    async fetchTicker (symbol, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.publicGetMarketsummary (this.extend ({
            'market': market['id'],
        }, params));
        let ticker = response['result'][0];
        return this.parseTicker (ticker, market);
    }

    parseTrade (trade, market = undefined) {
        let timestamp = this.parse8601 (trade['TimeStamp'] + '+00:00');
        let side = undefined;
        if (trade['OrderType'] === 'BUY') {
            side = 'buy';
        } else if (trade['OrderType'] === 'SELL') {
            side = 'sell';
        }
        let id = undefined;
        if ('Id' in trade)
            id = trade['Id'].toString ();
        return {
            'id': id,
            'info': trade,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': market['symbol'],
            'type': 'limit',
            'side': side,
            'price': this.safeFloat (trade, 'Price'),
            'amount': this.safeFloat (trade, 'Quantity'),
        };
    }

    async fetchTrades (symbol, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.publicGetMarkethistory (this.extend ({
            'market': market['id'],
        }, params));
        if ('result' in response) {
            if (typeof response['result'] !== 'undefined')
                return this.parseTrades (response['result'], market, since, limit);
        }
        throw new ExchangeError (this.id + ' fetchTrades() returned undefined response');
    }

    parseOHLCV (ohlcv, market = undefined, timeframe = '1d', since = undefined, limit = undefined) {
        let timestamp = this.parse8601 (ohlcv['T'] + '+00:00');
        return [
            timestamp,
            ohlcv['O'],
            ohlcv['H'],
            ohlcv['L'],
            ohlcv['C'],
            ohlcv['V'],
        ];
    }

    async fetchOHLCV (symbol, timeframe = '1m', since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'tickInterval': this.timeframes[timeframe],
            'marketName': market['id'],
        };
        let response = await this.v2GetMarketGetTicks (this.extend (request, params));
        if ('result' in response) {
            if (response['result'])
                return this.parseOHLCVs (response['result'], market, timeframe, since, limit);
        }
        throw new ExchangeError (this.id + ' returned an empty or unrecognized response: ' + this.json (response));
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let request = {};
        let market = undefined;
        if (typeof symbol !== 'undefined') {
            market = this.market (symbol);
            request['market'] = market['id'];
        }
        let response = await this.marketGetOpenorders (this.extend (request, params));
        let orders = this.parseOrders (response['result'], market, since, limit);
        return this.filterBySymbol (orders, symbol);
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = {}) {
        if (type !== 'limit')
            throw new ExchangeError (this.id + ' allows limit orders only');
        await this.loadMarkets ();
        let market = this.market (symbol);
        let method = 'marketGet' + this.capitalize (side) + type;
        let order = {
            'market': market['id'],
            'quantity': this.amountToPrecision (symbol, amount),
            'rate': this.priceToPrecision (symbol, price),
        };
        // if (type == 'limit')
        //     order['rate'] = this.priceToPrecision (symbol, price);
        let response = await this[method] (this.extend (order, params));
        let orderIdField = this.getOrderIdField ();
        let result = {
            'info': response,
            'id': response['result'][orderIdField],
            'symbol': symbol,
            'type': type,
            'side': side,
            'status': 'open',
        };
        return result;
    }

    getOrderIdField () {
        return 'uuid';
    }

    async cancelOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let orderIdField = this.getOrderIdField ();
        let request = {};
        request[orderIdField] = id;
        let response = await this.marketGetCancel (this.extend (request, params));
        return this.extend (this.parseOrder (response), {
            'status': 'canceled',
        });
    }

    parseSymbol (id) {
        let [ quote, base ] = id.split ('-');
        base = this.commonCurrencyCode (base);
        quote = this.commonCurrencyCode (quote);
        return base + '/' + quote;
    }

    parseOrder (order, market = undefined) {
        let side = this.safeString (order, 'OrderType');
        if (typeof side === 'undefined')
            side = this.safeString (order, 'Type');
        let isBuyOrder = (side === 'LIMIT_BUY') || (side === 'BUY');
        let isSellOrder = (side === 'LIMIT_SELL') || (side === 'SELL');
        if (isBuyOrder) {
            side = 'buy';
        }
        if (isSellOrder) {
            side = 'sell';
        }
        // We parse different fields in a very specific order.
        // Order might well be closed and then canceled.
        let status = undefined;
        if (('Opened' in order) && order['Opened'])
            status = 'open';
        if (('Closed' in order) && order['Closed'])
            status = 'closed';
        if (('CancelInitiated' in order) && order['CancelInitiated'])
            status = 'canceled';
        if (('Status' in order) && this.options['parseOrderStatus'])
            status = this.parseOrderStatus (order['Status']);
        let symbol = undefined;
        if ('Exchange' in order) {
            let marketId = order['Exchange'];
            if (marketId in this.markets_by_id) {
                market = this.markets_by_id[marketId];
                symbol = market['symbol'];
            } else {
                symbol = this.parseSymbol (marketId);
            }
        } else {
            if (typeof market !== 'undefined') {
                symbol = market['symbol'];
            }
        }
        let timestamp = undefined;
        if ('Opened' in order)
            timestamp = this.parse8601 (order['Opened'] + '+00:00');
        if ('Created' in order)
            timestamp = this.parse8601 (order['Created'] + '+00:00');
        let lastTradeTimestamp = undefined;
        if (('TimeStamp' in order) && (typeof order['TimeStamp'] !== 'undefined'))
            lastTradeTimestamp = this.parse8601 (order['TimeStamp'] + '+00:00');
        if (('Closed' in order) && (typeof order['Closed'] !== 'undefined'))
            lastTradeTimestamp = this.parse8601 (order['Closed'] + '+00:00');
        if (typeof timestamp === 'undefined')
            timestamp = lastTradeTimestamp;
        let iso8601 = (typeof timestamp !== 'undefined') ? this.iso8601 (timestamp) : undefined;
        let fee = undefined;
        let commission = undefined;
        if ('Commission' in order) {
            commission = 'Commission';
        } else if ('CommissionPaid' in order) {
            commission = 'CommissionPaid';
        }
        if (commission) {
            fee = {
                'cost': parseFloat (order[commission]),
            };
            if (typeof market !== 'undefined') {
                fee['currency'] = market['quote'];
            } else if (typeof symbol !== 'undefined') {
                let currencyIds = symbol.split ('/');
                let quoteCurrencyId = currencyIds[1];
                if (quoteCurrencyId in this.currencies_by_id)
                    fee['currency'] = this.currencies_by_id[quoteCurrencyId]['code'];
                else
                    fee['currency'] = this.commonCurrencyCode (quoteCurrencyId);
            }
        }
        let price = this.safeFloat (order, 'Limit');
        let cost = this.safeFloat (order, 'Price');
        let amount = this.safeFloat (order, 'Quantity');
        let remaining = this.safeFloat (order, 'QuantityRemaining');
        let filled = undefined;
        if (typeof amount !== 'undefined' && typeof remaining !== 'undefined') {
            filled = amount - remaining;
        }
        if (!cost) {
            if (price && filled)
                cost = price * filled;
        }
        if (!price) {
            if (cost && filled)
                price = cost / filled;
        }
        let average = this.safeFloat (order, 'PricePerUnit');
        let id = this.safeString (order, 'OrderUuid');
        if (typeof id === 'undefined')
            id = this.safeString (order, 'OrderId');
        let result = {
            'info': order,
            'id': id,
            'timestamp': timestamp,
            'datetime': iso8601,
            'lastTradeTimestamp': lastTradeTimestamp,
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': price,
            'cost': cost,
            'average': average,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': fee,
        };
        return result;
    }

    async fetchOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let response = undefined;
        try {
            let orderIdField = this.getOrderIdField ();
            let request = {};
            request[orderIdField] = id;
            response = await this.accountGetOrder (this.extend (request, params));
        } catch (e) {
            if (this.last_json_response) {
                let message = this.safeString (this.last_json_response, 'message');
                if (message === 'UUID_INVALID')
                    throw new OrderNotFound (this.id + ' fetchOrder() error: ' + this.last_http_response);
            }
            throw e;
        }
        if (!response['result']) {
            throw new OrderNotFound (this.id + ' order ' + id + ' not found');
        }
        return this.parseOrder (response['result']);
    }

    async fetchClosedOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let request = {};
        let market = undefined;
        if (typeof symbol !== 'undefined') {
            market = this.market (symbol);
            request['market'] = market['id'];
        }
        let response = await this.accountGetOrderhistory (this.extend (request, params));
        let orders = this.parseOrders (response['result'], market, since, limit);
        if (typeof symbol !== 'undefined')
            return this.filterBySymbol (orders, symbol);
        return orders;
    }

    async fetchDepositAddress (code, params = {}) {
        await this.loadMarkets ();
        let currency = this.currency (code);
        let response = await this.accountGetDepositaddress (this.extend ({
            'currency': currency['id'],
        }, params));
        let address = this.safeString (response['result'], 'Address');
        let message = this.safeString (response, 'message');
        if (!address || message === 'ADDRESS_GENERATING')
            throw new AddressPending (this.id + ' the address for ' + code + ' is being generated (pending, not ready yet, retry again later)');
        let tag = undefined;
        if ((code === 'XRP') || (code === 'XLM')) {
            tag = address;
            address = currency['address'];
        }
        this.checkAddress (address);
        return {
            'currency': code,
            'address': address,
            'tag': tag,
            'info': response,
        };
    }

    async withdraw (code, amount, address, tag = undefined, params = {}) {
        this.checkAddress (address);
        await this.loadMarkets ();
        let currency = this.currency (code);
        let request = {
            'currency': currency['id'],
            'quantity': amount,
            'address': address,
        };
        if (tag)
            request['paymentid'] = tag;
        let response = await this.accountGetWithdraw (this.extend (request, params));
        let id = undefined;
        if ('result' in response) {
            if ('uuid' in response['result'])
                id = response['result']['uuid'];
        }
        return {
            'info': response,
            'id': id,
        };
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let url = this.urls['api'] + '/' + this.implodeParams (path, params);
        if (api === 'public') {
            if (Object.keys (params).length)
                url += '?' + this.urlencode (params);
        } else {
            this.checkRequiredCredentials ();
            let nonce = this.nonce ();
            url += api + '/';
            if (((api === 'account') && (path !== 'withdraw')) || (path === 'openorders'))
                url += method.toLowerCase ();
            url += path + '?' + this.urlencode (this.extend ({
                'nonce': nonce,
                'apikey': this.apiKey,
            }, params));
            let auth = '';
            let query = this.extend (params, {
                'country': this.options['country'],
                'mobile': this.options['mobile'],
            });
            let signature = this.hash (this.encode (auth));
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'apisign': signature,
            };
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    handleErrors (httpCode, reason, url, method, headers, body) {
        if (typeof body !== 'string')
            return; // fallback to default error handler
        if (body.length < 2)
            return; // fallback to default error handler
        if ((body[0] === '{') || (body[0] === '[')) {
            let response = JSON.parse (body);
            //
            // {"code":"0","msg":"suc","data":[{"
            //
            const code = this.safeString (response, 'code');
            // const message = this.safeString (response, 'msg');
            const feedback = this.id + ' ' + this.json (response);
            const exceptions = this.exceptions;
            if (code !== '0') {
                if (code in exceptions) {
                    throw new exceptions[code] (feedback);
                } else {
                    throw new ExchangeError (feedback);
                }
            }
        }
    }
};
