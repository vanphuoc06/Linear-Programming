import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from solver import SimplexSolver, _frac

# Debug bai kinh dien qua two-phase
print("=== DEBUG: Two-Phase bai <= kinh dien ===")
s=SimplexSolver(c=[3,5],constraints=[
    {"coeffs":[1,0],"type":"<=","rhs":4},
    {"coeffs":[0,2],"type":"<=","rhs":12},
    {"coeffs":[3,2],"type":"<=","rhs":18},
],objective="max",method="two-phase")

# Xem std rows
cons=s.constraints
std=[]
for con in cons:
    a=[_frac(x) for x in con["coeffs"]]
    b=_frac(con["rhs"])
    t=con["type"]
    if t=="<=":
        std.append((list(a),b))
    elif t==">=":
        std.append(([-x for x in a],-b))
    elif t=="=":
        std.append((list(a),b))
        std.append(([-x for x in a],-b))

print("std rows before ensure b>=0:")
for a,b in std: print(f"  a={[str(x) for x in a]}, b={b}")

# ensure b>=0
for i in range(len(std)):
    a,b=std[i]
    if b<0: std[i]=([-x for x in a],-b)

print("std rows after ensure b>=0:")
for a,b in std: print(f"  a={[str(x) for x in a]}, b={b}")

r=s.solve()
print(f"\nStatus: {r['status']}, Z={r['optimal_value']}")
print(f"Sol: {r['solution']}")
# Show phase1 steps
for step in r['steps']:
    if 'rows' in step:
        print(f"  [{step.get('note','')[:50]}] obj_rhs={step['rows'][-1][-1]}")
