# -*- coding: utf-8 -*-
"""Tests unitaires de la publication multiple."""

from publication_batch_service import PublicationBatchService


class _Settings(object):
    def __init__(self, name):
        self.output_directory = "C:/exports/" + name
        self.pdf_enabled = True
        self.pdf_mode = "COMBINED"
        self.dwg_enabled = False
        self.dwg_mode = "SEPARATE"
        self.dwg_setup_name = None
        self.dwg_true_color = True

    def validate(self):
        return []


class _Target(object):
    def __init__(self, name):
        self.name = name


def test_publish_multiple_carnets():
    calls = []

    class _PublicationService(object):
        def publish(self, target, output_directory, **kwargs):
            calls.append((target.name, output_directory))
            return {
                "success": True,
                "results": [{"format": "PDF", "success": True}],
                "errors": [],
                "warnings": []
            }

    service = PublicationBatchService(_PublicationService())
    targets = [_Target("Plans"), _Target("Coupes")]

    result = service.publish(
        targets,
        lambda target, folder=None: _Settings(target.name),
        lambda target: None
    )

    assert result["success"] is True
    assert calls == [
        ("Plans", "C:/exports/Plans"),
        ("Coupes", "C:/exports/Coupes")
    ]
    assert len(result["results"]) == 2


def test_publish_multiple_carnets_keeps_errors_per_carnet():
    class _PublicationService(object):
        def publish(self, target, output_directory, **kwargs):
            if target.name == "Coupes":
                return {
                    "success": False,
                    "results": [],
                    "errors": ["Export PDF en échec."],
                    "warnings": []
                }
            return {
                "success": True,
                "results": [{"format": "PDF", "success": True}],
                "errors": [],
                "warnings": ["Fichier existant."]
            }

    service = PublicationBatchService(_PublicationService())
    targets = [_Target("Plans"), _Target("Coupes")]
    result = service.publish(
        targets,
        lambda target, folder=None: _Settings(target.name),
        lambda target: None
    )

    assert result["success"] is False
    assert "Coupes : Export PDF en échec." in result["errors"]
    assert "Plans : Fichier existant." in result["warnings"]
