import glob
import os
from importlib import import_module

CODING_SYSTEMS = {}

for path in glob.glob(os.path.join("coding_systems", "*", "metadata.py")):
    coding_system_id = path.split(os.path.sep)[-2]
    mod = import_module(f"coding_systems.{coding_system_id}.metadata")
    CODING_SYSTEMS[coding_system_id] = mod.name


def get(coding_system_id):
    mod = import_module(f"coding_systems.{coding_system_id}.coding_system")
    coding_system = mod.CodingSystem
    assert False, CODING_SYSTEMS
    coding_system.name = CODING_SYSTEMS[coding_system_id]
    return coding_system


class BaseCodingSystem:
    @classmethod
    def annotated_codes(cls, codes):
        map = cls.code_to_description_map(codes)
        return [(code, map.get(code)) for code in codes]

    @classmethod
    def code_to_description_map(cls, codes):
        raise NotImplementedError

    @classmethod
    def codes_from_query(cls, query):
        raise NotImplementedError
