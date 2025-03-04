import catboost
import numpy as np
import pandas as pd
import json
from bglabutils.basic import *
import sklearn
from sklearn.model_selection import train_test_split
import optuna
from catboost.metrics import RMSE
import sklearn.pipeline

def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    n_vars = 1# if type(data) is list else data.shape[1]
    df = pd.DataFrame(data)
    cols = list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
      cols.append(df.shift(i))
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
      cols.append(df.shift(-i))
    # put it all together
    agg = pd.concat(cols, axis=1)
    # drop rows with NaN values
    if dropnan:
      agg.dropna(inplace=True)
    return agg.values


@dict_transformer
def opt_catboost_hyperparameters(data, target, features, metrics=sklearn.metrics.mean_absolute_error, loss=catboost.metrics.RMSE()):

    training_data = data.loc[np.invert(pd.isnull(data[target]))].copy()
    if len(training_data) < 10:
        print("Not enough data")
        return {}
    training_data[features] = training_data[features].ffill()
    training_data[features] = training_data[features].fillna(0)

    scaler = sklearn.preprocessing.StandardScaler(with_std=True)
    training_data[features] = scaler.fit_transform(training_data[features])
    X_train, X_test, y_train, y_test = train_test_split(training_data[features], training_data[target])

    def objective(trial):
        # define the grid
        param = {
            "objective": "RMSE",
            "iterations": trial.suggest_int("iterations", 100, 1500),
            "learning_rate": trial.suggest_float('learning_rate', 1e-3, 1.0, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-2, 1, log=True),
            "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.01, 0.1),
            "depth": trial.suggest_int("depth", 3, 10),
            "boosting_type": trial.suggest_categorical("boosting_type", ["Ordered", "Plain"]),
            "bootstrap_type": trial.suggest_categorical(
                "bootstrap_type", ["Bayesian", "Bernoulli", "MVS"]
            ),
            "used_ram_limit": "6gb",
        }

        if param["bootstrap_type"] == "Bayesian":
            param["bagging_temperature"] = trial.suggest_float("bagging_temperature", 0, 10)
        elif param["bootstrap_type"] == "Bernoulli":
            param["subsample"] = trial.suggest_float("subsample", 0.1, 1)

        bst = catboost.CatBoostRegressor(loss_function=loss, **param)
        bst.fit(X_train, y_train)
        preds = bst.predict(X_test)
        pred_labels = np.rint(preds)
        # objective should return the metrics that you want to optimize
        accuracy = metrics(y_test, pred_labels)
        return accuracy

    study = optuna.create_study(direction="minimize")
    # you may increase the nubmer of trials in case you have enough time
    study.optimize(objective, n_trials=10, timeout=600)

    print("  Best value: {}".format(study.best_trial.value))
    print(study.best_params)
    return study.best_params


@double_dict_transformer
def train_clf_and_make_predictions(data, params, target, features, loss=catboost.metrics.RMSE()):
    scaler = sklearn.preprocessing.StandardScaler(with_std=True)
    clf = catboost.CatBoostRegressor(loss_function=loss, **params)

    clf_data = data.loc[np.invert(pd.isnull(data[target]))].copy()
    clf_data[features] = clf_data[features].ffill()
    clf_data[features] = clf_data[features].fillna(0)

    if len(clf_data.index) < 5:
        print('Not enough data')
        return None

    pipeline = sklearn.pipeline.Pipeline([('scaler', scaler), ('catboost', clf)])
    pipeline.fit(clf_data[features], clf_data[target])
    data[f'{target}_pred'] = pipeline.predict(data[features].ffill())
    return pipeline


@double_dict_transformer
def cross_val_check(data, params, target, features, loss=catboost.metrics.RMSE(), scoring='neg_root_mean_squared_error'):
    scaler = sklearn.preprocessing.StandardScaler(with_std=True)
    clf = catboost.CatBoostRegressor(loss_function=loss, **params)

    clf_data = data.loc[np.invert(pd.isnull(data[target]))].copy()
    clf_data[features] = clf_data[features].ffill()
    clf_data[features] = clf_data[features].fillna(0)

    pipeline = sklearn.pipeline.Pipeline([('scaler', scaler), ('catboost', clf)])
    if len(clf_data.index) < 5:
        print('Not enough data')
        return 0
    score = sklearn.model_selection.cross_val_score(pipeline,  clf_data[features],  clf_data[target], cv=5, scoring=scoring)
    return score

# @dict_transformer
# def get_importances(data_f, target, features, time_col, clf_params={}, sl=False, sl_length=6, name=""):
#   data, new_features = add_time_features(data_f, time_col)
#   features = features + new_features
#   print('features: ', features)
#   data['process'] = np.invert(pd.isnull(data[target]))
#   if sl:
#     tmp_data = series_to_supervised(data[target], n_in=sl_length, dropnan=False)
#     new_cols = [f'target_{i}' for i in range(tmp_data.shape[1])]
#     new_sup_data = pd.DataFrame(tmp_data, columns=new_cols)
#     data = pd.concat([data, new_sup_data])
#     exist_cols = []
#     for col in  new_cols:
#       data[f'exists_{col}'] = np.invert(pd.isnull(data[col]))
#       exist_cols.append(f'exists_{col}')
#     features = features + new_cols
#
#   training_data = data.query('process==True').copy()
#   target_data = training_data[target].copy()
#   training_data[features] = training_data[features].fillna(method='ffill')
#   training_data[features] = training_data[features].fillna(0)
#
#   if sl:
#     clf = catboost.CatBoostRegressor(iterations=300,
#                                   learning_rate=0.03,
#                                   depth=10,
#                                   l2_leaf_reg=1,
#                                   grow_policy = 'Depthwise',
#                                   loss_function=RMSE(),
#                                   cat_features = exist_cols)  #-2.2270208121057506 0.7252204307404376
#   else:
#     clf = catboost.CatBoostRegressor(loss_function=RMSE(), **clf_params)
#   scaler = sklearn.preprocessing.StandardScaler()
#   clf_X = scaler.fit_transform(training_data[features])
#   clf_X = pd.DataFrame(clf_X, columns=features)
#   clf_y = target_data
#   scores = sklearn.model_selection.cross_val_score(clf, clf_X, clf_y, cv=5, scoring='neg_mean_absolute_percentage_error')
#   print(scores, scores.mean())
#   clf_test = catboost.CatBoostRegressor(iterations=300,
#                                   learning_rate=0.03,
#                                   depth=10,
#                                   l2_leaf_reg=1,
#                                   grow_policy = 'Depthwise',
#                                   loss_function=RMSE())
#   clf_test.fit(clf_X, clf_y)
#
#   print(clf_test.feature_importances_)
#
#   feature_importance = clf_test.feature_importances_
#   sorted_idx = np.argsort(feature_importance)
#   fig = plt.figure(figsize=(12, 6))
#   plt.barh(range(len(sorted_idx)), feature_importance[sorted_idx], align='center')
#
#   if use_sl:
#     plt.yticks(range(len(sorted_idx)), np.array(features)[sorted_idx])
#   else:
#     plt.yticks(range(len(sorted_idx)), np.array(features)[sorted_idx])
#   plt.title(f'Feature Importance for {name}')
#   plt.savefig(f"{name}.png")
#   return {np.array(features)[i]:feature_importance[i] for i in sorted_idx}