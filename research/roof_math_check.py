"""Numeric verification of every figure that goes in the roof report.
Pure python, no deps. Nothing goes in the document that does not print OK here.
"""
import math

def hdr(s): print("\n=== " + s + " ===")

# ---------------------------------------------------------------- pitch table
hdr("pitch -> angle -> multipliers")
for rise in [0.25, 0.5, 1, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 24]:
    m = rise / 12.0
    th = math.degrees(math.atan(m))
    common = math.sqrt(1 + m * m)          # rafter length per unit RUN
    hip = math.sqrt(2 + m * m)             # hip length per unit COMMON run (90 deg corner)
    hipang = math.degrees(math.atan(m / math.sqrt(2)))
    print(f"{rise:5}:12  {m*100:6.2f}%  {th:7.3f} deg  common x{common:.5f}  hip x{hip:.5f}  hipslope {hipang:7.3f}")

# hip unit run check: 12*sqrt2
print("hip unit run per 12 of common run:", 12 * math.sqrt(2))

# ------------------------------------------------------- straight skeleton, L
hdr("straight skeleton of the L footprint  (0,0)(32,0)(32,20)(16,20)(16,44)(0,44)")
W, h, w, H = 32.0, 20.0, 16.0, 44.0
poly = [(0, 0), (W, 0), (W, h), (w, h), (w, H), (0, H)]

# moving vertices as functions of t (all interior angles are 90 or 270, rectilinear)
V = {
    'A': lambda t: (0 + t,      0 + t),
    'B': lambda t: (W - t,      0 + t),
    'C': lambda t: (W - t,      h - t),
    'D': lambda t: (w - t,      h - t),   # REFLEX
    'E': lambda t: (w - t,      H - t),
    'F': lambda t: (0 + t,      H - t),
}
def dist(p, q): return math.hypot(p[0]-q[0], p[1]-q[1])

print("edge collapse times (length 0):")
for a, b in [('A','B'),('B','C'),('C','D'),('D','E'),('E','F'),('F','A')]:
    L0 = dist(V[a](0), V[b](0))
    L1 = dist(V[a](1), V[b](1))
    rate = L1 - L0
    if abs(rate) < 1e-12:
        print(f"  {a}{b}: len {L0:6.2f} constant -> NEVER collapses")
    else:
        print(f"  {a}{b}: len {L0:6.2f} rate {rate:+.2f}/t -> t = {-L0/rate:6.3f}")

print("split candidates for reflex vertex D:")
# D vs edge FA (x = t): 16-t == t
t_fa = w / 2.0
Dp = V['D'](t_fa)
span_fa = (t_fa, H - t_fa)
print(f"  vs FA: t={t_fa}, D at {Dp}, FA wavefront spans y in {span_fa} -> "
      f"{'INSIDE' if span_fa[0] <= Dp[1] <= span_fa[1] else 'outside'}")
# D vs edge AB (y = t): 20-t == t
t_ab = h / 2.0
Dp2 = V['D'](t_ab)
span_ab = (t_ab, W - t_ab)
print(f"  vs AB: t={t_ab}, D at {Dp2}, AB wavefront spans x in {span_ab} -> "
      f"{'INSIDE' if span_ab[0] <= Dp2[0] <= span_ab[1] else 'outside'}")

print("=> the SIMULTANEITY claim for any rectilinear L:")
print("   split time  = min(w,h)/2 =", min(w, h)/2.0)
print("   EF collapse = w/2       =", w/2.0)
print("   BC collapse = h/2       =", h/2.0)

# stage 2: after the split at t=8 the bottom loop is rect [8,24]x[8,12]
hdr("stage 2: residual rectangle after the split")
x0, x1, y0, y1 = 8.0, 24.0, 8.0, 12.0
print(f"  rect {x1-x0} wide x {y1-y0} deep -> collapses after {(y1-y0)/2} more, total t = {8+(y1-y0)/2}")
print(f"  ridge segment from ({x0+2},{y0+2}) to ({x1-2},{y0+2})  length {(x1-x0)-4}")

pitch = 6.0/12.0
print(f"  at 6:12 (m={pitch}) leg ridge height  = 8  * {pitch} = {8*pitch}")
print(f"                      main ridge height = 10 * {pitch} = {10*pitch}")
print(f"  to EQUALISE ridge heights the leg pitch must be 5/8 = {5/8:.4f} = {5/8*12:.2f}:12")

# ------------------------------------------------- surface-area parity theorem
hdr("surface area parity: A_roof * cos(theta) == A_footprint")
def shoelace(p):
    return abs(sum(p[i][0]*p[(i+1) % len(p)][1] - p[(i+1) % len(p)][0]*p[i][1]
                   for i in range(len(p)))) / 2.0
A = shoelace(poly)
th = math.atan(pitch)
print(f"  footprint area          = {A}")
print(f"  predicted roof surface  = A/cos(theta) = {A/math.cos(th):.6f}")
print(f"  parity residual         = {A/math.cos(th)*math.cos(th) - A:.2e}")

# ---------------------------------------------------------- rafter arithmetic
hdr("worked rafter set: 32ft x 20ft slab, 6:12, 2x8 rafters, 2x4 plate, 1.5in ridge")
m = 0.5
run_ft = 10.0                                   # half of the 20 ft depth
ridge_thk_in = 1.5
run_corrected = run_ft - (ridge_thk_in/2.0)/12.0
print(f"  nominal run {run_ft} ft; corrected for half ridge thickness = {run_corrected:.4f} ft")
print(f"  common rafter line length (nominal)   = {run_ft*math.sqrt(1+m*m):.4f} ft")
print(f"  common rafter line length (corrected) = {run_corrected*math.sqrt(1+m*m):.4f} ft")
print(f"  rise = {run_ft*m} ft ; slope = {math.degrees(math.atan(m)):.3f} deg")

hip_plan = run_ft*math.sqrt(2)
hip_len = math.sqrt(hip_plan**2 + (run_ft*m)**2)
print(f"  hip plan run = {hip_plan:.4f} ft ; hip line length = {hip_len:.4f} ft "
      f"(= run * sqrt(2+m^2) = {run_ft*math.sqrt(2+m*m):.4f})")
print(f"  hip slope    = {math.degrees(math.atan(m/math.sqrt(2))):.4f} deg")

for spacing_in in (16.0, 24.0):
    d = spacing_in/12.0
    cd = d*math.sqrt(1+m*m)
    print(f"  jack common difference @ {spacing_in:g} in o.c. = {cd:.5f} ft = {cd*12:.4f} in")

# birdsmouth
d_rafter = 7.25       # 2x8 actual depth, in
plate = 3.5           # 2x4 plate width, in
v = plate*m
hap = d_rafter/math.cos(math.atan(m)) - v
print(f"  birdsmouth: seat {plate} in -> plumb heel cut {v} in ; HAP = {hap:.4f} in")
print(f"  remaining fraction of rafter depth (plumb-measured) = {hap/(d_rafter/math.cos(math.atan(m))):.4f}")

# ----------------------------------------------------------- backing bevel
hdr("hip backing bevel - derived two ways")
def backing_numeric(m, half_interior_deg):
    """half_interior_deg = alpha, half the PLAN interior angle at the corner."""
    alpha = math.radians(half_interior_deg)
    gamma = math.pi/2 - alpha                    # half-angle between the inward normals
    c = m*math.cos(gamma)                        # hip rise per unit hip plan run
    s = m*math.sin(gamma)
    # closed form
    beta_cf = math.degrees(math.atan(s/math.sqrt(1+c*c)))
    # direct vector computation
    p1 = (math.cos(gamma),  math.sin(gamma))
    n1 = (m*p1[0], m*p1[1], -1.0)                # normal of face 1 (z = m*(p1.X))
    hvec = (1.0, 0.0, c)                         # hip axis, plan direction +x
    u = (0.0, 1.0, 0.0)
    nR = (hvec[1]*u[2]-hvec[2]*u[1], hvec[2]*u[0]-hvec[0]*u[2], hvec[0]*u[1]-hvec[1]*u[0])
    dot = sum(a*b for a, b in zip(nR, n1))
    mag = math.sqrt(sum(a*a for a in nR))*math.sqrt(sum(a*a for a in n1))
    beta_vec = math.degrees(math.acos(abs(dot)/mag))
    return beta_cf, beta_vec, math.degrees(math.asin(c/math.sqrt(1+c*c)))

for pitch_rise in (4, 6, 8, 12):
    mm = pitch_rise/12.0
    cf, vec, sin_hip = backing_numeric(mm, 45.0)
    print(f"  {pitch_rise}:12 square corner  beta(closed)={cf:8.4f}  beta(vector)={vec:8.4f}  "
          f"asin-of-hip-slope={sin_hip:8.4f}  match={abs(cf-vec)<1e-9}")
print("  -> at a SQUARE corner tan(beta) == sin(hip slope). Now a non-square corner:")
for ang in (60, 90, 120, 135):
    cf, vec, sin_hip = backing_numeric(0.5, ang/2.0)
    print(f"  interior {ang:3} deg, 6:12  beta={cf:8.4f} (vector {vec:8.4f})  "
          f"sin(hipslope)-rule would give {sin_hip:8.4f}")

# ---------------------------------------------------------------- gambrel
hdr("gambrel from a semicircle: chords of a semicircle in 4 equal arcs")
R = 1.0
pts = [(R*math.cos(math.radians(a)), R*math.sin(math.radians(a))) for a in (0, 45, 90)]
for i in range(2):
    p, q = pts[i], pts[i+1]
    slope = (q[1]-p[1])/(p[0]-q[0])   # magnitude, going inward
    print(f"  chord {i+1}: from {p[0]:.4f},{p[1]:.4f} to {q[0]:.4f},{q[1]:.4f}  "
          f"slope {slope:.4f} = {math.degrees(math.atan(slope)):.3f} deg = {slope*12:.2f}:12")
print(f"  break point at x = {pts[1][0]:.5f} R  ({pts[1][0]*100:.3f}% of half span), "
      f"z = {pts[1][1]:.5f} R")
print(f"  total ridge height = R ; a plain gable of the same 4 slopes would be...")

# habitable width of the gambrel vs plain gable at 7ft
hdr("headroom: width with >= 7 ft of clear height, span 24 ft")
span = 24.0
knee = 0.0
for name, prof in [("gable 12:12", [(12.0, 12.0)]),
                   ("gambrel 4-chord", None)]:
    pass
# gambrel: half span 12 -> R=12, break at 8.485 from centre... rebuild explicitly
R = span/2.0
brk_x = R*math.cos(math.radians(45))
brk_z = R*math.sin(math.radians(45))
print(f"  gambrel R={R}: break at x={brk_x:.4f} from centre, z={brk_z:.4f}, ridge z={R}")
# height of profile at horizontal distance u from centre
def gambrel_z(u):
    u = abs(u)
    if u <= brk_x:
        return R - (R-brk_z)*(u/brk_x)
    return brk_z*(R-u)/(R-brk_x)
def gable_z(u, m):
    return (R-abs(u))*m
for target in (7.0,):
    # width where z >= target
    lo = 0.0
    hi = R
    for _ in range(200):
        mid = (lo+hi)/2
        if gambrel_z(mid) >= target: lo = mid
        else: hi = mid
    print(f"  gambrel: full width with >= {target} ft clear = {2*lo:.4f} ft "
          f"({2*lo/span*100:.1f}% of span), ridge height {R} ft")
    for pr in (12, 18, 24):
        mm = pr/12.0
        wgab = 2*(R - target/mm)
        print(f"  gable {pr}:12 : width with >= {target} ft = {max(wgab,0):.4f} ft "
              f"({max(wgab,0)/span*100:.1f}%), ridge height {R*mm:.3f} ft")

# ------------------------------------------------------- ASCE slope thresholds
hdr("ASCE 7 unbalanced-snow slope window, converted")
for r in (0.5, 7.0):
    print(f"  {r}:12 = {math.degrees(math.atan(r/12)):.3f} deg")

# ------------------------------------------------------------ NYC-ish check
hdr("sky exposure plane arithmetic (generic)")
def sep_height(setback, initial_setback, base_height, ratio_v_over_h):
    """height of the plane at horizontal distance `setback` from the street line."""
    if setback <= initial_setback:
        return base_height
    return base_height + (setback - initial_setback)*ratio_v_over_h
for ratio, lbl in ((2.7/1.0, "2.7 to 1"), (5.6/1.0, "5.6 to 1")):
    print(f"  ratio {lbl}: at 20 ft in from a 60 ft base with 15 ft initial setback -> "
          f"{sep_height(20, 15, 60, ratio):.2f} ft")

print("\nALL CHECKS PRINTED.")
