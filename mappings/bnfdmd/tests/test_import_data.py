from mappings.bnfdmd.import_data import import_release
from mappings.bnfdmd.models import Mapping

from .conftest import MOCK_BNFDMD_IMPORT_DATA_PATH


def test_import_release():
    """
    import mock data
    This consists of a minimal mapping file covering
    AMP/AMPP/VMP/VMPPs both with and without BNF mapping entries:

    |VMP / VMPP/ AMP / AMPP|BNF Code        |BNF Name                |SNOMED Code       |
    |----------------------|----------------|------------------------|------------------|
    |VMP                   | 0206020T0AAAGAG| Verapamil 160mg tablets| 42217211000001101|
    |VMPP                  | 0206020T0AAAGAG| Verapamil 160mg tablets| 982511000001103  |
    |AMP                   | 0212000Y0BBAAAA| Zocor 10mg tablets     | 108111000001106  |
    |AMPP                  | 0212000Y0BBAAAA| Zocor 10mg tablets     | 1328211000001104 |
    |AMP                   |                |                        | 5409611000001107 |
    |AMPP                  |                |                        | 5409811000001106 |
    |VMP                   |                |                        | 3377411000001106 |
    |VMPP                  |                |                        | 1139011000001107 |

    """

    import_release(MOCK_BNFDMD_IMPORT_DATA_PATH, None, None)

    assert Mapping.objects.count() == 4
    for dmd_type, bnf, dmd in [
        ("AMP", "0212000Y0BBAAAA", "108111000001106"),
        ("AMPP", "0212000Y0BBAAAA", "1328211000001104"),
        ("VMP", "0206020T0AAAGAG", "42217211000001101"),
        ("VMPP", "0206020T0AAAGAG", "982511000001103"),
    ]:
        mapping = Mapping.objects.get(dmd_type=dmd_type)
        assert mapping.dmd_code == dmd
        assert mapping.bnf_concept_id == bnf
