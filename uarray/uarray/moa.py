import matchpy

from .machinery import *
from .core import *


class Shape(matchpy.Operation):
    name = "ρ"
    arity = matchpy.Arity(1, True)


def _shape(length, getitem):

    inner_shape = Shape(Call(getitem, Unbound()))

    return Sequence(
        Add(Value(1), ExtractLength(inner_shape)),
        PushVectorCallable(length, Content(inner_shape)),
    )


register(Shape(Scalar(w._)), lambda _: vector())
register(Shape(Sequence(w.length, w.getitem)), _shape)


class Index(matchpy.Operation):
    name = "ψ"
    infix = True
    arity = matchpy.Arity(2, True)


def _index(idx_length, idx_getitem, seq):
    for i in range(idx_length.value):
        index_value = Call(idx_getitem, Value(i))
        seq = Call(Content(seq), Content(index_value))
    return seq


register(Index(Sequence(Value.w.idx_length, w.idx_getitem), w.seq), _index)


class ReduceVector(matchpy.Operation):
    """
    ReduceVector(initial_value, callable, sequence)
    """

    name = "red"
    arity = matchpy.Arity(3, True)


def _reduce_vector(value, operation, length, getitem):
    for i in range(length.value):
        value = Call(operation, value, Content(Call(getitem, Value(i))))
    return value


register(
    ReduceVector(w.operation, Value.w.value, Sequence(Value.w.length, w.getitem)),
    _reduce_vector,
)


class Add(matchpy.Operation):
    name = "+"
    infix = True
    arity = matchpy.Arity(2, True)


register(Add(Value.w.l, Value.w.r), lambda l, r: Value(l.value + r.value))


class Multiply(matchpy.Operation):
    name = "*"
    infix = True
    arity = matchpy.Arity(2, True)


register(Multiply(Value.w.l, Value.w.r), lambda l, r: Value(l.value * r.value))


class Pi(matchpy.Operation):
    name = "π"
    arity = matchpy.Arity(1, True)


register(Pi(w.x), lambda x: ReduceVector(scalar(1), function(2, Multiply), x))


class Total(matchpy.Operation):
    name = "τ"
    arity = matchpy.Arity(1, True)


register(Total(w.x), lambda x: Pi(Shape(w.x)))


class Iota(matchpy.Operation):
    """
    Iota(n) returns a vector of 0 to n-1.
    """

    name = "ι"
    arity = matchpy.Arity(1, True)


register(Iota(Scalar(w.n)), lambda n: Sequence(n, function(1, Scalar)))


class Dim(matchpy.Operation):
    """
    Dimensionality
    """

    name = "δ"
    arity = matchpy.Arity(1, True)


register(Dim(w.x), lambda x: Pi(Shape(Shape(x))))


# class Args(matchpy.Operation):
#     """
#     Args(x, y)
#     """

#     name = "Args"
#     arity = matchpy.Arity(2, True)


# class ComArgs(matchpy.Operation):
#     """
#     ComArgs(x, y)
#     """

#     name = "ComArgs"
#     arity = matchpy.Arity(2, True)
#     commutative = True


class BinaryOperation(matchpy.Operation):
    """
    BinaryOperation(op, l, r)
    """

    name = "BinaryOperation"
    arity = matchpy.Arity(3, True)


# Both scalars

register(
    BinaryOperation(w.op, Scalar(w.l), Scalar(w.r)),
    lambda op, l, r: Scalar(Call(op, l, r)),
)

# register(
#     BinaryOperation(w.op, Args(Scalar(w.l), Scalar(w.r))),
#     lambda op, l, r: Scalar(Call(op, l, r)),
# )

# One scalar

# register(
#     BinaryOperation(w.op, ComArgs(Scalar(w.s), Sequence(w.length, w.getitem))),
#     lambda op, s, length, getitem: Sequence(
#         length,
#         function(
#             1, lambda idx: BinaryOperation(op, ComArgs(Scalar(s), Call(getitem, idx)))
#         ),
#     ),
# )

register(
    BinaryOperation(w.op, Scalar(w.s), Sequence(w.length, w.getitem)),
    lambda op, s, length, getitem: Sequence(
        length,
        function(1, lambda idx: BinaryOperation(op, Scalar(s), Call(getitem, idx))),
    ),
)
register(
    BinaryOperation(w.op, Sequence(w.length, w.getitem), Scalar(w.s)),
    lambda op, s, length, getitem: Sequence(
        length,
        function(1, lambda idx: BinaryOperation(op, Call(getitem, idx), Scalar(s))),
    ),
)

# neither scalars

# register(
#     BinaryOperation(
#         w.op,
#         ComArgs(Sequence(w.l_length, w.r_getitem), Sequence(w.r_length, w.r_getitem)),
#     ),
#     lambda op, l_length, l_getitem, r_length, r_getitem: Sequence(
#         Unify(l_length, r_length),
#         function(
#             1,
#             lambda idx: BinaryOperation(
#                 op, ComArgs(Call(l_getitem, idx), Call(r_getitem, idx))
#             ),
#         ),
#     ),
# )

register(
    BinaryOperation(
        w.op, Sequence(w.l_length, w.r_getitem), Sequence(w.r_length, w.r_getitem)
    ),
    lambda op, l_length, l_getitem, r_length, r_getitem: Sequence(
        Unify(l_length, r_length),
        function(
            1,
            lambda idx: BinaryOperation(op, Call(l_getitem, idx), Call(r_getitem, idx)),
        ),
    ),
)


class OuterProduct(matchpy.Operation):
    """
    OuterProduct(op, l, r)
    """

    name = "·"
    arity = matchpy.Arity(3, True)

    def __str__(self):
        op, l, r = self.operands
        return f"({l} ·{op} {r})"


register(
    OuterProduct(w.op, Scalar(w.l), w.r),
    lambda op, l, r: BinaryOperation(op, Scalar(l), r),
)
register(
    OuterProduct(w.op, Sequence(w.length, w.getitem), w.r),
    lambda op, length, getitem, r: Sequence(
        length, function(1, lambda idx: OuterProduct(op, Call(getitem, idx), r))
    ),
)


class InnerProduct(matchpy.Operation):
    """
    InnerProduct(l_op, r_op, l, r)
    """

    name = "·"
    arity = matchpy.Arity(4, True)

    def __str__(self):
        op_l, op_r, l, r = self.operands
        return f"({l} {op_l}·{op_r} {r})"


# inner product is associative with scalar multiplication
# TODO: Make this commutative so works for other orders of inner product and binary op.
register(
    InnerProduct(
        Function(Add(ws.add_args), ws.add_args2),
        Function(Multiply(ws.mult_args), ws.mult_args2),
        w.l,
        BinaryOperation(
            Function(Multiply(ws.inner_mult_args), ws.inner_mult_args2),
            Scalar(w.s),
            w.r,
        ),
    ),
    lambda l, s, r, add_args, add_args2, mult_args, mult_args2, inner_mult_args, inner_mult_args2: BinaryOperation(
        Function(Multiply(*inner_mult_args), *inner_mult_args),
        Scalar(s),
        InnerProduct(
            Function(Add(*add_args), *add_args),
            Function(Multiply(*mult_args), mult_args),
            l,
            r,
        ),
    ),
)
