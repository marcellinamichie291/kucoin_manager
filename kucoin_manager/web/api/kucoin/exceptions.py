"""Exceptions."""


class NoAccountFoundError(Exception):
    """NoAccountFoundError."""

    def __init__(
        self,
        msg=None,
        *args,
        **kwargs,
    ):
        msg = msg or "No account found inside accounts file."
        super().__init__(msg, *args, **kwargs)
