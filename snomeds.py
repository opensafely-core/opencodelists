import webbrowser

slugs = [
    "asplenia-snomed",
    "aplastic-anaemia-snomed",
    "asthma-diagnosis-snomed",
    "bone-marrow-transplant-snomed",
    "cancer-excluding-lung-and-haematological-snomed",
    "chemotherapy-or-radiotherapy-snomed",
    "chronic-cardiac-disease-snomed",
    "chronic-liver-disease-snomed",
    "chronic-respiratory-disease-snomed",
    "dementia-snomed",
    "diabetes-snomed",
    "ethnicity-snomed",
    "gi-bleed-or-ulcer-snomed",
    "haematological-cancer-snomed",
    "hiv-snomed",
    "hypertension-snomed",
    "inflammatory-bowel-disease-snomed",
    "lung-cancer-snomed",
    "other-neurological-conditions-snomed",
    "permanent-immunosuppresion-snomed",
    "ra-sle-psoriasis-snomed",
    "sickle-cell-disease-snomed",
    "smoking-clear-snomed",
    "smoking-unclear-snomed",
    "solid-organ-transplantation-snomed",
    "stroke-snomed",
    "temporary-immunosuppresion-snomed",
    "chronic-kidney-disease-snomed",
]

for slug in slugs:
    url = f"http://localhost:8000/codelist/opensafely/{slug}/"
    webbrowser.open_new_tab(url)
