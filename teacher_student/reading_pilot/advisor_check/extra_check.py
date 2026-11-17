"""Advisor's extra checks on the reading pilot.
1. A reader that knows only the formation and group names (no curves, no pictures).
2. Curve-picture reader against the document teacher, step by step.
3. How often each reader changes rock class per 100 m.

Run:  python3 extra_check.py <path to teacher_student/reading_pilot> <path to train.csv>
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_check import KEYS, item_flags, summarise, STEP

REPO = sys.argv[1]
TRAIN = sys.argv[2]
df = pd.read_csv(TRAIN, sep=';', usecols=['WELL', 'DEPTH_MD', 'GROUP', 'FORMATION', 'FORCE_2020_LITHOFACIES_LITHOLOGY'])
df['expert'] = df['FORCE_2020_LITHOFACIES_LITHOLOGY'].map(KEYS)
roles = pd.read_csv(REPO + '/draw.csv').groupby('role')['well'].apply(list).to_dict()
TEST = roles['test']


def lookup_score(train_wells, label):
    tr = df[df.WELL.isin(train_wells)]
    f = tr.dropna(subset=['FORMATION']).groupby('FORMATION')['expert'].agg(lambda s: s.value_counts().index[0]).to_dict()
    g = tr.dropna(subset=['GROUP']).groupby('GROUP')['expert'].agg(lambda s: s.value_counts().index[0]).to_dict()
    fl = []; ex = []; known_f = 0; n = 0
    for w in TEST:
        t = df[df.WELL == w].sort_values('DEPTH_MD')
        pred = []
        for fo, gr in zip(t['FORMATION'], t['GROUP']):
            if isinstance(fo, str) and fo in f:
                pred.append(f[fo]); known_f += 1
            elif isinstance(gr, str) and gr in g:
                pred.append(g[gr])
            else:
                pred.append('Shale')
            n += 1
        e = t['expert'].values.astype(object)
        fl.append(item_flags(t['DEPTH_MD'].values, e, np.array(pred, dtype=object))); ex.append(e)
    s = summarise(fl, ex)
    print(f"{label:58s} strict {s['strict']:.1f}  tolerant {s['tolerant']:.1f}  balanced {s['balanced']:.1f}   (formation name known for {100*known_f/n:.0f}% of depth)")


print('=== 1. A reader that knows ONLY the formation and group names (no curves, no pictures)')
lookup_score(roles['example'], 'name -> most common rock, learned from the 10 example wells')
lookup_score(roles['example'] + roles['extra'] + roles['curve'], 'name -> most common rock, learned from all 93 other wells')
t = df[df.WELL.isin(TEST)]
print('share of test-well depth with a formation name:', round(100 * t['FORMATION'].notna().mean(), 1),
      '%; with a group name:', round(100 * t['GROUP'].notna().mean(), 1), '%')

rows = []
for w in TEST:
    s = pd.read_csv(f"{REPO}/scores/steps_{w.replace('/', '_')}.csv", dtype=str, keep_default_na=False)
    l = df[(df.WELL == w) & df.expert.notna()].sort_values('DEPTH_MD')
    s['expert'] = l['expert'].values; s['well'] = w
    rows.append(s)
S = pd.concat(rows, ignore_index=True)

both = (S['curve picture'] != '') & (S['combined'] != '')
agree = both & (S['curve picture'] == S['combined'])
dis = both & ~agree
print('\n=== 2. Curve-picture reader against the document teacher, step by step (strict)')
print('both gave a class:', round(100 * both.mean(), 1), '% of depth; they agree on', round(100 * agree.sum() / both.sum(), 1), '% of that')
print('where they agree, they match the experts on', round(100 * (S.loc[agree, 'curve picture'] == S.loc[agree, 'expert']).mean(), 1), '%')
cr = (S.loc[dis, 'curve picture'] == S.loc[dis, 'expert']).mean(); tr = (S.loc[dis, 'combined'] == S.loc[dis, 'expert']).mean()
print('where they disagree (', round(dis.sum() * STEP), 'm ): curve picture right', round(100 * cr, 1), '%, teacher right', round(100 * tr, 1), '%, neither', round(100 * (1 - cr - tr), 1), '%')
print('curve picture agrees with the all-well model on', round(100 * (S['all-well model'] == S['curve picture']).mean(), 1),
      '% of depth; with the ten-well model on', round(100 * (S['ten-well model'] == S['curve picture']).mean(), 1), '%')

print('\n=== 3. Changes of rock class per 100 m (steps without a class are skipped)')
for col in ['expert', 'curve picture', 'combined', 'ten-well model', 'all-well model', 'curve picture (Sonnet)', 'curve picture (Haiku)']:
    changes = 0; metres = 0.0
    for w in TEST:
        v = S.loc[S.well == w, col].values
        v = v[v != '']
        changes += int((v[1:] != v[:-1]).sum()); metres += len(v) * STEP
    print(f"{col:26s} {100 * changes / metres:5.1f}")
