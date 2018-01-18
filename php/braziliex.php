<?php

namespace ccxt;

class braziliex extends Exchange {

    public function describe () {
        return array_replace_recursive (parent::describe (), array (
            'id' => 'braziliex',
            'name' => 'Braziliex',
            'countries' => 'BR',
            'rateLimit' => 1000,
            // obsolete metainfo interface
            'hasFetchTickers' => true,
            'hasFetchOpenOrders' => true,
            'hasFetchMyTrades' => true,
            // new metainfo interface
            'has' => array (
                'fetchTickers' => true,
                'fetchOpenOrders' => true,
                'fetchMyTrades' => true,
            ),
            'urls' => array (
                'logo' => 'https://user-images.githubusercontent.com/1294454/34703593-c4498674-f504-11e7-8d14-ff8e44fb78c1.jpg',
                'api' => 'https://braziliex.com/api/v1',
                'www' => 'https://braziliex.com/',
                'doc' => 'https://braziliex.com/exchange/api.php',
                'fees' => 'https://braziliex.com/exchange/fees.php',
            ),
            'api' => array (
                'public' => array (
                    'get' => array (
                        'currencies',
                        'ticker',
                        'ticker/{market}',
                        'orderbook/{market}',
                        'tradehistory/{market}',
                    ),
                ),
                'private' => array (
                    'post' => array (
                        'balance',
                        'complete_balance',
                        'open_orders',
                        'trade_history',
                        'deposit_address',
                        'sell',
                        'buy',
                        'cancel_order',
                    ),
                ),
            ),
            'fees' => array (
                'trading' => array (
                    'maker' => 0.005,
                    'taker' => 0.005,
                ),
            ),
            'precision' => array (
                'amount' => 8,
                'price' => 8,
            ),
        ));
    }

    public function fetch_currencies ($params = array ()) {
        $currencies = $this->publicGetCurrencies ($params);
        $ids = is_array ($currencies) ? array_keys ($currencies) : array ();
        $result = array ();
        for ($i = 0; $i < count ($ids); $i++) {
            $id = $ids[$i];
            $currency = $currencies[$id];
            $precision = $currency['decimal'];
            $uppercase = strtoupper ($id);
            $code = $this->common_currency_code($uppercase);
            $active = $currency['active'] == 1;
            $status = 'ok';
            if ($currency['under_maintenance'] != 0) {
                $active = false;
                $status = 'maintenance';
            }
            $canWithdraw = $currency['is_withdrawal_active'] == 1;
            $canDeposit = $currency['is_deposit_active'] == 1;
            if (!$canWithdraw || !$canDeposit)
                $active = false;
            $result[$code] = array (
                'id' => $id,
                'code' => $code,
                'name' => $currency['name'],
                'active' => $active,
                'status' => $status,
                'precision' => $precision,
                'wallet' => array (
                    'address' => null,
                    'extra' => null,
                    'withdraw' => array (
                        'active' => $canWithdraw,
                        'fee' => $currency['txWithdrawalFee'],
                    ),
                    'deposit' => array (
                        'active' => $canDeposit,
                        'fee' => $currency['txDepositFee'],
                    ),
                ),
                'limits' => array (
                    'amount' => array (
                        'min' => $currency['minAmountTrade'],
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
                        'min' => $currency['MinWithdrawal'],
                        'max' => pow (10, $precision),
                    ),
                    'deposit' => array (
                        'min' => $currency['minDeposit'],
                        'max' => null,
                    ),
                ),
                'info' => $currency,
            );
        }
        return $result;
    }

    public function fetch_markets () {
        $markets = $this->publicGetTicker ();
        $ids = is_array ($markets) ? array_keys ($markets) : array ();
        $result = array ();
        for ($i = 0; $i < count ($ids); $i++) {
            $id = $ids[$i];
            $market = $markets[$id];
            list ($baseId, $quoteId) = explode ('_', $id);
            $base = strtoupper ($baseId);
            $quote = strtoupper ($quoteId);
            $base = $this->common_currency_code($base);
            $quote = $this->common_currency_code($quote);
            $symbol = $base . '/' . $quote;
            $active = $market['active'] == 1;
            $precision = array (
                'amount' => 8,
                'price' => 8,
            );
            $lot = pow (10, -$precision['amount']);
            $result[] = array (
                'id' => $id,
                'symbol' => strtoupper ($symbol),
                'base' => $base,
                'quote' => $quote,
                'baseId' => $baseId,
                'quoteId' => $quoteId,
                'active' => $active,
                'lot' => $lot,
                'precision' => $precision,
                'limits' => array (
                    'amount' => array (
                        'min' => $lot,
                        'max' => pow (10, $precision['amount']),
                    ),
                    'price' => array (
                        'min' => pow (10, -$precision['price']),
                        'max' => pow (10, $precision['price']),
                    ),
                    'cost' => array (
                        'min' => null,
                        'max' => null,
                    ),
                ),
                'info' => $market,
            );
        }
        return $result;
    }

    public function parse_ticker ($ticker, $market = null) {
        $symbol = $market['symbol'];
        $timestamp = $ticker['date'];
        $ticker = $ticker['ticker'];
        return array (
            'symbol' => $symbol,
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'high' => floatval ($ticker['highestBid24']),
            'low' => floatval ($ticker['lowestAsk24']),
            'bid' => floatval ($ticker['highestBid']),
            'ask' => floatval ($ticker['lowestAsk']),
            'vwap' => null,
            'open' => null,
            'close' => null,
            'first' => null,
            'last' => floatval ($ticker['last']),
            'change' => floatval ($ticker['percentChange']),
            'percentage' => null,
            'average' => null,
            'baseVolume' => floatval ($ticker['baseVolume24']),
            'quoteVolume' => floatval ($ticker['quoteVolume24']),
            'info' => $ticker,
        );
    }

    public function fetch_ticker ($symbol, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $ticker = $this->publicGetTickerMarket (array_merge (array (
            'market' => $market['id'],
        ), $params));
        $ticker = array (
            'date' => $this->milliseconds (),
            'ticker' => $ticker,
        );
        return $this->parse_ticker($ticker, $market);
    }

    public function fetch_tickers ($symbols = null, $params = array ()) {
        $this->load_markets();
        $tickers = $this->publicGetTicker ($params);
        $result = array ();
        $timestamp = $this->milliseconds ();
        $ids = is_array ($tickers) ? array_keys ($tickers) : array ();
        for ($i = 0; $i < count ($ids); $i++) {
            $id = $ids[$i];
            $market = $this->markets_by_id[$id];
            $symbol = $market['symbol'];
            $ticker = array (
                'date' => $timestamp,
                'ticker' => $tickers[$id],
            );
            $result[$symbol] = $this->parse_ticker($ticker, $market);
        }
        return $result;
    }

    public function fetch_order_book ($symbol, $params = array ()) {
        $this->load_markets();
        $orderbook = $this->publicGetOrderbookMarket (array_merge (array (
            'market' => $this->market_id($symbol),
        ), $params));
        return $this->parse_order_book($orderbook, null, 'bids', 'asks', 'price', 'amount');
    }

    public function parse_trade ($trade, $market = null) {
        $timestamp = null;
        if (is_array ($trade) && array_key_exists ('date_exec', $trade)) {
            $timestamp = $this->parse8601 ($trade['date_exec']);
        } else {
            $timestamp = $this->parse8601 ($trade['date']);
        }
        $price = floatval ($trade['price']);
        $amount = floatval ($trade['amount']);
        $symbol = $market['symbol'];
        $cost = floatval ($trade['total']);
        $orderId = $this->safe_string($trade, 'order_number');
        return array (
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'symbol' => $symbol,
            'id' => $this->safe_string($trade, '_id'),
            'order' => $orderId,
            'type' => 'limit',
            'side' => $trade['type'],
            'price' => $price,
            'amount' => $amount,
            'cost' => $cost,
            'fee' => null,
            'info' => $trade,
        );
    }

    public function fetch_trades ($symbol, $since = null, $limit = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $trades = $this->publicGetTradehistoryMarket (array_merge (array (
            'market' => $market['id'],
        ), $params));
        return $this->parse_trades($trades, $market, $since, $limit);
    }

    public function fetch_balance ($params = array ()) {
        $this->load_markets();
        $balances = $this->privatePostCompleteBalance ($params);
        $result = array ( 'info' => $balances );
        $currencies = is_array ($balances) ? array_keys ($balances) : array ();
        for ($i = 0; $i < count ($currencies); $i++) {
            $id = $currencies[$i];
            $balance = $balances[$id];
            $currency = $this->common_currency_code($id);
            $account = array (
                'free' => floatval ($balance['available']),
                'used' => 0.0,
                'total' => floatval ($balance['total']),
            );
            $account['used'] = $account['total'] - $account['free'];
            $result[$currency] = $account;
        }
        return $this->parse_balance($result);
    }

    public function parse_order ($order, $market = null) {
        $symbol = null;
        if (!$market) {
            $marketId = $this->safe_string($order, 'market');
            if ($marketId)
                if (is_array ($this->markets_by_id) && array_key_exists ($marketId, $this->markets_by_id))
                    $market = $this->markets_by_id[$marketId];
        }
        if ($market)
            $symbol = $market['symbol'];
        $timestamp = $this->safe_value($order, 'timestamp');
        if (!$timestamp)
            $timestamp = $this->parse8601 ($order['date']);
        $price = floatval ($order['price']);
        $cost = $this->safe_float($order, 'total', 0.0);
        $amount = $this->safe_float($order, 'amount');
        $filledPercentage = $this->safe_float($order, 'progress');
        $filled = $amount * $filledPercentage;
        $remaining = $this->amount_to_precision($symbol, $amount - $filled);
        $info = $order;
        if (is_array ($info) && array_key_exists ('info', $info))
            $info = $order['info'];
        return array (
            'id' => $order['order_number'],
            'datetime' => $this->iso8601 ($timestamp),
            'timestamp' => $timestamp,
            'status' => 'open',
            'symbol' => $symbol,
            'type' => 'limit',
            'side' => $order['type'],
            'price' => $price,
            'cost' => $cost,
            'amount' => $amount,
            'filled' => $filled,
            'remaining' => $remaining,
            'trades' => null,
            'fee' => $this->safe_value($order, 'fee'),
            'info' => $info,
        );
    }

    public function create_order ($symbol, $type, $side, $amount, $price = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $method = 'privatePost' . $this->capitalize ($side);
        $response = $this->$method (array_merge (array (
            'market' => $market['id'],
            // 'price' => $this->price_to_precision($symbol, $price),
            // 'amount' => $this->amount_to_precision($symbol, $amount),
            'price' => $price,
            'amount' => $amount,
        ), $params));
        $success = $this->safe_integer($response, 'success');
        if ($success != 1)
            throw new InvalidOrder ($this->id . ' ' . $this->json ($response));
        $parts = explode (' / ', $response['message']);
        $parts = mb_substr ($parts, 1);
        $feeParts = explode (' ', $parts[5]);
        $order = $this->parse_order(array (
            'timestamp' => $this->milliseconds (),
            'order_number' => $response['order_number'],
            'type' => strtolower ($parts[0]),
            'market' => strtolower ($parts[0]),
            'amount' => explode (' ', $parts[2])[1],
            'price' => explode (' ', $parts[3])[1],
            'total' => explode (' ', $parts[4])[1],
            'fee' => array (
                'cost' => floatval ($feeParts[1]),
                'currency' => $feeParts[2],
            ),
            'progress' => '0.0',
            'info' => $response,
        ), $market);
        $id = $order['id'];
        $this->orders[$id] = $order;
        return $order;
    }

    public function cancel_order ($id, $symbol = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $result = $this->privatePostCancelOrder (array_merge (array (
            'order_number' => $id,
            'market' => $market['id'],
        ), $params));
        return $result;
    }

    public function fetch_open_orders ($symbol = null, $since = null, $limit = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $orders = $this->privatePostOpenOrders (array_merge (array (
            'market' => $market['id'],
        ), $params));
        return $this->parse_orders($orders['order_open'], $market, $since, $limit);
    }

    public function fetch_my_trades ($symbol = null, $since = null, $limit = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $trades = $this->privatePostTradeHistory (array_merge (array (
            'market' => $market['id'],
        ), $params));
        return $this->parse_trades($trades['trade_history'], $market, $since, $limit);
    }

    public function fetch_deposit_address ($currencyCode, $params = array ()) {
        $this->load_markets();
        $currency = $this->currency ($currencyCode);
        $response = $this->privatePostDepositAddress (array_merge (array (
            'currency' => $currency['id'],
        ), $params));
        $address = $this->safe_string($response, 'deposit_address');
        if (!$address)
            throw new ExchangeError ($this->id . ' fetchDepositAddress failed => ' . $this->last_http_response);
        $tag = $this->safe_string($response, 'payment_id');
        return array (
            'currency' => $currencyCode,
            'address' => $address,
            'tag' => $tag,
            'status' => 'ok',
            'info' => $response,
        );
    }

    public function sign ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $url = $this->urls['api'] . '/' . $api;
        $query = $this->omit ($params, $this->extract_params($path));
        if ($api == 'public') {
            $url .= '/' . $this->implode_params($path, $params);
            if ($query)
                $url .= '?' . $this->urlencode ($query);
        } else {
            $this->check_required_credentials();
            $query = array_merge (array (
                'command' => $path,
                'nonce' => $this->nonce (),
            ), $query);
            $body = $this->urlencode ($query);
            $signature = $this->hmac ($this->encode ($body), $this->encode ($this->secret), 'sha512');
            $headers = array (
                'Content-type' => 'application/x-www-form-urlencoded',
                'Key' => $this->apiKey,
                'Sign' => $this->decode ($signature),
            );
        }
        return array ( 'url' => $url, 'method' => $method, 'body' => $body, 'headers' => $headers );
    }

    public function request ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $response = $this->fetch2 ($path, $api, $method, $params, $headers, $body);
        if (is_array ($response) && array_key_exists ('success', $response)) {
            $success = $this->safe_integer($response, 'success');
            if ($success == 0) {
                $message = $this->safe_string($response, 'message');
                if ($message == 'Invalid APIKey')
                    throw new AuthenticationError ($message);
                throw new ExchangeError ($message);
            }
        }
        return $response;
    }
}
