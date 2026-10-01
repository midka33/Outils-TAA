# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Contrôleur de l'étape 01 du module Plans de vente."""


class PlansVenteController(object):
    def __init__(self, analysis_service):
        self.analysis_service = analysis_service

    def load_context(self):
        return self.analysis_service.load_context()

    def analyze(self, descriptor):
        return self.analysis_service.analyze(descriptor)
