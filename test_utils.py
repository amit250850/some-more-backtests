import unittest
from utils import get_lot_size, calculate_costs, black_scholes_call

class TestUtils(unittest.TestCase):
    def test_get_lot_size(self):
        self.assertEqual(get_lot_size("SILVERMIC25JUNFUT"), 30)
        self.assertEqual(get_lot_size("NIFTY"), 75)

    def test_calculate_costs(self):
        # 100k entry, 100k exit
        costs = calculate_costs(100000, 100000)
        # 50 + 50 (slippage) + 40 (brokerage) + 10 + 10 (stt) = 160
        self.assertEqual(costs, 160)

    def test_black_scholes_call(self):
        # ITM call should have intrisic value
        price = black_scholes_call(110, 100, 0, 0.05, 0.15)
        self.assertEqual(price, 10)

if __name__ == '__main__':
    unittest.main()
