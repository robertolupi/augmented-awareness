import ast
import calendar
import datetime
import enum
import math
import statistics
from types import SimpleNamespace


class UnsafeExpressionError(ValueError):
    """Raised when an expression uses unsupported Python features."""


SAFE_MODULES = {
    "math": SimpleNamespace(
        ceil=math.ceil,
        comb=math.comb,
        copysign=math.copysign,
        fabs=math.fabs,
        factorial=math.factorial,
        floor=math.floor,
        gcd=math.gcd,
        isclose=math.isclose,
        isfinite=math.isfinite,
        isinf=math.isinf,
        isnan=math.isnan,
        lcm=math.lcm,
        perm=math.perm,
        pow=math.pow,
        prod=math.prod,
        remainder=math.remainder,
        sqrt=math.sqrt,
        trunc=math.trunc,
        exp=math.exp,
        log=math.log,
        log10=math.log10,
        log2=math.log2,
        sin=math.sin,
        cos=math.cos,
        tan=math.tan,
        asin=math.asin,
        acos=math.acos,
        atan=math.atan,
        atan2=math.atan2,
        degrees=math.degrees,
        radians=math.radians,
        pi=math.pi,
        e=math.e,
        tau=math.tau,
    ),
    "calendar": SimpleNamespace(
        monthrange=calendar.monthrange,
        isleap=calendar.isleap,
        leapdays=calendar.leapdays,
        weekday=calendar.weekday,
    ),
    "statistics": SimpleNamespace(
        mean=statistics.mean,
        median=statistics.median,
        median_low=statistics.median_low,
        median_high=statistics.median_high,
        fmean=statistics.fmean,
        geometric_mean=statistics.geometric_mean,
        multimode=statistics.multimode,
        mode=statistics.mode,
        pstdev=statistics.pstdev,
        pvariance=statistics.pvariance,
        stdev=statistics.stdev,
        variance=statistics.variance,
    ),
}


def today() -> datetime.date:
    return datetime.date.today()


def now() -> datetime.datetime:
    return datetime.datetime.now()


SAFE_GLOBALS = {
    "date": datetime.date,
    "datetime": datetime.datetime,
    "timedelta": datetime.timedelta,
    "timezone": datetime.timezone,
    "today": today,
    "now": now,
    **SAFE_MODULES,
}

ALLOWED_AST_NODES = {
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Attribute,
    ast.Call,
    ast.keyword,
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Dict,
    ast.Subscript,
    ast.Slice,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.MatMult,
    ast.UAdd,
    ast.USub,
    ast.Invert,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
}

ALLOWED_NAME_CONSTANTS = {"True", "False", "None"}


class SafeExpressionValidator(ast.NodeVisitor):
    """Allow only a restricted expression subset."""

    def generic_visit(self, node):
        if type(node) not in ALLOWED_AST_NODES:
            raise UnsafeExpressionError(
                f"Unsupported Python construct: {type(node).__name__}"
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id not in SAFE_GLOBALS and node.id not in ALLOWED_NAME_CONSTANTS:
            raise UnsafeExpressionError(f"Unknown name: {node.id}")

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr.startswith("_"):
            raise UnsafeExpressionError("Private and dunder attributes are not allowed.")
        self.visit(node.value)

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise UnsafeExpressionError("Only direct function and method calls are allowed.")
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword)


def evaluate_expression(expression: str) -> object:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {exc.msg}") from exc

    SafeExpressionValidator().visit(tree)
    return eval(compile(tree, "<python_eval_tool>", "eval"), {"__builtins__": {}}, SAFE_GLOBALS)


def normalize_result(value: object) -> object:
    if isinstance(value, enum.IntEnum):
        return int(value)
    if isinstance(value, tuple):
        return tuple(normalize_result(item) for item in value)
    if isinstance(value, list):
        return [normalize_result(item) for item in value]
    if isinstance(value, dict):
        return {
            normalize_result(key): normalize_result(item)
            for key, item in value.items()
        }
    if isinstance(value, set):
        return {normalize_result(item) for item in value}
    return value
