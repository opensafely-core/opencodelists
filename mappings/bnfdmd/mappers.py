from coding_systems.dmd.models import AMP, AMPP, VMP, VMPP

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
    vmpp_id_to_bnf_code = dict(
        Mapping.objects.filter(
            bnf_concept_id__in=bnf_codes, dmd_type="VMPP"
        ).values_list("dmd_code", "bnf_concept_id")
    )
    ampp_id_to_bnf_code = dict(
        Mapping.objects.filter(
            bnf_concept_id__in=bnf_codes, dmd_type="AMPP"
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

    for vmpp in VMPP.objects.filter(id__in=list(vmpp_id_to_bnf_code)):
        rows.append(
            {
                "dmd_type": "VMPP",
                "dmd_id": vmpp.id,
                "dmd_name": vmpp.nm,
                "bnf_code": vmpp_id_to_bnf_code[vmpp.id],
            }
        )

    for ampp in AMPP.objects.filter(id__in=list(ampp_id_to_bnf_code)):
        rows.append(
            {
                "dmd_type": "AMPP",
                "dmd_id": ampp.id,
                "dmd_name": ampp.nm,
                "bnf_code": ampp_id_to_bnf_code[ampp.id],
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["bnf_code"],
            ["VMP", "AMP", "VMPP", "AMPP"].index(row["dmd_type"]),
        ),
    )
