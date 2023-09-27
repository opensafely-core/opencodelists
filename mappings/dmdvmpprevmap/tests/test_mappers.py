from mappings.dmdvmpprevmap.mappers import vmp_ids_to_previous, vmpprev_full_mappings
from mappings.dmdvmpprevmap.models import Mapping


def test_codes_to_previous_no_previous():
    # in the dmd fixture data, there are no previous codes
    vmp_to_previous_mapping, vmp_to_previous_tuples = vmp_ids_to_previous()
    assert vmp_to_previous_mapping == {}
    assert vmp_to_previous_tuples == []


def test_codes_to_previous_with_retired_previous():
    # give two of the VMPs previous IDs that are only have one previous
    Mapping.objects.create(id="11", vpidprev="2")
    Mapping.objects.create(id="22", vpidprev="3")

    vmp_to_previous_mapping, vmp_to_previous_tuples = vmp_ids_to_previous()
    assert vmp_to_previous_mapping == {"11": "2", "22": "3"}
    assert vmp_to_previous_tuples == [
        ("11", "2"),
        ("22", "3"),
    ]


def test_codes_to_previous_with_chained_previous():
    # make one the prev for the other.
    # vmp1 itself has a previous, so its previous is also
    # included in the set of previous ids for vmp2
    Mapping.objects.create(id="1", vpidprev="0")
    Mapping.objects.create(id="2", vpidprev="1")
    Mapping.objects.create(id="3", vpidprev="2")

    vmp_to_previous_mapping, vmp_to_previous_tuples = vmp_ids_to_previous()
    assert vmp_to_previous_mapping == {
        "1": "0",
        "2": "1",
        "3": "2",
    }
    assert sorted(vmp_to_previous_tuples) == [
        ("1", "0"),
        ("2", "0"),
        ("2", "1"),
        ("3", "0"),
        ("3", "1"),
        ("3", "2"),
    ]


def test_codes_to_previous_with_self_previous():
    # This happens in the data, where a vmp's previous id is set to its own code.
    # Presumably this is an error; in any case, there's no need to include it in
    # the mapping
    Mapping.objects.create(id="1", vpidprev="1")
    vmp_to_previous_mapping, vmp_to_previous_tuples = vmp_ids_to_previous()
    assert vmp_to_previous_mapping == {}
    assert vmp_to_previous_tuples == []


def test_codes_to_previous_with_codes():
    # return previous for selected codes "1" and "2" only

    # These mappings directly affect a specified code
    Mapping.objects.create(id="1", vpidprev="0")
    Mapping.objects.create(id="2", vpidprev="1")
    Mapping.objects.create(id="3", vpidprev="2")
    # This mapping affects a code via a related mapping ("4" -> "3" -> "2")
    Mapping.objects.create(id="4", vpidprev="3")
    # This mapping doesn't affect specified codes
    Mapping.objects.create(id="5", vpidprev="6")

    vmp_to_previous_mapping, vmp_to_previous_tuples = vmpprev_full_mappings(
        codes=["1", "2"]
    )

    assert vmp_to_previous_mapping == {
        "1": "0",
        "2": "1",
        "3": "2",
        "4": "3",
    }

    assert sorted(vmp_to_previous_tuples) == [
        # mapped previous for the specified codes
        ("1", "0"),
        ("2", "0"),
        ("2", "1"),
        # mapped code that supercedes one of the specified codes
        ("3", "1"),
        ("3", "2"),
        # mapped code that supercedes specified codes, via another code (3)
        ("4", "1"),
        ("4", "2"),
    ]
