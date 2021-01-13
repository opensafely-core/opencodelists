# Generated from ECLsubset.g4 by ANTLR 4.9.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ECLsubsetParser import ECLsubsetParser
else:
    from ECLsubsetParser import ECLsubsetParser

# This class defines a complete generic visitor for a parse tree produced by ECLsubsetParser.

class ECLsubsetVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ECLsubsetParser#expressionconstraint.
    def visitExpressionconstraint(self, ctx:ECLsubsetParser.ExpressionconstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#compoundexpressionconstraint.
    def visitCompoundexpressionconstraint(self, ctx:ECLsubsetParser.CompoundexpressionconstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#disjunctionexpressionconstraint.
    def visitDisjunctionexpressionconstraint(self, ctx:ECLsubsetParser.DisjunctionexpressionconstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#exclusionexpressionconstraint.
    def visitExclusionexpressionconstraint(self, ctx:ECLsubsetParser.ExclusionexpressionconstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#subexpressionconstraint.
    def visitSubexpressionconstraint(self, ctx:ECLsubsetParser.SubexpressionconstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#eclfocusconcept.
    def visitEclfocusconcept(self, ctx:ECLsubsetParser.EclfocusconceptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#eclconceptreference.
    def visitEclconceptreference(self, ctx:ECLsubsetParser.EclconceptreferenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#conceptid.
    def visitConceptid(self, ctx:ECLsubsetParser.ConceptidContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#constraintoperator.
    def visitConstraintoperator(self, ctx:ECLsubsetParser.ConstraintoperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#descendantof.
    def visitDescendantof(self, ctx:ECLsubsetParser.DescendantofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#descendantorselfof.
    def visitDescendantorselfof(self, ctx:ECLsubsetParser.DescendantorselfofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#childof.
    def visitChildof(self, ctx:ECLsubsetParser.ChildofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#ancestorof.
    def visitAncestorof(self, ctx:ECLsubsetParser.AncestorofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#ancestororselfof.
    def visitAncestororselfof(self, ctx:ECLsubsetParser.AncestororselfofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#parentof.
    def visitParentof(self, ctx:ECLsubsetParser.ParentofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#disjunction.
    def visitDisjunction(self, ctx:ECLsubsetParser.DisjunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#exclusion.
    def visitExclusion(self, ctx:ECLsubsetParser.ExclusionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#sctid.
    def visitSctid(self, ctx:ECLsubsetParser.SctidContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#ws.
    def visitWs(self, ctx:ECLsubsetParser.WsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#mws.
    def visitMws(self, ctx:ECLsubsetParser.MwsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#comment.
    def visitComment(self, ctx:ECLsubsetParser.CommentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#nonstarchar.
    def visitNonstarchar(self, ctx:ECLsubsetParser.NonstarcharContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#starwithnonfslash.
    def visitStarwithnonfslash(self, ctx:ECLsubsetParser.StarwithnonfslashContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#nonfslash.
    def visitNonfslash(self, ctx:ECLsubsetParser.NonfslashContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#sp.
    def visitSp(self, ctx:ECLsubsetParser.SpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#htab.
    def visitHtab(self, ctx:ECLsubsetParser.HtabContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#cr.
    def visitCr(self, ctx:ECLsubsetParser.CrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#lf.
    def visitLf(self, ctx:ECLsubsetParser.LfContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#qm.
    def visitQm(self, ctx:ECLsubsetParser.QmContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#bs.
    def visitBs(self, ctx:ECLsubsetParser.BsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#digit.
    def visitDigit(self, ctx:ECLsubsetParser.DigitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#zero.
    def visitZero(self, ctx:ECLsubsetParser.ZeroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#digitnonzero.
    def visitDigitnonzero(self, ctx:ECLsubsetParser.DigitnonzeroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#nonwsnonpipe.
    def visitNonwsnonpipe(self, ctx:ECLsubsetParser.NonwsnonpipeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#anynonescapedchar.
    def visitAnynonescapedchar(self, ctx:ECLsubsetParser.AnynonescapedcharContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ECLsubsetParser#escapedchar.
    def visitEscapedchar(self, ctx:ECLsubsetParser.EscapedcharContext):
        return self.visitChildren(ctx)



del ECLsubsetParser