from coding_systems.dmd.models import AMP, VMP

from .models import Mapping


def bnf_to_dmd(bnf_codes):
    vmp_id_to_bnf_code = dict(
        Mapping.objects.filter(
            bnf_concept_id__in=bnf_codes, dmd_type="VMP"
        ).values_list("dmd_code", "bnf_concept_id")
    )
    amp_id_to_bnf_code = dict(
        Mapping.objects.filter(
            bnf_concept_id__in=bnf_codes, dmd_type="AMP"
        ).values_list("dmd_code", "bnf_concept_id")
    )

    rows = []

    for vmp in VMP.objects.filter(id__in=list(vmp_id_to_bnf_code)):
        rows.append(
            {
                "dmd_type": "VMP",
                "dmd_id": vmp.id,
                "dmd_name": vmp.nm,
                "bnf_code": vmp_id_to_bnf_code[vmp.id],
            }
        )

    for amp in AMP.objects.filter(id__in=list(amp_id_to_bnf_code)):
        rows.append(
            {
                "dmd_type": "AMP",
                "dmd_id": amp.id,
                "dmd_name": amp.nm,
                "bnf_code": amp_id_to_bnf_code[amp.id],
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["bnf_code"],
            ["VMP", "AMP"].index(row["dmd_type"]),
        ),
    )
