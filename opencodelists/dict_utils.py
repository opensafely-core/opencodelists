from collections import defaultdict


def invert_dict(d):
    inv_d = defaultdict(list)
    for k, v in d.items():
        inv_d[v].append(k)
    return dict(inv_d)
