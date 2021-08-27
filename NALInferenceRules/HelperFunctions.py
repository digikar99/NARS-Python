import math

import Config
import Global
import NALGrammar
import NALSyntax
from NALInferenceRules.TruthValueFunctions import TruthFunctionOnArrayAndRevise, TruthFunctionOnArray, F_Deduction, \
    F_Revision

import NALInferenceRules.Local


def get_truthvalue_from_evidence(wp, w):
    """
        Input:
            wp: positive evidence w+

            w: total evidence w
        Returns:
            frequency, confidence
    """
    if wp == w:
        f = 1.0
    else:
        f = wp / w
    c = get_confidence_from_evidence(w)
    return f, c


def get_evidence_fromfreqconf(f, c):
    """
        Input:
            f: frequency

            c: confidence
        Returns:
            w+, w, w-
    """
    wp = Config.k * f * c / (1 - c)
    w = Config.k * c / (1 - c)
    return wp, w, w - wp


def get_confidence_from_evidence(w):
    """
        Input:
            w: Total evidence
        Returns:
            confidence
    """
    return w / (w + Config.k)




def create_resultant_sentence_two_premise(j1, j2, result_statement, truth_value_function):
    """
        Creates the resultant sentence between 2 premises, the resultant statement, and the truth function
    :param j1:
    :param j2:
    :param result_statement:
    :param truth_value_function:
    :return:
    """
    result_statement = NALGrammar.Terms.simplify(result_statement)

    result_type = premise_result_type(j1,j2)

    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal:
        # Judgment or Goal
        # Get Truth Value
        (f1, c1) = (j1.value.frequency, j1.value.confidence)
        if j1.is_event() and j2.is_event():
            proj_value = NALInferenceRules.Local.Value_Projection(j1, j2.stamp.occurrence_time)
            (f2, c2) = proj_value.frequency, proj_value.confidence
        else:
            (f2, c2) = (j2.value.frequency, j2.value.confidence)
        result_truth_array = None
        if j1.is_array and j2.is_array:
            result_truth, result_truth_array = TruthFunctionOnArrayAndRevise(j1.truth_values,
                                                                        j2.truth_values,
                                                                        truth_value_function=truth_value_function)
        else:
            result_truth = truth_value_function(f1, c1, f2, c2)

        occurrence_time = None

        # if the result is a first-order statement,  or a compound statement, it may need an occurrence time
        if (isinstance(result_statement, NALGrammar.Terms.StatementTerm)
            and NALSyntax.Copula.is_first_order(result_statement.get_copula())) \
                or (not isinstance(result_statement, NALGrammar.Terms.StatementTerm)
                    and isinstance(result_statement, NALGrammar.Terms.CompoundTerm)
                    and not NALSyntax.TermConnector.is_first_order(result_statement.connector)):
            if j1.is_event() and j2.is_event():
                if j1.stamp.occurrence_time > j2.stamp.occurrence_time:
                    occurrence_time = j1.stamp.occurrence_time
                else:
                    occurrence_time = j2.stamp.occurrence_time
            elif j1.is_event():
                occurrence_time = j1.stamp.occurrence_time
            elif j2.is_event():
                #todo dont map to j2 occurrence times
                occurrence_time = j2.stamp.occurrence_time

        if result_type == NALGrammar.Sentences.Judgment:
            result = NALGrammar.Sentences.Judgment(result_statement, (result_truth, result_truth_array),
                                                   occurrence_time=occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            # if isinstance(result_statement,NALGrammar.Terms.CompoundTerm):
            #     result_statement, result_truth = simplify_implication_subject_or_goal(result_statement, result_truth)
            #     if result_statement is None:
            #         return None # goal is already true

            result = NALGrammar.Sentences.Goal(result_statement, (result_truth, result_truth_array), occurrence_time=occurrence_time)
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)
    stamp_and_print_inference_rule(result, truth_value_function, [j1,j2])

    return result

def create_resultant_sentence_one_premise(j, result_statement, truth_value_function, result_truth=None):
    """
        Creates the resultant sentence for 1 premise, the resultant statement, and the truth function
        if truth function is None, uses j's truth-value
    :param j:
    :param result_statement:
    :param truth_value_function:
    :param result_truth: Optional truth result
    :return:
    """

    result_type = type(j)
    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal:
        # Get Truth Value
        result_truth_array = None
        if result_truth is None:
            if truth_value_function is None:
                if result_type == NALGrammar.Sentences.Judgment:
                    result_truth = NALGrammar.Values.TruthValue(j.value.frequency,j.value.confidence)
                elif result_type == NALGrammar.Sentences.Goal:
                    result_truth = NALGrammar.Values.DesireValue(j.value.frequency, j.value.confidence)
            else:
                if j.is_array:
                    result_truth_array = TruthFunctionOnArray(j.truth_values, None, truth_value_function)
                result_truth = truth_value_function(j.value.frequency, j.value.confidence)


        if result_type == NALGrammar.Sentences.Judgment:
            result = NALGrammar.Sentences.Judgment(result_statement, (result_truth, result_truth_array),
                                                   occurrence_time=j.stamp.occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            result = NALGrammar.Sentences.Goal(result_statement, (result_truth, result_truth_array),
                                               occurrence_time=j.stamp.occurrence_time)
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)
    result.stamp.from_one_premise_inference = True

    if truth_value_function is None:
        stamp_and_print_inference_rule(result, truth_value_function, j.stamp.parent_premises)
    else:
        stamp_and_print_inference_rule(result, truth_value_function, [j])

    return result

def stamp_and_print_inference_rule(sentence, inference_rule, parent_sentences):
    sentence.stamp.derived_by = "Structural Transformation" if inference_rule is None else inference_rule.__name__

    sentence.stamp.parent_premises = []

    parent_strings = []
    for parent in parent_sentences:
        sentence.stamp.parent_premises.append(parent)
        parent_strings.append(str(parent))

    if Config.DEBUG: Global.Global.debug_print(sentence.stamp.derived_by + " derived " + sentence.__class__.__name__ + sentence.get_formatted_string()
                                               + " by parents " + str(parent_strings))

def premise_result_type(j1,j2):
    """
        Given 2 sentence premises, determines the type of the resultant sentence
    """
    if not isinstance(j1, NALGrammar.Sentences.Judgment):
        return type(j1)
    elif not isinstance(j2, NALGrammar.Sentences.Judgment):
        return type(j2)
    else:
        return NALGrammar.Sentences.Judgment

def convert_to_interval(working_cycles):
    """
        return interval from working cycles
    """
    #round(Config.INTERVAL_SCALE*math.sqrt(working_cycles))
    return working_cycles#round(math.log(Config.INTERVAL_SCALE * working_cycles)) + 1 #round(math.log(working_cycles)) + 1 ##round(5*math.log(0.05*(working_cycles + 9))+4)

def convert_from_interval(interval):
    """
        return working cycles from interval
    """
    #round((interval/Config.INTERVAL_SCALE) ** 2)
    return interval#round(math.exp(interval) / Config.INTERVAL_SCALE) #round(math.exp(interval))  # round(math.exp((interval-4)/5)/0.05 - 9)

def interval_weighted_average(interval1, interval2, weight1, weight2):
    return round((interval1*weight1 + interval2*weight2)/(weight1 + weight2))