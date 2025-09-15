# cspell:ignore privatemethod
import inspect
from functools import wraps


def privatemethod(func):
    """Decorator to mark an instance method as private to the class.

    Allows calls via self.method() or from class/staticmethods within the same
    class context. Raises AttributeError if called from outside the class.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        frame = inspect.currentframe()
        try:
            caller = frame.f_back
            allowed = False

            while caller is not None:
                caller_self = caller.f_locals.get("self")
                if caller_self is self:
                    allowed = True
                    break

                caller_cls = caller.f_locals.get("cls")
                if caller_cls is not None and isinstance(self, caller_cls):
                    allowed = True
                    break

                caller = caller.f_back

            if not allowed:
                raise AttributeError(
                    "This method is private and can only be called from within the class."
                )

            return func(self, *args, **kwargs)
        finally:
            # Avoid reference cycles by explicitly deleting frame references
            del frame

    return wrapper
