import numbers
from sympy import (Eq, Derivative)
from symplyphysics import (
    angle_type, units, expr_to_quantity, Quantity, Function, Symbol, print_expression,
    validate_input_symbols, validate_output_symbol
)

# Description
## The movement along circle might be easily represented in polar coordinates with the pole in the center of the circle.
## Object position is described by radius-vector from pole to object. 
## Magnitude of this vector is radius of circle. Angle between this vector and X axis it is also known as movement phase.

# Definition: ω(t) = φ(t)/dt
# Where:
## ω(t) is angular velocity function of time
## φ(t) is angle function of time

time = Symbol("time", units.time)
angular_velocity = Function("angular_velocity", 1 / units.time)
angle_function = Function("angle_function", angle_type)

definition = Eq(angular_velocity(time), Derivative(angle_function(time), time))

definition_units_SI = units.radian / units.second

def print() -> str:
    return print_expression(definition)

@validate_input_symbols(angle_start_=angle_function, angle_end_=angle_function, moving_time_=time)
@validate_output_symbol(angular_velocity)
def calculate_angular_velocity(angle_start_: Quantity | float, angle_end_: Quantity | float, moving_time_: Quantity) -> Quantity:
    #HACK: SymPy angles are always in radians
    angle_start_radians = angle_start_ if isinstance(angle_start_, numbers.Number) else angle_start_.scale_factor
    angle_end_radians = angle_end_ if isinstance(angle_end_, numbers.Number) else angle_end_.scale_factor
    angle_function_ = time * (angle_end_radians - angle_start_radians) / moving_time_
    applied_definition = definition.subs(angle_function(time), angle_function_)
    dsolved = applied_definition.doit()
    result_expr = dsolved.rhs
    return expr_to_quantity(result_expr)
