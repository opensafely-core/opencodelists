# This module contains a pair of functions for efficiently converting between integers
# and strings, such that unhash(hash(n, k), k) == n.  It is useful for generating
# random-looking identifiers from sequential ids.  It is not suitable for cryptography!
#
# For instance:
#
# >>> for i in range(10):
# ...   print(hash(i, "OpenCodelists"))
# ...
# 00000000
# 01c5057f
# 038a0afe
# 054f107d
# 071415fc
# 08d91b7b
# 0a9e20fa
# 0c632679
# 0e282bf8
# 0fed3177
#
# I can't remember how this works, but mumble mumble Euler's theorem mumble mumble .


N = 2 ** 31 - 1  # Do not change this value!


def hash(n, key):
    if n >= N:
        raise ValueError(f"{n} is too large")
    c = int(key, 36)
    return hex((n * c) % N)[2:].rjust(8, "0")


def unhash(h, key):
    if len(h) > 8:
        raise ValueError(f"{h} is too long")
    c = int(key, 36)
    inv_c = pow(c, N - 2, N)
    return int(h, 16) * inv_c % N
