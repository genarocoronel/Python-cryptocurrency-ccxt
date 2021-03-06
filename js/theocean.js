'use strict';

const Exchange = require ('./base/Exchange');
const { ExchangeError, AuthenticationError, InvalidOrder, OrderNotFound, NotSupported, OrderImmediatelyFillable, OrderNotFillable, InvalidAddress, InsufficientFunds } = require ('./base/errors');
const { ROUND } = require ('./base/functions/number');

module.exports = class theocean extends Exchange {
    describe () {
        return this.deepExtend (super.describe (), {
            'id': 'theocean',
            'name': 'The Ocean',
            'countries': [ 'US' ],
            'rateLimit': 3000,
            'version': 'v0',
            'certified': true,
            'parseJsonResponse': false,
            // add GET https://api.staging.theocean.trade/api/v0/candlesticks/intervals to fetchMarkets
            'timeframes': {
                '5m': '300',
                '15m': '900',
                '1h': '3600',
                '6h': '21600',
                '1d': '86400',
            },
            'has': {
                'CORS': false, // ?
                'fetchTickers': true,
                'fetchOHLCV': false,
                'fetchOpenOrders': true,
                'fetchClosedOrders': true,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/43103756-d56613ce-8ed7-11e8-924e-68f9d4bcacab.jpg',
                'api': 'https://api.theocean.trade/api',
                'www': 'https://theocean.trade',
                'doc': 'https://docs.theocean.trade',
                'fees': 'https://theocean.trade/fees',
            },
            'api': {
                'public': {
                    'get': [
                        'fee_components',
                        'token_pairs',
                        'ticker',
                        'tickers',
                        'candlesticks',
                        'candlesticks/intervals',
                        'trade_history',
                        'order_book',
                        'order/{orderHash}',
                    ],
                },
                'private': {
                    'get': [
                        'available_balance',
                        'user_history',
                    ],
                    'post': [
                        'limit_order/reserve',
                        'limit_order/place',
                        'market_order/reserve',
                        'market_order/place',
                    ],
                    'delete': [
                        'order/{orderHash}',
                        'orders',
                    ],
                },
            },
            'exceptions': {
                "Schema validation failed for 'query'": ExchangeError, // { "message": "Schema validation failed for 'query'", "errors": ... }
                "Logic validation failed for 'query'": ExchangeError, // { "message": "Logic validation failed for 'query'", "errors": ... }
                "Schema validation failed for 'body'": ExchangeError, // { "message": "Schema validation failed for 'body'", "errors": ... }
                "Logic validation failed for 'body'": ExchangeError, // { "message": "Logic validation failed for 'body'", "errors": ... }
                'Order not found': OrderNotFound, // {"message":"Order not found","errors":...}
                'Greater than available wallet balance.': InsufficientFunds, // {"message":"Greater than available wallet balance.","type":"walletBaseTokenAmount"}
            },
            'options': {
                'fetchOrderMethod': 'fetch_order_from_history',
            },
        });
    }

    calculateFee (symbol, type, side, amount, price, takerOrMaker = 'taker', params = {}) {
        let market = this.markets[symbol];
        let key = 'quote';
        let rate = market[takerOrMaker];
        let cost = parseFloat (this.costToPrecision (symbol, amount * rate));
        if (side === 'sell') {
            cost *= price;
        } else {
            key = 'base';
        }
        return {
            'type': takerOrMaker,
            'currency': market[key],
            'rate': rate,
            'cost': cost,
        };
    }

    async fetchMarkets () {
        let markets = await this.publicGetTokenPairs ();
        //
        //     [
        //       {
        //         "baseToken": {
        //           "address": "0xa8e9fa8f91e5ae138c74648c9c304f1c75003a8d",
        //           "symbol": "ZRX",
        //           "decimals": "18",
        //           "minAmount": "1000000000000000000",
        //           "maxAmount": "100000000000000000000000",
        //           "precision": "18"
        //         },
        //         "quoteToken": {
        //           "address": "0xc00fd9820cd2898cc4c054b7bf142de637ad129a",
        //           "symbol": "WETH",
        //           "decimals": "18",
        //           "minAmount": "5000000000000000",
        //           "maxAmount": "100000000000000000000",
        //           "precision": "18"
        //         }
        //       }
        //     ]
        //
        let result = [];
        for (let i = 0; i < markets.length; i++) {
            let market = markets[i];
            let baseToken = market['baseToken'];
            let quoteToken = market['quoteToken'];
            let baseId = baseToken['address'];
            let quoteId = quoteToken['address'];
            let base = baseToken['symbol'];
            let quote = quoteToken['symbol'];
            base = this.commonCurrencyCode (base);
            quote = this.commonCurrencyCode (quote);
            let symbol = base + '/' + quote;
            let id = baseId + '/' + quoteId;
            let precision = {
                'amount': this.safeInteger (baseToken, 'precision'),
                'price': this.safeInteger (quoteToken, 'precision'),
            };
            let amountLimits = {
                'min': this.fromWei (this.safeString (baseToken, 'minAmount')),
                'max': this.fromWei (this.safeString (baseToken, 'maxAmount')),
            };
            let priceLimits = {
                'min': undefined,
                'max': undefined,
            };
            let costLimits = {
                'min': this.fromWei (this.safeString (quoteToken, 'minAmount')),
                'max': this.fromWei (this.safeString (quoteToken, 'maxAmount')),
            };
            let limits = {
                'amount': amountLimits,
                'price': priceLimits,
                'cost': costLimits,
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
                'precision': precision,
                'limits': limits,
                'info': market,
            });
        }
        return result;
    }

    parseOHLCV (ohlcv, market = undefined, timeframe = '5m', since = undefined, limit = undefined) {
        return [
            this.safeInteger (ohlcv, 'startTime') * 1000,
            this.safeFloat (ohlcv, 'open'),
            this.safeFloat (ohlcv, 'high'),
            this.safeFloat (ohlcv, 'low'),
            this.safeFloat (ohlcv, 'close'),
            this.fromWei (this.safeString (ohlcv, 'baseVolume')),
            // this.safeString (ohlcv, 'quoteVolume'),
        ];
    }

    async fetchOHLCV (symbol, timeframe = '5m', since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'baseTokenAddress': market['baseId'],
            'quoteTokenAddress': market['quoteId'],
            'interval': this.timeframes[timeframe],
            // 'endTime': endTime, // (optional) Snapshot end time
        };
        if (typeof since === 'undefined') {
            throw new ExchangeError (this.id + ' fetchOHLCV requires a since argument');
        }
        request['startTime'] = parseInt (since / 1000);
        let response = await this.publicGetCandlesticks (this.extend (request, params));
        //
        //   [
        //     {
        //         "high": "100.52",
        //         "low": "97.23",
        //         "open": "98.45",
        //         "close": "99.23",
        //         "baseVolume": "2400000000000000000000",
        //         "quoteVolume": "1200000000000000000000",
        //         "startTime": "1512929323784"
        //     },
        //     {
        //         "high": "100.52",
        //         "low": "97.23",
        //         "open": "98.45",
        //         "close": "99.23",
        //         "volume": "2400000000000000000000",
        //         "startTime": "1512929198980"
        //     }
        //   ]
        //
        return this.parseOHLCVs (response, market, timeframe, since, limit);
    }

    async fetchBalanceByCode (code, params = {}) {
        if (!this.walletAddress || (this.walletAddress.indexOf ('0x') !== 0)) {
            throw new InvalidAddress (this.id + ' fetchBalanceByCode() requires the .walletAddress to be a "0x"-prefixed hexstring like "0xbF2d65B3b2907214EEA3562f21B80f6Ed7220377"');
        }
        await this.loadMarkets ();
        let currency = this.currency (code);
        let request = {
            'walletAddress': this.walletAddress.toLowerCase (),
            'tokenAddress': currency['id'],
        };
        let response = await this.privateGetAvailableBalance (this.extend (request, params));
        //
        //     {
        //       "availableBalance": "1001006594219628829207"
        //     }
        //
        let balance = this.fromWei (this.safeString (response, 'availableBalance'));
        return {
            'free': balance,
            'used': 0,
            'total': undefined,
        };
    }

    async fetchBalance (params = {}) {
        if (!this.walletAddress || (this.walletAddress.indexOf ('0x') !== 0)) {
            throw new InvalidAddress (this.id + ' fetchBalance() requires the .walletAddress to be a "0x"-prefixed hexstring like "0xbF2d65B3b2907214EEA3562f21B80f6Ed7220377"');
        }
        const codes = this.safeValue (params, 'codes');
        if ((typeof codes === 'undefined') || (!Array.isArray (codes))) {
            throw new ExchangeError (this.id + ' fetchBalance() requires a `codes` parameter (an array of currency codes)');
        }
        await this.loadMarkets ();
        let result = {};
        for (let i = 0; i < codes.length; i++) {
            const code = codes[i];
            result[code] = await this.fetchBalanceByCode (code);
        }
        return this.parseBalance (result);
    }

    parseBidAsk (bidask, priceKey = 0, amountKey = 1) {
        let price = parseFloat (bidask[priceKey]);
        let amount = this.fromWei (bidask[amountKey]);
        // return [ price, amount, bidask ];
        return [ price, amount ];
    }

    async fetchOrderBook (symbol, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'baseTokenAddress': market['baseId'],
            'quoteTokenAddress': market['quoteId'],
        };
        if (typeof limit !== 'undefined') {
            request['depth'] = limit;
        }
        let response = await this.publicGetOrderBook (this.extend (request, params));
        //
        //     {
        //       "bids": [
        //         {
        //           "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //           "price": "0.00050915",
        //           "availableAmount": "100000000000000000000",
        //           "creationTimestamp": "1512929327792",
        //           "expirationTimestampInSec": "1534449466"
        //         }
        //       ],
        //       "asks": [
        //         {
        //           "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //           "price": "0.00054134",
        //           "availableAmount": "100000000000000000000",
        //           "creationTimestamp": "1512929323784",
        //           "expirationTimestampInSec": "1534449466"
        //         }
        //       ]
        //     }
        //
        return this.parseOrderBook (response, undefined, 'bids', 'asks', 'price', 'availableAmount');
    }

    parseTicker (ticker, market = undefined) {
        //
        //     {
        //         "bid": "0.00050915",
        //         "ask": "0.00054134",
        //         "last": "0.00052718",
        //         "volume": "3000000000000000000",
        //         "timestamp": "1512929327792"
        //     }
        //
        let timestamp = parseInt (this.safeFloat (ticker, 'timestamp') / 1000);
        let symbol = undefined;
        if (typeof market !== 'undefined') {
            symbol = market['symbol'];
        }
        let last = this.safeFloat (ticker, 'last');
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'high': undefined,
            'low': undefined,
            'bid': this.safeFloat (ticker, 'bid'),
            'bidVolume': undefined,
            'ask': this.safeFloat (ticker, 'ask'),
            'askVolume': undefined,
            'vwap': undefined,
            'open': undefined,
            'close': last,
            'last': last,
            'previousClose': undefined,
            'change': undefined,
            'percentage': this.safeFloat (ticker, 'priceChange'),
            'average': undefined,
            'baseVolume': this.fromWei (this.safeString (ticker, 'volume')),
            'quoteVolume': undefined,
            'info': ticker,
        };
    }

    async fetchTickers (symbols = undefined, params = {}) {
        await this.loadMarkets ();
        let tickers = await this.publicGetTickers (params);
        //
        //     [{
        //     "baseTokenAddress": "0xa8e9fa8f91e5ae138c74648c9c304f1c75003a8d",
        //     "quoteTokenAddress": "0xc00fd9820cd2898cc4c054b7bf142de637ad129a",
        //     "ticker": {
        //         "bid": "0.00050915",
        //         "ask": "0.00054134",
        //         "last": "0.00052718",
        //         "volume": "3000000000000000000",
        //         "timestamp": "1512929327792"
        //     }
        //     }]
        //
        let result = {};
        for (let i = 0; i < tickers.length; i++) {
            let ticker = tickers[i];
            let baseId = this.safeString (ticker, 'baseTokenAddress');
            let quoteId = this.safeString (ticker, 'quoteTokenAddress');
            let marketId = baseId + '/' + quoteId;
            let market = undefined;
            let symbol = marketId;
            if (marketId in this.markets_by_id) {
                market = this.markets_by_id[marketId];
                symbol = market['symbol'];
            }
            result[symbol] = this.parseTicker (ticker['ticker'], market);
        }
        return result;
    }

    async fetchTicker (symbol, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'baseTokenAddress': market['baseId'],
            'quoteTokenAddress': market['quoteId'],
        };
        let response = await this.publicGetTicker (this.extend (request, params));
        return this.parseTicker (response, market);
    }

    parseTrade (trade, market = undefined) {
        //
        // fetchTrades
        //
        //     {
        //         "id": "37212",
        //         "transactionHash": "0x5e6e75e1aa681b51b034296f62ac19be7460411a2ad94042dd8ba637e13eac0c",
        //         "amount": "300000000000000000",
        //         "price": "0.00052718",
        // ------- they also have a "confirmed" status here ??? -----------------
        //         "status": "filled", // filled | settled | failed
        //         "lastUpdated": "1520265048996"
        //     }
        //
        // parseOrder trades (timeline "actions", "fills")
        //
        //     {      action: "confirmed",
        //            amount: "1000000000000000000",
        //          intentID: "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //            txHash: "0x043488fdc3f995bf9e632a32424e41ed126de90f8cb340a1ff006c2a74ca8336",
        //       blockNumber: "8094822",
        //         timestamp: "1532261686"                                                          }
        //
        let timestamp = this.safeInteger (trade, 'lastUpdated');
        if (typeof timestamp === 'undefined') {
            timestamp = this.safeInteger (trade, 'timestamp');
        }
        if (typeof timestamp !== 'undefined') {
            // their timestamps are in seconds, mostly
            timestamp = timestamp * 1000;
        }
        let price = this.safeFloat (trade, 'price');
        let orderId = this.safeString (trade, 'order');
        let id = this.safeString2 (trade, 'transactionHash', 'txHash');
        let symbol = undefined;
        if (typeof market !== 'undefined') {
            symbol = market['symbol'];
        }
        let amount = this.fromWei (this.safeString (trade, 'amount'));
        let cost = undefined;
        if (typeof amount !== 'undefined') {
            if (typeof price !== 'undefined') {
                cost = amount * price;
            }
        }
        let takerOrMaker = 'taker';
        let fee = undefined;
        // let fee = this.calculateFee (symbol, type, side, amount, price, takerOrMaker);
        return {
            'id': id,
            'order': orderId,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'symbol': symbol,
            'type': undefined,
            'side': undefined,
            'takerOrMaker': takerOrMaker,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': fee,
            'info': trade,
        };
    }

    async fetchTrades (symbol, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let market = this.market (symbol);
        let request = {
            'baseTokenAddress': market['baseId'],
            'quoteTokenAddress': market['quoteId'],
        };
        let response = await this.publicGetTradeHistory (this.extend (request, params));
        //
        //     [
        //       {
        //         "id": "37212",
        //         "transactionHash": "0x5e6e75e1aa681b51b034296f62ac19be7460411a2ad94042dd8ba637e13eac0c",
        //         "amount": "300000000000000000",
        //         "price": "0.00052718",
        //         "status": "filled", // filled | settled | failed
        //         "lastUpdated": "1520265048996"
        //       }
        //     ]
        //
        return this.parseTrades (response, market, since, limit);
    }

    priceToPrecision (symbol, price) {
        return this.decimalToPrecision (price, ROUND, this.markets[symbol]['precision']['price'], this.precisionMode);
    }

    async createOrder (symbol, type, side, amount, price = undefined, params = {}) {
        const errorMessage = this.id + ' createOrder() requires `exchange.walletAddress` and `exchange.privateKey`. The .walletAddress should be a "0x"-prefixed hexstring like "0xbF2d65B3b2907214EEA3562f21B80f6Ed7220377". The .privateKey for that wallet should be a "0x"-prefixed hexstring like "0xe4f40d465efa94c98aec1a51f574329344c772c1bce33be07fa20a56795fdd09".';
        if (!this.walletAddress || (this.walletAddress.indexOf ('0x') !== 0)) {
            throw new InvalidAddress (errorMessage);
        }
        if (!this.privateKey || (this.privateKey.indexOf ('0x') !== 0)) {
            throw new InvalidAddress (errorMessage);
        }
        await this.loadMarkets ();
        const makerOrTaker = this.safeString (params, 'makerOrTaker');
        const isMarket = (type === 'market');
        const isMakerOrTakerUndefined = (typeof makerOrTaker === 'undefined');
        const isTaker = (makerOrTaker === 'taker');
        const isMaker = (makerOrTaker === 'maker');
        if (isMarket && !isMakerOrTakerUndefined && !isTaker) {
            throw new InvalidOrder (this.id + ' createOrder() ' + type + ' order type cannot be a ' + makerOrTaker + '. The createOrder() method of ' + type + ' type can be used with taker orders only.');
        }
        let query = this.omit (params, 'makerOrTaker');
        let timestamp = this.milliseconds ();
        let market = this.market (symbol);
        let reserveRequest = {
            'walletAddress': this.walletAddress.toLowerCase (), // Your Wallet Address
            'baseTokenAddress': market['baseId'], // Base token address
            'quoteTokenAddress': market['quoteId'], // Quote token address
            'side': side, // "buy" or "sell"
            'orderAmount': this.toWei (this.amountToPrecision (symbol, amount)), // Base token amount in wei
            'feeOption': 'feeInNative', // Fees can be paid in native currency ("feeInNative"), or ZRX ("feeInZRX")
        };
        if (type === 'limit') {
            reserveRequest['price'] = this.priceToPrecision (symbol, price); // Price denominated in quote tokens (limit orders only)
        }
        let method = 'privatePost' + this.capitalize (type) + 'Order';
        let reserveMethod = method + 'Reserve';
        let reserveResponse = await this[reserveMethod] (this.extend (reserveRequest, query));
        //
        // ---- market orders -------------------------------------------------
        //
        // let reserveResponse =
        //     {       matchingOrderID:   "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //       unsignedMatchingOrder: {                      maker: "",
        //                                                     taker: "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //                                         makerTokenAddress: "0xd0a1e359811322d97991e03f863a0c30c2cf029c",
        //                                         takerTokenAddress: "0x6ff6c0ff1d68b964901f986d4c9fa3ac68346570",
        //                                          makerTokenAmount: "27100000000000000",
        //                                          takerTokenAmount: "874377028175459241",
        //                                                  makerFee: "0",
        //                                                  takerFee: "0",
        //                                expirationUnixTimestampSec: "1534809575",
        //                                              feeRecipient: "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //                                                      salt: "3610846705800197954038657082705100176266402776121341340841167002345284333867",
        //                                   exchangeContractAddress: "0x90fe2af704b34e0224bf2299c838e04d4dcf1364"                                    } }
        //
        // ---- limit orders --------------------------------------------------
        //
        // 1. if the order is completely fillable:
        //    + unsignedMatchingOrder will be present
        //    - unsignedTargetOrder will be missing
        // 2. if the order is partially fillable:
        //    + unsignedMatchingOrder and
        //    + unsignedTarget order will be present
        // 3. if the order is not fillable at the moment:
        //    + unsignedTargetOrder will be present
        //    - unsignedMatchingOrder will be missing
        // In other words, unsignedMatchingOrder is only present
        // if there is some fillable amount in the order book.
        //
        // Note: ecSignature is empty at this point and missing in the actual
        // response, there's no need for it here at this point anyway.
        //
        // let reserveResponse =
        //     { unsignedTargetOrder: {                      maker: "",
        //                                                   taker: "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //                                       makerTokenAddress: "0xd0a1e359811322d97991e03f863a0c30c2cf029c",
        //                                       takerTokenAddress: "0x6ff6c0ff1d68b964901f986d4c9fa3ac68346570",
        //                                        makerTokenAmount: "2700000000000000",
        //                                        takerTokenAmount: "937912044575392743",
        //                                                makerFee: "0",
        //                                                takerFee: "0",
        //                              expirationUnixTimestampSec: "1534813319",
        //                                            feeRecipient: "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //                                                    salt: "54933934472162523007303314622614098849759889305199720392701919179357703099693",
        //                                 exchangeContractAddress: "0x90fe2af704b34e0224bf2299c838e04d4dcf1364"                                     } }
        //
        // let reserveResponse =
        //     {
        //       "unsignedTargetOrder": {
        //         "exchangeContractAddress": "0x516bdc037df84d70672b2d140835833d3623e451",
        //         "maker": "",
        //         "taker": "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //         "makerTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //         "takerTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //         "feeRecipient": "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //         "makerTokenAmount": "10000000000000000000",
        //         "takerTokenAmount": "10000000000000000000",
        //         "makerFee": "0",
        //         "takerFee": "0",
        //         "expirationUnixTimestampSec": "525600",
        //         "salt": "37800593840622773016017857006417214310534675667008850948421364357744823963318",
        //         "ecSignature": {
        //           "v": 0,
        //           "r": "",
        //           "s": ""
        //         }
        //       },
        //       "unsignedMatchingOrder": {
        //         "exchangeContractAddress": "0x516bdc037df84d70672b2d140835833d3623e451",
        //         "maker": "",
        //         "taker": "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //         "makerTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //         "takerTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //         "feeRecipient": "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //         "makerTokenAmount": "10000000000000000000",
        //         "takerTokenAmount": "10000000000000000000",
        //         "makerFee": "0",
        //         "takerFee": "0",
        //         "expirationUnixTimestampSec": "525600",
        //         "salt": "37800593840622773016017857006417214310534675667008850948421364357744823963318",
        //         "ecSignature": {
        //           "v": 0,
        //           "r": "",
        //           "s": ""
        //         }
        //       },
        //       "matchingOrderID": "MARKET_INTENT:8ajjh92s1r8ajjh92s1sjjh92s1t"
        //     }
        //
        // --------------------------------------------------------------------
        let unsignedMatchingOrder = this.safeValue (reserveResponse, 'unsignedMatchingOrder');
        let unsignedTargetOrder = this.safeValue (reserveResponse, 'unsignedTargetOrder');
        const isUnsignedMatchingOrderDefined = (typeof unsignedMatchingOrder !== 'undefined');
        const isUnsignedTargetOrderDefined = (typeof unsignedTargetOrder !== 'undefined');
        const makerAddress = {
            'maker': this.walletAddress.toLowerCase (),
        };
        let placeRequest = {};
        let signedMatchingOrder = undefined;
        let signedTargetOrder = undefined;
        if (isUnsignedMatchingOrderDefined && isUnsignedTargetOrderDefined) {
            if (isTaker) {
                signedMatchingOrder = this.signZeroExOrder (this.extend (unsignedMatchingOrder, makerAddress), this.privateKey);
                placeRequest['signedMatchingOrder'] = signedMatchingOrder;
                placeRequest['matchingOrderID'] = reserveResponse['matchingOrderID'];
            } else if (isMaker) {
                signedTargetOrder = this.signZeroExOrder (this.extend (unsignedTargetOrder, makerAddress), this.privateKey);
                placeRequest['signedTargetOrder'] = signedTargetOrder;
            } else {
                signedMatchingOrder = this.signZeroExOrder (this.extend (unsignedMatchingOrder, makerAddress), this.privateKey);
                placeRequest['signedMatchingOrder'] = signedMatchingOrder;
                placeRequest['matchingOrderID'] = reserveResponse['matchingOrderID'];
                signedTargetOrder = this.signZeroExOrder (this.extend (unsignedTargetOrder, makerAddress), this.privateKey);
                placeRequest['signedTargetOrder'] = signedTargetOrder;
            }
        } else if (isUnsignedMatchingOrderDefined) {
            if (isMaker) {
                throw new OrderImmediatelyFillable (this.id + ' createOrder() ' + type + ' order to ' + side + ' ' + symbol + ' is not fillable as a maker order');
            } else {
                signedMatchingOrder = this.signZeroExOrder (this.extend (unsignedMatchingOrder, makerAddress), this.privateKey);
                placeRequest['signedMatchingOrder'] = signedMatchingOrder;
                placeRequest['matchingOrderID'] = reserveResponse['matchingOrderID'];
            }
        } else if (isUnsignedTargetOrderDefined) {
            if (isTaker || isMarket) {
                throw new OrderNotFillable (this.id + ' createOrder() ' + type + ' order to ' + side + ' ' + symbol + ' is not fillable as a taker order');
            } else {
                signedTargetOrder = this.signZeroExOrder (this.extend (unsignedTargetOrder, makerAddress), this.privateKey);
                placeRequest['signedTargetOrder'] = signedTargetOrder;
            }
        } else {
            throw new OrderNotFillable (this.id + ' ' + type + ' order to ' + side + ' ' + symbol + ' is not fillable at the moment');
        }
        let placeMethod = method + 'Place';
        let placeResponse = await this[placeMethod] (this.extend (placeRequest, query));
        //
        // ---- market orders -------------------------------------------------
        //
        // let placeResponse =
        //     { matchingOrder: { transactionHash: "0x043488fdc3f995bf9e632a32424e41ed126de90f8cb340a1ff006c2a74ca8336",
        //                                 amount: "1000000000000000000",
        //                              orderHash: "0xe815dc92933b68e7fc2b7102b8407ba7afb384e4080ac8d28ed42482933c5cf5"  },
        //            parentID:   "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl"                                              }
        //
        // ---- limit orders -------------------------------------------------
        //
        // let placeResponse =
        //     { targetOrder: {    amount: "1000000000000000000",
        //                      orderHash: "0x517aef1ce5027328c40204833b624f04a54c913e93cffcdd500fe9252c535251" },
        //          parentID:   "MARKET_INTENT:90jjw50gpk90jjw50gpljjw50gpm"                                       }
        //
        // let placeResponse =
        //     {
        //         "targetOrder": {
        //             "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //             "amount": "100000000000"
        //         },
        //         "matchingOrder": {
        //             "orderHash": "0x3d6b287c1dc79262d2391ae2ca9d050fdbbab2c8b3180e4a46f9f321a7f1d7a9",
        //             "transactionHash": "0x5e6e75e1aa681b51b034296f62ac19be7460411a2ad94042dd8ba637e13eac0c",
        //             "amount": "100000000000"
        //         }
        //     }
        //
        let matchingOrder = this.safeValue (placeResponse, 'matchingOrder');
        let targetOrder = this.safeValue (placeResponse, 'targetOrder');
        const orderParams = {
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'price': price,
            'side': side,
            'filled': 0,
            'status': 'open',
        };
        let taker = undefined;
        let maker = undefined;
        if (typeof matchingOrder !== 'undefined') {
            matchingOrder = this.extend (signedMatchingOrder, matchingOrder);
            taker = this.parseOrder (matchingOrder, market);
            taker = this.extend (taker, {
                'type': 'market',
                'remaining': taker['amount'],
            }, orderParams);
            if (isTaker)
                return taker;
        }
        if (typeof targetOrder !== 'undefined') {
            targetOrder = this.extend (signedTargetOrder, targetOrder);
            maker = this.parseOrder (targetOrder, market);
            maker = this.extend (maker, {
                'type': 'limit',
                'remaining': maker['amount'],
            }, orderParams);
            if (isMaker)
                return maker;
        }
        return {
            'info': this.extend (reserveResponse, placeRequest, placeResponse),
            'maker': maker,
            'taker': taker,
        };
    }

    async cancelOrder (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let request = {
            'orderHash': id,
        };
        let response = await this.privateDeleteOrderOrderHash (this.extend (request, params));
        //
        //     {
        //       "canceledOrder": {
        //         "orderHash": "0x3d6b287c1dc79262d2391ae2ca9d050fdbbab2c8b3180e4a46f9f321a7f1d7a9",
        //         "amount": "100000000000"
        //       }
        //     }
        //
        let market = undefined;
        if (typeof symbol !== 'undefined') {
            market = this.market (symbol);
        }
        return this.extend (this.parseOrder (response['canceledOrder'], market), {
            'status': 'canceled',
        });
    }

    async cancelAllOrders (params = {}) {
        const response = await this.privateDeleteOrders (params);
        //
        //     [{
        //       "canceledOrder": {
        //         "orderHash": "0x3d6b287c1dc79262d2391ae2ca9d050fdbbab2c8b3180e4a46f9f321a7f1d7a9",
        //         "amount": "100000000000"
        //       }
        //     }]
        //
        return response;
    }

    parseOrderStatus (status) {
        let statuses = {
            'placed': 'open',
            'reserved': 'open',
            'filled': 'closed',
            'settled': 'closed',
            'confirmed': 'closed',
            'returned': 'open',
            'canceled': 'canceled',
            'pruned': 'failed',
        };
        if (status in statuses) {
            return statuses[status];
        }
        return status;
    }

    parseOrder (order, market = undefined) {
        //
        // fetchOrder, fetchOrderBook
        //
        //     {
        //       "baseTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //       "quoteTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //       "side": "buy",
        //       "amount": "10000000000000000000",
        //       "price": "1.000",
        //       "created": "1512929327792",
        //       "expires": "1512929897118",
        //       "zeroExOrder": {
        //         "exchangeContractAddress": "0x516bdc037df84d70672b2d140835833d3623e451",
        //         "maker": "0x006dc83e5b21854d4afc44c9b92a91e0349dda13",
        //         "taker": "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //         "makerTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //         "takerTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //         "feeRecipient": "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //         "makerTokenAmount": "10000000000000000000",
        //         "takerTokenAmount": "10000000000000000000",
        //         "makerFee": "0",
        //         "takerFee": "0",
        //         "expirationUnixTimestampSec": "525600",
        //         "salt": "37800593840622773016017857006417214310534675667008850948421364357744823963318",
        //         "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //         "ecSignature": {
        //           "v": 28,
        //           "r": "0x5307b6a69e7cba8583e1de39efb93a9ae1afc11849e79d99f462e49c18c4d6e4",
        //           "s": "0x5950e82364227ccca95c70b47375e8911a2039d3040ba0684329634ebdced160"
        //         }
        //       }
        //     }
        //
        // fetchOrders
        //
        //     {              orderHash:   "0xe815dc92933b68e7fc2b7102b8407ba7afb384e4080ac8d28ed42482933c5cf5",
        //             baseTokenAddress:   "0x6ff6c0ff1d68b964901f986d4c9fa3ac68346570",
        //            quoteTokenAddress:   "0xd0a1e359811322d97991e03f863a0c30c2cf029c",
        //                         side:   "buy",
        //                        price:   "0.0271",
        //                   openAmount:   "0",
        //               reservedAmount:   "0",
        //                 filledAmount:   "0",
        //                settledAmount:   "0",
        //              confirmedAmount:   "1000000000000000000",
        //                 failedAmount:   "0",
        //                   deadAmount:   "0",
        //                 prunedAmount:   "0",
        //                    feeAmount:   "125622971824540759",
        //                    feeOption:   "feeInNative",
        //                     parentID:   "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //       siblingTargetOrderHash:    null,
        //                     timeline: [ {      action: "filled",
        //                                        amount: "1000000000000000000",
        //                                      intentID: "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //                                        txHash:  null,
        //                                   blockNumber: "0",
        //                                     timestamp: "1532217579"                                  },
        //                                 {      action: "settled",
        //                                        amount: "1000000000000000000",
        //                                      intentID: "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //                                        txHash: "0x043488fdc3f995bf9e632a32424441ed126de90f8cb340a1ff006c2a74ca8336",
        //                                   blockNumber: "8094822",
        //                                     timestamp: "1532261671"                                                          },
        //                                 {      action: "confirmed",
        //                                        amount: "1000000000000000000",
        //                                      intentID: "MARKET_INTENT:90jjw2s7gj90jjw2s7gkjjw2s7gl",
        //                                        txHash: "0x043488fdc3f995bf9e632a32424441ed126de90f8cb340a1ff006c2a74ca8336",
        //                                   blockNumber: "8094822",
        //                                     timestamp: "1532261686"                                                          }  ] }
        //
        //
        //
        let zeroExOrder = this.safeValue (order, 'zeroExOrder');
        let id = this.safeString (order, 'orderHash');
        if ((typeof id === 'undefined') && (typeof zeroExOrder !== 'undefined')) {
            id = this.safeString (zeroExOrder, 'orderHash');
        }
        let side = this.safeString (order, 'side');
        let type = 'limit';
        let timestamp = this.safeInteger (order, 'created');
        timestamp = (typeof timestamp !== 'undefined') ? timestamp * 1000 : timestamp;
        let symbol = undefined;
        if (typeof market === 'undefined') {
            let baseId = this.safeString (order, 'baseTokenAddress');
            let quoteId = this.safeString (order, 'quoteTokenAddress');
            let marketId = baseId + '/' + quoteId;
            if (marketId in this.markets_by_id) {
                market = this.markets_by_id[marketId];
            }
        }
        if (typeof market !== 'undefined') {
            symbol = market['symbol'];
        }
        let price = this.safeFloat (order, 'price');
        let openAmount = this.fromWei (this.safeString (order, 'openAmount'));
        let reservedAmount = this.fromWei (this.safeString (order, 'reservedAmount'));
        let filledAmount = this.fromWei (this.safeString (order, 'filledAmount'));
        let settledAmount = this.fromWei (this.safeString (order, 'settledAmount'));
        let confirmedAmount = this.fromWei (this.safeString (order, 'confirmedAmount'));
        let failedAmount = this.fromWei (this.safeString (order, 'failedAmount'));
        let deadAmount = this.fromWei (this.safeString (order, 'deadAmount'));
        let prunedAmount = this.fromWei (this.safeString (order, 'prunedAmount'));
        let amount = this.fromWei (this.safeString (order, 'amount'));
        if (typeof amount === 'undefined') {
            amount = this.sum (openAmount, reservedAmount, filledAmount, settledAmount, confirmedAmount, failedAmount, deadAmount, prunedAmount);
        }
        let filled = this.sum (filledAmount, settledAmount, confirmedAmount);
        let remaining = undefined;
        let lastTradeTimestamp = undefined;
        let timeline = this.safeValue (order, 'timeline');
        let trades = undefined;
        let status = 'open';
        if (typeof timeline !== 'undefined') {
            let numEvents = timeline.length;
            if (numEvents > 0) {
                status = this.safeString (timeline[numEvents - 1], 'action');
                status = this.parseOrderStatus (status);
                let timelineEventsGroupedByAction = this.groupBy (timeline, 'action');
                if ('placed' in timelineEventsGroupedByAction) {
                    let placeEvents = this.safeValue (timelineEventsGroupedByAction, 'placed');
                    if (typeof amount === 'undefined') {
                        amount = this.fromWei (this.safeString (placeEvents[0], 'amount'));
                    }
                    timestamp = this.safeInteger (placeEvents[0], 'timestamp');
                    timestamp = (typeof timestamp !== 'undefined') ? timestamp * 1000 : timestamp;
                } else {
                    if ('filled' in timelineEventsGroupedByAction) {
                        timestamp = this.safeInteger (timelineEventsGroupedByAction['filled'][0], 'timestamp');
                        timestamp = (typeof timestamp !== 'undefined') ? timestamp * 1000 : timestamp;
                    }
                    type = 'market';
                }
                if ('filled' in timelineEventsGroupedByAction) {
                    let fillEvents = this.safeValue (timelineEventsGroupedByAction, 'filled');
                    let numFillEvents = fillEvents.length;
                    if (typeof timestamp === 'undefined') {
                        timestamp = this.safeInteger (fillEvents[0], 'timestamp');
                        timestamp = (typeof timestamp !== 'undefined') ? timestamp * 1000 : timestamp;
                    }
                    lastTradeTimestamp = this.safeInteger (fillEvents[numFillEvents - 1], 'timestamp');
                    lastTradeTimestamp = (typeof lastTradeTimestamp !== 'undefined') ? lastTradeTimestamp * 1000 : lastTradeTimestamp;
                    trades = [];
                    for (let i = 0; i < numFillEvents; i++) {
                        let trade = this.parseTrade (this.extend (fillEvents[i], {
                            'price': price,
                        }), market);
                        trades.push (this.extend (trade, {
                            'order': id,
                            'type': type,
                            'side': side,
                        }));
                    }
                }
            }
        }
        let cost = undefined;
        if (typeof filled !== 'undefined') {
            if (typeof remaining === 'undefined') {
                if (typeof amount !== 'undefined') {
                    remaining = amount - filled;
                }
            }
            if (typeof price !== 'undefined') {
                cost = filled * price;
            }
        }
        let fee = undefined;
        let feeCost = this.fromWei (this.safeString (order, 'feeAmount'));
        if (typeof feeCost !== 'undefined') {
            let feeOption = this.safeString (order, 'feeOption');
            let feeCurrency = undefined;
            if (feeOption === 'feeInNative') {
                if (typeof market !== 'undefined') {
                    feeCurrency = market['base'];
                }
            } else if (feeOption === 'feeInZRX') {
                feeCurrency = 'ZRX';
            } else {
                throw new NotSupported (this.id + ' encountered an unsupported order fee option: ' + feeOption);
            }
            fee = {
                'feeCost': feeCost,
                'feeCurrency': feeCurrency,
            };
        }
        let result = {
            'info': order,
            'id': id,
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': this.iso8601 (timestamp),
            'lastTradeTimestamp': lastTradeTimestamp,
            'type': type,
            'side': side,
            'price': price,
            'cost': cost,
            'amount': amount,
            'remaining': remaining,
            'filled': filled,
            'status': status,
            'fee': fee,
            'trades': trades,
        };
        return result;
    }

    async fetchOpenOrder (id, symbol = undefined, params = {}) {
        let method = this.options['fetchOrderMethod'];
        return await this[method] (id, symbol, this.extend ({
            'openAmount': 1,
        }, params));
    }

    async fetchClosedOrder (id, symbol = undefined, params = {}) {
        let method = this.options['fetchOrderMethod'];
        return await this[method] (id, symbol, this.extend (params));
    }

    async fetchOrderFromHistory (id, symbol = undefined, params = {}) {
        let orders = await this.fetchOrders (symbol, undefined, undefined, this.extend ({
            'orderHash': id,
        }, params));
        let ordersById = this.indexBy (orders, 'id');
        if (id in ordersById)
            return ordersById[id];
        throw new OrderNotFound (this.id + ' could not find order ' + id + ' in order history');
    }

    async fetchOrderById (id, symbol = undefined, params = {}) {
        await this.loadMarkets ();
        let request = {
            'orderHash': id,
        };
        let response = await this.publicGetOrderOrderHash (this.extend (request, params));
        //
        //     {
        //       "baseTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //       "quoteTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //       "side": "buy",
        //       "amount": "10000000000000000000",
        //       "price": "1.000",
        //       "created": "1512929327792",
        //       "expires": "1512929897118",
        //       "zeroExOrder": {
        //         "exchangeContractAddress": "0x516bdc037df84d70672b2d140835833d3623e451",
        //         "maker": "0x006dc83e5b21854d4afc44c9b92a91e0349dda13",
        //         "taker": "0x00ba938cc0df182c25108d7bf2ee3d37bce07513",
        //         "makerTokenAddress": "0x7cc7fdd065cfa9c7f4f6a3c1bfc6dfcb1a3177aa",
        //         "takerTokenAddress": "0x17f15936ef3a2da5593033f84487cbe9e268f02f",
        //         "feeRecipient": "0x88a64b5e882e5ad851bea5e7a3c8ba7c523fecbe",
        //         "makerTokenAmount": "10000000000000000000",
        //         "takerTokenAmount": "10000000000000000000",
        //         "makerFee": "0",
        //         "takerFee": "0",
        //         "expirationUnixTimestampSec": "525600",
        //         "salt": "37800593840622773016017857006417214310534675667008850948421364357744823963318",
        //         "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //         "ecSignature": {
        //           "v": 28,
        //           "r": "0x5307b6a69e7cba8583e1de39efb93a9ae1afc11849e79d99f462e49c18c4d6e4",
        //           "s": "0x5950e82364227ccca95c70b47375e8911a2039d3040ba0684329634ebdced160"
        //         }
        //       }
        //     }
        //
        return this.parseOrder (response);
    }

    async fetchOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        await this.loadMarkets ();
        let request = {
            // openAmount (optional) Return orders with an openAmount greater than or equal to this value
            // reservedAmount (optional) Return orders with a reservedAmount greater than or equal to this value
            // filledAmount (optional) Return orders with a filledAmount greater than or equal to this value
            // confirmedAmount (optional) Return orders with a confirmedAmount greater than or equal to this value
            // deadAmount (optional) Return orders with a deadAmount greater than or equal to this value
            // baseTokenAddress (optional) Return orders with a baseTokenAddress equal to this value
            // quoteTokenAddress (optional) Return orders with a quoteTokenAddress equal to this value
        };
        let market = undefined;
        if (typeof symbol !== 'undefined') {
            market = this.market (symbol);
            request['baseTokenAddress'] = market['baseId'];
            request['quoteTokenAddress'] = market['quoteId'];
        }
        if (typeof limit !== 'undefined') {
            // request['start'] = 0; // the number of orders to offset from the end
            request['limit'] = limit;
        }
        let response = await this.privateGetUserHistory (this.extend (request, params));
        //
        //     [
        //       {
        //         "orderHash": "0x94629386298dee69ae63cd3e414336ae153b3f02cffb9ffc53ad71e166615618",
        //         "baseTokenAddress": "0x323b5d4c32345ced77393b3530b1eed0f346429d",
        //         "quoteTokenAddress": "0xef7fff64389b814a946f3e92105513705ca6b990",
        //         "side": "buy",
        //         "openAmount": "10000000000000000000",
        //         "filledAmount": "0",
        //         "reservedAmount": "0",
        //         "settledAmount": "0",
        //         "confirmedAmount": "0",
        //         "deadAmount": "0",
        //         "price": "0.00050915",
        //         "timeline": [
        //           {
        //             "action": "placed",
        //             "amount": "10000000000000000000",
        //             "timestamp": "1512929327792"
        //           }
        //         ]
        //       }
        //     ]
        //
        return this.parseOrders (response, undefined, since, limit);
    }

    async fetchOpenOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        return await this.fetchOrders (symbol, since, limit, this.extend ({
            'openAmount': 1, // returns open orders with remaining openAmount >= 1
        }, params));
    }

    async fetchClosedOrders (symbol = undefined, since = undefined, limit = undefined, params = {}) {
        return await this.fetchOrders (symbol, since, limit, this.extend ({
            'openAmount': 0, // returns closed orders with remaining openAmount === 0
        }, params));
    }

    sign (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let url = this.urls['api'] + '/' + this.version + '/' + this.implodeParams (path, params);
        let query = this.omit (params, this.extractParams (path));
        if (api === 'private') {
            this.checkRequiredCredentials ();
            let timestamp = this.seconds ().toString ();
            let prehash = this.apiKey + timestamp + method;
            if (method === 'POST') {
                body = this.json (query);
                prehash += body;
            } else {
                if (Object.keys (query).length) {
                    url += '?' + this.urlencode (query);
                }
                prehash += this.json ({});
            }
            let signature = this.hmac (this.encode (prehash), this.encode (this.secret), 'sha256', 'base64');
            headers = {
                'TOX-ACCESS-KEY': this.apiKey,
                'TOX-ACCESS-SIGN': signature,
                'TOX-ACCESS-TIMESTAMP': timestamp,
                'Content-Type': 'application/json',
            };
        } else if (api === 'public') {
            if (Object.keys (query).length) {
                url += '?' + this.urlencode (query);
            }
        }
        return { 'url': url, 'method': method, 'body': body, 'headers': headers };
    }

    handleErrors (httpCode, reason, url, method, headers, body) {
        if (typeof body !== 'string')
            return; // fallback to default error handler
        if (body.length < 2)
            return; // fallback to default error handler
        // code 401 and plain body 'Authentication failed' (with single quotes)
        // this error is sent if you do not submit a proper Content-Type
        if (body === "'Authentication failed'") {
            throw new AuthenticationError (this.id + ' ' + body);
        }
        if ((body[0] === '{') || (body[0] === '[')) {
            let response = JSON.parse (body);
            const message = this.safeString (response, 'message');
            if (typeof message !== 'undefined') {
                //
                // {"message":"Schema validation failed for 'query'","errors":[{"name":"required","argument":"startTime","message":"requires property \"startTime\"","instance":{"baseTokenAddress":"0x6ff6c0ff1d68b964901f986d4c9fa3ac68346570","quoteTokenAddress":"0xd0a1e359811322d97991e03f863a0c30c2cf029c","interval":"300"},"property":"instance"}]}
                // {"message":"Logic validation failed for 'query'","errors":[{"message":"startTime should be between 0 and current date","type":"startTime"}]}
                // {"message":"Order not found","errors":[]}
                // {"message":"Orderbook exhausted for intent MARKET_INTENT:8yjjzd8b0e8yjjzd8b0fjjzd8b0g"}
                // {"message":"Intent validation failed.","errors":[{"message":"Greater than available wallet balance.","type":"walletBaseTokenAmount"}]}
                //
                const feedback = this.id + ' ' + this.json (response);
                const exceptions = this.exceptions;
                let errors = this.safeValue (response, 'errors');
                if (message in exceptions) {
                    throw new exceptions[message] (feedback);
                } else {
                    if (message.indexOf ('Orderbook exhausted for intent') >= 0) {
                        throw new OrderNotFillable (feedback);
                    } else if (message === 'Intent validation failed.') {
                        if (Array.isArray (errors)) {
                            for (let i = 0; i < errors.length; i++) {
                                let error = errors[i];
                                let errorMessage = this.safeString (error, 'message');
                                if (errorMessage in exceptions) {
                                    throw new exceptions[errorMessage] (feedback);
                                }
                            }
                        }
                    }
                    throw new ExchangeError (feedback);
                }
            }
        }
    }

    async request (path, api = 'public', method = 'GET', params = {}, headers = undefined, body = undefined) {
        let response = await this.fetch2 (path, api, method, params, headers, body);
        if (typeof response !== 'string') {
            throw new ExchangeError (this.id + ' returned a non-string response: ' + response.toString ());
        }
        if ((response[0] === '{' || response[0] === '[')) {
            return JSON.parse (response);
        }
        return response;
    }
};
