
class SingletonMetaclass(type):
    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
            return cls.__instance
        else:
            return cls.__instance
