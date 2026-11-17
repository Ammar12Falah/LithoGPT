"""Advisor's own plain model, written afresh, to see whether the run's two
plain models and its learning curve are in the right range.
Different features (no window features), different settings, different draws.

Run:  python3 baseline_check.py <path to teacher_student/reading_pilot> <path to train.csv>
"""
import os, sys, time
import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_check import KEYS, item_flags, summarise

REPO = sys.argv[1]
TRAIN = sys.argv[2]
DRAW = REPO + '/draw.csv'

t0 = time.time()
df = pd.read_csv(TRAIN, sep=';')
df['expert'] = df['FORCE_2020_LITHOFACIES_LITHOLOGY'].map(KEYS)
df = df[df['expert'].notna()].reset_index(drop=True)
classes = sorted(df['expert'].unique())
cid = {c: i for i, c in enumerate(classes)}
df['y'] = df['expert'].map(cid).astype(int)
for c in ['GROUP', 'FORMATION']:
    df[c] = df[c].astype('category')
num = ['DEPTH_MD', 'X_LOC', 'Y_LOC', 'Z_LOC', 'CALI', 'RSHA', 'RMED', 'RDEP', 'RHOB', 'GR', 'SGR', 'NPHI',
       'PEF', 'DTC', 'SP', 'BS', 'ROP', 'DTS', 'DCAL', 'DRHO', 'MUDWEIGHT', 'RMIC', 'ROPA', 'RXO']
feats = num + ['GROUP', 'FORMATION']
roles = pd.read_csv(DRAW).groupby('role')['well'].apply(list).to_dict()
print('loaded', len(df), 'rows; roles', {k: len(v) for k, v in roles.items()}, flush=True)

PARAMS = dict(objective='multiclass', num_class=len(classes), learning_rate=0.1, num_leaves=31,
              min_data_in_leaf=100, feature_fraction=0.6, bagging_fraction=0.7, bagging_freq=1,
              lambda_l2=5.0, max_bin=63, num_threads=2, verbose=-1, seed=11)


def train(wells, every):
    m = df['WELL'].isin(wells).values
    idx = np.nonzero(m)[0][::every]
    ds = lgb.Dataset(df.loc[idx, feats], label=df.loc[idx, 'y'], categorical_feature=['GROUP', 'FORMATION'])
    return lgb.train(PARAMS, ds, num_boost_round=100)


def score(model, wells):
    fl, ex = [], []
    for w in wells:
        g = df[df['WELL'] == w].sort_values('DEPTH_MD')
        pred = np.array(classes, dtype=object)[model.predict(g[feats]).argmax(1)]
        e = g['expert'].values.astype(object)
        fl.append(item_flags(g['DEPTH_MD'].values, e, pred)); ex.append(e)
    s = summarise(fl, ex)
    return {k: round(float(s[k]), 1) for k in ['strict', 'tolerant', 'soft', 'balanced']}


pool = roles['example'] + roles['extra']
nontest = pool + roles['curve']

m = train(roles['example'], 1)
print('ten example wells  -> 5 test wells :', score(m, roles['test']), '| -> 23 curve wells:', score(m, roles['curve']), flush=True)

rng = np.random.default_rng(7)
res = []
for k in range(3):
    wells = list(rng.choice(pool, 10, replace=False))
    r = score(train(wells, 1), roles['curve'])
    res.append(r)
    print('ten random pool wells, draw', k + 1, '-> 23 curve wells:', r, flush=True)
print('mean of the three ten-well draws on the curve wells:',
      {k: round(float(np.mean([r[k] for r in res])), 1) for k in res[0]}, flush=True)

m = train(pool, 3)
print('all 70 pool wells   -> 23 curve wells:', score(m, roles['curve']), flush=True)

m = train(nontest, 3)
print('all 93 other wells  -> 5 test wells  :', score(m, roles['test']), flush=True)
print('done in', round(time.time() - t0), 's', flush=True)
