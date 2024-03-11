import unittest
import time  # simulate runtime


class DummyTest(unittest.TestCase):

    def setUp(self):
        self.x = 3

    def tearDown(self):
        pass

    def test_dummy(self):
        time.sleep(2)
        y = self.x + 4
        self.assertEqual(y, 7)
