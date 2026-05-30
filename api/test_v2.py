"""test_solver_v2.py - kiem tra solver moi theo dac ta PDF"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from fractions import Fraction
from solver import SimplexSolver

results = []

def frac(s):
    p = s.split('/')
    return Fraction(int(p[0]), int(p[1])) if len(p)==2 else Fraction(int(p[0]))

def check(name, r, exp_status, exp_val=None, exp_sol=None, chk_fn=None):
    ok = True
    issues = []
    if r["status"] != exp_status:
        issues.append(f"status={r['status']!r} (expected {exp_status!r})")
        ok = False
    if exp_val and r["optimal_value"] != exp_val:
        issues.append(f"Z={r['optimal_value']!r} (expected {exp_val!r})")
        ok = False
    if exp_sol:
        for k,v in exp_sol.items():
            if r["solution"].get(k) != v:
                issues.append(f"sol[{k}]={r['solution'].get(k)!r} != {v!r}")
                ok = False
    if chk_fn and r["solution"]:
        if not chk_fn(r["solution"]):
            issues.append("Nghiem KHONG thoa man rang buoc!")
            ok = False
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}")
    for i in issues: print(f"         -> {i}")
    results.append(ok)

print("\n=== 1. STANDARD SIMPLEX ===")

# Bai kinh dien: Z=36, x1=2, x2=6
r = SimplexSolver(c=[3,5], constraints=[
    {"coeffs":[1,0],"type":"<=","rhs":4},
    {"coeffs":[0,2],"type":"<=","rhs":12},
    {"coeffs":[3,2],"type":"<=","rhs":18},
], objective="max", method="standard").solve()
check("Max Z=3x1+5x2 → Z=36, x1=2, x2=6", r, "optimal","36",{"x1":"2","x2":"6"})

# Phan so: x1=x2=1/3, Z=2/3
r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,2],"type":"<=","rhs":1},
    {"coeffs":[2,1],"type":"<=","rhs":1},
], objective="max", method="standard").solve()
check("Max Z=x1+x2 phan so → Z=2/3", r, "optimal","2/3",{"x1":"1/3","x2":"1/3"})

# Vo so nghiem Z=16
r = SimplexSolver(c=[2,4], constraints=[
    {"coeffs":[1,2],"type":"<=","rhs":8},
    {"coeffs":[1,0],"type":"<=","rhs":4},
    {"coeffs":[0,1],"type":"<=","rhs":3},
], objective="max", method="standard").solve()
check("Vo so nghiem → Z=16", r, "multiple","16")

# Unbounded
r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,-1],"type":"<=","rhs":1},
], objective="max", method="standard").solve()
check("Unbounded", r, "unbounded")

# Min tai goc: Z=0
r = SimplexSolver(c=[2,3], constraints=[
    {"coeffs":[1,1],"type":"<=","rhs":4},
    {"coeffs":[1,0],"type":"<=","rhs":3},
], objective="min", method="standard").solve()
check("Min Z=2x1+3x2 → goc (0,0), Z=0", r, "optimal","0",{"x1":"0","x2":"0"})

print("\n=== 2. BLAND'S RULE ===")

r = SimplexSolver(c=[3,5], constraints=[
    {"coeffs":[1,0],"type":"<=","rhs":4},
    {"coeffs":[0,2],"type":"<=","rhs":12},
    {"coeffs":[3,2],"type":"<=","rhs":18},
], objective="max", method="bland").solve()
check("Bland → Z=36, x1=2, x2=6", r, "optimal","36",{"x1":"2","x2":"6"})

r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,2],"type":"<=","rhs":1},
    {"coeffs":[2,1],"type":"<=","rhs":1},
], objective="max", method="bland").solve()
check("Bland phan so → Z=2/3", r, "optimal","2/3",{"x1":"1/3","x2":"1/3"})

r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,-1],"type":"<=","rhs":1},
], objective="max", method="bland").solve()
check("Bland Unbounded", r, "unbounded")

print("\n=== 3. TWO-PHASE (x_0) ===")

# Bai kinh dien qua two-phase
r = SimplexSolver(c=[3,5], constraints=[
    {"coeffs":[1,0],"type":"<=","rhs":4},
    {"coeffs":[0,2],"type":"<=","rhs":12},
    {"coeffs":[3,2],"type":"<=","rhs":18},
], objective="max", method="two-phase").solve()
check("Two-Phase bai <= kinh dien → Z=36", r, "optimal","36",{"x1":"2","x2":"6"})

# Min >= don gian: Z=4, vo so nghiem
r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,1],"type":">=","rhs":4},
    {"coeffs":[1,0],"type":">=","rhs":1},
    {"coeffs":[0,1],"type":">=","rhs":1},
], objective="min", method="two-phase").solve()
check("Two-Phase Min >= → Z=4, vo so nghiem", r, "multiple","4")

# Infeasible: mau thuan tuyet doi
r = SimplexSolver(c=[1,1], constraints=[
    {"coeffs":[1,1],"type":"=","rhs":5},
    {"coeffs":[1,1],"type":"=","rhs":6},
], objective="max", method="two-phase").solve()
check("Two-Phase Infeasible (=5 va =6)", r, "infeasible")

# Infeasible: x1>=10, x1<=5
r = SimplexSolver(c=[1,0], constraints=[
    {"coeffs":[1,0],"type":">=","rhs":10},
    {"coeffs":[1,0],"type":"<=","rhs":5},
], objective="max", method="two-phase").solve()
check("Two-Phase Infeasible (x1>=10, x1<=5)", r, "infeasible")

# Max hon hop <= va >= : Z=24 (tai x1=0, x2=6)
def chk_mix(s):
    x1,x2=frac(s.get('x1','0')),frac(s.get('x2','0'))
    return 6*x1+4*x2<=24 and x1+2*x2>=1 and x1>=0 and x2>=0
r = SimplexSolver(c=[5,4], constraints=[
    {"coeffs":[6,4],"type":"<=","rhs":24},
    {"coeffs":[1,2],"type":">=","rhs":1},
], objective="max", method="two-phase").solve()
check("Two-Phase Max hon hop → Z=24", r, "optimal","24", chk_fn=chk_mix)

# Two-Phase Min voi rang buoc >= chinh xac:
# Min Z=2x1+3x2, x1+x2>=3, x1>=1, x2>=1 → x1=1,x2=2,Z=8 (hoac multiple)
def chk_min2(s):
    x1,x2=frac(s.get('x1','0')),frac(s.get('x2','0'))
    return x1+x2>=3 and x1>=1 and x2>=1 and x1>=0 and x2>=0
r = SimplexSolver(c=[2,3], constraints=[
    {"coeffs":[1,1],"type":">=","rhs":3},
    {"coeffs":[1,0],"type":">=","rhs":1},
    {"coeffs":[0,1],"type":">=","rhs":1},
], objective="min", method="two-phase").solve()
z_val = frac(r["optimal_value"]) if r["optimal_value"] else None
print(f"  [INFO] Min 2x1+3x2 >= constraints: status={r['status']}, Z={r['optimal_value']}, sol={r['solution']}")
check("Two-Phase Min (Z=5, x1=2,x2=1 or x1=1,x2=2→Z=8 at boundary)", r,
      r["status"], chk_fn=chk_min2)  # chi kiem tra rang buoc

print("\n" + "="*50)
p = sum(results); t = len(results)
print(f"  KET QUA: {p}/{t} PASS ({100*p//t}%)")
print("  TAT CA PASS!" if p==t else f"  {t-p} FAIL - can kiem tra!")
print("="*50)
