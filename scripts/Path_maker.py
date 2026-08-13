import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ---------- parameters ----------
DSV_MM       = 40                  # diameter of spherical volume (DSV)
RADIUS_MM    = DSV_MM / 2          # 30 mm DSV -> 15 mm sphere radius
LATTICE_STEP = 1                   # robot can only move in 1 mm increments,
                                    # so every candidate point sits on this
                                    # integer mm lattice
MAX_POINTS   = 550                 # target budget on total points
OUTFILE      = "path.csv"
# ---------------------------------


# ============================================================
# 1. Build a REGULAR grid inside the sphere at a given step.
#    Unlike FPS sampling, this keeps points aligned in clean
#    rows/columns, which is what lets us raster-scan them into
#    a smooth boustrophedon path instead of a scattered cloud.
#    step_mm can be fractional (used for fine budget tuning);
#    every resulting axis position is snapped to the nearest
#    integer mm and deduped, since the robot only moves in
#    1 mm increments.
# ============================================================
def generate_grid(step_mm):
    n_steps = int(round(RADIUS_MM / step_mm))
    axis_raw = [i * step_mm for i in range(-n_steps, n_steps + 1)]
    axis = sorted(set(int(round(a)) for a in axis_raw))
    r2 = RADIUS_MM ** 2
    pts = [(x, y, z) for z in axis for y in axis for x in axis
           if x * x + y * y + z * z <= r2]
    return np.array(pts, dtype=float)


# ============================================================
# 2. Pick the finest step whose grid still fits within
#    MAX_POINTS. Integer-only steps leave big gaps in point
#    count (e.g. step=4mm might be well over budget while
#    step=5mm undershoots by a lot), so the search sweeps
#    fractional steps at 0.01 mm resolution -- each still
#    snaps onto the 1 mm lattice, but this gets the final
#    point count much closer to the requested budget.
# ============================================================
def choose_step_for_budget(max_points, resolution=0.01):
    step = 1.0
    best = None
    while step <= RADIUS_MM:
        pts = generate_grid(step)
        if len(pts) <= max_points:
            best = (step, pts)
            break
        step += resolution
    if best is not None:
        return best
    # step > radius means even a single center point plus the
    # radius itself can't be subdivided further; return whatever
    # the coarsest valid grid gives, since that's the sparsest
    # this sphere can go on an integer-mm lattice.
    pts = generate_grid(RADIUS_MM)
    print(f"WARNING: cannot fit within MAX_POINTS={max_points} even at the "
          f"coarsest step ({RADIUS_MM} mm); returning {len(pts)} points instead.")
    return RADIUS_MM, pts


step_mm, sample = choose_step_for_budget(MAX_POINTS)
print(f"Grid step chosen                : {step_mm:.2f} mm")
print(f"Points inside sphere at this step: {len(sample)} (budget {MAX_POINTS})")


# ============================================================
# 3. Boustrophedon ("snake") ordering, plane by plane:
#      - layers (z) visited bottom -> top
#      - within a layer, rows (y) visited in a snake order too
#      - within a row, x is swept alternately L->R / R->L
#    The direction each layer/row starts in is chosen so the
#    path never has to jump back across the volume -- each
#    stroke picks up almost exactly where the last one ended.
# ============================================================
def boustrophedon_path(pts):
    zs = sorted(set(pts[:, 2]))
    path_rows = []
    row_dir = True  # True = sweep x ascending, False = descending

    for zi, z in enumerate(zs):
        layer = pts[pts[:, 2] == z]
        ys = sorted(set(layer[:, 1]))
        if zi % 2 == 1:          # alternate row order between layers
            ys = ys[::-1]

        for y in ys:
            row = layer[layer[:, 1] == y]
            row = row[np.argsort(row[:, 0])]
            if not row_dir:
                row = row[::-1]
            path_rows.append(row)
            row_dir = not row_dir  # flip sweep direction for next row

    return np.vstack(path_rows)


def path_length(pts):
    return float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1)))


t0 = time.time()
path = boustrophedon_path(sample)
zs = sorted(np.unique(sample[:, 2]))
print(f"Planes (z-layers) traversed     : {len(zs)}")
print(f"Points per plane (min/avg/max)  : "
      f"{min(np.sum(sample[:, 2] == z) for z in zs)} / "
      f"{len(sample)/len(zs):.1f} / "
      f"{max(np.sum(sample[:, 2] == z) for z in zs)}")
print(f"Total path length (boustrophedon): {path_length(path):.1f} mm")
print(f"Build time                       : {time.time()-t0:.3f} s")

# ============================================================
# 4. Write path to CSV
# ============================================================
with open(OUTFILE, "w", newline="") as f:
    writer = csv.writer(f, delimiter=' ')
    writer.writerow(["x", "y", "z"])
    writer.writerows(path.astype(int).tolist())

print(f"{len(path)} points written to {OUTFILE}")

# ============================================================
# 5. Animate the raster-scan path
# ============================================================
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect([1, 1, 1])
ax.set_xlim(-RADIUS_MM, RADIUS_MM)
ax.set_ylim(-RADIUS_MM, RADIUS_MM)
ax.set_zlim(-RADIUS_MM, RADIUS_MM)
ax.set_xlabel('X (mm)')
ax.set_ylabel('Y (mm)')
ax.set_zlabel('Z (mm)')
ax.set_title(f'Boustrophedon scan path — {DSV_MM} mm DSV, {len(path)} points')

line, = ax.plot([], [], [], '-', lw=1, c='tab:orange', alpha=0.6)
scatter = ax.scatter([], [], [], s=20, c='tab:blue')
start_marker = ax.scatter(*path[0], s=60, c='tab:green', label='start')
end_marker = ax.scatter([], [], [], s=60, c='tab:red', label='end')
ax.legend(loc='upper right')


def update(frame):
    current = path[:frame + 1]
    scatter._offsets3d = (current[:, 0], current[:, 1], current[:, 2])
    line.set_data(current[:, 0], current[:, 1])
    line.set_3d_properties(current[:, 2])
    if frame == len(path) - 1:
        end_marker._offsets3d = ([path[-1, 0]], [path[-1, 1]], [path[-1, 2]])
    return scatter, line, end_marker


ani = FuncAnimation(fig,
                     update,
                     frames=len(path),
                     interval=15,
                     blit=False,
                     repeat=False)

plt.show()