from sympy import (
    Expr, S, exp, Derivative, Function
)
from sympy.physics.units import Quantity
from sympy.physics.units.systems.si import SI
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core.power import Pow
from sympy.physics.units.dimensions import Dimension
from sympy.vector import VectorAdd
from ..core.coordinate_systems.coordinate_systems import CoordinateSystem
from ..core.vectors.vectors import Vector, vector_from_sympy_vector
from ..core.symbols.symbols import Symbol

#TODO: return symplyphysics Quantity
def expr_to_quantity(expr: Expr, quantity_name: str=None, randomize: bool=True) -> Quantity:
    quantity_scale = collect_factor_and_dimension(expr)
    dimension = quantity_scale[1]
    #HACK: this allows to treat angle type as dimensionless
    dimension = dimension.subs("angle", S.One)
    if isinstance(dimension, exp):
        dimension_args = dimension.nargs.args[0]
        # power of the exponent should be dimensionless
        assert dimension_args == S.One
        dimension = S.One
    name = "Q" if quantity_name is None else quantity_name
    result = Quantity(Symbol.random_name(name, 8) if randomize else name)
    dimsys_SI = SI.get_dimension_system()
    dimsys_SI.set_quantity_dimension(result, dimension)
    dimsys_SI.set_quantity_scale_factor(result, quantity_scale[0])
    return result

def expr_to_vector_of_quantities(expr: Expr, quantity_name: str=None, coordinate_system: CoordinateSystem=None, randomize: bool=True) -> Vector:    
    if isinstance(expr, Mul):
        expr = expr.expand()
    if isinstance(expr, Add):
        expr = VectorAdd(expr)
    vector = vector_from_sympy_vector(expr, coordinate_system)
    components = []
    base_name = "Q" if quantity_name is None else quantity_name
    name = Symbol.random_name(base_name, 8) if randomize else base_name
    for idx, c in enumerate(vector.components):
        d = expr_to_quantity(c, f"{name}[{idx + 1}]", False)
        components.append(d)
    return Vector(components, coordinate_system)

# HACK: copy of SI._collect_factor_and_dimension with fixed exp() dimension evaluation
def collect_factor_and_dimension(expr: Expr):
    """
    Return tuple with scale factor expression and dimension expression.
    """
    from sympy.physics.units import Quantity
    if isinstance(expr, Quantity):
        return expr.scale_factor, expr.dimension
    elif isinstance(expr, Mul):
        factor = 1
        dimension = Dimension(1)
        for arg in expr.args:
            arg_factor, arg_dim = collect_factor_and_dimension(arg)
            factor *= arg_factor
            dimension *= arg_dim
        return factor, dimension
    elif isinstance(expr, Pow):
        factor, dim = collect_factor_and_dimension(expr.base)
        exp_factor, exp_dim = collect_factor_and_dimension(expr.exp)
        if SI.get_dimension_system().is_dimensionless(exp_dim):
            exp_dim = 1
        return factor ** exp_factor, dim ** (exp_factor * exp_dim)
    elif isinstance(expr, Add):
        factor, dim = collect_factor_and_dimension(expr.args[0])
        for addend in expr.args[1:]:
            addend_factor, addend_dim = collect_factor_and_dimension(addend)
            # automatically convert zero to the dimension of it's additives
            if dim != addend_dim and not SI.get_dimension_system().equivalent_dims(dim, addend_dim):
                if factor == S.Zero:
                    dim = addend_dim
                elif addend_factor == S.Zero:
                    addend_dim = dim
            if dim != addend_dim and not SI.get_dimension_system().equivalent_dims(dim, addend_dim):
                raise ValueError(
                    'Dimension of "{}" is {}, '
                    'but it should be {}'.format(addend, addend_dim, dim))
            factor += addend_factor
        return factor, dim
    elif isinstance(expr, Derivative):
        factor, dim = collect_factor_and_dimension(expr.args[0])
        for independent, count in expr.variable_count:
            ifactor, idim = collect_factor_and_dimension(independent)
            factor /= ifactor**count
            dim /= idim**count
        return factor, dim
    elif isinstance(expr, Function):
        fds = [collect_factor_and_dimension(arg) for arg in expr.args]
        dims = [Dimension(1) if SI.get_dimension_system().is_dimensionless(d[1]) else d[1] for d in fds]
        return (expr.func(*(f[0] for f in fds)), *dims)
    elif isinstance(expr, Dimension):
        return S.One, expr
    else:
        return expr, Dimension(1)
