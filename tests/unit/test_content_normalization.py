from microservices.research_agent.src.content.utils import normalize_set_name


def test_normalize_set_name_subject_1():
    expected = "subject_1"
    inputs = [
        "subject 1",
        "Subject 1",
        "SUBJECT 1",
        "subject1",
        "s1",
        "sub1",
        "subject_1",
        "subject-1",
        "الموضوع الأول",
        "الموضوع 1",
    ]
    for i in inputs:
        assert normalize_set_name(i) == expected, f"Failed for input: {i}"


def test_normalize_set_name_subject_2():
    expected = "subject_2"
    inputs = [
        "subject 2",
        "Subject 2",
        "s2",
        "sub2",
        "subject_2",
        "subject-2",
        "الموضوع الثاني",
        "الموضوع 2",
    ]
    for i in inputs:
        assert normalize_set_name(i) == expected, f"Failed for input: {i}"


def test_normalize_set_name_unknown():
    assert normalize_set_name("unknown") == "unknown"
    assert normalize_set_name("bac 2024") == "bac 2024"
    assert normalize_set_name("") is None
    assert normalize_set_name(None) is None
