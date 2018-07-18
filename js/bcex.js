'use strict';

//  ---------------------------------------------------------------------------

const Exchange = require ('./base/Exchange');
const { ExchangeError } = require ('./base/errors');

//  ---------------------------------------------------------------------------

module.exports = class bcex extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'bcex',
            'name': 'bcex',
            'countries': [ 'CA' ],
            'rateLimit': 500,
            'version': '1',
            'has': {
                'fetchBalance': true,
                'fetchMarkets': true,
                'createOrder': true,
                'cancelOrder': true,
                'fetchTicker': true,
                'fetchTickers': false,
                'fetchOrder': true,
                'fetchOrders': true,
                'fetchOpenOrders': true,
            },
            'urls': {
                'logo': 'https://www.bcex.top/images/bcex_logo0.png',
                'api': 'https://www.bcex.top',
                'www': 'https://www.bcex.ca',
                'doc': 'https://www.bcex.ca/api_market/market/',
                'fees': 'http://bcex.udesk.cn/hc/articles/57085',
            },
            'api': {
                'public': {
                    'get': [
                        'Api_Market/getPriceList'
                    ],
                },
                'private': {
                    'post': [
                        'Api_User/userBalance',
                        'Api_Order/coinTrust',
                        'Api_Order/cancel',
                        'Api_Order/ticker',
                        'Api_Order/orderList',
                        'Api_Order/tradeList',
                    ],
                },
            },
            'fees': {
            },
        });
    }

    async fetchMarkets () {
        let response = await this.publicGetApiMarketGetPriceList ();
        let result = [];
        let keys = Object.keys(response);
        for (let i = 0; i < keys.length; i++) {
            var currentMarketId = keys[i];
            var currentMarkets = response[currentMarketId];
            for (let j = 0; j < currentMarkets.length; j++) {
                var market = currentMarkets[j];
                let baseId = market.coin_from;
                let quoteId = market.coin_to;
                let base = this.commonCurrencyCode(baseId);
                let quote = this.commonCurrencyCode(quoteId);
                let id = base + "2" + quote;
                let symbol = base + '/' + quote;
                let active = true;
                result.push({
                    'id': id,
                    'symbol': symbol,
                    'base': base,
                    'quote': quote,
                    'baseId': baseId,
                    'quoteId': quoteId,
                    'active': active,
                    'info': market
                    });
            }
        }
        return result;
    }

    async fetchBalance (params = {}) {
        return 0;
    }

    async fetchOrderBook (symbol, limit = undefined, params = {}) {
        return 0;
    }

    async fetchMyTrades (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        return 0;
    }

    async fetchOrder (id, symbol = undefined, params = {}) {
        return 0;
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        return 0;
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = {}) {
        return 0;
    }

    async cancelOrder (id, symbol = undefined, params = {}) {
        return 0;
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let request = '/' + this.implodeParams(path, params);
        let query = this.omit(params, this.extractParams(path));
        if (method === 'GET') {
            if (Object.keys(query).length)
                request += '?' + this.urlencode(query);
        }
        let url = this.urls['api'] + request;
        if (api === 'private') {
            this.checkRequiredCredentials();
            if (method !== 'GET') {
                if (Object.keys(query).length) {
                    let messageParts = []
                    let paramsKeys = Object.keys(params).sort();
                    for (let i = 0; i < paramsKeys.length; i++) {
                        let paramKey = paramsKeys[i];
                        let param = params[paramKey];
                        messageParts.push(this.encode(paramKey) + '=' + encodeURIComponent(param));
                    }
                    body = messageParts.join ('&');
                    let message = body + "&secret_key=" + this.secret;
                    let signedMessage = this.hash(message);
                    body = body + "&sign=" + signedMessage;
                    params['sign'] = signedMessage;
                    headers = {}
                    headers['Content-Type'] = 'application/x-www-form-urlencoded';
                }
            }
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }
};
