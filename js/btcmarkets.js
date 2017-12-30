"use strict";

//  ---------------------------------------------------------------------------

const Exchange = require ('./base/Exchange')
const { ExchangeError } = require ('./base/errors')

//  ---------------------------------------------------------------------------

module.exports = class btcmarkets extends Exchange {

    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'btcmarkets',
            'name': 'BTC Markets',
            'countries': 'AU', // Australia
            'rateLimit': 1000, // market data cached for 1 second (trades cached for 2 seconds)
            'hasCORS': false,
            'hasFetchOrder': true,
            'hasFetchOrders': true,
            'hasFetchClosedOrders': true,
            'hasFetchOpenOrders': true,
            'has': {
                'fetchOrder': true,
                'fetchOrders': true,
                'fetchClosedOrders': 'emulated',
                'fetchOpenOrders': true,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/29142911-0e1acfc2-7d5c-11e7-98c4-07d9532b29d7.jpg',
                'api': 'https://api.btcmarkets.net',
                'www': 'https://btcmarkets.net/',
                'doc': 'https://github.com/BTCMarkets/API',
            },
            'api': {
                'public': {
                    'get': [
                        'market/{id}/tick',
                        'market/{id}/orderbook',
                        'market/{id}/trades',
                    ],
                },
                'private': {
                    'get': [
                        'account/balance',
                        'account/{id}/tradingfee',
                    ],
                    'post': [
                        'fundtransfer/withdrawCrypto',
                        'fundtransfer/withdrawEFT',
                        'order/create',
                        'order/cancel',
                        'order/history',
                        'order/open',
                        'order/trade/history',
                        'order/createBatch', // they promise it's coming soon...
                        'order/detail',
                    ],
                },
            },
            'markets': {
                'BTC/AUD': { 'id': 'BTC/AUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'LTC/AUD': { 'id': 'LTC/AUD', 'symbol': 'LTC/AUD', 'base': 'LTC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'ETH/AUD': { 'id': 'ETH/AUD', 'symbol': 'ETH/AUD', 'base': 'ETH', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'ETC/AUD': { 'id': 'ETC/AUD', 'symbol': 'ETC/AUD', 'base': 'ETC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'XRP/AUD': { 'id': 'XRP/AUD', 'symbol': 'XRP/AUD', 'base': 'XRP', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'BCH/AUD': { 'id': 'BCH/AUD', 'symbol': 'BCH/AUD', 'base': 'BCH', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085 },
                'LTC/BTC': { 'id': 'LTC/BTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022 },
                'ETH/BTC': { 'id': 'ETH/BTC', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022 },
                'ETC/BTC': { 'id': 'ETC/BTC', 'symbol': 'ETC/BTC', 'base': 'ETC', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022 },
                'XRP/BTC': { 'id': 'XRP/BTC', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022 },
                'BCH/BTC': { 'id': 'BCH/BTC', 'symbol': 'BCH/BTC', 'base': 'BCH', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022 },
            },
        });
    }

    async fetchBalance (params = {}) {
        await this.loadMarkets ();
        let balances = await this.privateGetAccountBalance ();
        let result = { 'info': balances };
        for (let b = 0; b < balances.length; b++) {
            let balance = balances[b];
            let currency = balance['currency'];
            let multiplier = 100000000;
            let total = parseFloat (balance['balance'] / multiplier);
            let used = parseFloat (balance['pendingFunds'] / multiplier);
            let free = total - used;
            let account = {
                'free': free,
                'used': used,
                'total': total,
            };
            result[currency] = account;
        }
        return this.parseBalance (result);
    }

    async fetchOrderBook (symbol, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let orderbook = await this.publicGetMarketIdOrderbook (this.extend ({
            'id': market['id'],
        }, params));
        let timestamp = orderbook['timestamp'] * 1000;
        return this.parseOrderBook (orderbook, timestamp);
    }

    parseTicker (ticker, market = undefined) {
        let timestamp = ticker['timestamp'] * 1000;
        let symbol = undefined;
        if (market)
            symbol = market['symbol'];
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'high': undefined,
            'low': undefined,
            'bid': parseFloat (ticker['bestBid']),
            'ask': parseFloat (ticker['bestAsk']),
            'vwap': undefined,
            'open': undefined,
            'close': undefined,
            'first': undefined,
            'last': parseFloat (ticker['lastPrice']),
            'change': undefined,
            'percentage': undefined,
            'average': undefined,
            'baseVolume': parseFloat (ticker['volume24h']),
            'quoteVolume': undefined,
            'info': ticker,
        };
    }

    async fetchTicker (symbol, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let ticker = await this.publicGetMarketIdTick (this.extend ({
            'id': market['id'],
        }, params));
        return this.parseTicker (ticker, market);
    }

    parseTrade (trade, market) {
        let timestamp = trade['date'] * 1000;
        return {
            'info': trade,
            'id': trade['tid'].toString (),
            'order': undefined,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': market['symbol'],
            'type': undefined,
            'side': undefined,
            'price': trade['price'],
            'amount': trade['amount'],
        };
    }

    async fetchTrades (symbol, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let response = await this.publicGetMarketIdTrades (this.extend ({
            // 'since': 59868345231,
            'id': market['id'],
        }, params));
        return this.parseTrades (response, market, since, limit);
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let multiplier = 100000000; // for price and volume
        // does BTC Markets support market orders at all?
        let orderSide = (side == 'buy') ? 'Bid' : 'Ask';
        let order = this.ordered ({
            'currency': market['quote'],
        });
        order['currency'] = market['quote'];
        order['instrument'] = market['base'];
        order['price'] = parseInt (price * multiplier);
        order['volume'] = parseInt (amount * multiplier);
        order['orderSide'] = orderSide;
        order['ordertype'] = this.capitalize (type);
        order['clientRequestId'] = this.nonce ().toString ();
        let response = await this.privatePostOrderCreate (order);
        return {
            'info': response,
            'id': response['id'].toString (),
        };
    }

    async cancelOrders (ids) {
        await this.loadMarkets ();
        return await this.privatePostOrderCancel ({ 'order_ids': ids });
    }

    async cancelOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        return await this.cancelOrders ([ id ]);
    }

    parseOrderTrade (trade, market) {
        let multiplier = 100000000;
        let timestamp = trade['creationTime'];
        let side = (trade['side'] == 'Bid') ? 'buy' : 'sell';
        return {
            'info': trade,
            'id': trade['id'].toString (),
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': market['symbol'],
            'type': undefined,
            'side': side,
            'price': trade['price'] / multiplier,
            'fee': trade['fee'] / multiplier,
            'amount': trade['volume'] / multiplier,
        };
    }

    parseOrder (order, market = undefined) {
        let multiplier = 100000000;
        let side = (order['orderSide'] == 'Bid') ? 'buy' : 'sell';
        let type = (order['ordertype'] == 'Limit') ? 'limit' : 'market';
        let timestamp = order['creationTime'];
        if (!market) {
            market = this.market(order['instrument'] + "/" + order['currency']);
        }
        let status = 'open';
        if (order['status'] == 'Failed' || order['status'] == 'Cancelled' || order['status'] == 'Partially Cancelled' || order['status'] == 'Error') {
            status = 'canceled';
        } else if (order['status'] == "Fully Matched" || order['status'] == "Partially Matched") {
            status = 'closed';
        }
        let price = this.safeFloat (order, 'price') / multiplier;
        let amount = this.safeFloat (order, 'volume') / multiplier;
        let remaining = this.safeFloat (order, 'openVolume', 0.0) / multiplier;
        let filled = amount - remaining;
        let cost = price * amount;
        let trades = [];
        for (let i=0; i< order['trades'].length; i++) {
            trades.push(this.parseOrderTrade(order['trades'][i], market));
        }
        let result = {
            'info': order,
            'id': order['id'].toString (),
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': market['symbol'],
            'type': type,
            'side': side,
            'price': price,
            'cost': cost,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'trades': trades,
        };
        return result;
    }

    async fetchOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let response = await this.privatePostOrderDetail (this.extend ({ 'orderIds': [id] }, params));
        if (response['orders'].length == 0) {
            throw new OrderNotFound (this.id + ' No matching order found: ' + id);
        }
        return this.parseOrder (response['orders'][0]);
    }

    async prepRequest (market, since = undefined, limit = undefined, params = {}) {
        let request = this.ordered({
            'currency': market['quote'],
            'instrument': market['base'],
        });
        if (limit) {
            request['limit'] = limit;
        } else {
            request['limit'] = 100;
        }
        if (since) {
            request['since'] = since;
        } else {
            request['since'] = 0;
        }
        return request;
    }

    async fetchOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets();
        let market = undefined;
        if (!symbol) {
            throw new NotSupported (this.id + ': fetchOrders requires a `symbol` parameter.');
        }
        market = this.market(symbol);
        let request = this.prepRequest(market, since, limit, params);
        let response = await this.privatePostOrderHistory (this.extend (request, params));
        return this.parseOrders (response['orders'], market);
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets();
        let market = undefined;
        if (!symbol) {
            throw new NotSupported (this.id + ': fetchOrders requires a `symbol` parameter.');
        }
        market = this.market(symbol);
        let request = this.prepRequest(market, since, limit, params);
        let response = await this.privatePostOrderOpen (this.extend (request, params));
        return this.parseOrders (response['orders'], market);
    }

    async fetchClosedOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        let orders = await this.fetchOrders (symbol, params);
        return this.filterBy (orders, 'status', 'closed');
        return [];
    }

    nonce () {
        return this.milliseconds ();
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let uri = '/' + this.implodeParams (path, params);
        let url = this.urls['api'] + uri;
        if (api == 'public') {
            if (Object.keys (params).length)
                url += '?' + this.urlencode (params);
        } else {
            this.checkRequiredCredentials ();
            let nonce = this.nonce ().toString ();
            let auth = uri + "\n" + nonce + "\n";
            headers = {
                'Content-Type': 'application/json',
                'apikey': this.apiKey,
                'timestamp': nonce,
            };
            if (method == 'POST') {
                body = this.json (params);
                auth += body;
            }
            let secret = this.base64ToBinary (this.secret);
            let signature = this.hmac (this.encode (auth), secret, 'sha512', 'base64');
            headers['signature'] = this.decode (signature);
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    async request (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let response = await this.fetch2 (path, api, method, params, headers, body);
        if (api == 'private') {
            if ('success' in response)
                if (!response['success'])
                    throw new ExchangeError (this.id + ' ' + this.json (response));
            return response;
        }
        return response;
    }
}
