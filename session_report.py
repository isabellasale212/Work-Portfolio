"""
GPS Session Physical Report
===========================
Parses a 10 Hz Catapult GPS export from a single training session and produces
a one-page physical summary: total distance, work rate, speed-zone distribution,
Player Load, heart-rate response and a per-phase demand breakdown.

Usage:
    python session_report.py [path/to/session.csv]

Outputs (written to ./outputs):
    - summary printed to stdout
    - speed_zones.png       distance covered in each speed zone
    - phase_distance.png    distance by session phase, coloured by peak speed
    - session_summary.csv   machine-readable metrics

Author: Isabella Sale
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # headless / CI-safe
import matplotlib.pyplot as plt

# --- speed zones (km/h). Standard team-sport thresholds; edit to your club's model ---
ZONES = [
    ("Z1  <6",     0.0,   6.0),
    ("Z2  6-12",   6.0,  12.0),
    ("Z3  12-15", 12.0,  15.0),
    ("Z4  15-20", 15.0,  20.0),
    ("Z5  >20",   20.0,  np.inf),
]
HSR_THRESHOLD_KMH = 19.8   # high-speed running
SAMPLE_HZ = 10             # Catapult 10 Hz feed

# palette (matches the portfolio's intensity ramp)
COOL, WARM, HOT = "#4A79A8", "#D2913A", "#C24A3D"
INK, MUTE, GRID = "#141C24", "#7B8791", "#E2E6EB"


def load(path: Path) -> pd.DataFrame:
    """Read a Catapult export. The file has a one-line title above the header."""
    df = pd.read_csv(path, skiprows=1)
    df.columns = [c.strip() for c in df.columns]
    # be tolerant about column naming across exports
    rename = {
        "Velocity (km/h)": "vel_kmh",
        "Velocity (m/s)": "vel_ms",
        "Acceleration (m/s2)": "accel",
        "Odometer (m)": "odometer",
        "Player Load (au)": "player_load",
        "Heart Rate (bpm)": "hr",
        "Session Phase": "phase",
        "Seconds": "seconds",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "vel_ms" not in df and "vel_kmh" in df:
        df["vel_ms"] = df["vel_kmh"] / 3.6
    return df


def summarise(df: pd.DataFrame) -> dict:
    dt = 1.0 / SAMPLE_HZ
    duration_min = (df["seconds"].iloc[-1] - df["seconds"].iloc[0]) / 60
    total_distance = float(df["odometer"].iloc[-1])

    # distance per speed zone: integrate velocity over time within each band
    step = df["vel_ms"] * dt
    zone_dist = {}
    for name, lo, hi in ZONES:
        mask = (df["vel_kmh"] >= lo) & (df["vel_kmh"] < hi)
        zone_dist[name] = float(step[mask].sum())

    hsr = float(step[df["vel_kmh"] >= HSR_THRESHOLD_KMH].sum())

    return {
        "duration_min": round(duration_min, 1),
        "total_distance_m": round(total_distance),
        "work_rate_m_per_min": round(total_distance / duration_min),
        "peak_speed_kmh": round(float(df["vel_kmh"].max()), 1),
        "player_load_au": round(float(df["player_load"].iloc[-1])),
        "avg_hr_bpm": round(float(df["hr"].mean())),
        "max_hr_bpm": round(float(df["hr"].max())),
        "hsr_distance_m": round(hsr),
        "zone_distance_m": {k: round(v) for k, v in zone_dist.items()},
    }


def per_phase(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("phase", sort=False)
    out = pd.DataFrame({
        "distance_m": g["odometer"].last() - g["odometer"].first(),
        "peak_speed_kmh": g["vel_kmh"].max().round(1),
        "duration_min": (g["seconds"].last() - g["seconds"].first()) / 60,
    })
    return out.round(1)


def zone_color(kmh: float) -> str:
    if kmh < 12:
        return COOL
    if kmh < 16:
        return WARM
    return HOT


def plot_zones(summary: dict, out: Path) -> None:
    names = list(summary["zone_distance_m"].keys())
    vals = list(summary["zone_distance_m"].values())
    colors = [COOL, COOL, WARM, HOT, HOT]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(names[::-1], vals[::-1], color=colors[::-1], height=0.68)
    for i, v in enumerate(vals[::-1]):
        ax.text(v + max(vals) * 0.01, i, f"{v:,} m", va="center", fontsize=9, color=MUTE)
    ax.set_title("Distance by speed zone", loc="left", fontsize=12, color=INK, weight="bold")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_phases(phase_df: pd.DataFrame, out: Path) -> None:
    phase_df = phase_df.iloc[::-1]
    colors = [zone_color(v) for v in phase_df["peak_speed_kmh"]]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.barh(phase_df.index, phase_df["distance_m"], color=colors, height=0.66)
    for i, (v, pk) in enumerate(zip(phase_df["distance_m"], phase_df["peak_speed_kmh"])):
        ax.text(v + phase_df["distance_m"].max() * 0.01, i,
                f"{int(v):,} m  ·  {pk:.0f} km/h", va="center", fontsize=8.5, color=MUTE)
    ax.set_title("Distance by session phase (colour = peak speed)",
                 loc="left", fontsize=12, color=INK, weight="bold")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def _style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTE, labelsize=9)
    ax.margins(x=0.14)


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1
                else "data/catapult_rugby_training_session.csv")
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    df = load(path)
    summary = summarise(df)
    phases = per_phase(df)

    print(f"\nGPS Session Physical Report  —  {path.name}")
    print("=" * 52)
    print(f"  Duration            {summary['duration_min']} min")
    print(f"  Total distance      {summary['total_distance_m']:,} m")
    print(f"  Work rate           {summary['work_rate_m_per_min']} m/min")
    print(f"  Peak speed          {summary['peak_speed_kmh']} km/h")
    print(f"  Player Load         {summary['player_load_au']} au")
    print(f"  Heart rate          {summary['avg_hr_bpm']} avg / {summary['max_hr_bpm']} max bpm")
    print(f"  High-speed running  {summary['hsr_distance_m']} m  (>{HSR_THRESHOLD_KMH} km/h)")
    print("\n  Distance by speed zone:")
    for k, v in summary["zone_distance_m"].items():
        print(f"    {k:<10} {v:>6,} m")
    print("\n  Per-phase demand:")
    print(phases.to_string())

    # save machine-readable + charts
    flat = {k: v for k, v in summary.items() if k != "zone_distance_m"}
    flat.update({f"zone_{k.split()[0]}_m": v for k, v in summary["zone_distance_m"].items()})
    pd.DataFrame([flat]).to_csv(out_dir / "session_summary.csv", index=False)
    phases.to_csv(out_dir / "phase_breakdown.csv")
    plot_zones(summary, out_dir / "speed_zones.png")
    plot_phases(phases, out_dir / "phase_distance.png")
    print(f"\nWrote charts + CSVs to {out_dir}/\n")


if __name__ == "__main__":
    main()
