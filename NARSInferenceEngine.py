"""
    Author: Christian Hahm
    Created: March 8, 2021
    Purpose: Identifies and performs proper inference for the system
"""
import NALGrammar
import NALInferenceRules
import NARSDataStructures
import NALSyntax


def do_inference_two_premise(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence) -> [NARSDataStructures.Task]:
    """
        Derives a new task by performing the appropriate inference rules on the given semantically related sentences.
        The resultant sentence's evidential base is merged from its parents.

        :param t1: Task containing sentence j1
        :param j2: Belief containing sentence j2

        :assume j1 and j2 have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
                (no evidential overlap)

        :returns An array of the derived Tasks, or None if the inputs have evidential overlap
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    if j1.statement.term.term_connector is not None or j2.statement.term.term_connector is not None:
        return []

    """
    ===============================================
    ===============================================
        Pre-Processing
    ===============================================
    ===============================================
    """
    derived_sentences = []

    j1_term = j1.statement.term
    j2_term = j2.statement.term
    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()
    j1_predicate_term = j1.statement.get_predicate_term()
    j2_predicate_term = j2.statement.get_predicate_term()
    j1_copula = j1.statement.copula
    j2_copula = j2.statement.copula

    # check if the result will lead to tautology
    tautology = (j1_subject_term == j2_predicate_term and j1_predicate_term == j2_subject_term) or\
                (j1_subject_term == j2_subject_term and j1_predicate_term == j2_predicate_term
                 and not (j1_copula == NALSyntax.Copula.Inheritance and j2_copula == NALSyntax.Copula.Inheritance))

    # check if copula are the same
    different_copulas = (j1_copula != j2_copula)

    if tautology or different_copulas:
        # can't do inference
        return derived_sentences

    is_question = isinstance(j1, NALGrammar.Question) or isinstance(j2, NALGrammar.Question)

    """
    ===============================================
    ===============================================
        First-order and Higher-Order Syllogistic Rules
    ===============================================
    ===============================================
    """

    if j1_term == j2_term:
        """
        # Revision
        # j1=S-->P, j2=S-->P
        # or j1=S<->P, j2=S<->P or P<->S
        """
        if is_question: return derived_sentences # can't do revision with questions

        derived_sentence = NALInferenceRules.Revision(j1, j2)  # S-->P
        print_inference_rule(inference_rule="Revision")
        derived_sentences.append(derived_sentence)
    elif not NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula):
        if j1_subject_term == j2_predicate_term or j1_predicate_term == j2_subject_term:
            """
            # j1=M-->P, j2=S-->M
            # or j1=M-->S, j2=P-->M
            # OR swapped premises
            # j1=S-->M, j2=M-->P
            # or j1=P-->M, j2=M-->S
            """
            swapped = False
            if j1_subject_term != j2_predicate_term:
                # j1=S-->M, j2=M-->P
                # or j1=P-->M, j2=M-->S
                j1, j2 = j2, j1  # swap sentences
                swapped = True
            # deduction
            derived_sentence = NALInferenceRules.Deduction(j1, j2)  # S-->P or P-->S
            print_inference_rule(inference_rule="Deduction")
            derived_sentences.append(derived_sentence)

            """
            # Swapped Exemplification
            """
            derived_sentence = NALInferenceRules.Exemplification(j2, j1)  # P-->S or S-->P
            print_inference_rule(inference_rule="Swapped Exemplification")
            derived_sentences.append(derived_sentence)

            if swapped:
                j1, j2 = j2, j1  # restore sentences
                swapped = False
        elif j1_subject_term == j2_subject_term:
            """
            # j1=M-->P, j2=M-->S
            # Induction
            """
            derived_sentence = NALInferenceRules.Induction(j1, j2)  # S-->P
            print_inference_rule(inference_rule="Induction")
            derived_sentences.append(derived_sentence)

            """
            # Swapped Induction
            """
            derived_sentence = NALInferenceRules.Induction(j2, j1)  # P-->S
            print_inference_rule(inference_rule="Swapped Induction")
            derived_sentences.append(derived_sentence)

            """
            # Comparison
            """
            derived_sentence = NALInferenceRules.Comparison(j1, j2)  # S<->P
            print_inference_rule(inference_rule="Comparison")
            derived_sentences.append(derived_sentence)

            """
            # Intensional Intersection
            """
            derived_sentence = NALInferenceRules.IntensionalIntersection(j1, j2)  # M --> (S | P)
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Extensional Intersection
            """
            derived_sentence = NALInferenceRules.ExtensionalIntersection(j1, j2)  # M --> (S & P)
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Extensional Difference
            """
            derived_sentence = NALInferenceRules.Difference(j1, j2)  # M --> (S - P)
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Swapped Extensional Difference
            """
            derived_sentence = NALInferenceRules.Difference(j2, j1)  # M --> (S - P)
            print_inference_rule( inference_rule="Intersection")
            derived_sentences.append(derived_sentence)
        elif j1_predicate_term == j2_predicate_term:
            """
            # j1=P-->M, j2=S-->M
            # Abduction
            """
            derived_sentence = NALInferenceRules.Abduction(j1, j2)  # S-->P
            print_inference_rule(inference_rule="Abduction")
            derived_sentences.append(derived_sentence)

            """
            # Swapped Abduction
            """
            derived_sentence = NALInferenceRules.Abduction(j2, j1)  # P-->S
            print_inference_rule(inference_rule="Swapped Abduction")
            derived_sentences.append(derived_sentence)

            """
            # Comparison
            """
            derived_sentence = NALInferenceRules.Comparison(j1, j2)  # S<->P
            print_inference_rule(inference_rule="Comparison")
            derived_sentences.append(derived_sentence)

            """
            # Intensional Intersection
            """
            derived_sentence = NALInferenceRules.IntensionalIntersection(j1, j2)  # (S | P) --> M
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Extensional Intersection
            """
            derived_sentence = NALInferenceRules.ExtensionalIntersection(j1, j2)  # (S & P) --> M
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Intensional Difference
            """
            derived_sentence = NALInferenceRules.Difference(j1, j2)  # (S ~ P) --> M
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)

            """
            # Swapped Intensional Difference
            """
            derived_sentence = NALInferenceRules.Difference(j2, j1)  # (P ~ S) --> M
            print_inference_rule(inference_rule="Intersection")
            derived_sentences.append(derived_sentence)
        else:
            assert False, "error, concept " + str(j1.statement.term) + " and " + str(j2.statement.term) + " not related"
    elif not NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
        """
        # j1=M-->P or P-->M
        # j2=S<->M or M<->S
        # Analogy
        """
        derived_sentence = NALInferenceRules.Analogy(j1, j2)  # S-->P or P-->S
        print_inference_rule(inference_rule="Analogy")
        derived_sentences.append(derived_sentence)
    elif NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula):
        """
        # j1=M<->P or P<->M
        # j2=S-->M or M-->S
        # Swapped Analogy
        """
        derived_sentence = NALInferenceRules.Analogy(j2, j1)  # S-->P or P-->S
        print_inference_rule(inference_rule="Swapped Analogy")
        derived_sentences.append(derived_sentence)
    elif NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
        """
        # j1=M<->P or P<->M
        # j2=S<->M or M<->S
        # Resemblance
        """
        derived_sentence = NALInferenceRules.Resemblance(j1, j2)  # S<->P
        print_inference_rule(inference_rule="Resemblance")
        derived_sentences.append(derived_sentence)

    immediate_inference_derived_sentences = []
    for derived_sentence in derived_sentences:
        immediate_inference_derived_sentences.extend(do_inference_one_premise(derived_sentence))

    derived_sentences.extend(immediate_inference_derived_sentences)

    """
    ===============================================
    ===============================================
        Post-Processing
    ===============================================
    ===============================================
    """
    # mark sentences as interacted with each other
    j1.stamp.mutually_add_to_interacted_sentences(j2)

    return derived_sentences

def do_inference_one_premise(j):
    """
        Immediate Inference Rules

    """
    derived_sentences = []
    if isinstance(j, NALGrammar.Judgment):
        # Negation
        derived_sentence = NALInferenceRules.Negation(j)
        print_inference_rule(inference_rule="Negation")
        derived_sentences.append(derived_sentence)

        # Conversion
        if not NALSyntax.Copula.is_symmetric(j.statement.copula) and j.value.frequency > 0:
            derived_sentence = NALInferenceRules.Conversion(j)
            print_inference_rule(inference_rule="Conversion")
            derived_sentences.append(derived_sentence)

        # Contraposition
        if j.statement.copula == NALSyntax.Copula.Implication and j.value.frequency < 1:
            derived_sentence = NALInferenceRules.Contraposition(j)
            print_inference_rule(inference_rule="Contraposition")
            derived_sentences.append(derived_sentence)

    return derived_sentences


def print_inference_rule(inference_rule="Inference"): print(inference_rule)