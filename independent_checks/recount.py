"""Recount the four protocol comparisons. Usage: python3 recount.py INPUT_ROOT

INPUT_ROOT contains copies of the pod_results gens/ and out/ input files.
Requires NumPy. Reads JSON only and writes results to standard output.
"""
import json
import sys
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(path.read_bytes())


def score_grid(root):
    setting = read(root / "out/selected_setting.json")["setting"]
    grids = {}
    wells = None
    for model in ("A", "B2", "chain", "trigram", "block"):
        metrics = ("bias_abs", "structure") if model == "A" else (
            ("bias_abs",) if model in ("B2", "chain") else ("structure",))
        for seed in range(20260715, 20260727):
            if model in ("A", "B2"):
                folder = Path("gens") / f"{model}_seed{seed}_{setting}" / "best/csv"
            else:
                folder = Path("gens") / f"baseline_{model}" / f"seed{seed}" / "csv"
            meta = read(root / folder / "meta.json")
            scores = read(root / folder / "scores.json")
            if model in ("A", "B2"):
                assert meta["run"] == folder.parts[1] and meta["ckpt"] == "best"
                assert meta["skipped_lt_2000_valid"] == [] and meta["n_real"] == 5
            else:
                assert (meta["source"], meta["seed"], meta["side"]) == (model, seed, False)
            rows = scores["per_well"]
            if wells is None:
                wells = sorted(rows)
            assert sorted(rows) == sorted(meta["wells"]) == wells
            assert scores["dir"] == str(folder) and scores["n_wells"] == len(wells)
            for metric in metrics:
                values = np.array([rows[w]["per_realization"][metric] for w in wells])
                assert values.shape == (len(wells), 5) and np.isfinite(values).all()
                assert values.dtype.kind in "fiu"
                saved_means = np.array([rows[w][metric] for w in wells])
                assert saved_means.dtype.kind in "fiu" and np.isfinite(saved_means).all()
                means = values.mean(axis=1)
                np.testing.assert_allclose(means, saved_means, rtol=1e-12, atol=1e-15)
                if metric == "bias_abs":
                    signed = [rows[w]["per_realization"]["bias_signed"] for w in wells]
                    np.testing.assert_array_equal(values, np.abs(signed))
                grids.setdefault((model, metric), []).append(means)
    return wells, {key: np.stack(cols, axis=1) for key, cols in grids.items()}


def draw_indices(rng, n_wells, n_seeds, *, seeds_first=False):
    wi = np.empty((10000, n_wells), dtype=int)
    si = np.empty((10000, n_seeds), dtype=int)
    dims = (si, wi) if seeds_first else (wi, si)
    for draw in range(10000):
        for indices in dims:
            size = indices.shape[1]
            indices[draw] = rng.integers(size, size=size)
    return wi[:, :, None], si[:, None, :]


def recount(grids, n_wells, convention):
    engine = np.random.MT19937 if convention == "MT19937" else np.random.PCG64
    rng = np.random.Generator(engine(20260715))
    draws = None
    rows = []
    for left, right, metric in (("B2", "A", "bias_abs"), ("A", "chain", "bias_abs"),
                                ("A", "trigram", "structure"), ("A", "block", "structure")):
        diff = grids[left, metric] - grids[right, metric]
        assert diff.shape == (n_wells, 12)
        if draws is None or convention == "continue stream":
            draws = draw_indices(rng, *diff.shape, seeds_first=convention == "seeds first")
        means = diff[draws].mean(axis=(1, 2))
        method = "inverted_cdf" if convention == "nearest rank" else "linear"
        lower, upper = np.percentile(means, [2.5, 97.5], method=method)
        rows.append([float(diff.mean()), float(lower), float(upper)])
    return rows


if __name__ == "__main__":
    wells, grids = score_grid(Path(sys.argv[1]))
    conventions = ("primary", "seeds first", "continue stream", "MT19937", "nearest rank")
    scored_cells = sum(grid.size for grid in grids.values())
    print(json.dumps({"wells": wells, "seeds": list(range(20260715, 20260727)),
                      "finite_per_well_scores": scored_cells,
                      "finite_realization_scores": 5 * scored_cells,
                      "results": {c: recount(grids, len(wells), c) for c in conventions}}, indent=2))
