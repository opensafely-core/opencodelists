from mappings.dmdvmpprevmap.mappers import vmp_ids_to_previous
from mappings.dmdvmpprevmap.models import Mapping


def test_codes_to_previous_no_previous():
    # in the dmd fixture data, there are no previous codes
    assert vmp_ids_to_previous() == []


def test_codes_to_previous_with_retired_previous():
    # give two of the VMPs previous IDs that are only have one previous
    Mapping.objects.create(id="11", vpidprev="2")
    Mapping.objects.create(id="22", vpidprev="3")

    assert vmp_ids_to_previous() == [
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

    assert sorted(vmp_ids_to_previous()) == [
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
    assert vmp_ids_to_previous() == []


def test_codes_to_previous_with_codes():
    # return previous for selected codes only
    Mapping.objects.create(id="1", vpidprev="0")
    Mapping.objects.create(id="2", vpidprev="1")
    Mapping.objects.create(id="3", vpidprev="2")

    assert sorted(vmp_ids_to_previous(codes=[1, 2])) == [
        ("1", "0"),
        ("2", "0"),
        ("2", "1"),
    ]
