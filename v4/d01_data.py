"""Step 1, data. Fit the tokenizer once on the 80 training wells and save it with
its SHA-256. Build boundary-token sequences for the 98 pool wells. Print the 20
most common tokens in training, development and pilot wells side by side.

  python -B d01_data.py            fit (only if no tokenizer is saved), then report
  python -B d01_data.py --verify   refit in memory and compare with the saved one
  python -B d01_data.py --check    (pod) rebuild the sequences and compare their checksum with
                                   out/d01_data.json; exits 1 on a mismatch, writes nothing

Writes cache/tokenizer_v4.joblib, cache/tokenizer_v4.sha256, out/d01_data.json, out/d01_top20.md.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4_common as vc  # noqa: E402


def fit_and_save(split, df):
    import joblib
    import sklearn
    if vc.TOKENIZER_PATH.exists():
        print(f"tokenizer already saved at {vc.TOKENIZER_PATH.name}; not refitting (fit once)")
        return
    t0 = time.time()
    tk, n_rows = vc.fit_tokenizer(split["train"], df)
    secs = time.time() - t0
    joblib.dump(dict(scaler=tk.scaler, kmeans=tk.kmeans, canonical_sha256=tk.canonical_sha256(),
                     n_train_rows=n_rows, seed=vc.SEED, k=vc.K, features="GR, log10 RDEP, NPHI, RHOB",
                     sklearn=sklearn.__version__, numpy=np.__version__, fit_seconds=secs,
                     train_wells=list(split["train"])), vc.TOKENIZER_PATH)
    sha = vc.sha256_file(vc.TOKENIZER_PATH)
    vc.TOKENIZER_SHA_PATH.write_text(f"{sha}  {vc.TOKENIZER_PATH.name}\n")
    print(f"tokenizer fitted on {n_rows:,} training rows in {secs:.1f}s; SHA-256 {sha}")


def sequences_sha256(data, split):
    arrs = []
    for w in split["pool98"]:
        arrs += [data.seq[w]["tok"], data.seq[w]["seg"]]
    return vc.sha256_arrays(*arrs)


def top_tokens(seqs, n=20):
    t = np.concatenate([s["tok"] for s in seqs])
    t = t[t != vc.BOUNDARY]
    c = np.bincount(t, minlength=vc.K)
    order = np.argsort(-c, kind="stable")[:n]
    return [(int(k), float(c[k] / t.size)) for k in order], int(t.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    vc.check_protocol()
    split = vc.load_split()
    df = vc.load_df()
    if args.check:
        tk = vc.load_tokenizer()
        data = vc.Data(split, df, tk)
        got = sequences_sha256(data, split)
        want = __import__("json").loads((vc.OUT / "d01_data.json").read_text())["sequences_sha256"]
        print(f"sequences SHA-256 {got} ({'same as' if got == want else 'DIFFERENT from'} the Mac build)")
        sys.exit(0 if got == want else 1)
    fit_and_save(split, df)
    tk = vc.load_tokenizer()
    sha = vc.TOKENIZER_SHA_PATH.read_text().split()[0]
    res = dict(tokenizer_file_sha256=sha, tokenizer_canonical_sha256=tk.canonical_sha256())

    if args.verify:
        tk2, _ = vc.fit_tokenizer(split["train"], df)
        res["refit_identical_centers"] = bool(np.array_equal(tk2.centers, tk.centers))
        res["refit_max_center_diff"] = float(np.max(np.abs(tk2.centers - tk.centers)))
        print(f"refit identical: {res['refit_identical_centers']} (max diff {res['refit_max_center_diff']:.3g})")

    data = vc.Data(split, df, tk)
    stats = {}
    for part in ("train", "dev", "pilot"):
        seqs = [data.seq[w] for w in split[part]]
        nb = int(sum((s["tok"] == vc.BOUNDARY).sum() for s in seqs))
        stats[part] = dict(n_wells=len(seqs), n_valid_rows=int(sum(data.rows[w]["n_valid"] for w in split[part])),
                           n_file_rows=int(sum(data.rows[w]["n_file_rows"] for w in split[part])),
                           n_boundary_tokens=nb, n_segments=nb + len(seqs))
    res["stats"] = stats
    res["sequences_sha256"] = sequences_sha256(data, split)
    # round trip check: centroid -> decode -> encode returns the same token
    rt = tk.encode(tk.decode_std(tk.centers))
    res["centroid_round_trip_same_token"] = int((rt == np.arange(vc.K)).sum())

    tops = {}
    for part in ("train", "dev", "pilot"):
        tops[part], ntok = top_tokens([data.seq[w] for w in split[part]])
        stats[part]["n_real_tokens"] = ntok
    res["top20"] = tops
    lines = ["| Rank | Training token | Share | Development token | Share | Pilot token | Share |",
             "|---|---|---|---|---|---|---|"]
    for i in range(20):
        row = [str(i + 1)]
        for part in ("train", "dev", "pilot"):
            k, p = tops[part][i]
            row += [str(k), f"{100 * p:.2f}%"]
        lines.append("| " + " | ".join(row) + " |")
    table = "\n".join(lines)
    (vc.OUT / "d01_top20.md").write_text(table + "\n")
    print("\n20 most common tokens (share of real tokens in each set):")
    print(table)
    tr = set(k for k, _ in tops["train"])
    res["top20_overlap_with_training"] = {p: len(tr & set(k for k, _ in tops[p])) for p in ("dev", "pilot")}
    print(f"\noverlap with the training top 20: dev {res['top20_overlap_with_training']['dev']}, "
          f"pilot {res['top20_overlap_with_training']['pilot']}")
    for part, s in stats.items():
        print(f"{part}: {s['n_wells']} wells, {s['n_valid_rows']:,} valid of {s['n_file_rows']:,} rows, "
              f"{s['n_segments']} segments, {s['n_boundary_tokens']} boundary tokens")
    print(f"centroid round trip keeps the token for {res['centroid_round_trip_same_token']} of {vc.K}")
    vc.save_json(res, vc.OUT / "d01_data.json")


if __name__ == "__main__":
    main()
