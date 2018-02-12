<?php

namespace ccxt;

// PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
// https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

class bibox extends Exchange {

    public function describe () {
        return array_replace_recursive (parent::describe (), array (
            'id' => 'bibox',
            'name' => 'Bibox',
            'countries' => array ( 'CN', 'US', 'KR' ),
            'version' => 'v1',
            'has' => array (
                'CORS' => false,
                'publicAPI' => false,
                'fetchBalance' => true,
                'fetchCurrencies' => true,
                'fetchDepositAddress' => true,
                'fetchTickers' => true,
                'fetchOpenOrders' => true,
                'fetchClosedOrders' => true,
                'fetchMyTrades' => true,
                'fetchOHLCV' => true,
                'withdraw' => true,
            ),
            'timeframes' => array (
                '1m' => '1min',
                '5m' => '5min',
                '15m' => '15min',
                '30m' => '30min',
                '1h' => '1hour',
                '8h' => '12hour',
                '1d' => 'day',
                '1w' => 'week',
            ),
            'urls' => array (
                'logo' => 'https://user-images.githubusercontent.com/1294454/34902611-2be8bf1a-f830-11e7-91a2-11b2f292e750.jpg',
                'api' => 'https://api.bibox.com',
                'www' => 'https://www.bibox.com',
                'doc' => array (
                    'https://github.com/Biboxcom/api_reference/wiki/home_en',
                    'https://github.com/Biboxcom/api_reference/wiki/api_reference',
                ),
                'fees' => 'https://bibox.zendesk.com/hc/en-us/articles/115004417013-Fee-Structure-on-Bibox',
            ),
            'api' => array (
                'public' => array (
                    'post' => array (
                        // TODO => rework for full endpoint/cmd paths here
                        'mdata',
                    ),
                    'get' => array (
                        'mdata',
                    ),
                ),
                'private' => array (
                    'post' => array (
                        'user',
                        'orderpending',
                        'transfer',
                    ),
                ),
            ),
            'fees' => array (
                'trading' => array (
                    'tierBased' => false,
                    'percentage' => true,
                    'taker' => 0.001,
                    'maker' => 0.0,
                ),
                'funding' => array (
                    'tierBased' => false,
                    'percentage' => false,
                    'withdraw' => array (
                    ),
                    'deposit' => 0.0,
                ),
            ),
        ));
    }

    public function fetch_markets ($params = array ()) {
        $response = $this->publicGetMdata (array_merge (array (
            'cmd' => 'marketAll',
        ), $params));
        $markets = $response['result'];
        $result = array ();
        for ($i = 0; $i < count ($markets); $i++) {
            $market = $markets[$i];
            $base = $market['coin_symbol'];
            $quote = $market['currency_symbol'];
            $base = $this->common_currency_code($base);
            $quote = $this->common_currency_code($quote);
            $symbol = $base . '/' . $quote;
            $id = $base . '_' . $quote;
            $precision = array (
                'amount' => 8,
                'price' => 8,
            );
            $result[] = array (
                'id' => $id,
                'symbol' => $symbol,
                'base' => $base,
                'quote' => $quote,
                'active' => null,
                'info' => $market,
                'lot' => pow (10, -$precision['amount']),
                'precision' => $precision,
                'limits' => array (
                    'amount' => array (
                        'min' => pow (10, -$precision['amount']),
                        'max' => null,
                    ),
                    'price' => array (
                        'min' => null,
                        'max' => null,
                    ),
                ),
            );
        }
        return $result;
    }

    public function parse_ticker ($ticker, $market = null) {
        $timestamp = $this->safe_integer($ticker, 'timestamp', $this->seconds ());
        $symbol = null;
        if ($market) {
            $symbol = $market['symbol'];
        } else {
            $symbol = $ticker['coin_symbol'] . '/' . $ticker['currency_symbol'];
        }
        return array (
            'symbol' => $symbol,
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'high' => $this->safe_float($ticker, 'high'),
            'low' => $this->safe_float($ticker, 'low'),
            'bid' => $this->safe_float($ticker, 'buy'),
            'ask' => $this->safe_float($ticker, 'sell'),
            'vwap' => null,
            'open' => null,
            'close' => null,
            'first' => null,
            'last' => $this->safe_float($ticker, 'last'),
            'change' => null,
            'percentage' => $this->safe_string($ticker, 'percent'),
            'average' => null,
            'baseVolume' => $this->safe_float($ticker, 'vol'),
            'quoteVolume' => null,
            'info' => $ticker,
        );
    }

    public function fetch_ticker ($symbol, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $response = $this->publicGetMdata (array_merge (array (
            'cmd' => 'ticker',
            'pair' => $market['id'],
        ), $params));
        return $this->parse_ticker($response['result'], $market);
    }

    public function fetch_tickers ($symbols = null, $params = array ()) {
        $response = $this->publicGetMdata (array_merge (array (
            'cmd' => 'marketAll',
        ), $params));
        $tickers = $response['result'];
        $result = array ();
        for ($t = 0; $t < count ($tickers); $t++) {
            $ticker = $this->parse_ticker($tickers[$t]);
            $symbol = $ticker['symbol'];
            if ($symbols && (!(is_array ($symbols) && array_key_exists ($symbol, $symbols)))) {
                continue;
            }
            $result[$symbol] = $ticker;
        }
        return $result;
    }

    public function parse_trade ($trade, $market = null) {
        $timestamp = $trade['time'];
        $side = $this->safe_integer($trade, 'side');
        $side = $this->safe_integer($trade, 'order_side', $side);
        $side = ($side === 1) ? 'buy' : 'sell';
        if ($market === null) {
            $marketId = $this->safe_string($trade, 'pair');
            if ($marketId !== null)
                if (is_array ($this->markets_by_id) && array_key_exists ($marketId, $this->markets_by_id))
                    $market = $this->markets_by_id[$marketId];
        }
        $symbol = ($market !== null) ? $market['symbol'] : null;
        $fee = null;
        if (is_array ($trade) && array_key_exists ('fee', $trade)) {
            $fee = array (
                'cost' => $this->safe_float($trade, 'fee'),
                'currency' => null,
            );
        }
        return array (
            'id' => null,
            'info' => $trade,
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'symbol' => $symbol,
            'type' => 'limit',
            'side' => $side,
            'price' => floatval ($trade['price']),
            'amount' => floatval ($trade['amount']),
            'fee' => $fee,
        );
    }

    public function fetch_trades ($symbol, $since = null, $limit = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $size = ($limit) ? $limit : 200;
        $response = $this->publicGetMdata (array_merge (array (
            'cmd' => 'deals',
            'pair' => $market['id'],
            'size' => $size,
        ), $params));
        return $this->parse_trades($response['result'], $market, $since, $limit);
    }

    public function fetch_order_book ($symbol, $limit = 200, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $request = array (
            'cmd' => 'depth',
            'pair' => $market['id'],
        );
        $request['size'] = $limit; // default = 200 ?
        $response = $this->publicGetMdata (array_merge ($request, $params));
        return $this->parse_order_book($response['result'], $this->safe_float($response['result'], 'update_time'), 'bids', 'asks', 'price', 'volume');
    }

    public function parse_ohlcv ($ohlcv, $market = null, $timeframe = '1m', $since = null, $limit = null) {
        return [
            $ohlcv['time'],
            $ohlcv['open'],
            $ohlcv['high'],
            $ohlcv['low'],
            $ohlcv['close'],
            $ohlcv['vol'],
        ];
    }

    public function fetch_ohlcv ($symbol, $timeframe = '1m', $since = null, $limit = 1000, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $response = $this->publicGetMdata (array_merge (array (
            'cmd' => 'kline',
            'pair' => $market['id'],
            'period' => $this->timeframes[$timeframe],
            'size' => $limit,
        ), $params));
        return $this->parse_ohlcvs($response['result'], $market, $timeframe, $since, $limit);
    }

    public function fetch_currencies ($params = array ()) {
        $response = $this->privatePostTransfer (array (
            'cmd' => 'transfer/coinList',
            'body' => array (),
        ));
        $currencies = $response['result'];
        $result = array ();
        for ($i = 0; $i < count ($currencies); $i++) {
            $currency = $currencies[$i];
            $id = $currency['symbol'];
            $code = $this->common_currency_code($id);
            $precision = 8;
            $deposit = $currency['enable_deposit'];
            $withdraw = $currency['enable_withdraw'];
            $active = ($deposit && $withdraw);
            $result[$code] = array (
                'id' => $id,
                'code' => $code,
                'info' => $currency,
                'name' => $currency['name'],
                'active' => $active,
                'status' => 'ok',
                'fee' => null,
                'precision' => $precision,
                'limits' => array (
                    'amount' => array (
                        'min' => pow (10, -$precision),
                        'max' => pow (10, $precision),
                    ),
                    'price' => array (
                        'min' => pow (10, -$precision),
                        'max' => pow (10, $precision),
                    ),
                    'cost' => array (
                        'min' => null,
                        'max' => null,
                    ),
                    'withdraw' => array (
                        'min' => null,
                        'max' => pow (10, $precision),
                    ),
                ),
            );
        }
        return $result;
    }

    public function fetch_balance ($params = array ()) {
        $this->load_markets();
        $response = $this->privatePostTransfer (array (
            'cmd' => 'transfer/assets',
            'body' => array_merge (array (
                'select' => 1,
            ), $params),
        ));
        $balances = $response['result'];
        $result = array ( 'info' => $balances );
        $indexed = null;
        if (is_array ($balances) && array_key_exists ('assets_list', $balances)) {
            $indexed = $this->index_by($balances['assets_list'], 'coin_symbol');
        } else {
            $indexed = array ();
        }
        $keys = is_array ($indexed) ? array_keys ($indexed) : array ();
        for ($i = 0; $i < count ($keys); $i++) {
            $id = $keys[$i];
            $currency = $this->common_currency_code($id);
            $account = $this->account ();
            $balance = $indexed[$id];
            $used = floatval ($balance['freeze']);
            $free = floatval ($balance['balance']);
            $total = $this->sum ($free, $used);
            $account['free'] = $free;
            $account['used'] = $used;
            $account['total'] = $total;
            $result[$currency] = $account;
        }
        return $this->parse_balance($result);
    }

    public function create_order ($symbol, $type, $side, $amount, $price = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $orderType = ($type === 'limit') ? 2 : 1;
        $orderSide = ($side === 'buy') ? 1 : 2;
        $response = $this->privatePostOrderpending (array (
            'cmd' => 'orderpending/trade',
            'body' => array_merge (array (
                'pair' => $market['id'],
                'account_type' => 0,
                'order_type' => $orderType,
                'order_side' => $orderSide,
                'pay_bix' => 0,
                'amount' => $amount,
                'price' => $price,
            ), $params),
        ));
        return array (
            'info' => $response,
            'id' => $this->safe_string($response, 'result'),
        );
    }

    public function cancel_order ($id, $symbol = null, $params = array ()) {
        $response = $this->privatePostOrderpending (array (
            'cmd' => 'orderpending/cancelTrade',
            'body' => array_merge (array (
                'orders_id' => $id,
            ), $params),
        ));
        return $response;
    }

    public function parse_order ($order, $market = null) {
        $symbol = null;
        if ($market) {
            $symbol = $market['symbol'];
        } else {
            $symbol = $order['coin_symbol'] . '/' . $order['currency_symbol'];
        }
        $type = ($order['order_type'] === 1) ? 'market' : 'limit';
        $timestamp = $order['createdAt'];
        $price = $order['price'];
        $filled = $this->safe_float($order, 'deal_amount');
        $amount = $this->safe_float($order, 'amount');
        $cost = $this->safe_float($order, 'money');
        $remaining = null;
        if ($filled !== null) {
            if ($amount !== null)
                $remaining = $amount - $filled;
            if ($cost === null)
                $cost = $price * $filled;
        }
        $side = ($order['order_side'] === 1) ? 'buy' : 'sell';
        $status = $this->safe_string($order, 'status');
        if ($status !== null)
            $status = $this->parse_order_status($status);
        $result = array (
            'info' => $order,
            'id' => $this->safe_string($order, 'id'),
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'symbol' => $symbol,
            'type' => $type,
            'side' => $side,
            'price' => $price,
            'amount' => $amount,
            'cost' => $cost ? $cost : floatval ($price) * $filled,
            'filled' => $filled,
            'remaining' => $remaining,
            'status' => $status,
            'fee' => $this->safe_float($order, 'fee'),
        );
        return $result;
    }

    public function parse_order_status ($status) {
        $statuses = array (
            // original comments from bibox:
            '1' => 'pending', // pending
            '2' => 'open', // part completed
            '3' => 'closed', // completed
            '4' => 'canceled', // part canceled
            '5' => 'canceled', // canceled
            '6' => 'canceled', // canceling
        );
        return $this->safe_string($statuses, $status, strtolower ($status));
    }

    public function fetch_open_orders ($symbol = null, $since = null, $limit = null, $params = array ()) {
        $market = null;
        $pair = null;
        if ($symbol !== null) {
            $this->load_markets();
            $market = $this->market ($symbol);
            $pair = $market['id'];
        }
        $size = ($limit) ? $limit : 200;
        $response = $this->privatePostOrderpending (array (
            'cmd' => 'orderpending/orderPendingList',
            'body' => array_merge (array (
                'pair' => $pair,
                'account_type' => 0, // 0 - regular, 1 - margin
                'page' => 1,
                'size' => $size,
            ), $params),
        ));
        $orders = $this->safe_value($response['result'], 'items', array ());
        return $this->parse_orders($orders, $market, $since, $limit);
    }

    public function fetch_closed_orders ($symbol = null, $since = null, $limit = 200, $params = array ()) {
        if ($symbol === null)
            throw new ExchangeError ($this->id . ' fetchClosedOrders requires a $symbol argument');
        $this->load_markets();
        $market = $this->market ($symbol);
        $response = $this->privatePostOrderpending (array (
            'cmd' => 'orderpending/pendingHistoryList',
            'body' => array_merge (array (
                'pair' => $market['id'],
                'account_type' => 0, // 0 - regular, 1 - margin
                'page' => 1,
                'size' => $limit,
            ), $params),
        ));
        $orders = $this->safe_value($response['result'], 'items', array ());
        return $this->parse_orders($orders, $market, $since, $limit);
    }

    public function fetch_my_trades ($symbol = null, $since = null, $limit = null, $params = array ()) {
        if (!$symbol)
            throw new ExchangeError ($this->id . ' fetchMyTrades requires a $symbol argument');
        $this->load_markets();
        $market = $this->market ($symbol);
        $size = ($limit) ? $limit : 200;
        $response = $this->privatePostOrderpending (array (
            'cmd' => 'orderpending/orderHistoryList',
            'body' => array_merge (array (
                'pair' => $market['id'],
                'account_type' => 0, // 0 - regular, 1 - margin
                'page' => 1,
                'size' => $size,
            ), $params),
        ));
        $trades = $this->safe_value($response['result'], 'items', array ());
        return $this->parse_trades($trades, $market, $since, $limit);
    }

    public function fetch_deposit_address ($code, $params = array ()) {
        $this->load_markets();
        $currency = $this->currency ($code);
        $response = $this->privatePostTransfer (array (
            'cmd' => 'transfer/transferOutInfo',
            'body' => array_merge (array (
                'coin_symbol' => $currency['id'],
            ), $params),
        ));
        $result = array (
            'info' => $response,
            'address' => null,
        );
        return $result;
    }

    public function withdraw ($code, $amount, $address, $tag = null, $params = array ()) {
        $this->load_markets();
        $currency = $this->currency ($code);
        if ($this->password === null)
            if (!(is_array ($params) && array_key_exists ('trade_pwd', $params)))
                throw new ExchangeError ($this->id . ' withdraw() requires $this->password set on the exchange instance or a trade_pwd parameter');
        if (!(is_array ($params) && array_key_exists ('totp_code', $params)))
            throw new ExchangeError ($this->id . ' withdraw() requires a totp_code parameter for 2FA authentication');
        $body = array (
            'trade_pwd' => $this->password,
            'coin_symbol' => $currency['id'],
            'amount' => $amount,
            'addr' => $address,
        );
        if ($tag !== null)
            $body['address_remark'] = $tag;
        $response = $this->privatePostTransfer (array (
            'cmd' => 'transfer/transferOut',
            'body' => array_merge ($body, $params),
        ));
        return array (
            'info' => $response,
            'id' => null,
        );
    }

    public function sign ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $url = $this->urls['api'] . '/' . $this->version . '/' . $path;
        $cmds = $this->json (array ( $params ));
        if ($api === 'public') {
            if ($method !== 'GET')
                $body = array ( 'cmds' => $cmds );
            else if ($params)
                $url .= '?' . $this->urlencode ($params);
        } else {
            $this->check_required_credentials();
            $body = array (
                'cmds' => $cmds,
                'apikey' => $this->apiKey,
                'sign' => $this->hmac ($this->encode ($cmds), $this->encode ($this->secret), 'md5'),
            );
        }
        if ($body !== null)
            $body = $this->json ($body, array ( 'convertArraysToObjects' => true ));
        $headers = array ( 'Content-Type' => 'application/json' );
        return array ( 'url' => $url, 'method' => $method, 'body' => $body, 'headers' => $headers );
    }

    public function request ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $response = $this->fetch2 ($path, $api, $method, $params, $headers, $body);
        $message = $this->id . ' ' . $this->json ($response);
        if (is_array ($response) && array_key_exists ('error', $response)) {
            if (is_array ($response['error']) && array_key_exists ('code', $response['error'])) {
                $code = $response['error']['code'];
                if ($code === '2068')
                    // \u4e0b\u5355\u6570\u91cf\u4e0d\u80fd\u4f4e\u4e8e
                    // The number of orders can not be less than
                    throw new InvalidOrder ($message);
                else if ($code === '3012')
                    throw new AuthenticationError ($message); // invalid $api key
                else if ($code === '3025')
                    throw new AuthenticationError ($message); // signature failed
                else if ($code === '4000')
                    // \u5f53\u524d\u7f51\u7edc\u8fde\u63a5\u4e0d\u7a33\u5b9a\uff0c\u8bf7\u7a0d\u5019\u91cd\u8bd5
                    // The current network connection is unstable. Please try again later
                    throw new ExchangeNotAvailable ($message);
                else if ($code === '4003')
                    throw new DDoSProtection ($message); // server is busy, try again later
            }
            throw new ExchangeError ($message);
        }
        if (!(is_array ($response) && array_key_exists ('result', $response)))
            throw new ExchangeError ($message);
        if ($method === 'GET') {
            return $response;
        } else {
            return $response['result'][0];
        }
    }
}
