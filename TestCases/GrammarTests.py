import NARSDataStructures
from NALGrammar import *
from NALSyntax import Punctuation
import NARS
from NARSMemory import Concept

"""
    Author: Christian Hahm
    Created: March 11, 2021
    Purpose: Unit Testing for NARS grammar
"""

def calculate_syntactic_complexity_test():
    atomic_term = Term.get_term_from_string("A")
    atomic_term_complexity = 1

    singleton_set_compound_term = Term.get_term_from_string("[A]")
    singleton_set_compound_term_complexity = 2

    extensional_set_compound_term = Term.get_term_from_string("{A,B}")
    extensional_set_compound_term_complexity = 3

    singleton_set_internal_compound_term = Term.get_term_from_string("[(*,A,B)]")
    singleton_set_internal_compound_term_complexity = 4

    statement_term = Term.get_term_from_string("(A-->B)")
    statement_term_complexity = 3

    assert atomic_term.calculate_syntactic_complexity() == atomic_term_complexity
    assert singleton_set_compound_term.calculate_syntactic_complexity() == singleton_set_compound_term_complexity
    assert extensional_set_compound_term.calculate_syntactic_complexity() == extensional_set_compound_term_complexity
    assert singleton_set_internal_compound_term.calculate_syntactic_complexity() == singleton_set_internal_compound_term_complexity
    assert statement_term.calculate_syntactic_complexity() == statement_term_complexity



if __name__ == "__main__":
    """
        Term Tests
    """
    calculate_syntactic_complexity_test()

    print("All tests successfully passed.")