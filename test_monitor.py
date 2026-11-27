import sqlite3
import unittest
from unittest.mock import patch
from monitor import matches, process


class Filters(unittest.TestCase):
    def test_sizes(self):
        for size in ['2XL', '3XL', '4XL', 'XXL', 'XXXL', 'XXXXL', '尺寸: 3XL']:
            self.assertTrue(matches('camisetas', size), size)
        for size in ['XL', '5XL', '12XL', 'XXXXXL', '']:
            self.assertFalse(matches('camisetas', size), size)
        for size in ['45', '46', 'US11=EUR45', '尺码 : EUR46']:
            self.assertTrue(matches('tenis', size), size)
        for size in ['44', '145', '45.5', 'EUR46.5', 'US45', 'UK 46']:
            self.assertFalse(matches('tenis', size), size)
        self.assertFalse(matches('tenis', '45', 'Summer slippers'))

    def test_baseline_duplicates_failure_retry(self):
        db = sqlite3.connect(':memory:')
        first = {'id': 'a', 'sku': '45'}
        second = {'id': 'b', 'sku': '46'}
        with patch('monitor.notify') as send:
            self.assertEqual(process(db, [first]), (0, False))
            send.assert_not_called()
            self.assertEqual(process(db, [first, second]), (1, True))
            self.assertEqual(process(db, [first, second]), (0, True))
        third = {'id': 'c', 'sku': '45'}
        with patch('monitor.notify', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError):
                process(db, [third])
        with patch('monitor.notify') as send:
            self.assertEqual(process(db, [third]), (1, True))
            send.assert_called_once()


if __name__ == '__main__':
    unittest.main()
