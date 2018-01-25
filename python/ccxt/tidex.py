# -*- coding: utf-8 -*-

from ccxt.liqui import liqui

# -----------------------------------------------------------------------------

try:
    basestring  # Python 3
except NameError:
    basestring = str  # Python 2


class tidex (liqui):

    def describe(self):
        return self.deep_extend(super(tidex, self).describe(), {
            'id': 'tidex',
            'name': 'Tidex',
            'countries': 'UK',
            'rateLimit': 2000,
            'version': '3',
            'has': {
                # 'CORS': False,
                # 'fetchTickers': True
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/30781780-03149dc4-a12e-11e7-82bb-313b269d24d4.jpg',
                'api': {
                    'public': 'https://api.tidex.com/api',
                    'private': 'https://api.tidex.com/tapi',
                },
                'www': 'https://tidex.com',
                'doc': 'https://tidex.com/public-api',
                'fees': [
                    'https://tidex.com/assets-spec',
                    'https://tidex.com/pairs-spec',
                ],
            },
            'fees': {
                'trading': {
                    'tierBased': False,
                    'percentage': True,
                    'taker': 0.1 / 100,
                    'maker': 0.1 / 100,
                },
                'funding': {
                    'tierBased': False,
                    'percentage': False,
                    'withdraw': {
                        'BTC': 0.002,
                        'LTC': 0.001,
                        'ETH': 0.01,
                        'DASH': 0.01,
                        'DOGE': 0.01,
                        'BTS': 5.0,
                        'STEEM': 0.01,
                        'WAVES': 0.01,
                        'WCT': 0.01,
                        'WBTC': 0.0001,
                        'INCNT': 0.1,
                        'B': 0.1,
                        'MRT': 1.0,
                        'MER': 5.0,
                        'AQUA': 0.001,
                        'RBX': 100.0,
                        'TKS': 0.1,
                        'WUSD': 0.1,
                        'WEUR': 0.1,
                        'WGO': 1.0,
                        'GNT': 1.0,
                        'EDG': 1.0,
                        'RLC': 0.3,
                        'ICN': 0.3,
                        'WINGS': 1.0,
                        'VSL': 1.0,
                        'TIME': 0.01,
                        'TAAS': 0.3,
                        'KOLION': 0.1,
                        'RIDDLE': 10.0,
                        'ANT': 0.1,
                        'EFYT': 0.1,
                        'MGO': 0.5,
                        'wETT': 1.0,
                        'eETT': 1.0,
                        'QRL': 1.0,
                        'eMGO': 1.0,
                        'BNT': 1.0,
                        'SNM': 10.0,
                        'ZRC': 0.1,
                        'SNT': 30.0,
                        'MCO': 0.3,
                        'STORJ': 1.0,
                        'EOS': 0.3,
                        'WGR': 3.0,
                        'STA': 0.1,
                        'PBT': 0.0001,
                        'BCH': 0.00125,
                        'wSUR': 0.05,
                        'SUR': 0.05,
                        'MSP': 5.0,
                        'InPay': 0.5,
                        'MTL': 0.1,
                        'AHT': 0.2,
                        'PING': 1.0,
                        'EOT': 0.2,
                        'AE': 3.0,
                        'PIX': 10.0,
                        'CREDO': 30.0,
                        'LIFE': 1000.0,
                        'MTH': 5.0,
                        'BMC': 1.0,
                        'TRCT': 5.0,
                        'KNC': 1.0,
                        'MSD': 0.2,
                        'SUB': 10.0,
                        'ENJ': 20.0,
                        'EVX': 1.0,
                        'OCL': 3.0,
                        'ENG': 2.0,
                        'TDX': 1.0,
                        'LA': 2.0,
                        'PRG': 0.5,
                        'ICOS': 0.03,
                        'USDT': 40.0,
                        'ARN': 2.0,
                        'RYZ': 10.0,
                        'B2B': 1.0,
                        'CAT': 10.0,
                        'SNOV': 25.0,
                        'DRGN': 3.0,
                        'TIE': 20.0,
                        'TRX': 50.0,
                        'WAX': 5.0,
                        'AGI': 5.0,
                        'VEE': 20.0,
                    },
                    'deposit': {
                        'BTC': 0,
                        'ETH': 0,
                        'LTC': 0,
                        'DOGE': 0,
                        'ICN': 0,
                        'DASH': 0,
                        'GNO': 0,
                        'EOS': 0,
                        'BCH': 0,
                        'USDT': 0,
                    },
                },
            },
        })

    def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = self.fetch2(path, api, method, params, headers, body)
        # well yeah, they return HTTP 200 + {"success": 0, "error": "not available"}
        if not isinstance(response, basestring):
            self.handle_errors(None, None, None, None, None, self.last_http_response)
        return response
