# pylint: disable=E1120,W0108,W0621,E1121,E1101
import matchpy

from .machinery import *

__all__ = [
    "Sequence",
    "Call",
    "Value",
    "scalar",
    "vector",
    "vector_of",
    "Unbound",
    "Scalar",
    "Content",
    "Function",
    "function",
    "ExtractLength",
    "PushVectorCallable",
    # "If",
    # "IsZero",
    "Unify",
    "UnboundWithDimension",
]


class Sequence(matchpy.Operation):
    """
    Sequence(length, getitem)
    """

    name = "Sequence"
    arity = matchpy.Arity(2, True)


class Content(matchpy.Operation):
    name = "Content"
    arity = matchpy.Arity(1, True)


register(Content(Sequence(w._, w.getitem)), lambda _, getitem: getitem)


class ExtractLength(matchpy.Operation):
    name = "ExtractLength"
    arity = matchpy.Arity(1, True)


register(ExtractLength(Sequence(w.length, w._)), lambda _, length: length)


class Scalar(matchpy.Operation):
    """
    Scalar(content)
    """

    name = "Scalar"
    arity = matchpy.Arity(1, True)

    def __str__(self):
        return str(self.operands[0])


register(Content(Scalar(w.content)), lambda content: content)


class Call(matchpy.Operation):
    """
    Call(callable, *args)
    """

    name = "Call"
    arity = matchpy.Arity(1, False)


class Function(matchpy.Operation):
    """
    Function(body, *args)
    """

    name = "Function"
    arity = matchpy.Arity(1, False)

    def __str__(self):
        body, *args = self.operands
        return f"({', '.join(a.variable_name for a in args)} -> {body})"


register(
    Call(Function(w.body, ws.args), ws.arg_vals),
    lambda body, args, arg_vals: matchpy.substitute(
        body, {arg.variable_name: arg_val for (arg, arg_val) in zip(args, arg_vals)}
    ),
)

_counter = 0


def gensym():
    global _counter
    variable_name = f"i{_counter}"
    _counter += 1
    return variable_name


def function(n, fn):
    """
    function(n, lambda arg_1, arg_2, ..., arg_n: body)
    """
    args = [Unbound(gensym()) for _ in range(n)]
    return Function(fn(*args), *args)


class Value(matchpy.Symbol):
    def __init__(self, value):
        self.value = value
        super().__init__(repr(value), None)

    def __str__(self):
        return str(self.value)


def scalar(value):
    return Scalar(Value(value))


class VectorCallable(matchpy.Operation):
    """
    VectorCallable(*items)
    """

    name = "VectorCallable"
    arity = matchpy.Arity(0, False)

    def __str__(self):
        return f"<{' '.join(map(str, self.operands))}>"


register(
    Call(VectorCallable(ws.items), w.index),
    lambda items, index: Scalar(VectorIndexed(index, *items)),
)


class PushVectorCallable(matchpy.Operation):
    """
    PushVectorCallable(new_item, VectorCallable())
    """

    name = "PushVectorCallable"
    arity = matchpy.Arity(2, True)

    def __str__(self):
        return f"<{self.operands[0]}, *{self.operands[1]}>"


register(
    PushVectorCallable(w.new_item, VectorCallable(ws.items)),
    lambda new_item, items: VectorCallable(new_item, *items),
)


class VectorIndexed(matchpy.Operation):
    """
    VectorIndexed(index, *items)
    """

    name = "VectorIndexed"
    arity = matchpy.Arity(1, False)


register(
    VectorIndexed(Value.w.index, ws.items), lambda index, items: items[index.value]
)


def vector_of(*values):
    return Sequence(Value(len(values)), VectorCallable(*values))


def vector(*values):
    return vector_of(*(Value(v) for v in values))


class Unbound(matchpy.Symbol):
    def __init__(self, variable_name=None):
        super().__init__(name="", variable_name=variable_name)

    def __str__(self):
        return self.variable_name or "_"


# class If(matchpy.Operation):
#     name = "If"
#     arity = matchpy.Arity(3, True)


# register(
#     If(Value.w.cond, w.true, w.false),
#     lambda cond, true, false: true if cond.value else false,
# )


# class IsZero(matchpy.Operation):
#     name = "IsZero"
#     arity = matchpy.Arity(1, True)


# register(IsZero(Value.w.x), lambda x: x.value == 0)


class Unify(matchpy.Operation):
    """
    Unify(x, y) asserts x and y are equivalen and returns them
    """

    name = "Unify"
    arity = matchpy.Arity(2, True)


register(Unify(w.x, w.y), matchpy.EqualVariablesConstraint("x", "y"), lambda x, y: x)


class UnboundWithDimension(matchpy.Symbol):
    def __init__(self, n, variable_name):
        self.n = n
        super().__init__(str(n), variable_name)

    def __str__(self):
        return f"{self.variable_name}^{self.n}"


def _abstract_with_dimension_inner(n_dim, x, i):

    if i == n_dim:
        return Scalar(Content(x))
    return Sequence(
        ExtractLength(x),
        function(
            1,
            lambda idx: _abstract_with_dimension_inner(
                n_dim, Call(Content(x), idx), i + 1
            ),
        ),
    )


register(
    UnboundWithDimension.w.a,
    lambda a: _abstract_with_dimension_inner(a.n, Unbound(a.variable_name), 0),
)
