__all__ = ["NameCollisionError"]


class NameCollisionError(Exception):
    """
    Duplicate command name during loading.
    """

    name: str
    message: str
    defined_in: str
    redefined_in: str

    def __init__(self, name: str, defined_in: str, redefined_in: str) -> None:
        self.name = name
        self.message = f"Duplicate command definition for '{name}' found. " \
                       f"First defined in '{defined_in}', " \
                       f"redefined in '{redefined_in}'."
        super().__init__(self.message)
