
import pytest
from app.services.chat.tools.retrieval.parsing import is_exercise_header_match, build_number_patterns

@pytest.mark.parametrize("header, exercise_num, expected", [
    ("1. Questions", 1, True),
    ("1) Questions", 1, True),
    ("1- Questions", 1, True),
    ("1 - Questions", 1, True),
    ("1. نص التمرين", 1, True),
    ("1 نص التمرين", 1, False), # Missing punctuation prefix
    ("11. Questions", 1, False), # Should not match 11 as 1
    ("Exercise 1", 1, True),
    ("التمرين الأول", 1, True),
    ("2. Questions", 1, False),
    ("1.1 Questions", 1, True), # Accepted as part of hierarchy logic
])
def test_is_exercise_header_match(header, exercise_num, expected):
    # Use the real pattern builder to ensure normalization consistency
    number_patterns = build_number_patterns(exercise_num)

    result = is_exercise_header_match(
        header_text=header,
        target_exercise_num=exercise_num,
        number_patterns=number_patterns,
        target_topics=[]
    )
    assert result == expected
