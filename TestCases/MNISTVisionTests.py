import gc
import glob
import queue
import random
import threading
import time
from keras.datasets import mnist

import numpy as np

import Config
import Global
import InputChannel
import NARS
import NALGrammar


from PIL import Image, ImageTk
import os
import tkinter as tk


directory = 'supervised_learning/'
dir_0 = directory + '0/'
dir_1 = directory + '1/'

digit_to_label = {}
digit_to_detected_term = {}
for i in range(0,10):
    term_str = "(" + str(i) + " --> SEEN)"
    term = NALGrammar.Terms.from_string(term_str)
    digit_to_label[i] = term_str + ". :|: %1.0;0.99%"
    digit_to_detected_term[i] = term

digit_to_goal_op_term = {}
for i in range(10):
    term_str = "((*,{SELF}) --> press_digit_" + str(i) + ")"
    term = NALGrammar.Terms.from_string(term_str)
    digit_to_goal_op_term[i] = term

current_trial = -1

"""
create dataset
"""
digit_to_image_dataset = {}
for i in range(10):
    digit_to_image_dataset[i] = [[],[]]
(train_x, train_y), (test_x, test_y) = mnist.load_data()
X = np.concatenate((train_x,test_x))
Y = np.concatenate((train_y,test_y))
# store digits
for i in range(len(Y)):
    x,y = X[i], Y[i]
    digit_to_image_dataset[y][0].append(x)
    digit_to_image_dataset[y][1].append(y)
# convert to numpy
for i in range(10):
    digit_to_image_dataset[i] = (np.array(digit_to_image_dataset[i][0]), np.array(digit_to_image_dataset[i][1]))


def load_dataset(length,bit=False,percent_of_train_img=0.25):
    """
        Load specific data from the dataset.
    """
    x_train = []
    y_train = []
    x_test = []
    y_test = []

    num_of_digits = 2 if bit else 10

    files_per_digit = round(length / num_of_digits)
    cutoff = round(percent_of_train_img * files_per_digit)

    for digit in range(num_of_digits):
        dataset_x, dataset_y = digit_to_image_dataset[digit]
        # shuffle and trim to desired length
        p = np.random.permutation(len(dataset_x))
        this_x_list, this_y_list = list(dataset_x[p][0:files_per_digit]), list(dataset_y[p][0:files_per_digit])

        x_train += this_x_list[0:cutoff]
        y_train += this_y_list[0:cutoff]
        x_test += this_x_list[cutoff:]
        y_test += this_y_list[cutoff:]


    # shuffle
    p = np.random.permutation(len(x_train))
    x_train, y_train = np.array(x_train)[p], np.array(y_train)[p]

    p = np.random.permutation(len(x_test))
    x_test, y_test = np.array(x_test)[p], np.array(y_test)[p]

    return x_train, y_train, x_test, y_test

def break_time(duration,clear_img=False):
    print('BREAK TIME...')
    # give the system a small break
    global_gui.update_test_buttons(None)
    if clear_img:
        Global.Global.NARS.vision_buffer.blank_image()
        global_gui.clear_visual_image()
        global_gui.set_visual_image(Image.fromarray(Global.Global.NARS.vision_buffer.img))
    global_gui.set_status_label('BREAK TIME...')
    for i in range(duration):
        Global.Global.NARS.do_working_cycle()
        global_gui.set_status_label('BREAK:\ncycle ' + str(i) + ' / ' + str(duration) \
                                       + '\n' + str(round(i* 100 / duration, 2)) + "%")
        global_gui.update_spotlight()
    print('END BREAK...')

def seed_goals(bit):
    """
    Seed goals to identify digit
    :return:
    """
    if bit:
        quantity = 2
    else:
        quantity = 10
    for i in range(quantity):
        label = "(&/,(" + str(i) + " --> SEEN),((*,{SELF}) --> press_digit_" + str(i) + "))! :|: %1.0;0.99%"
        InputChannel.parse_and_queue_input_string(label)


def binary_memorization():
    restart_NARS()
    training_cycles = 150

    images_per_class = 5
    dataset_len = 2*images_per_class

    x_train, y_train, x_test, y_test = load_dataset(length=dataset_len,
                                                    bit=True)


    x = np.concatenate((x_train, x_test), axis=0)
    y = np.concatenate((y_train, y_test), axis=0)



    """
        Training Phase
    """
    train(x_train=x,
          y_train=y,
          cycles=training_cycles)


    """
        Testing Phase
    """
    return test(bit=True,
         x_test=x,
         y_test=y)


def digit_memorization():
    restart_NARS()
    training_cycles = 500

    images_per_class = 1
    dataset_len = 10*images_per_class
    x = []
    y = []
    digit_folder_list = glob.glob(directory + '*')

    x_train, y_train, x_test, y_test = load_dataset(length=dataset_len)

    if len(y_train) == 0:
        x = x_test
        y = y_test
    elif len(y_test) == 0:
        x = x_train
        y = y_train
    else:
        x = np.concatenate((x_train, x_test), axis=0)
        y = np.concatenate((y_train, y_test), axis=0)


    """
        Training Phase
    """
    train(x_train=x,
          y_train=y,
          cycles=training_cycles)


    """
        Testing Phase
    """
    return test(bit=False,
         x_test=x,
         y_test=y)


def binary_classification():
    restart_NARS()

    length = 120
    assert length % 2 == 0, "ERROR: must use divisible by 2 number to create equal dataset"
    training_cycles = 750

    digit_folder_list = [glob.glob(directory + '0')[0], glob.glob(directory + '1')[0]]

    x_train, y_train, x_test, y_test = load_dataset(length=length,
                                                    bit=True)

    """
        Training Phase
    """
    train(x_train=x_train,
          y_train=y_train,
          cycles=training_cycles)


    """
        Testing Phase
    """
    return test(bit=True,
         x_test=x_test,
         y_test=y_test)


def digit_classification():
    restart_NARS()
    length = 500
    training_cycles = 200
    x_train, y_train, x_test, y_test = load_dataset(length=length,
                                                    bit=False,
                                                    percent_of_train_img=0.8)

    """
        Training Phase
    """
    train(x_train=x_train,
           y_train=y_train,
           cycles=training_cycles)


    """
        Testing Phase
    """
    return test(bit=False,
         x_test=x_test,
         y_test=y_test)


class MNISTVisionTestGUI:
    ZOOM = 16
    gui_disabled = False

    def start(self):
        if self.gui_disabled: return
        self.create_window()
        self.window.mainloop()

    def create_window(self):
        if self.gui_disabled: return
        window = tk.Tk()
        self.window = window
        window.title("NARS Vision Test")
        window.geometry("1000x650")

        self.HEIGHT, self.WIDTH = 28,28

        HEIGHT, WIDTH, ZOOM = self.HEIGHT, self.WIDTH, self.ZOOM

        # main image
        self.visual_image_canvas = tk.Canvas(window,
                                        width=WIDTH*ZOOM,
                                        height=HEIGHT*ZOOM,
                                        bg="#000000")
        self.visual_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                        height=HEIGHT * ZOOM)

        self.visual_image_canvas_img = self.visual_image_canvas.create_image((WIDTH*ZOOM / 2, HEIGHT*ZOOM / 2),
                                                                             image=self.visual_img,
                                                                             state="normal")

        # label
        self.status_label = tk.Label(window, text="Initializing...")
        self.test_accuracy_label = tk.Label(window, text="Test Accuracy: Need more data")


        # attended image
        self.attended_image_canvas = tk.Canvas(window,
                                             width=WIDTH * ZOOM,
                                             height=HEIGHT * ZOOM,
                                             bg="#000000")
        self.attended_img = tk.PhotoImage(width=WIDTH * ZOOM,
                                          height=HEIGHT * ZOOM)
        self.attended_image_canvas_img = self.attended_image_canvas.create_image((WIDTH*ZOOM / 2, HEIGHT*ZOOM / 2),
                                                                               image=self.attended_img,
                                                                               state="normal")

        # sliders
        self.digit_to_label = {}
        self.digit_to_label_lights = {}
        self.digit_to_label_sliders = {}
        self.digit_to_label_slider_guilabel = {}
        column = 2

        self.NARS_guess_label = tk.Label(window, text="NARS Guess:")

        for i in range(10):
            light = tk.Button(window,text="    ",bg="black")
            label = tk.Label(window, text=i)
            self.digit_to_label_lights[i] = light
            self.digit_to_label_slider_guilabel[i] = label
            column += 3

        self.button_correct = tk.Button(bg='grey', text="CORRECT")
        self.button_wrong = tk.Button(bg='grey', text="INCORRECT")

        self.visual_image_canvas.grid(row=0, column=1)
        self.attended_image_canvas.grid(row=0,column=2, columnspan=30)
        self.status_label.grid(row=1, column=1)

    def set_visual_image(self, new_img):
        if self.gui_disabled: return
        self.visual_img = ImageTk.PhotoImage(new_img.resize((self.WIDTH * MNISTVisionTestGUI.ZOOM, self.HEIGHT * MNISTVisionTestGUI.ZOOM), Image.NEAREST))
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_attended_image_array(self, img_array):
        if self.gui_disabled: return
        new_img = Image.fromarray(img_array)
        self.attended_img = ImageTk.PhotoImage(new_img.resize((new_img.width * MNISTVisionTestGUI.ZOOM, new_img.height * MNISTVisionTestGUI.ZOOM), Image.NEAREST))
        self.attended_image_canvas.itemconfig(self.attended_image_canvas_img, image=self.attended_img)

    def clear_visual_image(self):
        if self.gui_disabled: return
        self.visual_img = tk.PhotoImage(width=self.WIDTH * MNISTVisionTestGUI.ZOOM, VisionTestGUI=self.HEIGHT * MNISTVisionTestGUI.ZOOM)
        self.visual_image_canvas.itemconfig(self.visual_image_canvas_img, image=self.visual_img)

    def set_status_label(self, text):
        if self.gui_disabled: return
        self.status_label.config(text=text)

    def update_spotlight(self):
        if self.gui_disabled: return
        # update last attended image
        if Global.Global.NARS.vision_buffer.last_taken_img_array is not None:
            self.set_attended_image_array(Global.Global.NARS.vision_buffer.last_taken_img_array)

    def get_predicted_digit(self):
        operation_statement = Global.Global.NARS.last_executed
        predicted = -1
        if operation_statement is not None:
            for key in digit_to_goal_op_term:
                value = digit_to_goal_op_term[key]
                if value == operation_statement:
                    predicted = key

        return predicted


    def update_gui_lights(self, predicted, label_y):
        if self.gui_disabled: return
        # update GUI lights
        for i in range(10):
            if i == predicted:
                if predicted == label_y:
                    self.digit_to_label_lights[i].config(bg="green")
                else:
                    self.digit_to_label_lights[i].config(bg="red")
            else:
                self.digit_to_label_lights[i].config(bg="black")

        time.sleep(1.0)
        return predicted

    def get_predicted_bit(self):
        if self.gui_disabled: return
        operation_statement = Global.Global.NARS.last_executed
        predicted = -1
        if operation_statement is not None:
            for key in digit_to_goal_op_term:
                value = digit_to_goal_op_term[key]
                if value == operation_statement:
                    predicted = key

        return predicted



    def toggle_test_buttons(self, on):
        if self.gui_disabled: return

        if on:
            self.button_correct.grid(row=2, column=0)
            self.button_wrong.grid(row=3, column=0)
            self.test_accuracy_label.grid(row=2,column=1)

            column = 4
            self.NARS_guess_label.grid(row=1, column=column,columnspan=30)
            for i in range(10):
                self.digit_to_label_lights[i].grid(row=2,column=column)
                self.digit_to_label_slider_guilabel[i].grid(row=3,column=column)
                column += 3
        else:
            self.update_test_buttons(correct=None)
            self.button_correct.grid_remove()
            self.button_wrong.grid_remove()
            self.test_accuracy_label.grid_remove()

            column = 4
            self.NARS_guess_label.grid_remove()
            for i in range(10):
                self.digit_to_label_lights[i].grid_remove()
                self.digit_to_label_slider_guilabel[i].grid_remove()
                column += 3


    def update_test_buttons(self, correct):
        if self.gui_disabled: return

        if correct is not None:
            if correct:
                self.button_correct.config(bg='green')
                self.button_wrong.config(bg='grey')
            else:
                self.button_correct.config(bg='grey')
                self.button_wrong.config(bg='red')
        else:
            self.button_correct.config(bg='grey')
            self.button_wrong.config(bg='grey')

    def update_test_accuracy(self,accuracy):
        if self.gui_disabled: return
        self.test_accuracy_label.config(text="TRIAL " + str(current_trial+1) + " ACCURACY: " + str(accuracy) + "%")

    def create_final_score_popup_window(self,final_score):
        if self.gui_disabled: return
        popup_window = tk.Toplevel(self.window)
        labelExample = tk.Label(popup_window, text="AVERAGE TEST CASE\nACCURACY OVER 3 TRIALS:\n\n" + str(final_score) + "%\n\n")
        buttonExample = tk.Button(popup_window, text="OK", command=popup_window.destroy)

        labelExample.pack()
        buttonExample.pack()

def train(x_train, y_train, cycles):
    Config.Testing = False
    print('Begin Training Phase')


    global_gui.toggle_test_buttons(on=False)
    for train_idx,img_array in enumerate(x_train):
        img = Image.fromarray(img_array)
        InputChannel.queue_visual_sensory_image_array(img)
        global_gui.set_visual_image(img)

        label = digit_to_label[y_train[train_idx]]
        print('TRAINING digit ' + str(y_train[train_idx]) \
            + ':\nFile: #' + str(train_idx + 1) + "/" + str(len(x_train)) + ' for ' + str(cycles) + ' cycles')

        break_time(Config.EVENT_BUFFER_CAPACITY)
        for i in range(cycles):
            Global.Global.NARS.do_working_cycle()
            InputChannel.parse_and_queue_input_string(label)
            global_gui.set_status_label('TRAINING:\nFile: #' + str(train_idx+1) + "/" + str(len(x_train)) + '\nCycle ' + str(i) + ' / ' + str(cycles) \
                                           + '\n' + str(round(i * 100 / cycles, 2)) + "%")
            global_gui.update_spotlight()

def calculate_confusion_matrix(y_correct, y_prediction, print_matrix=True):
    uniq = [-1] + list(np.unique(y_correct))
    y_to_uniq_id = dict()
    for idx, y in enumerate(uniq): y_to_uniq_id[y] = idx+1

    confusion_matrix = np.zeros((len(uniq)+1, len(uniq)+1))
    for i in range(1, len(uniq)+1):
        confusion_matrix[i, 0] = uniq[i-1]
        confusion_matrix[0, i] = uniq[i-1]
    for yc, yp in zip(y_correct, y_prediction):
        yc_id = y_to_uniq_id[yc]
        yp_id = y_to_uniq_id[yp]
        confusion_matrix[yc_id, yp_id] += 1

    if print_matrix:
        print("CONFUSION MATRIX (Expected \\ Predicted)")
        print(confusion_matrix)
        print()

    return confusion_matrix, uniq

def test(bit,
         x_test,
         y_test):
    TIMEOUT = 1500 # in working cycles
    Config.Testing = True
    break_duration = 100
    print('Begin Testing Phase')
    # run tests
    global_gui.toggle_test_buttons(on=True)

    # examples accuracy measurements
    correct_examples_total_cnt = 0
    incorrect_examples_total_cnt = 0
    correct_cnt_dict = {}
    incorrect_cnt_dict = {}

    num_digits = 2 if bit else 10
    for i in range(num_digits):
        correct_cnt_dict[i] = 0
        incorrect_cnt_dict[i] = 0

    y_correct, y_prediction = [], []
    for test_idx,img_array in enumerate(x_test):
        label_y = y_test[test_idx]
        img = Image.fromarray(img_array)
        InputChannel.queue_visual_sensory_image_array(img)
        global_gui.set_visual_image(img)

        # blank out GUI lights
        global_gui.update_gui_lights(predicted=-1, label_y=None)
        break_time(break_duration)

        print('TESTING next example, digit ' + str(label_y) + ':\nFile: #' + str(test_idx + 1) + "/" + str(len(x_test)))

        # let NARS think and come to a prediction
        prediction = -1
        i = 0
        while prediction == -1 and i < TIMEOUT: #
            Global.Global.NARS.do_working_cycle()
            global_gui.set_status_label('TESTING:\nFile: #' + str(test_idx+1) + "/" + str(len(x_test)) + '\nCycle ' + str(i))
            global_gui.update_spotlight()

            prediction = global_gui.get_predicted_digit()
            seed_goals(bit=bit)
            i += 1

        # check prediction
        correct = None
        if prediction == label_y:
            correct_examples_total_cnt += 1
            correct_cnt_dict[label_y] += 1
            correct=True
        else:
            incorrect_examples_total_cnt += 1
            incorrect_cnt_dict[label_y] += 1
            correct=False
        global_gui.update_test_buttons(correct=correct)
        global_gui.update_gui_lights(prediction, label_y)

        accuracy = round(correct_examples_total_cnt / (test_idx + 1) * 100, 2)
        print("=========== System predicted " + str(prediction) + " and actual was " + str(label_y))
        print('=========== Trial Accuracy so far: ' + str(accuracy) + "%")

        global_gui.update_test_accuracy(accuracy=accuracy)

        y_prediction.append(prediction)
        y_correct.append(label_y)

        if test_idx >= 9 and accuracy < 0.001:
            print("Aborting trial, parameters could not identify anything in 10 tests.")
            break


    total_examples = len(x_test)
    total_accuracy = round(correct_examples_total_cnt / total_examples * 100, 2)

    print('======= Test Subtotals ========')
    for i in range(num_digits):
        print('+!+ Digit ' + str(i) + ' examples (correct | incorrect | total):' \
              + str(correct_cnt_dict[i]) \
              + " | " + str(incorrect_cnt_dict[i])
              + " | " + str(correct_cnt_dict[i] + incorrect_cnt_dict[i]))
    print('+!+ OVERALL TOTAL examples (correct | incorrect | total):' \
          + str(correct_examples_total_cnt) \
          + " | " + str(incorrect_examples_total_cnt)
          + " | " + str(correct_examples_total_cnt + incorrect_examples_total_cnt))
    print('=!=========!= OVERALL TOTAL Test Accuracy: ' + str(total_accuracy) + "%")

    calculate_confusion_matrix(y_correct, y_prediction, print_matrix=True)

    # fitness function
    return total_accuracy


def learn_best_params():
    # current_params = {'PROJECTION_DECAY_DESIRE': Config.PROJECTION_DECAY_DESIRE,
    #                   'PROJECTION_DECAY_EVENT': Config.PROJECTION_DECAY_EVENT,
    current_params = {'T':  Config.T,
                      'FOCUSX': Config.FOCUSX,
                      'FOCUSY': Config.FOCUSY,
                      'k': Config.k}

    best_params = current_params.copy()

    runs = 10000
    current_best_score = 0
    for i in range(runs):
        restart_NARS()

        # then use the better config.
        if i != 0:
            # mutate current params
            num_to_mutate = random.randint(1,len(current_params))
        else:
            num_to_mutate = 0

        current_params_list = list(current_params)
        for j in range(num_to_mutate):
            index = random.randint(0, len(current_params_list) - 1)
            key = current_params_list[index]
            new_param = current_params[key]

            # with a random sign increment
            sign = random.randint(0, 1)

            if key == 'k':
                inc = random.random()
                if sign == 0 and new_param - inc >= 1:
                    # 0 will be negative
                    new_param += -1*inc
                else:
                    # 1 will be positive
                    new_param += inc
            elif key == 'FOCUSX' or key == 'FOCUSY':
                inc = random.random()
                if sign == 0 and new_param - inc > 0.0:
                    # 0 will be negative
                    new_param -= inc
                else:
                    # 1 will be positive
                    new_param += inc
            else:
                inc = random.random()
                if sign == 0:
                    # 0 will be negative
                    new_param += -1 * inc * new_param
                else:
                    # 1 will be positive
                    new_param += inc * (1 - new_param)

            if key == 'T' and new_param < 0.55: new_param = 0.55

            if new_param < 0.00001: new_param = 0.00001

            current_params[key] = new_param

        # set NARS Params
        # Config.PROJECTION_DECAY_DESIRE = current_params['PROJECTION_DECAY_DESIRE']
        # Config.PROJECTION_DECAY_EVENT = current_params['PROJECTION_DECAY_EVENT']
        Config.T = current_params['T']
        Config.FOCUSX = current_params['FOCUSX']
        Config.FOCUSY = current_params['FOCUSY']
        Config.k = current_params['k']

        print('--TRYING NEW PARAMS--')
        for key in current_params:
            print('trying new ' + str(key) + ': ' + str(current_params[key]))

        q = queue.Queue()
        t = threading.Thread(target=run_trials, args=[q, 0], daemon=True)
        t.start()
        t.join()
        avg_result = q.get(block=True)

        if avg_result is None:
            print("!!! Score for these parameters could not keep up with the current best. Skipping them and Reverting Configs to best...")
            current_params = best_params.copy()
        else:
            print('Config optimization result ratio was: ' + str(avg_result))
            if avg_result > current_best_score:
                # store new best params and score
                print(']]]]]]]]]]]]]]]]] NEW BEST: ' + str(avg_result) +
                ' beating ' + str(current_best_score) + ' [[[[[[[[[[[[[[[[')
                current_best_score = avg_result
                best_params = current_params.copy()
            elif avg_result == current_best_score:
                # store new best params and score
                print(']]]]]]]]]]]]]]]]] TIE: ' + str(avg_result) +
                ' === ' + str(current_best_score) + ' [[[[[[[[[[[[[[[[')
                best_params = current_params.copy()
            else:
                print('WORSE result. Reverting Configs to best...')
                current_params = best_params.copy()

        # print current best params
        print('--CURRENT BEST ' + str(current_best_score) + ' --')
        for key in best_params:
            print('BEST ' + str(key) + ': ' + str(best_params[key]))


    print('[][][][][][][][][][][][] OVERALL BEST CONFIG RESULTS (ratio ' + str(current_best_score) + '):')
    for key in best_params:
        print('BEST ' + str(key) + ': ' + str(best_params[key]))


def restart_NARS():
    Config.GUI_USE_INTERFACE = False
    Config.SILENT_MODE = True
    if Global.Global.NARS is not None: del Global.Global.NARS
    Global.Global.NARS = NARS.NARS()
    Global.Global.set_paused(False)
    gc.collect()


def run_trials(q, current_best_score, function=digit_classification):
    global current_trial
    sum_of_scores = 0
    trials = 3

    for trial in range(trials):
        print("===== STARTING TRIAL " + str(trial+1) + " / " + str(trials))

        current_trial = trial
        score = function()

        print("===== TRIAL " + str(trial+1) + " ACCURACY: " + str(score) + "%")
        sum_of_scores += score

        if current_best_score is not None and trial != trials - 1:
            theoretical_best = sum_of_scores
            for _ in range(trial + 1, trials):
                theoretical_best += 100  # plus the maximum score for the rest of the trials

            theoretical_best = theoretical_best / trials

            if theoretical_best < current_best_score:
                # if the system can theoretically be perfect in the next trials and still have a worse average
                # accuracy than the current best, just skip this configuration altogether
                return None

    avg_score = round(sum_of_scores / trials, 2)
    q.put(avg_score)

def run_test():
    q = queue.Queue()
    t = threading.Thread(target=run_trials, args=[q, 0], daemon=True)
    t.start()
    t.join()

    global_gui.create_final_score_popup_window(final_score=q.get(block=True))

def test_main():
    time.sleep(1)

    learn_parameters = False
    if learn_parameters:
        learn_best_params()
    else:
        run_test()

    time.sleep(10)



if __name__ == "__main__":
    global_gui = MNISTVisionTestGUI()
    global_gui.gui_disabled = False
    if global_gui.gui_disabled:
        global_gui.start()
    else:
        thread = threading.Thread(target=global_gui.start, daemon=True)
        thread.start()
    test_main()