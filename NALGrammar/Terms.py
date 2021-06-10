"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import enum

import Global
import NALSyntax
from NALGrammar.Arrays import Array

import NALGrammar.Asserts


class Term:
    """
        Base class for all terms.
    """
    term_dict = {} # a dictionary of existing terms to prevent duplicate term creation. Key: term string ; Value: term

    def __init__(self, term_string):
        assert isinstance(term_string, str), term_string + " must be a str"
        self.string = term_string
        self.syntactic_complexity = self._calculate_syntactic_complexity()

    def get_formatted_string(self):
        return self.string

    def __eq__(self, other):
        """
            Terms are equal if their strings are the same
        """
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.get_formatted_string()

    def _calculate_syntactic_complexity(self):
        assert False, "Complexity not defined for Term base class"

    def is_operation(self):
        return False

    def contains_variable(self):
        return VariableTerm.VARIABLE_SYM in str(self) \
                or VariableTerm.QUERY_SYM in str(self)

    @classmethod
    def from_string(cls, term_string):
        """
            Determine if it is an atomic term (e.g. "A") or a statement/compound term (e.g. (&&,A,B,..) or (A --> B))
            or variable term and creates the corresponding Term.

            :param term_string - String from which to construct the term
            :returns Term constructed using the string
        """

        if term_string in cls.term_dict:
            return cls.term_dict[term_string]

        if term_string[0] == NALSyntax.StatementSyntax.Start.value:
            """
                Compound or Statement Term
            """
            assert (term_string[-1] == NALSyntax.StatementSyntax.End.value), "Compound/Statement term must have ending parenthesis: " + term_string

            copula, copula_idx = get_top_level_copula(term_string)
            if copula is None:
                # compound term
                term = CompoundTerm.from_string(term_string)
            else:
                term = StatementTerm.from_string(term_string)
        elif NALSyntax.TermConnector.is_set_bracket_start(term_string[0]):
            # set term
            term = CompoundTerm.from_string(term_string)
        elif term_string[0] == NALSyntax.TermConnector.Array.value:
            if NALSyntax.StatementSyntax.ArrayElementIndexStart.value in term_string:
                term = ArrayTermElementTerm.from_string(term_string)
            else:
                term = ArrayTerm.from_string(term_string)
        elif term_string[0] == VariableTerm.VARIABLE_SYM or term_string[0] == VariableTerm.QUERY_SYM:
            # variable term
            dependency_list_start_idx = term_string.find("(")
            if dependency_list_start_idx == -1:
                variable_name = term_string[1:]
                dependency_list_string = ""
            else:
                variable_name = term_string[1:dependency_list_start_idx]
                dependency_list_string = term_string[term_string.find("(") + 1:term_string.find(")")]

            term = VariableTerm.from_string(variable_name=variable_name,
                                            variable_type_symbol=term_string[0],
                                            dependency_list_string=dependency_list_string)
        else:
            term = AtomicTerm(term_string)

        cls.term_dict[term_string] = term

        return term

    @classmethod
    def simplify(cls, term):
        if isinstance(term,AtomicTerm):
            return term
        elif isinstance(term, StatementTerm):
            simplified_subject_term = Term.simplify(term.get_subject_term())
            simplified_predicate_term = Term.simplify(term.get_predicate_term())
            return StatementTerm(subject_term=simplified_subject_term, predicate_term=simplified_predicate_term, copula=term.copula)
        elif isinstance(term, CompoundTerm):
            if term.connector is NALSyntax.TermConnector.Negation:
                if len(term.subterms) == 1:
                    pass
            elif term.connector is NALSyntax.TermConnector.ExtensionalDifference:pass
            elif term.connector is NALSyntax.TermConnector.IntensionalDifference:pass
            elif term.connector is NALSyntax.TermConnector.ExtensionalImage:pass
            elif term.connector is NALSyntax.TermConnector.IntensionalImage:pass
            return term

class VariableTerm(Term):
    class Type(enum.Enum):
        Independent = 1
        Dependent = 2
        Query = 3

    VARIABLE_SYM = "#"
    QUERY_SYM = "?"

    def __init__(self, variable_name: str, variable_type: Type, dependency_list=None):
        """

        :param variable_string: variable name
        :param variable_type: type of variable
        :param dependency_list: array of independent variables this variable depends on
        """
        # todo parse variable terms from input strings
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.variable_symbol = VariableTerm.QUERY_SYM if variable_type == VariableTerm.Type.Query else VariableTerm.VARIABLE_SYM
        self.dependency_list = dependency_list
        super().__init__(self.get_formatted_string())

    def get_formatted_string(self):
        dependency_string = ""
        if self.dependency_list is not None:
            dependency_string = "("
            for dependency in self.dependency_list:
                dependency_string = dependency_string + str(dependency) + NALSyntax.StatementSyntax.TermDivider.value

            dependency_string = dependency_string[0:-1] + ")"

        return self.variable_symbol + self.variable_name + dependency_string

    @classmethod
    def from_string(cls, variable_name: str, variable_type_symbol: str, dependency_list_string: str):
        # parse dependency list
        dependency_list = None

        if len(dependency_list_string) > 0:
            dependency_list = []

        type = None
        if variable_type_symbol == VariableTerm.QUERY_SYM:
            type = VariableTerm.Type.Query
        elif variable_type_symbol == VariableTerm.VARIABLE_SYM:
            if dependency_list is None:
                type = VariableTerm.Type.Independent
            else:
                type = VariableTerm.Type.Dependent

        assert type is not None, "Error: Variable type symbol invalid"
        return cls(variable_name, type, dependency_list)

    def _calculate_syntactic_complexity(self):
        if self.dependency_list is None:
            return 1
        else:
            return 1 + len(self.dependency_list)


class AtomicTerm(Term):
    """
        An atomic term, named by a valid word.
    """

    def __init__(self, term_string):
        """
        Input:
            term_string = name of the term
        """
        assert (AtomicTerm.is_valid_term(term_string)), term_string + " is not a valid Atomic Term name."
        super().__init__(term_string)

    def _calculate_syntactic_complexity(self):
        return 1

    @classmethod
    def is_valid_term(cls, term_string):
        for char in term_string:
            if char not in NALSyntax.valid_term_chars: return False
        return True

class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms connected by a connector (including copula).

        (Connector T1, T2, ..., Tn)
    """

    def __init__(self, subterms: [Term], term_connector: NALSyntax.TermConnector = None):
        """
        Input:
            subterms: array of immediate subterms

            connector: subterm connector
        """
        self.connector = term_connector  # sets are represented by the opening bracket as the connector, { or [

        if term_connector is not None:
            if len(subterms) > 1 \
                    and NALSyntax.TermConnector.is_order_invariant(term_connector):
                # order doesn't matter, alphabetize so the system can recognize the same term
                subterms.sort(key=lambda t: str(t))

            is_extensional_set = (term_connector.value == NALSyntax.TermConnector.ExtensionalSetStart.value)
            is_intensional_set = (term_connector.value == NALSyntax.TermConnector.IntensionalSetStart.value)

            is_set = is_extensional_set or is_intensional_set

            if is_set and len(subterms) > 1:
                # multi_component_set
                # todo handle multi-component sets better
                singleton_set_subterms = []

                for subterm in subterms:
                    # decompose the set into an intersection of singleton sets
                    singleton_set_subterm = CompoundTerm.from_string(self.connector.value + str(subterm) + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value)
                    singleton_set_subterms.append(singleton_set_subterm)

                subterms = singleton_set_subterms

                # set new term connector as intersection
                if is_extensional_set:
                    self.connector = NALSyntax.TermConnector.IntensionalIntersection
                elif is_intensional_set:
                    self.connector = NALSyntax.TermConnector.ExtensionalIntersection

        self.subterms: [Term] = subterms

        Term.__init__(self,term_string=self.get_formatted_string())

    def is_intensional_set(self):
        return self.connector == NALSyntax.TermConnector.IntensionalSetStart

    def is_extensional_set(self):
        return self.connector == NALSyntax.TermConnector.ExtensionalSetStart

    def is_set(self):
        return self.is_intensional_set() or self.is_extensional_set()

    def get_formatted_string(self):
        if self.is_set():
            string = self.connector.value
        else:
            string = self.connector.value + NALSyntax.StatementSyntax.TermDivider.value

        for subterm in self.subterms:
            string = string + subterm.get_formatted_string() + NALSyntax.StatementSyntax.TermDivider.value

        string = string[:-1] # remove the final term divider

        if self.is_set():
            return string + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value
        else:
            return NALSyntax.StatementSyntax.Start.value + string + NALSyntax.StatementSyntax.End.value

    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        count = 0
        if self.connector is not None:
            count = 1 # the term connector
        for subterm in self.subterms:
            count = count + subterm._calculate_syntactic_complexity()
        return count


    @classmethod
    def from_string(cls, compound_term_string):
        """
            Create a compound term from a string representing a compound term
        """
        subterms, connector = cls.parse_toplevel_subterms_and_connector(compound_term_string)
        return cls(subterms, connector)

    @classmethod
    def parse_toplevel_subterms_and_connector(cls, compound_term_string):
        """
            Parse out all top-level subterms from a string representing a compound term

            compound_term_string - a string representing a compound term
        """
        compound_term_string = compound_term_string.replace(" ","")
        subterms = []
        internal_string = compound_term_string[1:-1] # string with no outer parentheses () or set brackets [], {}

        # check for intensional/extensional set [a,b], {a,b}
        connector = NALSyntax.TermConnector.get_term_connector_from_string(compound_term_string[0])
        if connector is None:
            # otherwise check for regular Term/Statement connectors
            if internal_string[1] == NALSyntax.StatementSyntax.TermDivider.value:
                connector_string = internal_string[0] # Term connector
            else:
                connector_string = internal_string[0:2] # Statement connector
            connector = NALSyntax.TermConnector.get_term_connector_from_string(connector_string)

            assert (internal_string[
                        len(
                            connector.value)] == NALSyntax.StatementSyntax.TermDivider.value), "Connector not followed by comma in CompoundTerm string " + compound_term_string
            internal_string = internal_string[len(connector.value) + 1:]

        assert (connector is not None), "Connector could not be parsed from CompoundTerm string."

        depth = 0
        subterm_string = ""
        for i, c in enumerate(internal_string):
            if c == NALSyntax.StatementSyntax.Start.value or NALSyntax.TermConnector.is_set_bracket_start(c):
                depth += 1
            elif c == NALSyntax.StatementSyntax.End.value or NALSyntax.TermConnector.is_set_bracket_end(c):
                depth -= 1

            if c == NALSyntax.StatementSyntax.TermDivider.value and depth == 0:
                subterm = Term.from_string(subterm_string)
                subterms.append(subterm)
                subterm_string = ""
            else:
                subterm_string += c

        subterm = Term.from_string(subterm_string)
        subterms.append(subterm)

        return subterms, connector



class StatementTerm(CompoundTerm,Array):
    """
        <subject><copula><predicate>

        A special kind of compound term with a subject, predicate, and copula.
        Statement connector is `None` for regular statements

        (P --> Q)

        May also represent a single-statement compound, like negation (--,(P-->Q))
        in which case the non-negated statement is stored in subject and predicate is None.
    """

    def __init__(self, subject_term: Term, predicate_term = None, copula=None, statement_connector = None):
        NALGrammar.Asserts.assert_term(subject_term)

        if predicate_term is None:
            NALGrammar.Asserts.assert_statement_term(subject_term)
            subterms = [subject_term]
        else:
            subterms = [subject_term, predicate_term]

        self.copula = None
        if copula is not None:
            self.copula = copula
            if NALSyntax.Copula.is_symmetric(copula):
                subterms.sort(key=lambda t: str(t))  # sort alphabetically

        CompoundTerm.__init__(self,subterms, statement_connector)

        subject_is_array_term = isinstance(subject_term, CompoundTerm) \
                             and subject_term.is_extensional_set() \
                             and isinstance(subject_term.subterms[0], Array) \
                             and subject_term.subterms[0].is_array
        predicate_is_array_term = isinstance(predicate_term, CompoundTerm) \
                             and predicate_term.is_extensional_set() \
                             and isinstance(predicate_term.subterms[0], Array) \
                             and predicate_term.subterms[0].is_array

        dimensions = None
        if subject_is_array_term and predicate_is_array_term:
            dimensions = subject_term.subterms[0].get_dimensions()
        elif subject_is_array_term:
            dimensions = subject_term.subterms[0].get_dimensions()
        elif predicate_is_array_term:
            dimensions = predicate_term.subterms[0].get_dimensions()

        Array.__init__(self, dimensions=dimensions)


    @classmethod
    def from_string(cls, statement_string):
        """
            Parameter: statement_string - String of NAL syntax "(term copula term)"

            Returns: top-level subject term, predicate term, copula, copula index
        """
        statement_connector = None

        if NALSyntax.TermConnector.get_term_connector_from_string(
                statement_string[1:3]) == NALSyntax.TermConnector.Negation:
            # found a negation statement connector
            statement_connector = NALSyntax.TermConnector.Negation
            statement_string = statement_string[4:-1]

        # get copula
        copula, copula_idx = get_top_level_copula(statement_string)
        assert (copula is not None), "Copula not found. Exiting.."

        subject_str = statement_string[1:copula_idx]  # get subject string
        predicate_str = statement_string[
                        copula_idx + len(copula.value):len(statement_string) - 1]  # get predicate string

        return StatementTerm(subject_term=Term.from_string(subject_str), predicate_term=Term.from_string(predicate_str),
                              copula=copula, statement_connector=statement_connector)



    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        count = 1  # the copula
        if self.connector is not None:
            count += 1
        for subterm in self.subterms:
            count = count + subterm._calculate_syntactic_complexity()

        return count

    def get_subject_term(self) -> Term:
        return self.subterms[0]

    def get_predicate_term(self) -> Term:
        return self.subterms[1]

    def get_copula(self):
        return self.copula

    def get_statement_connector(self):
        return self.connector

    def get_copula_string(self):
        return str(self.get_copula().value)

    def get_formatted_string(self):
        """
            returns: (Subject copula Predicate)
        """
        if len(self.subterms) > 1:
            string = NALSyntax.StatementSyntax.Start.value + \
               self.get_subject_term().get_formatted_string() + \
               " " + self.get_copula_string() + " " + \
               self.get_predicate_term().get_formatted_string() \
               + NALSyntax.StatementSyntax.End.value
        else:
            string = CompoundTerm.get_formatted_string(self)

        return string

    def is_operation(self):
        return isinstance(self.get_subject_term(), CompoundTerm) \
            and self.get_subject_term().connector == NALSyntax.TermConnector.Product \
            and self.get_subject_term().subterms[0] == Global.Global.TERM_SELF # product and first term is self means this is an operation


class ArrayTerm(CompoundTerm,Array):
    """
        A N-dimensional array term that can be indexed. (N between 1 and 3)

        Note that no values are stored in the array. The term only represents an array of terms.
    """
    def __init__(self, name, dimensions):
        """
        :param name: Name of the array term
        :param dimensions: the number of elements in each dimensional axis (x,y,z);
            provides a granularity = 2.0/(dim_length - 1)
        """
        self.name = name
        Array.__init__(self, dimensions)
        CompoundTerm.__init__(self, subterms=self.array.flatten(), term_connector=NALSyntax.TermConnector.Array)

    def get_formatted_string(self):
        return NALSyntax.TermConnector.Array.value + self.name

    @classmethod
    def from_string(cls, name, dimensions=None):
        """
            name: @ArrayTermName
            Create a compound term from a string representing a compound term
        """
        if dimensions is None:
            concept_item = Global.Global.NARS.memory.concepts_bag.peek(name)
            assert concept_item is not None,"ERROR: Cannot parse Array term without dimensions unless it already exists in the system"
            return concept_item.object.term
        else:
            return cls(name, dimensions)


class ArrayTermElementTerm(AtomicTerm):
    """
        A term that is an element of an array term.
        It is simply the array term with attached indices

        e.g. @A[x,y,z]
    """
    def __init__(self, array_term, indices):
        self.array_term = array_term # the array term of which this is an element
        self.indices = indices
        self.indices_string = ""
        for i in range(len(indices)):
            self.indices_string += str(indices[i])
            if i != len(indices)-1:
                #not the final element
                self.indices_string += ", "

    def get_formatted_string(self):
        return self.array_term.get_formatted_string() \
        + NALSyntax.StatementSyntax.ArrayElementIndexStart.value \
        + self.indices_string \
        + NALSyntax.StatementSyntax.ArrayElementIndexEnd.value

    @classmethod
    def from_string(cls, term_string):
        start_indices = term_string.find(NALSyntax.StatementSyntax.ArrayElementIndexStart.value)
        end_indices = term_string.rfind(NALSyntax.StatementSyntax.ArrayElementIndexEnd.value)
        array_term = ArrayTerm.from_string(term_string[0:start_indices])
        indices = term_string[start_indices+1:end_indices].replace(" ","").split(",")
        indices = [float(idx) for idx in indices]
        return ArrayTermElementTerm(array_term=array_term,indices=indices)


def get_top_level_copula(string):
    """
        Searches for top-level copula in the string.

        :returns copula and index if it exists,
        :returns none and -1 otherwise
    """
    copula = None
    copula_idx = -1

    depth = 0
    for i, v in enumerate(string):
        if v == NALSyntax.StatementSyntax.Start.value:
            depth += 1
        elif v == NALSyntax.StatementSyntax.End.value:
            depth -= 1
        elif depth == 1 and i + 3 <= len(string) and NALSyntax.Copula.is_string_a_copula(string[i:i + 3]):
            copula, copula_idx = NALSyntax.Copula.get_copula_from_string(string[i:i + 3]), i

    return copula, copula_idx