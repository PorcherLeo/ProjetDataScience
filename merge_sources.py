#!/usr/bin/env python3
"""
Fusionne deux historiques de snapshots Velib (CSV sans en-tête, 8 colonnes).

Règles :
  - les lignes identiques ne sont gardées qu'une fois ;
  - même (date, station_code) avec des valeurs différentes dans les deux sources :
    on garde la version de la source principale ;
  - même (date, station_code) avec des valeurs différentes dans une même source :
    le code station est ambigu, on écarte toutes ces lignes ;
  - le résultat est trié par (date, station_code), au même format que les entrées.

Usage : python merge_sources.py principal.csv secondaire.csv -o fusion.csv
"""

import argparse

import pandas as pd

COLUMNS = ["date", "station_code", "capacity", "available_mechanical",
           "available_electrical", "station_name", "station_geo", "operative"]
KEY = ["date", "station_code"]
VALUES = ["capacity", "available_mechanical", "available_electrical", "operative"]
DTYPES = {
    "station_code": "str",
    "capacity": "int16",
    "available_mechanical": "int16",
    "available_electrical": "int16",
    "station_name": "category",
    "station_geo": "category",
    "operative": "bool",
}


def read_history(path: str, source: int) -> pd.DataFrame:
    """Lit un historique et marque sa provenance (0 = principale)."""
    return pd.read_csv(path, header=None, names=COLUMNS, dtype=DTYPES).assign(source=source)


def merge_histories(primary: pd.DataFrame, secondary: pd.DataFrame) -> pd.DataFrame:
    """Union des deux historiques selon les règles décrites en tête de fichier."""
    merged = (
        pd.concat([primary, secondary], ignore_index=True)
        .drop_duplicates(KEY + VALUES)
    )
    sources_per_key = merged.groupby(KEY)["source"].transform("nunique")
    ambiguous = merged.duplicated(KEY, keep=False) & (sources_per_key == 1)
    return (
        merged[~ambiguous]
        .sort_values(KEY + ["source"], kind="stable")
        .drop_duplicates(KEY, keep="first")
        .drop(columns="source")
        .sort_values(KEY, kind="stable")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("primary", help="historique prioritaire (celui de la release)")
    parser.add_argument("secondary", help="historique complémentaire")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    primary = read_history(args.primary, source=0)
    secondary = read_history(args.secondary, source=1)
    merged = merge_histories(primary, secondary)
    merged.to_csv(args.output, header=False, index=False, lineterminator="\n")
    print(f"{len(primary)} + {len(secondary)} lignes -> {len(merged)} lignes fusionnées")


if __name__ == "__main__":
    main()
