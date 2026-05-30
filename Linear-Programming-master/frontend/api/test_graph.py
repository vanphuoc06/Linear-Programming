import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphical_solver import GraphicalSolver

def test():
    # Bài toán: 
    # Max Z = 3x1 + 2x2
    # Ràng buộc:
    # 2x1 + x2 <= 18
    # 2x1 + 3x2 <= 42
    # 3x1 + x2 <= 24
    # x1 >= 0, x2 >= 0
    c = [3, 2]
    constraints = [
        {"coeffs": [2, 1], "type": "<=", "rhs": 18},
        {"coeffs": [2, 3], "type": "<=", "rhs": 42},
        {"coeffs": [3, 1], "type": "<=", "rhs": 24}
    ]
    bounds = [[0, None], [0, None]]
    
    solver = GraphicalSolver(c=c, constraints=constraints, bounds=bounds, method="graphical", objective="max")
    res = solver.solve()
    print("STATUS:", res["status"])
    print("OPTIMAL_VALUE:", res["optimal_value"])
    print("SOLUTION:", res["solution"])
    print("VERTICES:", res["steps"][0]["vertices"])

if __name__ == "__main__":
    test()
