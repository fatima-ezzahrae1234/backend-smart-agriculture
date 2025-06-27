from abc import ABC, abstractmethod
import pickle
from pathlib import Path
from collections import Counter
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


from ai.aimodel import AIModel

parent_path = Path(__file__).parent


class RecommendationAIModel(AIModel, ABC):

    def __init__(self):
        self.scaler = None
        with open(parent_path / "scaler.pkl", "rb") as f:
            self.scaler = pickle.load(f)

    def predict(self, X):
        scaled_x = X
        if self.scaler is not None:
            scaled_x = self.scaler.transform([X])

        return self.forward(scaled_x)

    @abstractmethod
    def forward(self, scaled_x):
        pass


class SklearnBasedModel(RecommendationAIModel):

    def __init__(self, f_name):
        super().__init__()
        self.model = None
        with open(f_name, "rb") as f:
            self.model = pickle.load(f)

    def forward(self, scaled_x):
        predicted_y = self.model.predict(scaled_x)
        return predicted_y[0]


lr_model = SklearnBasedModel(parent_path / "logistic_model.pkl")
nb_model = SklearnBasedModel(parent_path / "naive_bayes_model.pkl")
svm_model = SklearnBasedModel(parent_path / "svm_model.pkl")


class MultiModelBasedRecommender(AIModel):

    def __init__(self, *models):
        for model in models:
            if not isinstance(model, AIModel):
                raise TypeError("Instance of AIModel class is required as model object")
        self.models = models

    def predict(self, x):
        predictions = [m(x) for m in self.models]
        counter = Counter(predictions)
        voted = counter.most_common(1)
        return voted[0][0]


recommender_model = MultiModelBasedRecommender(lr_model, nb_model, svm_model)
