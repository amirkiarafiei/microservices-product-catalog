def check_version(incoming_version: int, stored_version: int) -> bool:
    """
    Checks if an incoming event/update should be processed based on its version.
    Follows Optimistic Concurrency Control rules.

    Args:
        incoming_version: The version number of the incoming data/event.
        stored_version: The version number currently in the database/read-model.

    Returns:
        True if incoming data is newer and should be processed, False otherwise.
    """
    return incoming_version > stored_version
