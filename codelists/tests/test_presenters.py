# from codelists.coding_systems import CODING_SYSTEMS
# from codelists.hierarchy import Hierarchy
# from codelists.presenters import (
#     present_definition_for_download,
#     present_search_results,
#     present_tree,
#     present_tree_view_sections,
# )


# def test_present_search_results(version_with_complete_searches):
#     version = version_with_complete_searches
#     code_to_term = version.coding_system.code_to_term(version.codeset.all_codes())
#     results = present_search_results(version, code_to_term)
#     assert [r["term_or_code"] for r in results] == [
#         "arthritis",
#         "elbow",
#         "tennis",
#         "code: 439656005",
#     ]
#     assert results[0] == {
#         "term_or_code": "arthritis",
#         "num_included": 2,
#         "total": 3,
#         "rows": [
#             {"code": "3723001", "included": False, "term": "Arthritis"},
#             {"code": "439656005", "included": True, "term": "Arthritis of elbow"},
#             {"code": "202855006", "included": True, "term": "Lateral epicondylitis"},
#         ],
#     }


# def test_present_definition_for_download(version):
#     rows = present_definition_for_download(version)
#     assert rows == [
#         ("code", "term", "is_included"),
#         ("156659008", "(Epicondylitis &/or tennis elbow) or (golfers' elbow)", "+"),
#         ("128133004", "Disorder of elbow", "+"),
#     ]


# def test_present_tree_view_sections(disorder_of_elbow_codes):
#     # Remove high-level "Disorder of elbow" code from disorder_of_elbow_codes so that
#     # the "Disorder" section has mutliple trees.
#     codes = [c for c in disorder_of_elbow_codes if c != "128133004"]
#     snomedct = CODING_SYSTEMS["snomedct"]
#     code_to_term = snomedct.code_to_term(codes)
#     hierarchy = Hierarchy.from_codes(snomedct, codes)

#     sections = present_tree_view_sections(codes, hierarchy, snomedct, code_to_term)

#     assert sections == [
#         (
#             "Disorder",
#             [
#                 "429554009",  # Arthropathy of elbow
#                 "35185008",  # Enthesopathy of elbow region
#                 "239964003",  # Soft tissue lesion of elbow region
#             ],
#         ),
#         ("[inactive] Disorder", ["156659008"]),
#     ]


# def test_present_tree(disorder_of_elbow_codes):
#     snomedct = CODING_SYSTEMS["snomedct"]
#     code_to_term = snomedct.code_to_term(disorder_of_elbow_codes)
#     hierarchy = Hierarchy.from_codes(snomedct, disorder_of_elbow_codes)

#     tree = present_tree("128133004", hierarchy, code_to_term, 2)

#     assert tree == {
#         "code": "128133004",
#         "term": "Disorder of elbow",
#         "children": [
#             {
#                 "code": "429554009",
#                 "term": "Arthropathy of elbow",
#                 "children": [
#                     {
#                         "code": "439656005",
#                         "term": "Arthritis of elbow",
#                         "children": True,
#                     }
#                 ],
#             },
#             {
#                 "code": "35185008",
#                 "term": "Enthesopathy of elbow region",
#                 "children": [
#                     {
#                         "code": "73583000",
#                         "term": "Epicondylitis",
#                         "children": True,
#                     }
#                 ],
#             },
#             {
#                 "code": "239964003",
#                 "term": "Soft tissue lesion of elbow region",
#                 "children": False,
#             },
#         ],
#     }
