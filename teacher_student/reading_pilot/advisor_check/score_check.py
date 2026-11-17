"""Independent re-scoring of the reading pilot (advisor's check).

Reads the public FORCE training file, the frozen reading files and the
per-step tables of the run, and recomputes every headline score with code
that shares nothing with the run's own scoring code.
"""
import sys
import numpy as np
import pandas as pd

REPO = sys.argv[1] if len(sys.argv) > 2 else ''
TRAIN = sys.argv[2] if len(sys.argv) > 2 else ''

KEYS = {30000: 'Sandstone', 65030: 'Sandstone/Shale', 65000: 'Shale', 80000: 'Marl',
        74000: 'Dolomite', 70000: 'Limestone', 70032: 'Chalk', 88000: 'Halite',
        86000: 'Anhydrite', 99000: 'Tuff', 90000: 'Coal', 93000: 'Basement'}
FAM = [{'Sandstone', 'Sandstone/Shale', 'Shale'}, {'Limestone', 'Chalk', 'Marl'}]
TEST = ['31/3-1', '30/6-5', '35/11-13', '35/11-11', '25/6-2']
STEP = 0.152


def family(c):
    for f in FAM:
        if c in f:
            return f
    return {c}


def fname(well):
    return well.replace('/', '_')


def load_labels():
    use = ['WELL', 'DEPTH_MD', 'FORCE_2020_LITHOFACIES_LITHOLOGY', 'FORCE_2020_LITHOFACIES_CONFIDENCE']
    df = pd.read_csv(TRAIN, sep=';', usecols=use)
    df = df[df['WELL'].isin(TEST)].copy()
    df['expert'] = df['FORCE_2020_LITHOFACIES_LITHOLOGY'].map(KEYS)
    return df


def within(depths, mask, window=3.0):
    """For every depth: is there a True in mask within +-window metres?"""
    dc = depths[mask]
    if dc.size == 0:
        return np.zeros(depths.size, dtype=bool)
    lo = np.searchsorted(dc, depths - window - 1e-9, side='left')
    hi = np.searchsorted(dc, depths + window + 1e-9, side='right')
    return hi > lo


def item_flags(depths, expert, reader):
    """Per item: read, strict, tolerant, soft."""
    n = depths.size
    read = np.array([isinstance(x, str) and x != '' for x in reader])
    strict = read & (reader == expert)
    tol = np.zeros(n, dtype=bool)
    soft = np.zeros(n, dtype=bool)
    for c in pd.unique(expert):
        sel = expert == c
        has_c = within(depths, reader == c)
        tol[sel] = has_c[sel]
        fam_mask = np.isin(reader, list(family(c)))
        has_f = within(depths, fam_mask)
        soft[sel] = has_f[sel]
    return read, strict, tol, soft


def summarise(flags_by_well, expert_by_well):
    read = np.concatenate([f[0] for f in flags_by_well])
    strict = np.concatenate([f[1] for f in flags_by_well])
    tol = np.concatenate([f[2] for f in flags_by_well])
    soft = np.concatenate([f[3] for f in flags_by_well])
    expert = np.concatenate(expert_by_well)
    n = read.size
    out = {'n': n, 'coverage': 100 * read.mean(), 'strict': 100 * strict.mean(),
           'tolerant': 100 * tol.mean(), 'soft': 100 * soft.mean()}
    per = []
    for c in pd.unique(expert):
        sel = expert == c
        if sel.sum() * STEP >= 20:
            per.append(tol[sel].mean())
    out['balanced'] = 100 * float(np.mean(per))
    out['n_classes'] = len(per)
    return out


def rebuild_from_reading(path, depths):
    """Section 5 of reading_rules.md, written afresh."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for k, r in df.iterrows():
        cls = r.get('rock_class', '').strip()
        try:
            a = float(r['depth_from']); b = float(r['depth_to'])
        except Exception:
            continue
        if cls == '' or not np.isfinite(a) or not np.isfinite(b):
            continue
        conf = r.get('confidence', 'high').strip().lower() if 'confidence' in df.columns else 'high'
        rank = {'low': 0, 'medium': 1, 'high': 2}.get(conf, 1)
        if a == b:
            m = np.abs(depths - a) <= 0.25 + 1e-9
            length = 0.0
        else:
            m = (depths >= a - 1e-9) & (depths < b - 1e-9)
            length = b - a
        rows.append((m, cls, rank, length, k))
    out = np.array([None] * depths.size, dtype=object)
    best_key = [None] * depths.size
    # tier: medium/high rows beat low rows; inside a tier the shortest row wins,
    # ties go to the higher confidence, then to the later row
    for m, cls, rank, length, k in rows:
        tier = 0 if rank == 0 else 1
        key = (tier, -length, rank, k)
        idx = np.nonzero(m)[0]
        for i in idx:
            if best_key[i] is None or key > best_key[i]:
                best_key[i] = key
                out[i] = cls
    return out


def main():
    lab = load_labels()
    print('label rows of the five test wells:', len(lab))
    readers_main = ['text', 'log picture', 'combined', 'curve picture', 'ten-well model',
                    'all-well model', 'all-shale line']
    extra = ['text (Sonnet)', 'log picture (Sonnet)', 'combined (Sonnet)', 'curve picture (Sonnet)',
             'text (Haiku)', 'log picture (Haiku)', 'combined (Haiku)', 'curve picture (Haiku)']
    store = {r: ([], []) for r in readers_main + extra}
    rebuilt = {r: ([], []) for r in ['text', 'log picture', 'combined', 'curve picture',
                                      'text (Sonnet)', 'log picture (Sonnet)', 'curve picture (Sonnet)',
                                      'text (Haiku)', 'log picture (Haiku)', 'curve picture (Haiku)']}
    mismatch = {}
    per_well = {}
    for w in TEST:
        l = lab[lab['WELL'] == w].sort_values('DEPTH_MD')
        l = l[l['expert'].notna()]
        steps = pd.read_csv(f'{REPO}/scores/steps_{fname(w)}.csv', dtype=str, keep_default_na=False)
        d_steps = steps['depth_md'].astype(float).values
        d = l['DEPTH_MD'].values
        assert len(d) == len(d_steps), (w, len(d), len(d_steps))
        assert np.allclose(d, d_steps, atol=2e-3), w
        expert = l['expert'].values.astype(object)
        for r in readers_main + extra:
            col = steps[r].values.astype(object)
            col = np.array([x if x != '' else None for x in col], dtype=object)
            fl = item_flags(d, expert, col)
            store[r][0].append(fl); store[r][1].append(expert)
            per_well[(r, w)] = summarise([fl], [expert])
        files = {'text': 'text', 'log picture': 'log_picture', 'combined': 'combined',
                 'curve picture': 'curve_picture'}
        for r in rebuilt:
            base = r.split(' (')[0]
            suffix = ''
            if '(Sonnet)' in r:
                suffix = '__sonnet'
            if '(Haiku)' in r:
                suffix = '__haiku'
            path = f'{REPO}/readings/{fname(w)}__{files[base]}{suffix}.csv'
            mine = rebuild_from_reading(path, d)
            theirs = np.array([x if x != '' else None for x in steps[r].values.astype(object)], dtype=object)
            diff = np.array([a != b for a, b in zip(mine, theirs)])
            mismatch[(r, w)] = (int(diff.sum()), len(diff))
            fl = item_flags(d, expert, mine)
            rebuilt[r][0].append(fl); rebuilt[r][1].append(expert)

    theirs = pd.read_csv(f'{REPO}/scores/headline.csv').set_index('reader')
    print('\n=== pooled scores from the run\'s per-step tables, my scorer (run\'s own figure in brackets)')
    print(f"{'reader':26s} {'cover':>12s} {'strict':>12s} {'tolerant':>12s} {'soft':>12s} {'balanced':>12s}")
    worst = 0.0
    for r in readers_main + extra:
        s = summarise(*store[r])
        t = theirs.loc[r]
        pairs = [(s['coverage'], t['coverage_pct']), (s['strict'], t['strict_all_pct']),
                 (s['tolerant'], t['tolerant_all_pct']), (s['soft'], t['soft_all_pct']),
                 (s['balanced'], t['balanced_all_pct'])]
        worst = max(worst, max(abs(a - b) for a, b in pairs))
        print(f"{r:26s} " + ' '.join(f"{a:5.1f} ({b:4.1f})" for a, b in pairs))
    print('largest gap between my figure and the run\'s figure, in points:', round(worst, 2))

    print('\n=== per-step classes rebuilt by me from the frozen reading files, against the run\'s per-step tables')
    for r in rebuilt:
        tot = sum(mismatch[(r, w)][0] for w in TEST); n = sum(mismatch[(r, w)][1] for w in TEST)
        s = summarise(*rebuilt[r])
        print(f"{r:26s} steps that differ: {tot:6d} of {n} ({100*tot/n:.2f}%)   my tolerant {s['tolerant']:.1f}  strict {s['strict']:.1f}  balanced {s['balanced']:.1f}")

    print('\n=== per well, headline number (tolerant, unread counted wrong), my scorer')
    cols = ['combined', 'curve picture', 'ten-well model', 'all-well model', 'all-shale line', 'text', 'log picture']
    print(f"{'well':10s} {'metres':>7s} " + ' '.join(f"{c[:14]:>14s}" for c in cols))
    for w in TEST:
        m = per_well[('combined', w)]['n'] * STEP
        print(f"{w:10s} {m:7.0f} " + ' '.join(f"{per_well[(c, w)]['tolerant']:14.1f}" for c in cols))
    print('\n=== per well, strict and balanced for curve picture against the two models')
    for w in TEST:
        print(w, {c: (round(per_well[(c, w)]['strict'], 1), round(per_well[(c, w)]['balanced'], 1))
                  for c in ['curve picture', 'ten-well model', 'all-well model']})

    # expert class mix of the test wells
    allexp = np.concatenate(store['combined'][1])
    vc = pd.Series(allexp).value_counts()
    print('\n=== expert classes in the five test wells (metres)')
    print((vc * STEP).round(0).to_string())


if __name__ == '__main__':
    main()
