import subprocess

import polars as pl


def show(df: pl.DataFrame):
    with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=-1):
        subprocess.run(["less", "-S"], input=str(df), text=True)
