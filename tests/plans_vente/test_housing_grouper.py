# -*- coding: utf-8 -*-
from plans_vente.housing import RoomSnapshot
from plans_vente.housing_grouper import HousingGrouper


def test_groups_rooms_by_trimmed_housing_key():
    rooms = [
        RoomSnapshot("u1", level_name="RDC", housing_key=" A101 "),
        RoomSnapshot("u2", level_name="RDC", housing_key="A101"),
        RoomSnapshot("u3", level_name="R+1", housing_key="B201"),
    ]
    result = HousingGrouper().group(rooms, "Numéro logement")
    assert result.housing_count == 2
    assert result.room_count == 3
    assert [item.key for item in result.housings] == ["A101", "B201"]
    assert result.housings[0].room_count == 2
    assert result.housings[0].levels_label == "RDC"


def test_ignores_empty_values_and_tracks_them():
    rooms = [
        RoomSnapshot("u1", housing_key="A101"),
        RoomSnapshot("u2", housing_key=""),
        RoomSnapshot("u3", housing_key="   "),
        RoomSnapshot("u4", housing_key=None),
    ]
    result = HousingGrouper().group(rooms, "Logement")
    assert result.housing_count == 1
    assert result.room_count == 1
    assert result.empty_value_count == 3


def test_levels_are_unique_and_sorted():
    rooms = [
        RoomSnapshot("u1", level_name="R+1", housing_key="A101"),
        RoomSnapshot("u2", level_name="RDC", housing_key="A101"),
        RoomSnapshot("u3", level_name="rdc", housing_key="A101"),
    ]
    result = HousingGrouper().group(rooms, "Logement")
    assert result.housings[0].level_names == ["R+1", "RDC"]
    assert result.housings[0].levels_label == "R+1, RDC"
