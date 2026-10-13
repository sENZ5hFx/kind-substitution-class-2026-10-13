"""Kind-Substitution Class scorer. Research-stage. Not a measurement of nature.

A published rectangle contains a kind axis (here, a retention fraction).
With the axis kept, every corner lies on one side of a named residual.
With that axis dropped and every other conversion held fixed, the corners
straddle the residual. The straddle was manufactured. That is KSC.

It is not RSC (intact rectangle already all-short: that shortfall stands).
It is not IRC (intact corners already disagree: nothing was dropped).
It is not a new flux.
"""
from __future__ import annotations


def _corners(flux_lo, flux_hi, axis_lo, axis_hi, scale):
    vals = []
    for f in (flux_lo, flux_hi):
        for a in (axis_lo, axis_hi):
            vals.append(f * a * scale)
    return min(vals), max(vals)


def kind_substitution(
    *,
    flux_lo: float,
    flux_hi: float,
    axis_lo: float,
    axis_hi: float,
    scale: float,
    target: float,
    axis_published: bool,
    same_promotion: bool,
    spoken: float,
    prior_overlap: float,
    evidence: float,
):
    """Score one rectangle against one residual.

    score = 40 * evidence * (1 - spoken) * (1 - prior_overlap) if all gates pass.
    Otherwise 0. Research-stage heuristic, not a measurement of nature.
    """
    for name, val in {
        "spoken": spoken,
        "prior_overlap": prior_overlap,
        "evidence": evidence,
    }.items():
        if not 0 <= val <= 1:
            raise ValueError(f"{name} out of range: {val}")
    if flux_lo <= 0 or flux_hi < flux_lo:
        raise ValueError("flux rectangle must be positive and ordered")
    if not (0 < axis_lo <= axis_hi <= 1):
        raise ValueError("axis must lie in (0, 1] and be ordered")
    if scale <= 0 or target <= 0:
        raise ValueError("scale and target must be positive")

    intact_lo, intact_hi = _corners(flux_lo, flux_hi, axis_lo, axis_hi, scale)
    strip_lo, strip_hi = _corners(flux_lo, flux_hi, 1.0, 1.0, scale)
    intact_straddle = intact_lo < target < intact_hi
    strip_straddle = strip_lo < target < strip_hi
    gates = {
        "axis_published": bool(axis_published),
        "same_promotion": bool(same_promotion),
        "intact_one_side": not intact_straddle,
        "stripped_straddle": strip_straddle,
    }
    out = {
        "intact_gtc": [round(intact_lo, 6), round(intact_hi, 6)],
        "stripped_gtc": [round(strip_lo, 6), round(strip_hi, 6)],
        "target": target,
        "gates": gates,
    }
    if not all(gates.values()):
        failed = [k for k, v in gates.items() if not v]
        out.update({"score": 0.0, "verdict": "NOT_KSC", "failed_gates": failed})
        return out
    score = round(40 * evidence * (1 - spoken) * (1 - prior_overlap), 4)
    out.update({"score": score, "verdict": "KSC", "failed_gates": []})
    return out


def overshoot_screen(*, intact_hi, stripped_lo, target, same_rectangle):
    """Different kill rule. Do not mint.

    Intact entirely below the target, substituted figure entirely above,
    and the two figures are not one rectangle. Sign flip, not a straddle.
    """
    if intact_hi < target and stripped_lo > target and not same_rectangle:
        return {"verdict": "KIND_OVERSHOOT_QUEUED_NOT_MINTED", "score": 0.0}
    return {"verdict": "NOT_OVERSHOOT", "score": 0.0}


def _check():
    scale = 3.61e14 * 365.25 / 1e18
    assert abs(scale - 0.13185525) < 1e-9
    primary = kind_substitution(
        flux_lo=1.6, flux_hi=21.0, axis_lo=0.08, axis_hi=0.30,
        scale=scale, target=1.7, axis_published=True, same_promotion=True,
        spoken=0.80, prior_overlap=0.62, evidence=0.80,
    )
    assert primary["verdict"] == "KSC"
    assert primary["intact_gtc"][1] < 1.7
    assert primary["stripped_gtc"][0] < 1.7 < primary["stripped_gtc"][1]
    no_axis = kind_substitution(
        flux_lo=0.52, flux_hi=9.6, axis_lo=1.0, axis_hi=1.0,
        scale=scale, target=1.7, axis_published=False, same_promotion=True,
        spoken=0.8, prior_overlap=0.6, evidence=0.8,
    )
    assert no_axis["score"] == 0.0
    land = kind_substitution(
        flux_lo=0.8, flux_hi=3.0, axis_lo=1.0, axis_hi=1.0,
        scale=1.0, target=1.7, axis_published=False, same_promotion=True,
        spoken=0.9, prior_overlap=0.9, evidence=0.7,
    )
    assert land["score"] == 0.0
    painted = kind_substitution(
        flux_lo=1.6, flux_hi=21.0, axis_lo=0.08, axis_hi=0.30,
        scale=scale, target=1.7, axis_published=True, same_promotion=False,
        spoken=0.2, prior_overlap=0.2, evidence=1,
    )
    assert painted["score"] == 0.0 and "same_promotion" in painted["failed_gates"]
    over = overshoot_screen(intact_hi=0.13, stripped_lo=10.0, target=1.7, same_rectangle=False)
    assert over["verdict"] == "KIND_OVERSHOOT_QUEUED_NOT_MINTED"
    for area in (3.4e14, 3.61e14, 3.8e14):
        s = area * 365.25 / 1e18
        row = kind_substitution(
            flux_lo=1.6, flux_hi=21.0, axis_lo=0.08, axis_hi=0.30,
            scale=s, target=1.7, axis_published=True, same_promotion=True,
            spoken=0.80, prior_overlap=0.62, evidence=0.80,
        )
        assert row["verdict"] == "KSC", (area, row)
    print("ksc_score ok", primary["score"], primary["intact_gtc"], primary["stripped_gtc"])
    return primary


if __name__ == "__main__":
    _check()
