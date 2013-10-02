# -*- coding: utf-8 -*-

import unittest
import logging


class TestUnicodeInAssertion(unittest.TestCase):

    def test_a(self):
        logging.error('log_1')

    def test_b(self):
        logging.error('log_2')
