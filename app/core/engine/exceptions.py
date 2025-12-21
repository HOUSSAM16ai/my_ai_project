class FatalEngineError(Exception):
    """
    Raised when an unsafe or invalid engine configuration is detected.

    This is a critical security exception that prevents the application
    from starting with potentially dangerous database settings.
    """

    pass
