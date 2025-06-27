from abc import ABC, abstractmethod


class AIModel(ABC):
    @abstractmethod
    def predict(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)
