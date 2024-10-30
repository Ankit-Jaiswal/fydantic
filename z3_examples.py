from z3 import *

# Create a solver instance
solver = Solver()

# Define the variable
x = Real('x')

# Define the equation
equation = x**2 + 2*x + 1 == 0

# Define the given value for x
given_value = -1

# Add the equation and the condition that x equals the given value to the solver
solver.add(equation, x == given_value)

# Check if the equation is satisfiable with the given value
if solver.check() == sat:
    print(f"The value x = {given_value} satisfies the equation.")
else:
    print(f"The value x = {given_value} does not satisfy the equation.")