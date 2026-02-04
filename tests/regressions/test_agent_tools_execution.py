from app.services.agent_tools.search_tools import code_search_lexical


def test_tool_execution_imports_correctly():
    """
    Regression test for 'AttributeError: module ... has no attribute AUTOFILL'.
    Verifies that search tools can be imported and executed without circular dependency errors.
    """
    # This query should not crash the system, even if it returns no results (or some results)
    result = code_search_lexical(query="sanity_check_query_12345", root=".")

    # We mainly care that it didn't raise an exception and returned a ToolResult
    assert result is not None
    # 'ok' can be True or False depending on root existence, but for "." it should be True
    # If it crashed, we wouldn't be here.
    if result.ok:
        assert isinstance(result.data, dict)
    else:
        # If it failed, it should not be the specific AttributeError
        assert "AttributeError" not in str(result.error)
