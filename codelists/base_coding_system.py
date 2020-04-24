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
