# -*- coding: utf-8 -*-

import unittest
import logging
import sys

LOG = logging.getLogger('test_capture_logging')
LOG.addHandler(logging.StreamHandler())

class TestLoggingWithXunit(unittest.TestCase):

    def test_a(self):
        LOG.error('log_1')

    def test_b(self):
        LOG.error('log_2')
