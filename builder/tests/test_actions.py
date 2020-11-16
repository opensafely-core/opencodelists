from builder import actions
from opencodelists.tests.factories import UserFactory


def test_create_codelist():
    # Arrange: create a user
    owner = UserFactory()

    # Act: create a codelist
    cl = actions.create_codelist(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Assert...
    # that a codelist's attributes have been set
    assert cl.owner == owner
    assert cl.name == "Test Codelist"
    assert cl.slug == "test-codelist"
    assert cl.coding_system_id == "snomedct"


def test_create_codelist_with_codes():
    # Arrange: create a user
    owner = UserFactory()

    # Act: create a codelist with codes
    cl = actions.create_codelist_with_codes(
        owner=owner,
        name="Test Codelist",
        coding_system_id="snomedct",
        codes=["1067731000000107", "1068181000000106"],
    )

    # Assert...
    # that a codelist's attributes have been set
    assert cl.owner == owner
    assert cl.name == "Test Codelist"
    assert cl.slug == "test-codelist"
    assert cl.coding_system_id == "snomedct"
    assert cl.codes.count() == 2


def test_create_search():
    # Arrange: create a codelist
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Act: create a first search
    s = actions.create_search(
        codelist=cl, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Assert...
    # that the search's attributes have been set
    assert s.codelist == cl
    assert s.term == "swimming"
    assert s.slug == "swimming"

    # that the newly created search has 2 results
    assert s.results.count() == 2
    # that the codelist has 1 search
    assert cl.searches.count() == 1
    # that the codelist has 2 codes
    assert cl.codes.count() == 2

    # Act: create another search
    s = actions.create_search(
        codelist=cl, term="synchronised", codes=["1068181000000106"]
    )

    # Assert...
    # that the newly created search has 1 result
    assert s.results.count() == 1
    # that the codelist has 2 searches
    assert cl.searches.count() == 2
    # that the codelist still has 2 codes
    assert cl.codes.count() == 2


def test_delete_search():
    # Arrange: create a codelist with searches
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )
    s1 = actions.create_search(
        codelist=cl, term="synchronised", codes=["1068181000000106"]
    )
    s2 = actions.create_search(
        codelist=cl, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Act: delete the search for "swimming"
    actions.delete_search(search=s2)

    # Assert...
    # that the codelist has only 1 search
    assert cl.searches.count() == 1
    # that the codelist has only 1 code
    assert cl.codes.count() == 1

    # Arrange: recreate the search for "swimming"
    actions.create_search(
        codelist=cl, term="swimming", codes=["1067731000000107", "1068181000000106"]
    )

    # Act: delete the search for "synchronised"
    actions.delete_search(search=s1)

    # Assert...
    # that the codelist has only 1 search
    assert cl.searches.count() == 1
    # that the codelist still has both codes
    assert cl.codes.count() == 2


def test_update_code_statuses(tennis_elbow):
    # Arrange: load fixtures and create a codelist with a search
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Test Codelist", coding_system_id="snomedct"
    )

    # Search results have this structure in hierarchy
    #
    # 116309007 Finding of elbow region
    #     128133004 Disorder of elbow
    #         239964003 Soft tissue lesion of elbow region
    #         35185008 Enthesopathy of elbow region
    #             73583000 Epicondylitis
    #                 202855006 Lateral epicondylitis
    #         429554009 Arthropathy of elbow
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    #     298869002 Finding of elbow joint
    #         298163003 Elbow joint inflamed
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    #         429554009 Arthropathy of elbow
    #             439656005 Arthritis of elbow
    #                 202855006 Lateral epicondylitis
    actions.create_search(
        codelist=cl,
        term="elbow",
        codes=[
            "116309007",  # Finding of elbow region
            "128133004",  # Disorder of elbow
            "239964003",  # Soft tissue lesion of elbow region
            "35185008",  # Enthesopathy of elbow region
            "73583000",  # Epicondylitis
            "202855006",  # Lateral epicondylitis
            "429554009",  # Arthropathy of elbow
            "439656005",  # Arthritis of elbow
            "298869002",  # Finding of elbow joint
            "298163003",  # Elbow joint inflamed
        ],
    )

    # Act: process single update from the client
    actions.update_code_statuses(codelist=cl, updates=[("35185008", "+")])

    # Assert that results have the expected status
    assert dict(cl.codes.values_list("code", "status")) == {
        "116309007": "?",  # Finding of elbow region
        "128133004": "?",  # Disorder of elbow
        "239964003": "?",  # Soft tissue lesion of elbow region
        "35185008": "+",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "202855006": "(+)",  # Lateral epicondylitis
        "429554009": "?",  # Arthropathy of elbow
        "439656005": "?",  # Arthritis of elbow
        "298869002": "?",  # Finding of elbow joint
        "298163003": "?",  # Elbow joint inflamed
    }

    # Act: process multiple updates from the client
    actions.update_code_statuses(
        codelist=cl, updates=[("35185008", "-"), ("116309007", "+"), ("35185008", "?")]
    )

    # Assert that results have the expected status
    assert dict(cl.codes.values_list("code", "status")) == {
        "116309007": "+",  # Finding of elbow region
        "128133004": "(+)",  # Disorder of elbow
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "202855006": "(+)",  # Lateral epicondylitis
        "429554009": "(+)",  # Arthropathy of elbow
        "439656005": "(+)",  # Arthritis of elbow
        "298869002": "(+)",  # Finding of elbow joint
        "298163003": "(+)",  # Elbow joint inflamed
    }
