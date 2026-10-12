import time
class Dealer:
    def __init__(self, base_edge=8.0, gamma=0.5, budget=0.30):
        self.base_edge, self.gamma, self.budget = base_edge, gamma, budget
        self.state = {}  # O(1) deques: EWMA vol, mark-out sums, break w_t
        
    def quote(self, orders, market, portfolio):
        try:
            out = self._price_orders(orders, market, portfolio) # may raise exception
            return self._sanitize(out)                          # finite, tick-rounded
        except Exception:
            return {o["order_id"]: None for o in orders}        # withdraw on error
            
    def hedge(self, market, portfolio):
        try: return self._hedge(market, portfolio)              # execute partial hedge
        except Exception: return []                             # fail-safe: abort hedge
            
    def _price_orders(self, orders, market, portfolio):
        t0 = time.perf_counter(); res = {}
        # Priority sort by notional exposure
        for o in sorted(orders, key=lambda x: x['quantity'], reverse=True): 
            if time.perf_counter() - t0 > self.budget: 
                res[o["order_id"]] = None; continue             # soft timeout fallback
                
            fair = self._calc_fair(o, market)                   # mid + model averaging
            risk = self._calc_risk_shift(o, portfolio)          # skew + mark-out defense
            
            if self._would_breach(o, portfolio): 
                res[o["order_id"]] = None; continue             # prevent limit breach
                
            res[o["order_id"]] = fair + risk if o["side"] == "BUY" else fair - risk
        return res 
