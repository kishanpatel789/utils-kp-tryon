import subprocess
from typing import cast

import polars as pl


def show(df: pl.DataFrame):
    max_str_len = max(
        (
            cast(int, df[col].drop_nulls().str.len_chars().max() or 0)
            for col in df.columns
            if df[col].dtype == pl.Utf8
        ),
        default=32,
    )
    with pl.Config(
        tbl_rows=-1, tbl_cols=-1, tbl_width_chars=-1, fmt_str_lengths=max_str_len
    ):
        subprocess.run(["less", "-S"], input=str(df), text=True)
