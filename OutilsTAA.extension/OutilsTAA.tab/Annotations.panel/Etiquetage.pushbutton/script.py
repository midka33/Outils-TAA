# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__title__ = "Etiquetage\nauto"
__doc__ = "Etiquetage automatique des pieces de plusieurs vues."

import os
import sys

button_dir = os.path.dirname(__file__)
panel_dir = os.path.dirname(button_dir)
tab_dir = os.path.dirname(panel_dir)
extension_dir = os.path.dirname(tab_dir)
for path in (os.path.join(extension_dir, "lib"),
             os.path.join(tab_dir, "PlansDeVente.panel", "services"),
             os.path.join(panel_dir, "services")):
    if path not in sys.path:
        sys.path.insert(0, path)

from launcher import run
run("tags")
