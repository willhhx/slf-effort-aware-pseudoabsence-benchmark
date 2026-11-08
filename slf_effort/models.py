"""Presence/background classifiers.

rf : balanced-by-weights random forest
lr : L2-regularised logistic regression on quadratic features. With presence
     vs background data this is the standard regularised-regression analogue of
     MaxEnt (it is NOT the MaxEnt software; call it 'MaxEnt-style logistic').
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

MODELS = ("rf", "lr")
MODEL_LABELS = {"rf": "Random forest", "lr": "MaxEnt-style logistic"}


def make_model(name: str, n_features: int, cfg, seed: int):
    if name == "rf":
        mf = max(1, int(np.ceil(np.sqrt(n_features))))
        return RandomForestClassifier(n_estimators=cfg.n_trees, min_samples_leaf=3,
                                      max_features=mf, n_jobs=cfg.n_jobs, random_state=seed)
    if name == "lr":
        return Pipeline([
            ("sc", StandardScaler()),
            ("poly", PolynomialFeatures(2, include_bias=False)),
            ("lr", LogisticRegression(C=0.3, max_iter=5000)),
        ])
    raise ValueError(f"unknown model {name}")


def fit_predict(name, X, y, w, Xpred, cfg, seed):
    m = make_model(name, X.shape[1], cfg, seed)
    if name == "rf":
        m.fit(X, y, sample_weight=w)
    else:
        m.fit(X, y, lr__sample_weight=w)
    return m.predict_proba(Xpred)[:, 1]
