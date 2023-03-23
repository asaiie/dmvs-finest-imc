# spike on bananas, no spike on pearls
# note: if you want to change spike params, change bananas

from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
from math import floor


class Trader:

    SPIKE_PRODUCTS = ["BANANAS"]

    ## MARKET MAKING PARAMETERS
    RISK_ADJUSTMENT = {"BANANAS" : 0.10, "PEARLS" : 0.10, "PINA_COLADAS" : 0.10, "COCONUTS" : 0.10}
    ORDER_VOLUME = {"BANANAS" : 3, "PEARLS" : 5, "COCONUTS" : 0, "PINA_COLADAS" : 0}
    HALF_SPREAD_SIZE = {"BANANAS": 2, "PEARLS": 3, "COCONUTS": 1, "PINA_COLADAS": 1}

    ############################

    ## PARAMETERS
    prices = {
        "asks" : {}, 
        "bids" : {},
        "avg_prices" : {},
        "count" : {},
        "acceptable_price" : {}, 
        "avg" : {}
    }
    ############################

    # ## POSITION SIZING PARAMS
    MM_POSITION_LIMIT = {"BANANAS" : 8, "PEARLS" : 10, "PINA_COLADAS" : 0, "COCONUTS" : 0}
    MM_POSITION = {"BANANAS" : 0, "PEARLS" : 0, "PINA_COLADAS" : 0, "COCONUTS" : 0}
    MM_LAST_ORDER_PRICE = {"BANANAS" : {"BUY": 0, "SELL": 0}, "PEARLS" : {"BUY": 0, "SELL": 0}, "PINA_COLADAS" : {"BUY": 0, "SELL": 0}, "COCONUTS" : {"BUY": 0, "SELL": 0}}
    ############################
    MCGINLEY_POSITION_LIMIT = {"BANANAS" : 12, "PEARLS" : 10, "PINA_COLADAS" : 20, "COCONUTS" : 20}
    MCGINLEY_POSITION = {"BANANAS" : 0, "PEARLS" : 0, "PINA_COLADAS" : 0, "COCONUTS" : 0}
    MCGINLEY_LAST_ORDER_PRICE = {"BANANAS" : {"BUY": 0, "SELL": 0}, "PEARLS" : {"BUY": 0, "SELL": 0}, "PINA_COLADAS" : {"BUY": 0, "SELL": 0}, "COCONUTS" : {"BUY": 0, "SELL": 0}}

    ############################
    LAST_TIMESTAMP = -100000

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}

        

        for product in ["BANANAS, PEARLS"]:
            orders: list[Order] = []
            order_depth: OrderDepth = state.order_depths[product]

            if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                ##GET TRADES
                try:
                    own_trades = state.own_trades[product]
                except:
                    own_trades = []

                # position calcs

                if product in self.SPIKE_PRODUCTS:
                    try:
                        position = state.position[product]
                    except:
                        position = 0


                    ## CALCULATING THE POSITION SIZE OF MCGINLEY
                    for trade in own_trades:
                        if trade.timestamp == self.LAST_TIMESTAMP:
                            if trade.buyer == "SUBMISSION" and trade.price == self.MCGINLEY_LAST_ORDER_PRICE[product]["BUY"]:
                                self.MCGINLEY_POSITION[product] += trade.quantity
                            elif trade.seller == "SUBMISSION" and trade.price == self.MCGINLEY_LAST_ORDER_PRICE[product]["SELL"]:
                                self.MCGINLEY_POSITION[product] -= trade.quantity
                    ##############################

                    self.MM_POSITION[product] = position - self.MCGINLEY_POSITION[product]

                else:
                    ## CALCULATING THE POSITION SIZE OF MARKET MAKING
                    for trade in own_trades:
                        if trade.timestamp == self.LAST_TIMESTAMP:
                            if trade.buyer == "SUBMISSION" and trade.price == self.MM_LAST_ORDER_PRICE[product]["BUY"]:
                                self.MM_POSITION[product] += trade.quantity
                            elif trade.seller == "SUBMISSION" and trade.price == self.MM_LAST_ORDER_PRICE[product]["SELL"]:
                                self.MM_POSITION[product] -= trade.quantity
                    ##############################

                    ## CALCULATING THE POSITION SIZE OF MCGINLEY
                    for trade in own_trades:
                        if trade.timestamp == self.LAST_TIMESTAMP:
                            if trade.buyer == "SUBMISSION" and trade.price == self.MCGINLEY_LAST_ORDER_PRICE[product]["BUY"]:
                                self.MCGINLEY_POSITION[product] += trade.quantity
                            elif trade.seller == "SUBMISSION" and trade.price == self.MCGINLEY_LAST_ORDER_PRICE[product]["SELL"]:
                                self.MCGINLEY_POSITION[product] -= trade.quantity
                    ##############################

                ## CALCULATING STATS
                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())
                best_bid_volume = order_depth.buy_orders[best_bid]
                best_ask_volume = order_depth.sell_orders[best_ask]
                curr_spread = best_ask - best_bid
                value = (best_ask + best_bid)/2
                ##############################

                ## MARKET MAKING STRATEGY
                skew = -self.MM_POSITION[product] * self.RISK_ADJUSTMENT[product]
                buy_quote = floor(value - self.HALF_SPREAD_SIZE[product] + skew)
                sell_quote = floor(value + self.HALF_SPREAD_SIZE[product] + skew)
                ##############################

                ## MCGINLEY STRATEGY
                if product in self.prices["acceptable_price"]:
                    mcginley_price = self.prices["acceptable_price"][product]
                else:
                    mcginley_price = value

                if product not in self.prices["asks"]:
                    self.prices["asks"][product] = []
                if product not in self.prices["bids"]:
                    self.prices["bids"][product] = []
                
                self.prices["asks"][product].append(best_ask)
                self.prices["bids"][product].append(best_bid)

                n=12
                k=0.67
                curr_price = value

                # first iteration
                if product not in self.prices["acceptable_price"]:
                    self.prices["avg_prices"][product] = [curr_price]

                    self.prices["acceptable_price"][product] = curr_price

                    # don't place orders in the first iteration
                    result[product] = orders
                    return result

                mcginley_price = mcginley_price + (curr_price-mcginley_price)/(k * n * (curr_price/mcginley_price)**4)

                self.prices["acceptable_price"][product] = mcginley_price
                self.prices["avg_prices"][product].append(mcginley_price)
            
                acceptable_price = self.prices["acceptable_price"][product]
                ##############################
                
                if product in self.SPIKE_PRODUCTS:
                    ## SPIKE DETECTION
                    n = 7

                    if product not in self.prices["avg"]:
                        self.prices["avg"][product] = [value]

                    if curr_spread >= 6:
                        self.prices["avg"][product].append(value)
                    else:
                        self.prices["avg"][product].append(self.prices["avg"][product][-1])

                    i = len(self.prices["avg"][product])
                    n_lookback_index = max(i - n, 0)

                    window = self.prices["avg"][product][n_lookback_index:]
                    acceptable_price_spike_detection = sum(window) / len(window)
                    ##############################

                    ## MARKET MAKING + SPIKE DETECTION ORDERS
                    # buy_order_volume = 0
                    # sell_order_volume = 0
                    spike_order_made = False

                    if best_ask < acceptable_price_spike_detection: #second part of and is so that orders don't overlap, which lets me individually keep track of positions
                        buy_order_volume = max(0,min(-best_ask_volume, self.MM_POSITION_LIMIT[product] - self.MM_POSITION[product]))
                        print("BUY SPIKE", str(buy_order_volume) + "x", best_ask)
                        spike_order_made = True
                        orders.append(Order(product, best_ask, buy_order_volume))

                    if best_bid > acceptable_price_spike_detection: #second part of and is so that orders don't overlap, which lets me individually keep track of positions
                        sell_order_volume = max(0,min(best_bid_volume, self.MM_POSITION_LIMIT[product] + self.MM_POSITION[product]))
                        print("SELL SPIKE", str(sell_order_volume) + "x", best_bid)
                        spike_order_made = True
                        orders.append(Order(product, best_bid, -sell_order_volume))

                    if not spike_order_made:
                        orders.append(Order(product, buy_quote, max(0,min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] - self.MM_POSITION[product]))))
                        orders.append(Order(product, sell_quote, -max(0,min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] + self.MM_POSITION[product]))))
                    
                        print("BUY MM",  \
                            str(max(0, \
                                min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] - self.MM_POSITION[product]))) + "x", buy_quote)
                        
                        print("SELL MM", \
                            str(-max(0, \
                                min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] + self.MM_POSITION[product]))) + "x", sell_quote)
                    
                    
                        self.MM_LAST_ORDER_PRICE[product] = {"BUY": buy_quote, "SELL": sell_quote}
                
                else:
                    ## MARKET MAKING ORDERS
                    orders.append(Order(product, buy_quote, max(0,min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] - self.MM_POSITION[product]))))
                    orders.append(Order(product, sell_quote, -max(0,min(self.ORDER_VOLUME[product], self.MM_POSITION_LIMIT[product] + self.MM_POSITION[product]))))
                    self.MM_LAST_ORDER_PRICE[product] = {"BUY": buy_quote, "SELL": sell_quote}
                    ##############################
                ##############################

                ## MCGINLEY ORDERS
                if best_ask < acceptable_price and best_ask != buy_quote: #second part of and is so that orders don't overlap, which lets me individually keep track of positions
                    # print("BUY", str(-best_ask_volume) + "x", best_ask)
                    orders.append(Order(product, best_ask, max(0,min(-best_ask_volume, self.MCGINLEY_POSITION_LIMIT[product] - self.MCGINLEY_POSITION[product]))))
                    self.MCGINLEY_LAST_ORDER_PRICE[product]["BUY"] = best_ask
                else:
                    self.MCGINLEY_LAST_ORDER_PRICE[product]["BUY"] = 0

                if best_bid > acceptable_price and best_bid != sell_quote: #second part of and is so that orders don't overlap, which lets me individually keep track of positions
                    # print("SELL", str(best_bid_volume) + "x", best_bid)
                    orders.append(Order(product, best_bid, -max(0,min(best_bid_volume, self.MCGINLEY_POSITION_LIMIT[product] + self.MCGINLEY_POSITION[product]))))
                    self.MCGINLEY_LAST_ORDER_PRICE[product]["SELL"] = best_bid
                else:
                    self.MCGINLEY_LAST_ORDER_PRICE[product]["SELL"] = 0
                ##############################
                
                ## PRINT STATS
                print(f'{product}:')
                
                try:
                    position = state.position[product]
                except:
                    position = 0
                
                print(f'Actual position: {position}')
                print('Estimated MM + SPIKE position: ', self.MM_POSITION[product])
                print('Estimated MCGINLEY position: ', self.MCGINLEY_POSITION[product])
                ##############################
                
                result[product] = orders

        self.LAST_TIMESTAMP = state.timestamp
        
        print('\n----------------------------------------------------------------------------------------------------\n')
        return result