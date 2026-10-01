# -*- coding: utf-8 -*-
"""Contrats statiques de compatibilité des fichiers Calculs des pièces."""

import ast
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TARGET_ROOTS = [
    os.path.join(
        ROOT,
        "OutilsTAA.extension",
        "OutilsTAA.tab",
        "Calculs.panel",
    ),
    os.path.join(
        ROOT,
        "OutilsTAA.extension",
        "lib",
        "calculation",
    ),
]

COMMON_FILES = [
    "settings.py",
    "parameter_utils.py",
    "unit_utils.py",
    "transaction.py",
    "wpf_resources.py",
]


def _python_files():
    files = []
    for root in TARGET_ROOTS:
        for current, directories, names in os.walk(root):
            directories[:] = [
                name for name in directories
                if name != "__pycache__"
            ]
            for name in names:
                if name.endswith(".py"):
                    files.append(os.path.join(current, name))

    common_root = os.path.join(
        ROOT,
        "OutilsTAA.extension",
        "lib",
        "common",
    )
    for name in COMMON_FILES:
        files.append(os.path.join(common_root, name))

    return sorted(set(files))


def test_all_calculs_python_files_parse():
    for path in _python_files():
        with open(path, "r") as handle:
            source = handle.read()
        ast.parse(source, filename=path)


def test_no_bare_except_in_calculs_python_files():
    violations = []
    for path in _python_files():
        with open(path, "r") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                violations.append(path)

    assert violations == []


def test_no_active_view_dependency_in_calculs_module():
    violations = []
    for path in _python_files():
        with open(path, "r") as handle:
            source = handle.read()
        if "ActiveView" in source:
            violations.append(path)

    assert violations == []
