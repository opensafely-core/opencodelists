"""This module contains a parser for the subset of the SNOMED CT Expression Constraint
Language that describes codelists.

It can handle expressions of the form:

    concept_ref
    concept_ref OR concept_ref [OR ...]
    (concept_ref [OR ...])  MINUS (concept_ref [OR ...])

where concept_ref of the form:

    operator? code |term|?

and operator is one of < (ie include all descendants) or << (ie include self and all
descendants).

The parser will accept more complex expressions, but these are likely to be meaningless
(eg (a MINUS b) MINUS (c MINUS d)) and will trigger an exception in `handle()`.
"""

from antlr4 import CommonTokenStream, InputStream

from .parser_utils.ECLsubsetLexer import ECLsubsetLexer
from .parser_utils.ECLsubsetParser import ECLsubsetParser
from .parser_utils.ECLsubsetVisitor import ECLsubsetVisitor


def handle(expr):
    """Given an expression, return dict of included and excluded codes."""

    tree = parse(expr)

    if tree["type"] in ["expr", "or"]:
        return {"included": handle_expr_or_or(tree), "excluded": set()}
    elif tree["type"] == "minus":
        return handle_minus(tree)
    else:  # pragma: no cover
        assert False, tree


def handle_expr_or_or(node):
    if node["type"] == "expr":
        return handle_expr(node)
    elif node["type"] == "or":
        return handle_or(node)
    else:
        assert False, node


def handle_expr(node):
    assert node["operator"] in [None, "<<", "<"]
    return {(node["operator"], node["value"])}


def handle_or(node):
    return {list(handle_expr(child))[0] for child in node["children"]}


def handle_minus(node):
    return {
        "included": handle_expr_or_or(node["lhs"]),
        "excluded": handle_expr_or_or(node["rhs"]),
    }


def parse(expr):
    """Parse expression."""

    input_stream = InputStream(expr)
    lexer = ECLsubsetLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = ECLsubsetParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(ErrorListener())
    tree = parser.expressionconstraint()
    visitor = Visitor()
    return visitor.visit(tree)


class Visitor(ECLsubsetVisitor):
    def aggregateResult(self, aggregate, nextResult):
        return nextResult or aggregate

    def visitSubexpressionconstraint(self, node):
        concept = node.eclfocusconcept()

        if concept:
            constraint_operator_node = node.constraintoperator()
            if constraint_operator_node:
                operator = self.visit(constraint_operator_node)
            else:
                operator = None
            value = self.visit(concept)
            return {
                "type": "expr",
                "operator": operator,
                "value": value,
            }
        else:
            return self.visit(node.expressionconstraint())

    def visitDisjunctionexpressionconstraint(self, node):
        return {
            "type": "or",
            "children": [
                self.visit(subexpr) for subexpr in node.subexpressionconstraint()
            ],
        }

    def visitExclusionexpressionconstraint(self, node):
        subexpression_constraints = node.subexpressionconstraint()
        assert len(subexpression_constraints) == 2

        return {
            "type": "minus",
            "lhs": self.visit(subexpression_constraints[0]),
            "rhs": self.visit(subexpression_constraints[1]),
        }

    def visitConstraintoperator(self, node):
        return node.getText()

    def visitEclconceptreference(self, node):
        return node.conceptid().getText()


class ParseError(Exception):
    pass


class ErrorListener:
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise ParseError(f"{type(e).__name__}({msg}) (line: {line}, column: {column})")

    def reportAmbiguity(
        self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs
    ):  # pragma: no cover
        raise ParseError(
            f"Ambiguity (startIndex: {startIndex}, stopIndex: {stopIndex})"
        )

    def reportAttemptingFullContext(
        self, recognizer, dfa, startIndex, stopIndex, conflictingAlts, configs
    ):
        raise ParseError(
            f"Attempting full context (startIndex: {startIndex}, stopIndex: {stopIndex})"
        )

    def reportContextSensitivity(
        self, recognizer, dfa, startIndex, stopIndex, prediction, configs
    ):  # pragma: no cover
        raise ParseError(
            f"Context sensitivity (startIndex: {startIndex}, stopIndex: {stopIndex})"
        )
