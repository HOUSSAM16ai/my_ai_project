"""
Mutation Testing Configuration for MutMut
==========================================

Configuration for mutation testing to achieve 100% mutation score.
Mutations test the quality of our test suite by introducing bugs.
"""


def pre_mutation(context):
    """
    Hook called before each mutation.
    Can be used to skip certain mutations or files.
    """
    # Skip migrations
    if "migrations/" in context.filename:
        context.skip = True

    # Skip test files themselves
    if context.filename.startswith("tests/"):
        context.skip = True

    # Skip generated files
    if "__pycache__" in context.filename:
        context.skip = True


def post_mutation(context):
    """
    Hook called after each mutation test.
    Can be used for custom reporting or analysis.
    """
    pass
