<?php

namespace ccxt;

include_once ('base/Exchange.php');

class bxinth extends Exchange {

    public function describe () {
        return array_replace_recursive (parent::describe (), array (
            'id' => 'bxinth',
            'name' => 'BX.in.th',
            'countries' => 'TH', // Thailand
            'rateLimit' => 1500,
            'hasCORS' => false,
            'hasFetchTickers' => true,
            'urls' => array (
                'logo' => 'https://user-images.githubusercontent.com/1294454/27766412-567b1eb4-5ed7-11e7-94a8-ff6a3884f6c5.jpg',
                'api' => 'https://bx.in.th/api',
                'www' => 'https://bx.in.th',
                'doc' => 'https://bx.in.th/info/api',
            ),
            'api' => array (
                'public' => array (
                    'get' => array (
                        '', // ticker
                        'options',
                        'optionbook',
                        'orderbook',
                        'pairing',
                        'trade',
                        'tradehistory',
                    ),
                ),
                'private' => array (
                    'post' => array (
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
                    ),
                ),
            ),
            'fees' => array (
                'trading' => array (
                    'taker' => 0.25 / 100,
                    'maker' => 0.25 / 100,
                ),
            ),
        ));
    }

    public function fetch_markets () {
        $markets = $this->publicGetPairing ();
        $keys = array_keys ($markets);
        $result = array ();
        for ($p = 0; $p < count ($keys); $p++) {
            $market = $markets[$keys[$p]];
            $id = (string) $market['pairing_id'];
            $base = $market['secondary_currency'];
            $quote = $market['primary_currency'];
            $base = $this->common_currency_code($base);
            $quote = $this->common_currency_code($quote);
            $symbol = $base . '/' . $quote;
            $result[] = array (
                'id' => $id,
                'symbol' => $symbol,
                'base' => $base,
                'quote' => $quote,
                'info' => $market,
            );
        }
        return $result;
    }

    public function common_currency_code ($currency) {
        // why would they use three letters instead of four for $currency codes
        if ($currency == 'DAS')
            return 'DASH';
        if ($currency == 'DOG')
            return 'DOGE';
        return $currency;
    }

    public function fetch_balance ($params = array ()) {
        $this->load_markets();
        $response = $this->privatePostBalance ();
        $balance = $response['balance'];
        $result = array ( 'info' => $balance );
        $currencies = array_keys ($balance);
        for ($c = 0; $c < count ($currencies); $c++) {
            $currency = $currencies[$c];
            $code = $this->common_currency_code($currency);
            $account = array (
                'free' => floatval ($balance[$currency]['available']),
                'used' => 0.0,
                'total' => floatval ($balance[$currency]['total']),
            );
            $account['used'] = $account['total'] - $account['free'];
            $result[$code] = $account;
        }
        return $this->parse_balance($result);
    }

    public function fetch_order_book ($symbol, $params = array ()) {
        $this->load_markets();
        $orderbook = $this->publicGetOrderbook (array_merge (array (
            'pairing' => $this->market_id($symbol),
        ), $params));
        return $this->parse_order_book($orderbook);
    }

    public function parse_ticker ($ticker, $market = null) {
        $timestamp = $this->milliseconds ();
        $symbol = null;
        if ($market)
            $symbol = $market['symbol'];
        return array (
            'symbol' => $symbol,
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'high' => null,
            'low' => null,
            'bid' => floatval ($ticker['orderbook']['bids']['highbid']),
            'ask' => floatval ($ticker['orderbook']['asks']['highbid']),
            'vwap' => null,
            'open' => null,
            'close' => null,
            'first' => null,
            'last' => floatval ($ticker['last_price']),
            'change' => floatval ($ticker['change']),
            'percentage' => null,
            'average' => null,
            'baseVolume' => floatval ($ticker['volume_24hours']),
            'quoteVolume' => null,
            'info' => $ticker,
        );
    }

    public function fetch_tickers ($symbols = null, $params = array ()) {
        $this->load_markets();
        $tickers = $this->publicGet ($params);
        $result = array ();
        $ids = array_keys ($tickers);
        for ($i = 0; $i < count ($ids); $i++) {
            $id = $ids[$i];
            $ticker = $tickers[$id];
            $market = $this->markets_by_id[$id];
            $symbol = $market['symbol'];
            $result[$symbol] = $this->parse_ticker($ticker, $market);
        }
        return $result;
    }

    public function fetch_ticker ($symbol, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $tickers = $this->publicGet (array_merge (array (
            'pairing' => $market['id'],
        ), $params));
        $id = (string) $market['id'];
        $ticker = $tickers[$id];
        return $this->parse_ticker($ticker, $market);
    }

    public function parse_trade ($trade, $market) {
        $timestamp = $this->parse8601 ($trade['trade_date']);
        return array (
            'id' => $trade['trade_id'],
            'info' => $trade,
            'order' => $trade['order_id'],
            'timestamp' => $timestamp,
            'datetime' => $this->iso8601 ($timestamp),
            'symbol' => $market['symbol'],
            'type' => null,
            'side' => $trade['trade_type'],
            'price' => floatval ($trade['rate']),
            'amount' => $trade['amount'],
        );
    }

    public function fetch_trades ($symbol, $since = null, $limit = null, $params = array ()) {
        $this->load_markets();
        $market = $this->market ($symbol);
        $response = $this->publicGetTrade (array_merge (array (
            'pairing' => $market['id'],
        ), $params));
        return $this->parse_trades($response['trades'], $market, $since, $limit);
    }

    public function create_order ($symbol, $type, $side, $amount, $price = null, $params = array ()) {
        $this->load_markets();
        $response = $this->privatePostOrder (array_merge (array (
            'pairing' => $this->market_id($symbol),
            'type' => $side,
            'amount' => $amount,
            'rate' => $price,
        ), $params));
        return array (
            'info' => $response,
            'id' => (string) $response['order_id'],
        );
    }

    public function cancel_order ($id, $symbol = null, $params = array ()) {
        $this->load_markets();
        $pairing = null; // TODO fixme
        return $this->privatePostCancel (array (
            'order_id' => $id,
            'pairing' => $pairing,
        ));
    }

    public function sign ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $url = $this->urls['api'] . '/';
        if ($path)
            $url .= $path . '/';
        if ($params)
            $url .= '?' . $this->urlencode ($params);
        if ($api == 'private') {
            $this->check_required_credentials();
            $nonce = $this->nonce ();
            $auth = $this->apiKey . (string) $nonce . $this->secret;
            $signature = $this->hash ($this->encode ($auth), 'sha256');
            $body = $this->urlencode (array_merge (array (
                'key' => $this->apiKey,
                'nonce' => $nonce,
                'signature' => $signature,
                // twofa => $this->twofa,
            ), $params));
            $headers = array (
                'Content-Type' => 'application/x-www-form-urlencoded',
            );
        }
        return array ( 'url' => $url, 'method' => $method, 'body' => $body, 'headers' => $headers );
    }

    public function request ($path, $api = 'public', $method = 'GET', $params = array (), $headers = null, $body = null) {
        $response = $this->fetch2 ($path, $api, $method, $params, $headers, $body);
        if ($api == 'public')
            return $response;
        if (is_array ($response) && array_key_exists ('success', $response))
            if ($response['success'])
                return $response;
        throw new ExchangeError ($this->id . ' ' . $this->json ($response));
    }
}

?>