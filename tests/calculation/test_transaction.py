# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB_DIR = os.path.join(ROOT, "OutilsTAA.extension", "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from common.transaction import RevitTransaction


class FakeTransaction(object):
    def __init__(self, document, name, fail_commit=False):
        self.fail_commit = fail_commit
        self.started = False
        self.committed = False
        self.rolled_back = False

    def Start(self):
        self.started = True

    def Commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True

    def RollBack(self):
        self.rolled_back = True


class RevitTransactionTests(unittest.TestCase):

    def test_commits_on_success(self):
        holder = []
        def factory(document, name):
            value = FakeTransaction(document, name)
            holder.append(value)
            return value

        with RevitTransaction(object(), "Test", transaction_factory=factory) as context:
            self.assertTrue(holder[0].started)

        self.assertTrue(context.committed)
        self.assertTrue(holder[0].committed)
        self.assertFalse(holder[0].rolled_back)

    def test_rolls_back_on_body_error(self):
        holder = []
        def factory(document, name):
            value = FakeTransaction(document, name)
            holder.append(value)
            return value

        with self.assertRaises(ValueError):
            with RevitTransaction(object(), "Test", transaction_factory=factory):
                raise ValueError("boom")

        self.assertTrue(holder[0].rolled_back)
        self.assertFalse(holder[0].committed)

    def test_rolls_back_when_commit_fails(self):
        holder = []
        def factory(document, name):
            value = FakeTransaction(document, name, fail_commit=True)
            holder.append(value)
            return value

        with self.assertRaises(RuntimeError):
            with RevitTransaction(object(), "Test", transaction_factory=factory):
                pass

        self.assertTrue(holder[0].rolled_back)
        self.assertFalse(holder[0].committed)


if __name__ == "__main__":
    unittest.main()
