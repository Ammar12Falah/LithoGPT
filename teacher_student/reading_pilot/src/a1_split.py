"""A1 step 3: split train.csv into three files. Prints no rows.

 data/logs_all.parquet          logs of all 98 wells, WITHOUT the two label columns
 data/labels_pool.parquet       labels of all wells except the test wells
 data/labels_test_SEALED.parquet  labels of the test wells (not opened before the freeze)

Usage: python -I src/a1_split.py
"""
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LAB = "FORCE_2020_LITHOFACIES_LITHOLOGY"
CONF = "FORCE_2020_LITHOFACIES_CONFIDENCE"


def main() -> None:
    draw = pd.read_csv(ROOT / "draw.csv")
    test = set(draw[draw.role == "test"].well)
    assert len(test) == 5, "need exactly 5 test wells in draw.csv"
    with zipfile.ZipFile(ROOT / "raw" / "force" / "train.zip") as z:
        with z.open("train.csv") as f:
            df = pd.read_csv(f, sep=";")
    df = df.reset_index().rename(columns={"index": "row_id"})
    (ROOT / "data").mkdir(exist_ok=True)
    logs = df.drop(columns=[LAB, CONF])
    logs.to_parquet(ROOT / "data" / "logs_all.parquet", index=False)
    lab = df[["row_id", "WELL", "DEPTH_MD", LAB, CONF]]
    is_test = lab.WELL.isin(test)
    lab[~is_test].to_parquet(ROOT / "data" / "labels_pool.parquet", index=False)
    lab[is_test].to_parquet(ROOT / "data" / "labels_test_SEALED.parquet", index=False)
    print("rows in logs_all        :", len(logs), "wells:", logs.WELL.nunique())
    print("rows in labels_pool     :", int((~is_test).sum()), "wells:", lab[~is_test].WELL.nunique())
    print("rows in labels_test     :", int(is_test.sum()), "wells:", lab[is_test].WELL.nunique())
    print("columns of logs_all     :", list(logs.columns))


if __name__ == "__main__":
    main()
