from opencodelists.hash_utils import hash, unhash


def test_roundtrip():
    key = "roundtrip"
    for i in range(100):
        assert unhash(hash(i, key), key) == i
