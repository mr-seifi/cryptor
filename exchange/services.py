import re
import time
import base64
import hmac
import hashlib
import json
from uuid import uuid4
from requests.sessions import Session
from _helpers import singleton
from market.models import Signal
from account.models import User
from market.services import MarketService


class BaseKuCoinService:
    SANDBOX = False
    URLS = {'URL': 'https://api-futures.kucoin.com',
            'SANDBOX_URL': 'https://api-sandbox-futures.kucoin.com'}
    REQUESTS = {
        'get_account_overview': {
            'method': 'GET',
            'endpoint': '/api/v1/account-overview'
        },
        'place_order': {
            'method': 'POST',
            'endpoint': '/api/v1/orders'
        },
        'cancel_order': {
            'method': 'DELETE',
            'endpoint': '/api/v1/orders/{order_id}'
        },
        'get_order_list': {
            'method': 'GET',
            'endpoint': '/api/v1/orders'
        },
        'limit_order_mass_cancellation': {
            'method': 'DELETE',
            'endpoint': '/api/v1/orders'
        },
        'stop_order_mass_cancellation': {
            'method': 'DELETE',
            'endpoint': '/api/v1/stopOrders'
        },
        'get_open_contract_list': {
            'method': 'GET',
            'endpoint': '/api/v1/contracts/active'
        },
        'get_contract_info': {
            'method': 'GET',
            'endpoint': '/api/v1/contracts/{symbol}'
        },
        'get_position_list': {
            'method': 'GET',
            'endpoint': '/api/v1/positions'
        },
        'get_untriggered_stop_order_list': {
            'method': 'GET',
            'endpoint': '/api/v1/stopOrders'
        },
    }
    LOCKED = False

    def __init__(self):
        self.session = Session()
        self.BASE_URL = (self.URLS['URL'], self.URLS['SANDBOX_URL'])[self.SANDBOX]

    def refresh_session(self):
        if not self.LOCKED:
            self.__init__()

    @staticmethod
    def _generate_signature(api_secret: str, method: str, endpoint: str, data=None):
        now = int(time.time() * 1000)
        str_to_sign = '{now}{method}{endpoint}'.format(now=now,
                                                       method=method.upper(),
                                                       endpoint=endpoint)
        if data:
            str_to_sign += data

        signature = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

        return signature, now

    @staticmethod
    def _generate_passphrase(api_secret: str, api_passphrase: str):
        passphrase = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())

        return passphrase

    @classmethod
    def get_header(cls, api_key: str, api_secret: str, api_passphrase: str,
                   method: str, endpoint: str, is_json=False, data=None):
        signature, now = cls._generate_signature(api_secret=api_secret,
                                                 method=method,
                                                 endpoint=endpoint,
                                                 data=data)
        passphrase = cls._generate_passphrase(api_secret=api_secret,
                                              api_passphrase=api_passphrase)

        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2"
        }

        if is_json:
            headers['Content-Type'] = 'application/json'

        return headers

    @staticmethod
    def _params_to_endpoint(endpoint: str, **kwargs) -> str:

        endpoint += '?'
        for key in kwargs.keys():
            endpoint += f'{key}={kwargs[key]}&'
        endpoint = endpoint[:-1]

        return endpoint

    @staticmethod
    def _make_endpoint_format(endpoint: str, **kwargs) -> (str, list,):
        keys = re.findall(r'/{(.+?)}', endpoint)
        params_dict = {key: kwargs[key] for key in kwargs.keys()}

        endpoint = endpoint.format(**params_dict)

        return endpoint, keys

    def _request(self, api_key: str, api_secret: str, api_passphrase: str,
                 method: str, endpoint: str, data=None) -> (int, str,):
        self.LOCKED = True

        url = f'{self.BASE_URL}{endpoint}'

        data_json = json.dumps(data).replace(' ', '')
        data_json = (data_json, None)[data_json in ('null', '{}')]

        header = self.get_header(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase,
                                 method=method, endpoint=endpoint, is_json=True, data=data_json)
        response = self.session.request(method=method, url=url, headers=header, data=data_json)

        self.LOCKED = False
        return response.status_code, response.json()

    def request(self, api_key: str, api_secret: str, api_passphrase: str, point: str, **kwargs):
        req = self.REQUESTS.get(point)
        endpoint = req.get('endpoint')
        method = req.get('method')

        endpoint, keys = self._make_endpoint_format(endpoint=endpoint, **kwargs)
        [kwargs.pop(key) for key in keys]

        endpoint = self._params_to_endpoint(endpoint=endpoint, **kwargs)
        return self._request(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase,
                             method=method, endpoint=endpoint, data=kwargs)


@singleton
class KuCoinService(BaseKuCoinService):

    def get_account_overview(self, **kwargs):
        """
        HTTP Request
        GET /api/v1/account-overview

        Example
        GET /api/v1/account-overview?currency=XBT

        Parameters
        Param	Type	Description
        currency	String	[Optional] Currecny ,including XBT,USDT,Default XBT
        RESPONSES
        Field	Description
        accountEquity	Account equity = marginBalance + Unrealised PNL
        unrealisedPNL	Unrealised profit and loss
        marginBalance	Margin balance = positionMargin + orderMargin + frozenFunds + availableBalance - unrealisedPNL
        positionMargin	Position margin
        orderMargin	Order margin
        frozenFunds	Frozen funds for withdrawal and out-transfer
        availableBalance	Available balance
        currency	currency code
        API Permission
        This endpoint requires the General permission.

        REQUEST RATE LIMIT
        This API is restricted for each account, the request rate limit is 30 times/3s.
        """

        return self.request(point='get_account_overview', **kwargs)

    def _place_order(self, **kwargs):
        """
        You can place two types of orders: limit and market. Orders can only be placed if your account
        has sufficient funds. Once an order is placed, your funds will be put on hold for the duration of the order.
        The amount of funds on hold depends on the order type and parameters specified.

        Please be noted that the system would hold the fees from the orders entered the orderbook in advance.
         Read Get Fills to learn more.

        Do NOT include extra spaces in JSON strings.

        Place Order Limit:
        The maximum limit orders for a single contract is 100 per account, and the maximum stop orders
         for a single contract is 50 per account.

        HTTP Request
        POST /api/v1/orders

        API Permission
        This endpoint requires the Trade permission

        REQUEST RATE LIMIT
        This API is restricted for each account, the request rate limit is 30 times/3s.

        Parameters
        Param	type	Description
        clientOid	String	Unique order id created by users to identify their orders, e.g. UUID, Only allows numbers,
         characters, underline(_), and separator(-)
        side	String	buy or sell
        symbol	String	a valid contract code. e.g. XBTUSDM
        type	String	[optional] Either limit or market
        leverage	String	Leverage of the order
        remark	String	[optional] remark for the order, length cannot exceed 100 utf8 characters
        stop	String	[optional] Either down or up. Requires stopPrice and stopPriceType to be defined
        stopPriceType	String	[optional] Either TP, IP or MP, Need to be defined if stop is specified.
        stopPrice	String	[optional] Need to be defined if stop is specified.
        reduceOnly	boolean	[optional] A mark to reduce the position size only. Set to false by default.
         Need to set the position size when reduceOnly is true.
        closeOrder	boolean	[optional] A mark to close the position. Set to false by default.
         It will close all the positions when closeOrder is true.
        forceHold	boolean	[optional] A mark to forcely hold the funds for an order, even though
         it's an order to reduce the position size. This helps the order stay on the order book and
          not get canceled when the position size changes. Set to false by default.
        See Advanced Description for more details.

        LIMIT ORDER PARAMETERS
        Param	type	Description
        price	String	Limit price
        size	Integer	Order size. Must be a positive number
        timeInForce	String	[optional] GTC, IOC(default is GTC), read Time In Force
        postOnly	boolean	[optional] Post only flag, invalid when timeInForce is IOC. When postOnly chose,
         not allowed choose hidden or iceberg.
        hidden	boolean	[optional] Orders not displaying in order book. When hidden chose, not allowed choose postOnly.
        iceberg	boolean	[optional] Only visible portion of the order is displayed in the order book.
         When iceberg chose, not allowed choose postOnly.
        visibleSize	Integer	[optional] The maximum visible size of an iceberg order
        MARKET ORDER PARAMETERS
        Param	type	Description
        size	Integer	[optional] amount of contract to buy or sell
        RESPONSES
        Param	Type
        orderId	Order ID.
        Example
        POST /api/v1/orders

        """

        return self.request(point='place_order', **kwargs)

    def cancel_order(self, **kwargs):
        """
        Cancel an order (including a stop order).

        You will receive success message once the system has received the cancellation request. The cancellation request will be processed by matching engine in sequence. To know if the request has been processed, you may check the order status or update message from the pushes.

        The order id is the server-assigned order id，not the specified clientOid.

        If the order can not be canceled (already filled or previously canceled, etc), then an error response will indicate the reason in the message field.
        HTTP Request

        DELETE /api/v1/orders/{order-id}
        Example

        DELETE /api/v1/orders/5cdfc120b21023a909e5ad52
        API Permission

        This endpoint requires the Trade permission.
        REQUEST RATE LIMIT

        This API is restricted for each account, the request rate limit is 40 times/3s.
        RESPONSES
        Param 	Type
        cancelledOrderIds 	cancelled OrderIds.
        """

        return self.request(point='cancel_order', **kwargs)

    def _get_open_contract_list(self, **kwargs):
        """
        Submit request to get the info of all open contracts.

        HTTP Request
        GET /api/v1/contracts/active

        Example
        GET /api/v1/contracts/active

        PARAMETERS
        N/A

        RESPONSES
        Field	Description
        symbol	Contract status
        rootSymbol	Contract group
        type	Type of the contract
        firstOpenDate	First Open Date
        expireDate	Expiration date. Null means it will never expire
        settleDate	Settlement date. Null indicates that automatic settlement is not supported
        baseCurrency	Base currency
        quoteCurrency	Quote currency
        settleCurrency	Currency used to clear and settle the trades
        maxOrderQty	Maximum order quantity
        maxPrice	Maximum order price
        lotSize	Minimum lot size
        tickSize	Minimum price changes
        indexPriceTickSize	Index price of tick size
        multiplier	Contract multiplier
        initialMargin	Initial margin requirement
        maintainMargin	Maintenance margin requirement
        maxRiskLimit	Maximum risk limit (unit: XBT)
        minRiskLimit	Minimum risk limit (unit: XBT)
        riskStep	Risk limit increment value (unit: XBT)
        makerFeeRate	Maker fees
        takerFeeRate	Taker fees
        takerFixFee	Fixed taker fees(Deprecated field, no actual use of the value field)
        makerFixFee	Fixed maker fees(Deprecated field, no actual use of the value field)
        settlementFee	settlement fee
        isDeleverage	Enabled ADL or not
        isQuanto	Whether quanto or not(Deprecated field, no actual use of the value field)
        isInverse	Reverse contract or not
        markMethod	Marking method
        fairMethod	Fair price marking method
        fundingBaseSymbol	Ticker symbol of the based currency
        fundingQuoteSymbol	Ticker symbol of the quote currency
        fundingRateSymbol	Funding rate symbol
        indexSymbol	Index symbol
        settlementSymbol	Settlement Symbol
        status	Contract status
        fundingFeeRate	Funding fee rate
        predictedFundingFeeRate	Predicted funding fee rate
        openInterest	open interest
        turnoverOf24h	turnover of 24 hours
        volumeOf24h	volume of 24 hours
        markPrice	Mark price
        indexPrice	Index price
        lastTradePrice	last trade price
        nextFundingRateTime	next funding rate time
        maxLeverage	maximum leverage
        sourceExchanges	The contract index source exchange
        premiumsSymbol1M	Premium index symbol (1 minute)
        premiumsSymbol8H	Premium index symbol (8 hours)
        fundingBaseSymbol1M	Base currency interest rate symbol (1 minute)
        fundingQuoteSymbol1M	Quote currency interest rate symbol (1 minute)
        lowPrice	24H Low
        highPrice	24H High
        priceChgPct	24H Change%
        priceChg	24H Change
        """

        return self.request(point='get_open_contract_list', **kwargs)

    def stop_order_mass_cancellation(self, **kwargs):
        """
        Cancel all untriggered stop orders. The response is a list of orderIDs of the canceled stop orders.
         To cancel triggered stop orders, please use 'Limit Order Mass Cancelation'.

        HTTP Request
        DELETE /api/v1/stopOrders

        Example
        DELETE /api/v1/stopOrders?symbol=XBTUSDM

        API Permission
        This endpoint requires the Trade permission.

        PARAMETERS
        You can delete specific symbol using query parameters.

        Param	Type	Description
        symbol	String	[optional] Cancel all untriggered stop orders for a specific contract only
        RESPONSES
        Param	Type
        cancelledOrderIds	cancelled OrderIds.
        """

        return self.request(point='stop_order_mass_cancellation', **kwargs)

    def limit_order_mass_cancellation(self, **kwargs):
        """
        Cancel all open orders (excluding stop orders). The response is a list of orderIDs of the canceled orders.

        HTTP Request
        DELETE /api/v1/orders

        Example
        DELETE /api/v1/orders?symbol=XBTUSDM

        API Permission
        This endpoint requires the Trade permission.

        REQUEST RATE LIMIT
        This API is restricted for each account, the request rate limit is 9 times/3s.

        PARAMETERS
        Param	Type	Description
        symbol	String	[optional] Cancel all limit orders for a specific contract only
        You can delete specific symbol using query parameters. If not specified, all the limit orders will be deleted.

        RESPONSES
        Param	Type
        cancelledOrderIds	cancelled OrderIds.
        """

        return self.request(point='limit_order_mass_cancellation', **kwargs)

    def _get_contract_info(self, **kwargs):
        """
        Submit request to get info of the specified contract.

        HTTP Request
        GET /api/v1/contracts/{symbol}

        Example
        GET /api/v1/contracts/XBTUSDM

        PARAMETERS
        Param	Type	Description
        symbol	String	Path Parameter. Symbol of the contract
        RESPONSES
        Field	Description
        symbol	Contract status
        rootSymbol	Contract group
        type	Type of the contract
        firstOpenDate	First Open Date
        expireDate	Expiration date. Null means it will never expire
        settleDate	Settlement date. Null indicates that automatic settlement is not supported
        baseCurrency	Base currency
        quoteCurrency	Quote currency
        settleCurrency	Currency used to clear and settle the trades
        maxOrderQty	Maximum order quantity
        maxPrice	Maximum order price
        lotSize	Minimum lot size
        tickSize	Minimum price changes
        indexPriceTickSize	Index price of tick size
        multiplier	Contract multiplier
        initialMargin	Initial margin requirement
        maintainMargin	Maintenance margin requirement
        maxRiskLimit	Maximum risk limit (unit: XBT)
        minRiskLimit	Minimum risk limit (unit: XBT)
        riskStep	Risk limit increment value (unit: XBT)
        makerFeeRate	Maker fees
        takerFeeRate	Taker fees
        takerFixFee	Fixed taker fees(Deprecated field, no actual use of the value field)
        makerFixFee	Fixed maker fees(Deprecated field, no actual use of the value field)
        settlementFee	settlement fee
        isDeleverage	Enabled ADL or not
        isQuanto	Whether quanto or not(Deprecated field, no actual use of the value field)
        isInverse	Reverse contract or not
        markMethod	Marking method
        fairMethod	Fair price marking method
        fundingBaseSymbol	Ticker symbol of the based currency
        fundingQuoteSymbol	Ticker symbol of the quote currency
        fundingRateSymbol	Funding rate symbol
        indexSymbol	Index symbol
        settlementSymbol	Settlement Symbol
        status	Contract status
        fundingFeeRate	Funding fee rate
        predictedFundingFeeRate	Predicted funding fee rate
        openInterest	open interest
        turnoverOf24h	turnover of 24 hours
        volumeOf24h	volume of 24 hours
        markPrice	Mark price
        indexPrice	Index price
        lastTradePrice	last trade price
        nextFundingRateTime	next funding rate time
        maxLeverage	maximum leverage
        sourceExchanges	The contract index source exchange
        premiumsSymbol1M	Premium index symbol (1 minute)
        premiumsSymbol8H	Premium index symbol (8 hours)
        fundingBaseSymbol1M	Base currency interest rate symbol (1 minute)
        fundingQuoteSymbol1M	Quote currency interest rate symbol (1 minute)
        lowPrice	24H Low
        highPrice	24H High
        priceChgPct	24H Change%
        priceChg	24H Change
        """

        return self.request(point='get_contract_info', **kwargs)

    def get_order_list(self, **kwargs):
        """
        List your current orders.
        HTTP Request

        GET /api/v1/orders
        Example

        GET /api/v1/orders?status=active
        Submit the request to get all the active orders.
        API Permission

        This endpoint requires the General permission.
        REQUEST RATE LIMIT

        This API is restricted for each account, the request rate limit is 30 times/3s.
        PARAMETERS

        You can request for specific orders using query parameters.
        Param 	Type 	Description
        status 	String 	[optional] active or done, done as default. Only list orders for a specific status
        symbol 	String 	[optional] Symbol of the contract
        side 	String 	[optional] buy or sell
        type 	String 	[optional] limit, market, limit_stop or market_stop
        startAt 	long 	[optional] Start time (milisecond)
        endAt 	long 	[optional] End time (milisecond)
        RESPONSES
        Param 	Type
        id 	Order ID
        symbol 	Symbol of the contract
        type 	Order type, market order or limit order
        side 	Transaction side
        price 	Order price
        size 	Order quantity
        value 	Order value
        dealValue 	Executed size of funds
        dealSize 	Executed quantity
        stp 	Self trade prevention types
        stop 	Stop order type (stop limit or stop market)
        stopPriceType 	Trigger price type of stop orders
        stopTriggered 	Mark to show whether the stop order is triggered
        stopPrice 	Trigger price of stop orders
        timeInForce 	Time in force policy type
        postOnly 	Mark of post only
        hidden 	Mark of the hidden order
        iceberg 	Mark of the iceberg order
        leverage 	Leverage of the order
        forceHold 	A mark to forcely hold the funds for an order
        closeOrder 	A mark to close the position
        visibleSize 	Visible size of the iceberg order
        clientOid 	Unique order id created by users to identify their orders
        remark 	Remark of the order
        tags 	tag order source
        isActive 	Mark of the active orders
        cancelExist 	Mark of the canceled orders
        createdAt 	Time the order created
        updatedAt 	last update time
        endAt 	End time
        orderTime 	Order create time in nanosecond
        settleCurrency 	settlement currency
        status 	order status: “open” or “done”
        filledSize 	Value of the executed orders
        filledValue 	Executed order quantity
        reduceOnly 	A mark to reduce the position size only

        This request is paginated.
        Order Status and Settlement

        Any limit order on the exchange order book is in active status. Orders removed from the order book
         will be marked with done status. After an order becomes done, there may be a few milliseconds
          latency before it’s fully settled.

        You can check the orders in any status.
         If the status parameter is not specified, orders of done status will be returned by default.

        When you query orders in active status, there is no time limit. However,
         when you query orders in done status, the start and end time range cannot exceed 24*7 hours.
          An error will occur if the specified time window exceeds the range. If you specify the end time only,
           the system will automatically calculate the start time as end time minus 24 hours, and vice versa.
        POLLING
        For high-volume trading, it is highly recommended that you maintain your own list of open orders
         and use one of the streaming market data feeds to keep it updated. You should poll the open orders
          endpoint to obtain the current state of any open order.

        If you need to get your recent trade history with low latency,
         you may query the endpoint Get List of Orders Completed in 24h.
        """

        return self.request(point='get_order_list', **kwargs)

    def get_position_list(self, **kwargs):
        """
        Get the position details of a specified position.
        HTTP Request

        GET /api/v1/positions
        Example

        GET /api/v1/positions
        API Permission

        This endpoint requires the General permission.
        REQUEST RATE LIMIT

        This API is restricted for each account, the request rate limit is 9 times/3s.
        RESPONSES
        Field 	Description
        id 	Position ID
        symbol 	Symbol
        autoDeposit 	Auto deposit margin or not
        maintMarginReq 	Maintenance margin requirement
        riskLimit 	Risk limit
        realLeverage 	Leverage o the order
        crossMode 	Cross mode or not
        delevPercentage 	ADL ranking percentile
        openingTimestamp 	Open time
        currentTimestamp 	Current timestamp
        currentQty 	Current postion quantity
        currentCost 	Current postion value
        currentComm 	Current commission
        unrealisedCost 	Unrealised value
        realisedGrossCost 	Accumulated realised gross profit value
        realisedCost 	Current realised position value
        isOpen 	Opened position or not
        markPrice 	Mark price
        markValue 	Mark value
        posCost 	Position value
        posCross 	added margin
        posInit 	Leverage margin
        posComm 	Bankruptcy cost
        posLoss 	Funding fees paid out
        posMargin 	Position margin
        posMaint 	Maintenance margin
        maintMargin 	Position margin
        realisedGrossPnl 	Accumulated realised gross profit value
        realisedPnl 	Realised profit and loss
        unrealisedPnl 	Unrealised profit and loss
        unrealisedPnlPcnt 	Profit-loss ratio of the position
        unrealisedRoePcnt 	Rate of return on investment
        avgEntryPrice 	Average entry price
        liquidationPrice 	Liquidation price
        bankruptPrice 	Bankruptcy price
        settleCurrency 	Currency used to clear and settle the trades
        isInverse 	Reverse contract or not
        maintainMargin 	Maintenance margin requirement
        """

        return self.request(point='get_position_list', **kwargs)

    def get_untriggered_stop_order_list(self, **kwargs):
        """
        Get the un-triggered stop orders list.
        HTTP Request

        GET /api/v1/stopOrders
        Example

        GET /api/v1/stopOrders?symbol=XBTUSDM

        Query this endpoint to get the untriggered stop orders of the position in XBTUSDM.
        API Permission

        This endpoint requires the General permission.
        PARAMETERS

        You can request for specific orders using query parameters.
        Param 	Type 	Description
        symbol 	String 	[optional] Symbol of the contract
        side 	String 	[optional] buy or sell
        type 	String 	[optional] limit, market
        startAt 	long 	[optional] Start time (milisecond)
        endAt 	long 	[optional] End time (milisecond)
        RESPONSES
        Param 	Type
        id 	Order ID
        symbol 	Symbol of the contract
        type 	Order type, market order or limit order
        side 	Transaction side
        price 	Order price
        size 	Order quantity
        value 	Order value
        dealValue 	Executed size of funds
        dealSize 	Executed quantity
        stp 	Self trade prevention types
        stop 	Stop order type (stop limit or stop market)
        stopPriceType 	Trigger price type of stop orders
        stopTriggered 	Mark to show whether the stop order is triggered
        stopPrice 	Trigger price of stop orders
        timeInForce 	Time in force policy type
        postOnly 	Mark of post only
        hidden 	Mark of the hidden order
        iceberg 	Mark of the iceberg order
        leverage 	Leverage of the order
        forceHold 	A mark to forcely hold the funds for an order
        closeOrder 	A mark to close the position
        visibleSize 	Visible size of the iceberg order
        clientOid 	Unique order id created by users to identify their orders
        remark 	Remark of the order
        tags 	tag order source
        isActive 	Mark of the active orders
        cancelExist 	Mark of the canceled orders
        createdAt 	Time the order created
        updatedAt 	last update time
        endAt 	End time
        orderTime 	Order create time in nanosecond
        settleCurrency 	settlement currency
        status 	order status: “open” or “done”
        filledSize 	Value of the executed orders
        filledValue 	Executed order quantity
        reduceOnly 	A mark to reduce the position size only

        This request is paginated.
        """

        return self.request(point='get_untriggered_stop_order_list', **kwargs)

    def get_balance(self, **kwargs) -> float:
        code, data = self.get_account_overview(**kwargs)
        return data.get('data').get('availableBalance') or 0

    def get_active_contracts(self, **kwargs):
        contracts = self._get_open_contract_list(**kwargs)[1].get('data')
        return [contract['symbol'] for contract in contracts]

    def _get_lot_size_contract(self, symbol: str, **kwargs):
        contract = self._get_contract_info(symbol=symbol, **kwargs)[1].get('data')
        return contract.get('lotSize') * contract.get('multiplier')

    def get_lot_size(self, symbol: str, balance: float, price: float, leverage: int, **kwargs):
        return int((balance * leverage) / (self._get_lot_size_contract(symbol=symbol, **kwargs) * price))

    def place_stop_order(self, clientOid: str, side: str, symbol: str,
                         stop: str, stop_price: str, size: str, **kwargs):
        params = {
            'clientOid': clientOid,
            'side': side,
            'symbol': symbol,
            'type': 'market',
            'stop': stop,
            'stopPriceType': 'TP',
            'stopPrice': stop_price,
            'leverage': '1',
            'size': size,
        }

        return self._place_order(**params, **kwargs)

    def close_position(self, symbol: str, **kwargs):
        code, data = self.get_position_list(symbol=symbol, **kwargs)
        positions = data.get('data')

        current_position = ''
        for pos in positions:
            if pos['symbol'] == symbol:
                current_position = pos
                break

        return self._place_order(symbol=symbol, type='market',
                                 closeOrder=True, clientOid=current_position.get('id'), **kwargs)

    def place_order(self, symbol: str, leverage: str, price: str, order_type: str,
                    size: str, tp_prices: str, stop_price: str, tp_sizes: list, type: str,
                    **kwargs):
        side = ('sell', 'buy')[type == 'long']

        main_order = self._place_order(clientOid=uuid4().hex,
                                       side=side,
                                       symbol=symbol,
                                       leverage=leverage,
                                       price=price,
                                       size=size,
                                       type=order_type,
                                       **kwargs)

        tp_orders = [self.place_stop_order(clientOid=uuid4().hex,
                                           side='sell' if side == 'buy' else 'buy',
                                           symbol=symbol,
                                           stop='up' if side == 'buy' else 'down',
                                           stop_price=tp_price,
                                           size=tp_sizes[it],
                                           **kwargs) for it, tp_price in enumerate(tp_prices) if tp_price and tp_sizes[it]]

        sl_order = self.place_stop_order(clientOid=uuid4().hex,
                                         side='sell' if side == 'buy' else 'buy',
                                         symbol=symbol,
                                         stop='down' if side == 'buy' else 'up',
                                         stop_price=stop_price,
                                         size=size,
                                         **kwargs)

        return main_order, tp_orders, sl_order

    def execute_signal(self, signal: Signal, user: User, usable_balance: float, **kwargs):
        usable_balance_lot = self.get_lot_size(symbol=signal.pair, balance=usable_balance,
                                               price=signal.entry, leverage=signal.leverage,
                                               **kwargs)

        service: MarketService = MarketService()
        tp_sizes = [portion * usable_balance_lot for portion in service.calculate_target_shares(user.strategy,
                                                                                                len(signal.targets))]
        return self.place_order(symbol=signal.pair, leverage=str(signal.leverage),
                                price=str(signal.entry), type=signal.type, order_type=signal.order_type,
                                size=str(usable_balance_lot), tp_prices=signal.targets,
                                stop_price=str(signal.stop_loss), tp_sizes=tp_sizes, **kwargs)
