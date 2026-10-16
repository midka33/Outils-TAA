# -*- coding: utf-8 -*-
from plans_vente.housing import Housing, RoomSnapshot
from plans_vente.multilevel import split_housing_by_level


def room(uid, level, key="A101"):
    return RoomSnapshot(
        unique_id=uid,
        name="Pièce",
        number=uid,
        level_name=level,
        housing_key=key,
    )


def test_multilevel_split_creates_one_output_housing_per_level():
    housing = Housing(
        "A101",
        [
            room("1", "RDC"),
            room("2", "RDC"),
            room("3", "R+1"),
        ],
    )

    result = split_housing_by_level(housing)

    assert len(result) == 2
    assert [item.level_names for item in result] == [["R+1"], ["RDC"]]
    assert [item.room_count for item in result] == [1, 2]
    assert all(item.filter_key == "A101" for item in result)
    assert len(set(item.key for item in result)) == 2
    assert all(item.key.startswith("A101-") for item in result)


def test_single_level_housing_is_not_rewritten():
    housing = Housing("A101", [room("1", "RDC"), room("2", "RDC")])
    result = split_housing_by_level(housing)

    assert result == [housing]
    assert result[0].filter_key == "A101"


def test_generated_level_key_does_not_change_schedule_filter_key():
    housing = Housing(
        "A101",
        [room("1", "Niveau 01"), room("2", "Niveau 02")],
    )
    result = split_housing_by_level(housing)

    assert {item.filter_key for item in result} == {"A101"}
    assert {item.key for item in result} == {
        "A101-Niveau-01",
        "A101-Niveau-02",
    }


def test_multilevel_schedule_contract_keeps_business_key_for_all_levels():
    housing = Housing(
        "A101",
        [room("1", "RDC"), room("2", "R+1")],
    )
    result = split_housing_by_level(housing)

    assert all(item.filter_key == "A101" for item in result)
    assert all(item.key != item.filter_key for item in result)
