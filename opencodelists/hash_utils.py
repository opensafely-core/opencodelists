"""
This module contains a pair of functions for efficiently converting between integers
and strings, such that unhash(hash(m, k), k) == m.  It is useful for generating
random-looking identifiers from sequential ids.  It is not suitable for cryptography!

For instance:

>>> for i in range(10):
...   print(hash(i, "OpenCodelists"))
...
00000000
01c5057f
038a0afe
054f107d
071415fc
08d91b7b
0a9e20fa
0c632679
0e282bf8
0fed3177

How does it work?  Given a prime number N, then for every c ∈ {1..N-1}, there exists a
unique inv_c = pow(c, N - 2) % N such that (c * inv_c) % N == 1.  It follows that we can
convert any m ∈ {1..N-1} to m_hash ∈ {1..N-1} with (m * c) % N, and retrieve m with
(m_hash * c) % N.

When producing a string hash, we convert m_hash to hex, strip the leading `0x`, and pad
to 8 characters.

See https://en.wikipedia.org/wiki/Modular_multiplicative_inverse for more.
"""

# Do not change this value!  Doing so will invalidate any hashes that have been recorded
# elsewhere (eg in URLs).
N = 2 ** 31 - 1


def hash(m, key):
    """Hash integer m using key to give a string."""

    if m >= N:
        raise ValueError(f"{m} is too large")
    c = int(key, 36)
    assert c < N

    m_hash = (m * c) % N
    return hex(m_hash)[2:].rjust(8, "0")


def unhash(h, key):
    """Unhash string h using key to give an integer."""

    if len(h) > 8:
        raise ValueError(f"{h} is too long")
    c = int(key, 36)
    assert c < N
    inv_c = pow(c, N - 2, N)  # Equivalent to pow(c, N - 2) % N, but efficient!
    return int(h, 16) * inv_c % N
