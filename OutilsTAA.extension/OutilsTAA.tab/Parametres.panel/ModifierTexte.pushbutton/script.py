# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

PANEL = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.abspath(os.path.join(PANEL, "..", ".."))
for directory in (os.path.join(ROOT, "lib"), os.path.join(PANEL, "ui"), os.path.join(PANEL, "services")):
    if directory not in sys.path:
        sys.path.insert(0, directory)
from room_parameters_window import launch
launch("text")
