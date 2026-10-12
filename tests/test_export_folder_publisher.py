# -*- coding: utf-8 -*-
"""Contrats du Publisher simplifié : dossiers uniques et drag/drop Explorer."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

PANEL = (
    Path(__file__).resolve().parents[1]
    / "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
)
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from carnet_repository import CarnetRepository
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from publication_set import PublicationSet


def method(relative, class_name, method_name):
    source = (PANEL / relative).read_text(encoding="utf-8")
    source = source.replace(
        "DragDropEffects.None",
        "getattr(DragDropEffects, 'None')",
    )
    tree = ast.parse(source)
    parent = next(
        node
        for node in tree.body
        if getattr(node, "name", None) == class_name
    )
    fn = next(
        node
        for node in parent.body
        if isinstance(node, ast.FunctionDef)
        and node.name == method_name
    )
    namespace = {}
    exec(
        compile(
            ast.Module(body=[fn], type_ignores=[]),
            relative,
            "exec",
        ),
        namespace,
    )
    return namespace[method_name]


def _set(name, set_id, folder_id):
    value = PublicationSet(
        name,
        [PublicationItem(
            "uid-" + set_id,
            1,
            "SHEET",
            "A01",
            "Plan",
        )],
        set_id=set_id,
        folder_id=folder_id,
        persistent=True,
    )
    return value


def test_schema8_migrates_old_visual_order_without_losing_data(tmp_path):
    path = tmp_path / "sets.json"
    path.write_text(
        json.dumps({
            "schema_version": 6,
            "project_identity": None,
            "folders": [
                {
                    "id": "root",
                    "name": "DCE",
                    "parent_id": None,
                    "persistent": True,
                    "sort_order": 0,
                },
                {
                    "id": "child",
                    "name": "Plans",
                    "parent_id": "root",
                    "persistent": True,
                    "sort_order": 0,
                },
            ],
            "sets": [
                {
                    "id": "a",
                    "name": "A1000",
                    "persistent": True,
                    "folder_id": "root",
                    "sort_order": 0,
                    "source": {"mode": "MANUAL"},
                    "items": [],
                },
                {
                    "id": "b",
                    "name": "A2000",
                    "persistent": True,
                    "folder_id": "root",
                    "sort_order": 1,
                    "source": {"mode": "MANUAL"},
                    "items": [],
                },
            ],
        }),
        encoding="utf-8",
    )

    repo = CarnetRepository(str(path))
    folders = repo.list_folders()
    sets = repo.list_all()

    assert repo.SCHEMA_VERSION == 8
    assert next(f for f in folders if f.id == "child").tree_order == 0
    assert next(s for s in sets if s.id == "a").tree_order == 1
    assert next(s for s in sets if s.id == "b").tree_order == 2

    stored = json.loads(path.read_text(encoding="utf-8"))
    # La lecture seule ne réécrit pas le fichier ; la migration reste en mémoire
    # jusqu'à la prochaine mutation contrôlée.
    assert stored["schema_version"] == 6


def test_mixed_folders_and_publication_folders_share_one_order(tmp_path):
    repo = CarnetRepository(str(tmp_path / "sets.json"))
    root = PublicationFolder("DCE", "root")
    child = PublicationFolder("Sous-dossier", "child", "root")
    repo.save_folder(root)
    repo.save_folder(child)
    repo.save(_set("A1000", "a", "root"))
    repo.save(_set("A2000", "b", "root"))

    # Déplacer A2000 avant le sous-dossier : ordre mixte comme l'Explorateur.
    assert repo.move_tree_nodes(
        [("CARNET", "b")],
        "root",
        ("FOLDER", "child"),
    )

    folders = dict((f.id, f) for f in repo.list_folders())
    sets = dict((s.id, s) for s in repo.list_all())
    assert sets["b"].tree_order == 0
    assert folders["child"].tree_order == 1
    assert sets["a"].tree_order == 2

    # Puis déplacer le sous-dossier après A1000.
    assert repo.move_tree_nodes(
        [("FOLDER", "child")],
        "root",
        None,
    )
    folders = dict((f.id, f) for f in repo.list_folders())
    sets = dict((s.id, s) for s in repo.list_all())
    assert sets["b"].tree_order == 0
    assert sets["a"].tree_order == 1
    assert folders["child"].tree_order == 2


def test_any_visual_folder_can_become_a_real_parent(tmp_path):
    repo = CarnetRepository(str(tmp_path / "sets.json"))
    root = PublicationFolder("DCE", "root")
    publication = _set("A1000", "a", "root")
    child = PublicationFolder("Sous-dossier", "child", "root")
    nested = _set("A1100", "nested", "root")

    repo.save_folder(root)
    repo.save(publication)
    repo.save_folder(child)
    repo.save(nested)

    # Dossier d'organisation dans un ancien PublicationSet.
    assert repo.move_tree_nodes(
        [("FOLDER", "child")],
        "a",
        None,
    )
    # Autre dossier de publication dans ce même dossier.
    assert repo.move_tree_nodes(
        [("CARNET", "nested")],
        "a",
        None,
    )

    folders = dict((f.id, f) for f in repo.list_folders())
    sets = dict((s.id, s) for s in repo.list_all())
    assert folders["child"].parent_id == "a"
    assert sets["nested"].folder_id == "a"

    # Impossible de remettre le parent dans un de ses descendants.
    assert not repo.move_tree_nodes(
        [("CARNET", "a")],
        "child",
        None,
    )


def test_publication_folder_with_children_cannot_be_deleted(tmp_path):
    repo = CarnetRepository(str(tmp_path / "sets.json"))
    root = PublicationFolder("DCE", "root")
    parent = _set("A1000", "a", "root")
    child = PublicationFolder("Details", "child", "a")
    repo.save_folder(root)
    repo.save(parent)
    repo.save_folder(child)

    assert not repo.delete("a")
    assert repo.delete_folder("child")
    assert repo.delete("a")


def test_move_sheet_between_publication_folders_keeps_visual_order():
    move = method(
        "services/publication_tree_drag_drop.py",
        "PublicationTreeDragDrop",
        "_move_sheets",
    )

    a1 = PublicationItem("a1", 1, "SHEET", "A01", "Plan 1")
    a2 = PublicationItem("a2", 2, "SHEET", "A02", "Plan 2")
    b1 = PublicationItem("b1", 3, "SHEET", "B01", "Coupe")
    source = PublicationSet(
        "Plans",
        [a1, a2],
        set_id="source",
        persistent=True,
    )
    target = PublicationSet(
        "Coupes",
        [b1],
        set_id="target",
        persistent=True,
    )

    nodes = [
        SimpleNamespace(Tag=("SHEET", a1, source)),
        SimpleNamespace(Tag=("SHEET", a2, source)),
        SimpleNamespace(Tag=("SHEET", b1, target)),
    ]
    saved = []
    manager = SimpleNamespace()
    manager.window = SimpleNamespace(
        _carnets=[source, target],
        controller=SimpleNamespace(
            save_persistent=lambda value: saved.append(value.id)
        ),
    )
    manager._all = lambda: nodes
    manager._key = lambda tag: (
        "SHEET:{0}:{1}".format(tag[2].id, tag[1].unique_id)
    )
    manager._post_drop_selection = None

    target_node = SimpleNamespace(Tag=("CARNET", target))
    payload = {
        "kind": "SHEET",
        "items": ["SHEET:source:a1"],
    }

    assert move(manager, payload, target_node, "APPEND")
    assert [item.unique_id for item in source.items] == ["a2"]
    assert [item.unique_id for item in target.items] == ["b1", "a1"]
    assert saved == ["source", "target"]
    assert manager._post_drop_selection == ["SHEET:target:a1"]


def _visible_xaml_strings(path):
    root = ET.parse(path).getroot()
    values = []
    for element in root.iter():
        for name in ("Title", "Text", "Content", "Header", "ToolTip"):
            value = element.get(name)
            if value:
                values.append(value)
    return values


def test_main_ui_exposes_only_folder_vocabulary_and_folder_icons():
    main_strings = _visible_xaml_strings(PANEL / "ui.xaml")
    manager_strings = _visible_xaml_strings(PANEL / "carnet_manager.xaml")
    visible = main_strings + manager_strings

    assert not any("carnet" in value.lower() for value in visible)
    assert any("Ajouter des mises en page" in value for value in visible)

    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    cls = ast.parse(source)
    window = next(
        node for node in cls.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ExportWindow"
    )
    make = next(
        node for node in window.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_make_carnet_node"
    )
    snippet = ast.get_source_segment(source, make)
    assert "TaaFolderIcon" in snippet
    assert "TaaBookIcon" not in snippet


def test_drag_drop_has_explorer_contracts():
    source = (
        PANEL / "services/publication_tree_drag_drop.py"
    ).read_text(encoding="utf-8")

    assert "_mouse_down_point" in source
    assert "MinimumHorizontalDragDistance" in source
    assert "MinimumVerticalDragDistance" in source
    assert "LineUp()" in source and "LineDown()" in source
    assert "TotalMilliseconds" in source and ">= 700" in source
    assert "expand_to_key" in source
    assert "_restore_scroll" in source
    assert "move_tree_nodes" in source
    assert "height * 0.15" in source
    assert "_container_descendant" in source
