"""Which samples? A sampling simulator for the post "Which samples are you looking at?" (davenoel.me).

Same simulated city as sample-size/simulate.py, but now tests come from households,
and households don't all test the same amount. Usage: python3 sampling.py [--seed 7]
"""
import argparse
import numpy as np

FAST_MEDIAN, FAST_SIGMA = 250.0, 0.45
SLOW_MEDIAN, SLOW_SIGMA = 25.0, 0.70
SLOW_SHARE = 0.15
HOUSEHOLDS = 1000
POWER_SHARE = 0.05          # 5% of households are power users
POWER_TESTS = 40            # tests per power-user household per month
REGULAR_TESTS = (0, 3)      # everyone else runs 0 to 3
POWER_SPEEDUP = 2.0         # power users tend to pay for a faster plan
TEST_NOISE = 0.25           # test-to-test wobble within one home (lognormal sigma)


def city(rng):
    slow = rng.random(HOUSEHOLDS) < SLOW_SHARE
    plan = np.where(slow, rng.lognormal(np.log(SLOW_MEDIAN), SLOW_SIGMA, HOUSEHOLDS),
                    rng.lognormal(np.log(FAST_MEDIAN), FAST_SIGMA, HOUSEHOLDS))
    power = (~slow) & (rng.random(HOUSEHOLDS) < POWER_SHARE / (1 - SLOW_SHARE))
    plan = np.where(power, plan * POWER_SPEEDUP, plan)
    n = np.where(power, POWER_TESTS, rng.integers(REGULAR_TESTS[0], REGULAR_TESTS[1] + 1, HOUSEHOLDS))
    return plan, power, n


def tests(rng, plan, n):
    hh = np.repeat(np.arange(len(plan)), n)
    return hh, plan[hh] * rng.lognormal(0, TEST_NOISE, len(hh))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=42); a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    plan, power, n = city(rng)
    hh, sp = tests(rng, plan, n)
    tested = n > 0
    per_hh = np.array([np.median(sp[hh == h]) for h in np.flatnonzero(tested)])
    print(f"{HOUSEHOLDS} households, {tested.sum()} ran at least one test, {len(sp)} tests in all")
    print(f"power users: {power.sum()} households ({power.mean():.0%}) ran {n[power].sum()} tests ({n[power].sum()/len(sp):.0%} of all tests)")
    print(f"true household median (every home, tested or not): {np.median(plan):.0f} Mbps")
    print(f"median of all tests:                {np.median(sp):.0f} Mbps")
    print(f"median of households (one vote each): {np.median(per_hh):.0f} Mbps")
    print(f"share under 25 Mbps: households {np.mean(plan < 25):.1%}, tests {np.mean(sp < 25):.1%}, one vote each {np.mean(per_hh < 25):.1%}")
    # inverse probability weighting: each test weighted 1 / (tests from its home)
    w = 1 / n[hh]; o = np.argsort(sp); c = np.cumsum(w[o])
    print(f"weighted median of tests (w = 1/m):  {sp[o][np.searchsorted(c, c[-1] / 2)]:.0f} Mbps")
    # design effect: deff = 1 + (m_bar - 1) * rho, with rho the intraclass correlation (log scale)
    between = np.var(np.log(plan[tested])); rho = between / (between + TEST_NOISE**2)
    m_bar = n[tested].mean(); deff = 1 + (m_bar - 1) * rho
    print(f"tests per home {m_bar:.1f}, rho {rho:.2f}, design effect {deff:.1f}, "
          f"effective sample size {len(sp) / deff:.0f} (homes that tested: {tested.sum()})")
    print(f"10th pct: households {np.percentile(plan,10):.0f}, tests {np.percentile(sp,10):.0f}, one vote each {np.percentile(per_hh,10):.0f}")
    # repeat: wobble of each estimator across 2000 cities
    m_t, m_h = [], []
    for _ in range(2000):
        plan, power, n = city(rng); hh, sp = tests(rng, plan, n)
        truth = np.median(plan)
        pv = np.bincount(hh, weights=np.log(sp), minlength=HOUSEHOLDS) / np.maximum(np.bincount(hh, minlength=HOUSEHOLDS), 1)
        m_t.append(np.median(sp) / truth - 1); m_h.append(np.median(np.exp(pv[n > 0])) / truth - 1)
    for k, v in [("all tests", m_t), ("one vote each", m_h)]:
        v = np.array(v); print(f"over 2,000 cities, {k}: median off by {np.median(v):+.0%}, middle 90% {np.percentile(v,5):+.0%} to {np.percentile(v,95):+.0%}")


if __name__ == "__main__":
    main()
