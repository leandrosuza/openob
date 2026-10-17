"""Core constants"""




WEBSOCKET_ENDPOINTS = {
    "DEMO": "wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket",
    "api-eu": "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket",
    "api-c": "wss://api-c.po.market/socket.io/?EIO=4&transport=websocket",
    "api-fin": "wss://api-fin.po.market/socket.io/?EIO=4&transport=websocket",
    "api-fr2": "wss://api-fr2.po.market/socket.io/?EIO=4&transport=websocket",
    "api-us4": "wss://api-us4.po.market/socket.io/?EIO=4&transport=websocket",
    "api-us3": "wss://api-us3.po.market/socket.io/?EIO=4&transport=websocket",
    "api-us2": "wss://api-us2.po.market/socket.io/?EIO=4&transport=websocket",
    "api-us-north": "wss://api-us-north.po.market/socket.io/?EIO=4&transport=websocket",
    "api-sc": "wss://api-sc.po.market/socket.io/?EIO=4&transport=websocket",
    "api-hk": "wss://api-hk.po.market/socket.io/?EIO=4&transport=websocket",
    "api-msk": "wss://api-msk.po.market/socket.io/?EIO=4&transport=websocket",
    "api-l": "wss://api-l.po.market/socket.io/?EIO=4&transport=websocket",
    "api-in": "wss://api-in.po.market/socket.io/?EIO=4&transport=websocket",
    "api-fr": "wss://api-fr.po.market/socket.io/?EIO=4&transport=websocket",
    "api-asia": "wss://api-asia.po.market/socket.io/?EIO=4&transport=websocket",
    "api-us-south": "wss://api-us-south.po.market/socket.io/?EIO=4&transport=websocket",
}




REGIONS = list(WEBSOCKET_ENDPOINTS.keys())




ASSETS = {
    "EURUSD_otc": 66,
    "EURUSD": 1,
    "USDJPY": 2,
    "GBPUSD": 3,
    "AUDUSD": 4,
    "USDCAD": 5,
    "NZDUSD": 6,
    "USDCHF": 7,
    "EURJPY": 8,
    "GBPJPY": 9,
    "EURGBP": 10,
    "AUDJPY": 11,
    "CADJPY": 12,
    "CHFJPY": 13,
    "EURAUD": 14,
    "EURCAD": 15,
    "EURNZD": 16,
    "AUDNZD": 17,
    "AUDCAD": 18,
    "CADCHF": 19,
    "NZDJPY": 20,
    "GBPAUD": 21,
    "GBPCAD": 22,
    "GBPNZD": 23,
    "GBPAUD": 24,
    "EURNZD": 25,
    "AUDCHF": 26,
    "NZDCHF": 27,
    "NZDCAD": 28,
    "CADJPY": 29,
    "CHFJPY": 30,
}




TIMEFRAMES = {
    "5s": 5,
    "15s": 15,
    "30s": 30,
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}




API_LIMITS = {
    "min_order_amount": 1,
    "max_order_amount": 10000,
    "min_duration": 5,
    "max_duration": 3600,
}




CONNECTION_SETTINGS = {
    "ping_interval": 20,
    "ping_timeout": 10,
    "message_timeout": 30,
    "reconnect_delay": 5,
    "max_reconnect_attempts": 3,
}
