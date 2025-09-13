# cspell:ignore privatemethod
class privatemethod(classmethod):
    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError(
                "This method is only available on the class, not on instances."
            )
        return super().__get__(instance, owner)
