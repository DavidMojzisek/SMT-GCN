from six.moves import xrange
from pysmt.environment import get_env
from pysmt.walkers import TreeWalker, handles
from pysmt.utils import quote
import pysmt.operators as op


class CustomSmtPrinter(TreeWalker):

    def __init__(self, stream):
        TreeWalker.__init__(self)
        self.stream = stream
        self.write = self.stream.write
        self.mgr = get_env().formula_manager
        self.unique_symbols = set()
    def printer(self, f):
        self.walk(f)


    def walk(self, formula, threshold=None):
        """Generic walk method, will apply the function defined by the map
        self.functions.

        If threshold parameter is specified, the walk_threshold
        function will be called for all nodes with depth >= threshold.
        """
        nodes = {formula._node_id : op.op_to_str(formula.node_type())}
        self.unique_symbols.add(op.op_to_str(formula.node_type()))
        try:
            f = self.functions[formula.node_type()]
        except KeyError:
            f = self.walk_error

        iterator = f(formula)
        if iterator is None:
            return

        stack = [iterator]
        edge_list = []

        while stack:
            f = stack[-1]
            try:
                
                child = next(f)
                if not 's' in stack[-1].gi_frame.f_locals:
                    child = next(f)
                sym = op.op_to_str(stack[-1].gi_frame.f_locals['s'].node_type())
                #print(sym)
                """
                if str(child)[:3]=='div':
                    sym =  'div'
                if str(child)[:3]=='mod':
                    sym =  'mod'
                self.unique_symbols.add(sym)
                """
                edge_list.append((stack[-1].gi_frame.f_locals['formula']._node_id, stack[-1].gi_frame.f_locals['s']._node_id))
                nodes[stack[-1].gi_frame.f_locals['s']._node_id] = sym
                if threshold and len(stack) >= threshold:
                    iterator = self.walk_threshold(child)
                    if iterator is not None:
                        stack.append(iterator)
                else:
                    try:
                        cf = self.functions[child.node_type()]
                    except KeyError:
                        cf = self.walk_error
                    iterator = cf(child)
                    if iterator is not None:
                        stack.append(iterator)
            except StopIteration:
                stack.pop()
        return edge_list, nodes

    def walk_threshold(self, formula):
        """This is a complete printer"""
        raise NotImplementedError

    def walk_nary(self, formula, operator):
        self.write("(%s" % operator)
        for s in formula.args():
            self.write(" ")
            yield s
        self.write(")")

    def walk_and(self, formula): return self.walk_nary(formula, "and")
    def walk_or(self, formula): return self.walk_nary(formula, "or")
    def walk_not(self, formula): return self.walk_nary(formula, "not")
    def walk_implies(self, formula): return self.walk_nary(formula, "=>")
    def walk_iff(self, formula): return self.walk_nary(formula, "=")
    def walk_plus(self, formula): return self.walk_nary(formula, "+")
    def walk_minus(self, formula): return self.walk_nary(formula, "-")
    def walk_times(self, formula): return self.walk_nary(formula, "*")
    def walk_equals(self, formula): return self.walk_nary(formula, "=")
    def walk_le(self, formula): return self.walk_nary(formula, "<=")
    def walk_lt(self, formula): return self.walk_nary(formula, "<")
    def walk_ite(self, formula): return self.walk_nary(formula, "ite")
    def walk_toreal(self, formula): return self.walk_nary(formula, "to_real")
    def walk_div(self, formula): return self.walk_nary(formula, "/")
    def walk_pow(self, formula): return self.walk_nary(formula, "pow")
    def walk_bv_and(self, formula): return self.walk_nary(formula, "bvand")
    def walk_bv_or(self, formula): return self.walk_nary(formula, "bvor")
    def walk_bv_not(self, formula): return self.walk_nary(formula, "bvnot")
    def walk_bv_xor(self, formula): return self.walk_nary(formula, "bvxor")
    def walk_bv_add(self, formula): return self.walk_nary(formula, "bvadd")
    def walk_bv_sub(self, formula): return self.walk_nary(formula, "bvsub")
    def walk_bv_neg(self, formula): return self.walk_nary(formula, "bvneg")
    def walk_bv_mul(self, formula): return self.walk_nary(formula, "bvmul")
    def walk_bv_udiv(self, formula): return self.walk_nary(formula, "bvudiv")
    def walk_bv_urem(self, formula): return self.walk_nary(formula, "bvurem")
    def walk_bv_lshl(self, formula): return self.walk_nary(formula, "bvshl")
    def walk_bv_lshr(self, formula): return self.walk_nary(formula, "bvlshr")
    def walk_bv_ult(self, formula): return self.walk_nary(formula, "bvult")
    def walk_bv_ule(self, formula): return self.walk_nary(formula, "bvule")
    def walk_bv_slt(self, formula): return self.walk_nary(formula, "bvslt")
    def walk_bv_sle(self, formula): return self.walk_nary(formula, "bvsle")
    def walk_bv_concat(self, formula): return self.walk_nary(formula, "concat")
    def walk_bv_comp(self, formula): return self.walk_nary(formula, "bvcomp")
    def walk_bv_ashr(self, formula): return self.walk_nary(formula, "bvashr")
    def walk_bv_sdiv(self, formula): return self.walk_nary(formula, "bvsdiv")
    def walk_bv_srem(self, formula): return self.walk_nary(formula, "bvsrem")
    def walk_bv_tonatural(self, formula): return self.walk_nary(formula, "bv2nat")
    def walk_array_select(self, formula): return self.walk_nary(formula, "select")
    def walk_array_store(self, formula): return self.walk_nary(formula, "store")

    def walk_symbol(self, formula):
        self.write(quote(formula.symbol_name()))

    def walk_function(self, formula):
        return self.walk_nary(formula, quote(formula.function_name().symbol_name()))

    def walk_int_constant(self, formula):
        if formula.constant_value() < 0:
            self.write("(- " + str(-formula.constant_value()) + ")")
        else:
            self.write(str(formula.constant_value()))

    def walk_real_constant(self, formula):
        if formula.constant_value() < 0:
            template = "(- %s)"
        else:
            template = "%s"

        (n,d) = abs(formula.constant_value().numerator), \
                    formula.constant_value().denominator
        if d != 1:
            res = template % ( "(/ " + str(n) + " " + str(d) + ")" )
        else:
            res = template % (str(n) + ".0")

        self.write(res)

    def walk_bool_constant(self, formula):
        if formula.constant_value():
            self.write("true")
        else:
            self.write("false")

    def walk_bv_constant(self, formula):
        self.write("#b" + formula.bv_bin_str())

    def walk_str_constant(self, formula):
        self.write('"' + formula.constant_value().replace('"', '""') + '"')

    def walk_forall(self, formula):
        return self._walk_quantifier("forall", formula)

    def walk_exists(self, formula):
        return self._walk_quantifier("exists", formula)

    def _walk_quantifier(self, operator, formula):
        assert len(formula.quantifier_vars()) > 0
        self.write("(%s (" % operator)

        for s in formula.quantifier_vars():
            self.write("(")
            yield s
            self.write(" %s)" % s.symbol_type().as_smtlib(False))

        self.write(") ")
        yield formula.arg(0)
        self.write(")")

    def walk_bv_extract(self, formula):
        self.write("((_ extract %d %d) " % (formula.bv_extract_end(),
                                            formula.bv_extract_start()))
        yield formula.arg(0)
        self.write(")")

    @handles(op.BV_ROR, op.BV_ROL)
    def walk_bv_rotate(self, formula):
        if formula.is_bv_ror():
            rotate_type = "rotate_right"
        else:
            assert formula.is_bv_rol()
            rotate_type = "rotate_left"
        self.write("((_ %s %d) " % (rotate_type,
                                     formula.bv_rotation_step()))
        yield formula.arg(0)
        self.write(")")

    @handles(op.BV_ZEXT, op.BV_SEXT)
    def walk_bv_extend(self, formula):
        if formula.is_bv_zext():
            extend_type = "zero_extend"
        else:
            assert formula.is_bv_sext()
            extend_type = "sign_extend"
        self.write("((_ %s %d) " % (extend_type,
                                     formula.bv_extend_step()))
        yield formula.arg(0)
        self.write(")")

    def walk_str_length(self, formula):
        self.write("(str.len ")
        self.walk(formula.arg(0))
        self.write(")")

    def walk_str_charat(self,formula, **kwargs):
        self.write("( str.at " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(")")

    def walk_str_concat(self,formula, **kwargs):
        self.write("( str.++ " )
        for arg in formula.args():
            self.walk(arg)
            self.write(" ")
        self.write(")")

    def walk_str_contains(self,formula, **kwargs):
        self.write("( str.contains " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(")")

    def walk_str_indexof(self,formula, **kwargs):
        self.write("( str.indexof " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(" ")
        self.walk(formula.arg(2))
        self.write(")")

    def walk_str_replace(self,formula, **kwargs):
        self.write("( str.replace " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(" ")
        self.walk(formula.arg(2))
        self.write(")")

    def walk_str_substr(self,formula, **kwargs):
        self.write("( str.substr " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(" ")
        self.walk(formula.arg(2))
        self.write(")")

    def walk_str_prefixof(self,formula, **kwargs):
        self.write("( str.prefixof " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(")")

    def walk_str_suffixof(self,formula, **kwargs):
        self.write("( str.suffixof " )
        self.walk(formula.arg(0))
        self.write(" ")
        self.walk(formula.arg(1))
        self.write(")")

    def walk_str_to_int(self,formula, **kwargs):
        self.write("( str.to.int " )
        self.walk(formula.arg(0))
        self.write(")")

    def walk_int_to_str(self,formula, **kwargs):
        self.write("( int.to.str " )
        self.walk(formula.arg(0))
        self.write(")")

    def walk_array_value(self, formula):
        assign = formula.array_value_assigned_values_map()
        for _ in xrange(len(assign)):
            self.write("(store ")

        self.write("((as const %s) " % formula.get_type().as_smtlib(False))
        yield formula.array_value_default()
        self.write(")")

        for k in sorted(assign, key=str):
            self.write(" ")
            yield k
            self.write(" ")
            yield assign[k]
            self.write(")")