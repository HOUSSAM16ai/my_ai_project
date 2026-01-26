from app.services.chat.tools.retrieval import (
    _expand_query_semantics,
    _extract_specific_exercise,
    _is_specific_request,
)


def test_extracts_numbered_exercise_with_header() -> None:
    content = (
        "# اختبار الاسترجاع\n"
        "\n"
        "## بطاقة الامتحان\n"
        "السنة: 2024\n"
        "\n"
        "## التمرين الأول\n"
        "نص التمرين الأول\n"
        "\n"
        "## التمرين الثاني\n"
        "نص التمرين الثاني\n"
    )

    result = _extract_specific_exercise(content, "تمرين ١")

    assert result is not None
    assert "اختبار الاسترجاع" in result
    assert "بطاقة الامتحان" in result
    assert "التمرين الأول" in result
    assert "نص التمرين الأول" in result
    assert "التمرين الثاني" not in result


def test_extracts_topic_based_exercise() -> None:
    content = (
        "# اختبار الموضوعات\n"
        "\n"
        "## Exercise 3 - Probability\n"
        "Content for probability exercise\n"
        "\n"
        "## Exercise 4 - Geometry\n"
        "Content for geometry exercise\n"
    )

    result = _extract_specific_exercise(content, "Probability")

    assert result is not None
    assert "Exercise 3" in result
    assert "probability exercise" in result.lower()
    assert "Exercise 4" not in result


def test_returns_none_when_no_specific_request() -> None:
    content = "# اختبار بدون تطابق\n\n## التمرين الأول\nنص التمرين الأول\n"

    assert _extract_specific_exercise(content, "مقدمة عامة") is None


def test_specific_request_ignores_embedded_ex() -> None:
    assert _is_specific_request("next steps") is False


def test_specific_request_normalizes_arabic_variants() -> None:
    assert _is_specific_request("إحتمالات") is True


def test_extracts_numbered_exercise_with_explicit_number_label() -> None:
    content = (
        "# تمارين الحساب\n"
        "\n"
        "## التمرين الثاني\n"
        "محتوى التمرين الثاني\n"
        "\n"
        "## التمرين الثالث\n"
        "محتوى التمرين الثالث\n"
    )

    result = _extract_specific_exercise(content, "تمرين رقم ٢")

    assert result is not None
    assert "التمرين الثاني" in result
    assert "محتوى التمرين الثاني" in result
    assert "التمرين الثالث" not in result


def test_extracts_english_numbered_exercise_with_hash() -> None:
    content = (
        "# Algebra Exercises\n"
        "\n"
        "## Exercise 4 - Functions\n"
        "Exercise four content\n"
        "\n"
        "## Exercise 5 - Sequences\n"
        "Exercise five content\n"
    )

    result = _extract_specific_exercise(content, "Exercise #4")

    assert result is not None
    assert "Exercise 4" in result
    assert "Exercise four content" in result
    assert "Exercise 5" not in result


def test_extracts_english_numbered_exercise_with_number_word() -> None:
    content = (
        "# Linear Algebra Exercises\n"
        "\n"
        "## Exercise 2 - Matrices\n"
        "Matrices content\n"
        "\n"
        "## Exercise 3 - Vectors\n"
        "Vectors content\n"
    )

    result = _extract_specific_exercise(content, "exercise number 2")

    assert result is not None
    assert "Exercise 2" in result
    assert "Matrices content" in result
    assert "Exercise 3" not in result


def test_extracts_numbered_exercise_with_parentheses() -> None:
    content = (
        "# تمارين الهندسة\n"
        "\n"
        "## التمرين (2)\n"
        "محتوى التمرين الثاني\n"
        "\n"
        "## التمرين (3)\n"
        "محتوى التمرين الثالث\n"
    )

    result = _extract_specific_exercise(content, "التمرين (٢)")

    assert result is not None
    assert "التمرين (2)" in result
    assert "محتوى التمرين الثاني" in result
    assert "التمرين (3)" not in result


def test_extracts_english_exercise_with_parentheses() -> None:
    content = (
        "# Calculus Exercises\n"
        "\n"
        "## Exercise (4) - Limits\n"
        "Limits content\n"
        "\n"
        "## Exercise (5) - Derivatives\n"
        "Derivatives content\n"
    )

    result = _extract_specific_exercise(content, "Exercise (4)")

    assert result is not None
    assert "Exercise (4)" in result
    assert "Limits content" in result
    assert "Exercise (5)" not in result


def test_expand_query_semantics_adds_branch_synonyms() -> None:
    expanded = _expand_query_semantics(
        "بكالوريا رياضيات",
        year="2024",
        subject="رياضيات",
        branch="علوم تجريبية",
        exam_ref="الموضوع الأول",
    )

    assert "experimental sciences" in expanded
    assert "math" in expanded
