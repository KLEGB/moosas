import math
from typing import Any, Dict, List, Optional, Tuple


def estimate_curtainwall_cost(
    H: float,
    W: float,
    p: float,
    *,
    # --- Geometry defaults (typical for many unitized façade projects) ---
    mH: float = 4.2,
    mW: float = 1.5,
    min_unit_h: float = 1.0,
    min_unit_w: float = 0.6,
    # --- Pricing ---
    prices: Optional[Dict[str, Any]] = None,
    # --- Waste factors (fractions, e.g. 0.06 means +6%) ---
    waste: Optional[Dict[str, float]] = None,
    # --- Profile length counting method ---
    # "grid_shared": mullion/transom grid lines counted once
    # "unit_perimeter": each unit has its own perimeter (inner edges duplicated)
    profile_method: str = "grid_shared",
    # --- Openable distribution strategy ---
    # "auto": choose column-first if cols>=rows else row-first
    # "column": force column-first
    # "row": force row-first
    openable_distribution: str = "auto",
) -> Dict[str, Any]:
    """
    Estimate curtain wall grid splitting + openable distribution + cost breakdown.

    Parameters
    ----------
    H, W : float
        Overall façade height/width in meters.
    p : float
        Target openable area ratio in [0, 1]. Target openable area is S = H*W*p.
    mH, mW : float
        Max standard unit height/width (meters). Used as upper bounds of unit size.
    min_unit_h, min_unit_w : float
        Min manufacturable unit height/width (meters). Used to cap maximum rows/cols.
        If the required openable sash count exceeds possible units under min size,
        the model falls back to allowing multiple sashes per unit.
    prices : dict
        Optional unit-price dictionary. Suggested keys:
        - "profile_per_m" (RMB/m) or "profile_per_unit" (RMB/unit)
        - "glass_fixed_per_m2" (RMB/m²)  # fixed glazing only
        - "window_pricing": "per_m2" or "per_set"
        - "window_per_m2" (RMB/m²) or "window_per_set" (RMB/set)
        - "install_per_m2" (RMB/m²)      # labor+machine, excludes main materials
    waste : dict
        Optional waste factors. Suggested keys:
        - "profile", "glass", "window", "install" (fractions)
    profile_method : str
        "grid_shared" or "unit_perimeter"
    openable_distribution : str
        "auto", "column", "row"

    Returns
    -------
    dict with:
      - rows, cols, unit size
      - n_openable_sashes, sash size (nominal)
      - openable allocation matrix
      - quantities (profile length, areas)
      - cost breakdown (profile, glass, window, install, total)
    """

    # ------------------------
    # Validation
    # ------------------------
    if H <= 0 or W <= 0:
        raise ValueError("H and W must be positive.")
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be in [0, 1].")

    prices = prices or {}
    waste = waste or {}

    A = H * W  # total area (m2)
    S = A * p  # target openable area (m2)

    # ------------------------
    # Helpers
    # ------------------------
    def _ceil(x: float) -> int:
        # small epsilon to avoid ceil(2.0000000001) problems
        return int(math.ceil(x - 1e-12))

    def choose_even_indices(k: int, total: int) -> List[int]:
        """
        Choose k indices from [0..total-1] roughly evenly,
        avoiding edges when possible (more 'balanced' façade).
        """
        if k <= 0 or total <= 0:
            return []
        if k >= total:
            return list(range(total))
        if k == 1:
            return [total // 2]

        idx = []
        for i in range(k):
            # divide into (k+1) segments to avoid hard edges
            pos = round((i + 1) * (total - 1) / (k + 1))
            idx.append(int(pos))

        # ensure uniqueness by local shifting if needed
        used = set()
        for j in range(len(idx)):
            if idx[j] in used:
                for delta in range(1, total):
                    r = idx[j] + delta
                    l = idx[j] - delta
                    if 0 <= r < total and r not in used:
                        idx[j] = r
                        break
                    if 0 <= l < total and l not in used:
                        idx[j] = l
                        break
            used.add(idx[j])
        return idx

    def choose_grid(n_sashes: int) -> Tuple[int, int, bool]:
        """
        Solve:
          minimize rows*cols
          s.t. H/rows <= mH, W/cols <= mW, rows*cols >= n_sashes
               H/rows >= min_unit_h, W/cols >= min_unit_w
        Tie-break: prefer vertical splitting (larger rows / smaller cols).
        """
        eps = 1e-9
        r0 = max(1, _ceil(H / mH))
        c0 = max(1, _ceil(W / mW))

        r_max = max(r0, int(math.floor(H / min_unit_h + eps))) if min_unit_h else r0
        c_max = max(c0, int(math.floor(W / min_unit_w + eps))) if min_unit_w else c0

        best_key = None
        best_rc = None

        for rows in range(r0, r_max + 1):
            cols = max(c0, _ceil(n_sashes / rows)) if n_sashes > 0 else c0
            if cols > c_max:
                continue

            unit_h = H / rows
            unit_w = W / cols

            # upper bounds
            if unit_h > mH + 1e-9 or unit_w > mW + 1e-9:
                continue
            # lower bounds
            if min_unit_h and unit_h < min_unit_h - 1e-9:
                continue
            if min_unit_w and unit_w < min_unit_w - 1e-9:
                continue

            T = rows * cols
            # objective1: T minimal; objective2: cols minimal (vertical-first)
            key = (T, cols, -rows)
            if best_key is None or key < best_key:
                best_key = key
                best_rc = (rows, cols)

        if best_rc is not None:
            return best_rc[0], best_rc[1], False

        # fallback: constrained by min unit size too hard -> max rows/cols allowed
        return r_max, c_max, True

    def allocate_openables(rows: int, cols: int, n_sashes: int) -> Tuple[List[List[int]], Dict[str, Any]]:
        """
        Build an allocation matrix [rows][cols], each cell = number of openable sashes in that unit.
        Rules:
        - Prefer full columns or rows.
        - Distribute across façade evenly (avoid all on one edge).
        - If n_sashes > rows*cols, allow multiple sashes per unit (fallback).
        """
        T = rows * cols
        mat = [[0 for _ in range(cols)] for _ in range(rows)]
        if n_sashes <= 0:
            return mat, {"mode": "none"}

        # choose orientation
        if openable_distribution == "column":
            orientation = "column"
        elif openable_distribution == "row":
            orientation = "row"
        else:
            orientation = "column" if cols >= rows else "row"

        if n_sashes > T:
            # Everyone gets at least base
            base = n_sashes // T
            rem = n_sashes % T
            for r in range(rows):
                for c in range(cols):
                    mat[r][c] = base

            # Then distribute remaining 1-by-1 evenly (simple column-major index)
            positions = [(r, c) for c in range(cols) for r in range(rows)]
            extra_idx = choose_even_indices(rem, len(positions))
            for i in extra_idx:
                r, c = positions[i]
                mat[r][c] += 1

            return mat, {"mode": "multi", "orientation": orientation, "base_per_unit": base, "extra_units": rem}

        # n_sashes <= T: one-per-unit allocation
        if orientation == "column":
            k = min(_ceil(n_sashes / rows), cols)  # how many columns involved
            col_ids = choose_even_indices(k, cols)
            base = n_sashes // k
            extra = n_sashes % k
            counts = [base + (1 if i < extra else 0) for i in range(k)]

            # Place in each chosen column bottom-up (more 'practical' for access)
            for i, c in enumerate(col_ids):
                cnt = counts[i]
                for j in range(cnt):
                    r = rows - 1 - j
                    mat[r][c] = 1

            return mat, {"mode": "single", "orientation": "column", "columns": col_ids, "counts_per_column": counts}

        # orientation == "row"
        k = min(_ceil(n_sashes / cols), rows)
        row_ids = choose_even_indices(k, rows)
        base = n_sashes // k
        extra = n_sashes % k
        counts = [base + (1 if i < extra else 0) for i in range(k)]

        for i, r in enumerate(row_ids):
            cnt = counts[i]
            for j in range(cnt):
                c = j
                mat[r][c] = 1

        return mat, {"mode": "single", "orientation": "row", "rows": row_ids, "counts_per_row": counts}

    # ------------------------
    # Step 1: Initial n, then iterate until sash area fits inside unit area
    # ------------------------
    if S <= 1e-12:
        n = 0
    else:
        n = max(1, _ceil(S / (mH * mW)))

    # Iterate to enforce: (S/n) <= unit_area (because real unit could be smaller than mH*mW)
    iter_limit = 10000
    for _ in range(iter_limit):
        rows, cols, constrained = choose_grid(n if n > 0 else 0)
        unit_h = H / rows
        unit_w = W / cols
        unit_area = unit_h * unit_w

        if n == 0:
            break

        s_open = S / n
        if s_open <= unit_area + 1e-9:
            break
        n += 1
    else:
        raise RuntimeError("Failed to find a feasible n within iteration limit.")

    # Final geometry
    T = rows * cols
    unit_h = H / rows
    unit_w = W / cols
    unit_area = unit_h * unit_w
    s_open = S / n if n > 0 else 0.0

    # Nominal sash dimensions: keep same aspect ratio as unit to guarantee fit
    if n > 0:
        ratio = unit_w / unit_h
        sash_w = math.sqrt(max(0.0, s_open * ratio))
        sash_h = s_open / sash_w if sash_w > 0 else 0.0
    else:
        sash_w = sash_h = 0.0

    # ------------------------
    # Step 2: Openable allocation matrix
    # ------------------------
    alloc_mat, alloc_meta = allocate_openables(rows, cols, n)

    # ------------------------
    # Step 3: Quantities
    # ------------------------
    if profile_method == "grid_shared":
        # Mullion/transom grid counted once
        profile_length = (cols + 1) * H + (rows + 1) * W
    elif profile_method == "unit_perimeter":
        # Each unit has its own 4 edges (internal edges duplicated)
        profile_length = 2.0 * (unit_h + unit_w) * T
    else:
        raise ValueError("profile_method must be 'grid_shared' or 'unit_perimeter'.")

    fixed_glass_area = A - S
    openable_area = S

    # ------------------------
    # Step 4: Cost model
    # ------------------------
    # Read prices
    profile_per_m = prices.get("profile_per_m", None)
    profile_per_unit = prices.get("profile_per_unit", None)

    glass_fixed_per_m2 = float(prices.get("glass_fixed_per_m2", 0.0))

    window_pricing = prices.get("window_pricing", "per_m2")
    window_per_m2 = prices.get("window_per_m2", None)
    window_per_set = prices.get("window_per_set", None)

    install_per_m2 = float(prices.get("install_per_m2", 0.0))

    # Waste factors
    w_profile = float(waste.get("profile", 0.0))
    w_glass = float(waste.get("glass", 0.0))
    w_window = float(waste.get("window", 0.0))
    w_install = float(waste.get("install", 0.0))

    # Profile cost base
    if profile_per_m is not None:
        profile_cost_base = profile_length * float(profile_per_m)
        profile_basis = "per_m"
    elif profile_per_unit is not None:
        profile_cost_base = T * float(profile_per_unit)
        profile_basis = "per_unit"
    else:
        profile_cost_base = 0.0
        profile_basis = "none"

    # Glass cost base (fixed glazing only)
    glass_cost_base = fixed_glass_area * glass_fixed_per_m2

    # Window cost base (openable area)
    if n <= 0:
        window_cost_base = 0.0
    else:
        if window_pricing == "per_m2":
            if window_per_m2 is None:
                raise ValueError("window_per_m2 is required when window_pricing='per_m2'.")
            window_cost_base = openable_area * float(window_per_m2)
        elif window_pricing == "per_set":
            if window_per_set is None:
                raise ValueError("window_per_set is required when window_pricing='per_set'.")
            window_cost_base = n * float(window_per_set)
        else:
            raise ValueError("window_pricing must be 'per_m2' or 'per_set'.")

    # Installation base (typically exclude material waste)
    install_cost_base = A * install_per_m2

    # Apply waste
    profile_cost = profile_cost_base * (1.0 + w_profile)
    glass_cost = glass_cost_base * (1.0 + w_glass)
    window_cost = window_cost_base * (1.0 + w_window)
    install_cost = install_cost_base * (1.0 + w_install)

    total_cost = profile_cost + glass_cost + window_cost + install_cost

    return {
        # "inputs": {
        #     "H_m": H,
        #     "W_m": W,
        #     "p_openable": p,
        #     "mH_m": mH,
        #     "mW_m": mW,
        #     "min_unit_h_m": min_unit_h,
        #     "min_unit_w_m": min_unit_w,
        # },
        # "rows": rows,
        # "cols": cols,
        # "unit_size_m": {"h": unit_h, "w": unit_w},
        # "units_total": T,
        # "area_total_m2": A,
        # "openable_area_target_m2": S,
        # "n_openable_sashes": n,
        # "openable_area_per_sash_m2": s_open,
        # "sash_nominal_size_m": {"h": sash_h, "w": sash_w, "area_m2": s_open},
        # "openable_allocation": {"matrix": alloc_mat, "meta": alloc_meta},
        # "quantities": {
        #     "profile_method": profile_method,
        #     "profile_length_m": profile_length,
        #     "fixed_glass_area_m2": fixed_glass_area,
        #     "openable_area_m2": openable_area,
        #     "grid_constrained_by_min_unit": constrained,
        # },
        # "costs": {
            "profile_basis": profile_basis,
            "profile_base": profile_cost_base,
            "profile": profile_cost,
            "glass_base": glass_cost_base,
            "glass_fixed": glass_cost,
            "window_pricing": window_pricing,
            "window_base": window_cost_base,
            "window": window_cost,
            "install_base": install_cost_base,
            "install": install_cost,
            "waste": {"profile": w_profile, "glass": w_glass, "window": w_window, "install": w_install},
            "total": total_cost,
        # },
    }


# ------------------------
# Example usage (two cases)
# ------------------------
if __name__ == "__main__":
    prices_demo = {
        "profile_per_m": 220.0,  # RMB/m (assumed)
        "glass_fixed_per_m2": 190.0,  # RMB/m² (example)
        "window_pricing": "per_m2",
        "window_per_m2": 718.0,  # RMB/m² (example)
        "install_per_m2": 166.41,  # RMB/m² (example)
    }
    waste_demo = {"profile": 0.06, "glass": 0.02, "window": 0.03}

    cases = [estimate_curtainwall_cost(15, 10, p/100.0, prices=prices_demo, waste=waste_demo) for p in range(1,100)]
    import matplotlib.pyplot as plt

    profile,glass,window,install = ([cases[i]['profile'] for i in range(len(cases))],
                                    [cases[i]['glass_fixed'] for i in range(len(cases))],
                                    [cases[i]['window'] for i in range(len(cases))],
                                    [cases[i]['install'] for i in range(len(cases))])

    x = [p/100.0 for p in range(1,100)]
    plt.stackplot(x,profile,glass,window,install,labels=["profile","glass_fixed","window","install"],alpha=0.5)
    plt.legend(loc="best")
    plt.show()