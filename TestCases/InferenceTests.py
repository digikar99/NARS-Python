import multiprocessing
import os
import sys
import threading

import InputBuffer
import NARS
from multiprocessing import Process
from multiprocessing.queues import Queue

from NALGrammar import Term, TruthValue, Sentence, Statement
from NALInferenceRules import nal_abduction, nal_induction
from NALSyntax import Punctuation

"""
    Author: Christian Hahm
    Created: March 23, 2021
    Purpose: Unit Testing for NARS inference.
    Tests the overall NARS ability to perform inference, not simply the inference engine.
    This is not an exact science, since whether or not the tests pass depends not only the system's
    capability to do inference, but also whether its control mechanism selects the proper objects for inference.
"""
# This is a Queue that behaves like stdout
class StdoutQueue(Queue):
    def __init__(self,*args,**kwargs):
        super(StdoutQueue, self).__init__(*args,**kwargs,ctx=multiprocessing.get_context())

    def write(self,msg):
        self.put(msg)

    def flush(self):
        sys.__stdout__.flush()

def nars_process(input_judgment_q, input_question_q, output_q):
    testnars = NARS.NARS()
    sys.stdout = output_q

    # feed in judgments
    while input_judgment_q.qsize() > 0:
        InputBuffer.add_input_sentence(input_judgment_q.get())

    # process judgments
    testnars.do_working_cycles(50)

    # feed in questions
    while input_question_q.qsize() > 0:
        InputBuffer.add_input_sentence(input_question_q.get())

    # process questions
    testnars.do_working_cycles(100)

    sys.stdout = sys.__stdout__


def first_order_deduction():
    """
        Test first-order deduction:
        j1: (S-->M). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    input_judgment_q = StdoutQueue()
    input_question_q = StdoutQueue()
    output_q = StdoutQueue()

    j1 = InputBuffer.parse_sentence("(S-->M). %1.0;0.9%")
    j2 = InputBuffer.parse_sentence("(M-->P). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(InputBuffer.parse_sentence("(S-->P)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()


    success_criteria = []
    success_criteria.append(InputBuffer.parse_sentence("(S-->P). %1.0;0.81%").get_formatted_string_no_id())

    output = []
    while output_q.qsize() > 0:  # read and store result in log file
        output.append(output_q.get())

    success = True
    failed_criterion = ""
    for criterion in success_criteria:
        success = False
        for line in output:
            if criterion in line:
                success = True
                break
        if not success:
            failed_criterion = criterion
            break

    assert success,"TEST FAILURE: First-order Deduction test failed: " + failed_criterion

def first_order_induction():
    """
        Test first-order induction:
        j1: (M-->S). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
           and
           (P-->S). %1.0;0.45%
    """
    input_judgment_q = StdoutQueue()
    input_question_q = StdoutQueue()
    output_q = StdoutQueue()

    j1 = InputBuffer.parse_sentence("(M-->S). %1.0;0.9%")
    j2 = InputBuffer.parse_sentence("(M-->P). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(InputBuffer.parse_sentence("(S-->P)?"))
    input_question_q.put(InputBuffer.parse_sentence("(P-->S)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(nal_induction(j1,j2).get_formatted_string_no_id())
    success_criteria.append(nal_induction(j2,j1).get_formatted_string_no_id())

    output = []
    while output_q.qsize() > 0:  # read and store result in log file
         output.append(output_q.get())

    success = True
    failed_criterion = ""
    for criterion in success_criteria:
        success = False
        for line in output:
            if criterion in line:
                success = True
                break
        if not success:
            failed_criterion = criterion
            break

    assert success,"TEST FAILURE: First-order Induction test failed: " + failed_criterion

def first_order_abduction():
    """
        Test first-order abduction:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
           and
           (P-->S). %1.0;0.45%
    """
    input_judgment_q = StdoutQueue()
    input_question_q = StdoutQueue()
    output_q = StdoutQueue()

    j1 = InputBuffer.parse_sentence("(S-->M). %1.0;0.9%")
    j2 = InputBuffer.parse_sentence("(P-->M). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(InputBuffer.parse_sentence("(S-->P)?"))
    input_question_q.put(InputBuffer.parse_sentence("(P-->S)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(nal_abduction(j1,j2).get_formatted_string_no_id())
    success_criteria.append(nal_abduction(j2,j1).get_formatted_string_no_id())

    output = []
    while output_q.qsize() > 0:  # read and store result in log file
        output.append(output_q.get())

    success = True
    failed_criterion = ""
    for criterion in success_criteria:
        success = False
        for line in output:
            if criterion in line:
                success = True
                break
        if not success:
            failed_criterion = criterion
            break

    assert success,"TEST FAILURE: First-order Abduction test failed: " + failed_criterion


if __name__ == "__main__":
    """
        First-Order syllogism tests
    """
    first_order_deduction()
    first_order_induction()
    first_order_abduction()

    print("All tests successfully passed.")