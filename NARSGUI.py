
import Config
import NALGrammar
import NARSDataStructures
import NARSMemory

from PIL import Image, ImageTk
import numpy as np

import Global
import tkinter as tk
import numpy as np
"""
    GUI code
    Runs on its own separate process, and communicate with the NARS process using commands.
"""

class NARSGUI:
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None  # delay slider
    gui_total_cycles_lbl = None
    gui_total_cycles_stringvar = None
    gui_play_pause_button = None

    # Internal Data vars
    # listboxes
    gui_experience_buffer_listbox = None  # output for tasks in experience buffer
    gui_memory_listbox = None  # output for concepts in memory bag
    gui_event_buffer_listbox = None # output for tasks in event buffer

    # labels
    gui_event_buffer_output_label = None
    gui_experience_buffer_output_label = None
    gui_concepts_bag_output_label = None
    GUI_BUDGET_SYMBOL = "$"

    # array visualization
    gui_array_image_frame = None
    gui_array_image_dimensions = [300,300]

    # dictionary of data structure name to listbox
    dict_listboxes = {}
    gui_object_pipe = None # two-way object request communication
    gui_string_pipe = None # one way string communication

    # copied variables from Global
    gui_use_interface = None
    gui_use_internal_data = None

    # Keys
    KEY_STRING = "String"
    KEY_IS_ARRAY = "IsArray"
    KEY_STRING_NOID = "StringNoID"
    KEY_ID = "ID"
    KEY_OCCURRENCE_TIME = "OccurrenceTime"
    KEY_SENTENCE_TYPE = "SentenceType"
    KEY_DERIVED_BY = "DerivedBy"
    KEY_LIST_EVIDENTIAL_BASE = "ListEvidentialBase"
    KEY_LIST_INTERACTED_SENTENCES = "ListInteractedSentences"
    KEY_ARRAY_IMAGE = "ArrayImage"
    KEY_ARRAY_ELEMENT_STRINGS = "ArrayElementStrings"

    KEY_KEY = "Key"
    KEY_CLASS_NAME = "ClassName"
    KEY_OBJECT_STRING = "ObjectString"
    KEY_TERM_TYPE = "TermType"
    KEY_LIST_BELIEFS = "ListBeliefs"
    KEY_LIST_DESIRES = "ListDesires"
    KEY_LIST_TERM_LINKS = "ListTermLinks"
    KEY_LIST_PREDICTION_LINKS = "ListPredictionLinks"
    KEY_LIST_EXPLANATION_LINKS = "ListExplanationLinks"
    KEY_CAPACITY_BELIEFS = "CapacityBeliefs"
    KEY_CAPACITY_DESIRES = "CapacityDesires"

    KEY_CAPACITY_TERM_LINKS = "CapacityTermLinks"
    KEY_CAPACITY_PREDICTION_LINKS = "CapacityPredictionLinks"
    KEY_CAPACITY_EXPLANATION_LINKS = "CapacityExplanationLinks"
    KEY_SENTENCE_STRING = "SentenceString"


    def __init__(self):
        pass

    def print_to_output(self, msg, data_structure_name=None):
        """
             Print a message to an output GUI box
         """
        listbox = None
        if data_structure_name is not None and data_structure_name in self.dict_listboxes:
            listbox = self.dict_listboxes[data_structure_name]
        elif data_structure_name is None:
            # output to interface or shell
            if self.gui_use_interface:
                self.gui_output_textbox.insert(tk.END, msg + "\n")
            print(msg,flush=True)

        if listbox is None: return
        # internal data output
        # insert item sorted by priority
        if self.gui_use_internal_data:
            if listbox is self.gui_event_buffer_listbox:
                idx_to_insert = tk.END
            else:
                string_list = listbox.get(0, tk.END)  # get all items in the listbox
                msg_priority = msg[msg.find(self.GUI_BUDGET_SYMBOL) + 1:msg.rfind(
                    self.GUI_BUDGET_SYMBOL)]
                idx_to_insert = tk.END  # by default insert at the end
                i = 0
                for row in string_list:
                    row_priority = row[row.find(self.GUI_BUDGET_SYMBOL) + 1:row.rfind(
                        self.GUI_BUDGET_SYMBOL)]
                    if float(msg_priority) > float(row_priority):
                        idx_to_insert = i
                        break
                    i += 1

            listbox.insert(idx_to_insert, msg)
            self.update_datastructure_labels(data_structure_name)

    def remove_from_output(self, msg, data_structure_name=None):
        """
            Remove a message from an output GUI box
        """
        if data_structure_name is not None and data_structure_name in self.dict_listboxes:
            listbox = self.dict_listboxes[data_structure_name]
        else:
            assert False,'ERROR: Data structure name invalid ' + data_structure_name

        string_list = listbox.get(0, tk.END)
        msg_id = msg[len(Global.Global.MARKER_ITEM_ID):msg.rfind(
            Global.Global.MARKER_ID_END)]  # assuming ID is at the beginning, get characters from ID: to first spacebar
        idx_to_remove = -1
        i = 0
        for row in string_list:
            row_id = row[len(Global.Global.MARKER_ITEM_ID):row.rfind(Global.Global.MARKER_ID_END)]
            if msg_id == row_id:
                idx_to_remove = i
                break
            i = i + 1

        if idx_to_remove == -1:
            assert False, "GUI Error: cannot find msg to remove: " + msg

        listbox.delete(idx_to_remove)
        self.update_datastructure_labels(data_structure_name)

    def update_datastructure_labels(self, data_structure_name, length=0):
        assert data_structure_name is not None, "Cannot update label for Null data structure!"
        label_txt = ""
        label = None

        listbox = self.dict_listboxes[data_structure_name]
        if listbox is self.gui_experience_buffer_listbox:
            label_txt = "Experience Task "
            label = self.gui_experience_buffer_output_label
        elif listbox is self.gui_memory_listbox:
            label_txt = "Memory - Concepts "
            label = self.gui_concepts_bag_output_label
        elif listbox is self.gui_event_buffer_listbox:
            label = self.gui_event_buffer_output_label

        if label is None: return
        label.config(
            text=(label_txt + type(data_structure_name).__name__ + ": " + str(length) + " / " + str(
                self.dict_listboxes[data_structure_name + "capacity"])))

    def clear_output_gui(self, data_structure_name=None):
        if self.dict_listboxes[data_structure_name] == self.gui_memory_listbox:
            self.gui_memory_listbox.delete(0, tk.END)

    def execute_gui(self,gui_use_interface,gui_use_internal_data,data_structure_names,data_structure_capacities,pipe_gui_objects,pipe_gui_strings):
        """
            Setup and run 2 windows on a single thread
        """
        internal_data_dimensions = "1000x500"
        self.gui_object_pipe = pipe_gui_objects
        self.gui_string_pipe = pipe_gui_strings
        self.gui_use_interface = gui_use_interface
        self.gui_use_internal_data = gui_use_internal_data

        if self.gui_use_interface:
            # launch internal data GUI
            window = tk.Tk()
            window.title("NARS in Python - Interface")
            window.geometry('750x500')
            self.execute_interface_gui(window)

            if self.gui_use_internal_data:
                # launch GUI
                toplevel = tk.Toplevel()
                toplevel.title("NARS in Python - Internal Data")
                toplevel.geometry(internal_data_dimensions)
                self.execute_internal_gui(toplevel,data_structure_names,data_structure_capacities)
        elif not self.gui_use_interface and self.gui_use_internal_data:
            # launch GUI
            window = tk.Tk()
            window.title("NARS in Python - Internal Data")
            window.geometry(internal_data_dimensions)
            self.execute_internal_gui(window)

        # main GUI loop
        def handle_pipes(self):
            while self.gui_string_pipe.poll():  # check if there are messages to be received
                (command, msg, data_structure_name) = self.gui_string_pipe.recv()
                if command == "print":
                    self.print_to_output(msg=msg, data_structure_name=data_structure_name)
                elif command == "remove":
                    self.remove_from_output(msg=msg, data_structure_name=data_structure_name)
                elif command == "clear":
                    self.clear_output_gui(data_structure_name=data_structure_name)
                elif command == "paused":
                    self.set_paused(msg)
                elif command == "cycles":
                    self.gui_total_cycles_stringvar.set(msg)

            window.after(1, handle_pipes,self)  # todo call multiple times

        window.after(1, handle_pipes,self) #todo call multiple times
        pipe_gui_objects.send('ready')
        window.mainloop()


    def set_paused(self, paused):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        if not self.gui_use_interface: return
        self.paused = paused
        if self.paused:
            self.gui_play_pause_button.config(text="PLAY")
        else:
            self.gui_play_pause_button.config(text="PAUSE")

    def toggle_paused(self):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        self.set_paused(not self.paused)
        self.gui_string_pipe.send(("paused", self.paused))

    def execute_internal_gui(self,window,data_structure_names,data_structure_capacities):
        """
            Setup the internal GUI window, displaying the system's buffers and memory
        """
        listbox_height = 30
        listbox_width = 80

        (experience_task_buffer_name, event_buffer_name, memory_bag_name) = data_structure_names
        """
            Event buffer internal contents GUI
        """
        self.gui_event_buffer_output_label = tk.Label(window)
        self.gui_event_buffer_output_label.grid(row=0, column=0, sticky='w')

        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=1, column=2, sticky='ns')
        self.gui_event_buffer_listbox = tk.Listbox(window,
                                                  height=listbox_height//3,
                                                  width=listbox_width, font=('', 8),
                                                  yscrollcommand=buffer_scrollbar.set)
        self.gui_event_buffer_listbox.grid(row=1, column=0, columnspan=1)
        self.dict_listboxes[event_buffer_name] = self.gui_event_buffer_listbox

        """
            Experience Buffer internal contents GUI
        """
        self.gui_experience_buffer_output_label = tk.Label(window)
        self.gui_experience_buffer_output_label.grid(row=2, column=0, sticky='w')

        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=3, column=2, sticky='ns')
        self.gui_experience_buffer_listbox = tk.Listbox(window,
                                                       height=2*listbox_height//3,
                                                       width=listbox_width, font=('', 8),
                                                       yscrollcommand=buffer_scrollbar.set)
        self.gui_experience_buffer_listbox.grid(row=3, column=0, columnspan=1)
        self.dict_listboxes[experience_task_buffer_name] = self.gui_experience_buffer_listbox

        """
            Memory internal contents GUI
        """
        self.gui_concepts_bag_output_label = tk.Label(window)
        self.gui_concepts_bag_output_label.grid(row=0,
                                                column=3,
                                                sticky='w')

        concept_bag_scrollbar = tk.Scrollbar(window)
        concept_bag_scrollbar.grid(row=1,
                                   column=5,
                                   rowspan=4,
                                   sticky='ns')
        self.gui_memory_listbox = tk.Listbox(window,
                                            height=listbox_height,
                                            width=listbox_width,
                                            font=('', 8),
                                            yscrollcommand=concept_bag_scrollbar.set)
        self.gui_memory_listbox.grid(row=1,
                                    column=3,
                                    columnspan=1,
                                    rowspan=4)
        self.dict_listboxes[memory_bag_name] = self.gui_memory_listbox

        # define callbacks when clicking items in any box
        self.gui_memory_listbox.bind("<<ListboxSelect>>", self.listbox_datastructure_item_click_callback)
        self.gui_experience_buffer_listbox.bind("<<ListboxSelect>>", self.listbox_datastructure_item_click_callback)

        for i,name in enumerate(data_structure_names):
            self.dict_listboxes[name + "capacity"] = data_structure_capacities[i]
            if i == len(data_structure_names) - 1:
                # final name is the memory
                length = 1 # system starts with self concept
            else:
                length = 0
            self.update_datastructure_labels(name,length)


    def execute_interface_gui(self,window):
        """
            Setup the interface GUI window, displaying the system's i/o channels
        """
        output_width = 3
        output_height = 3

        # row 0
        output_lbl = tk.Label(window, text="Output: ")
        output_lbl.grid(row=0, column=0, columnspan=output_width)

        # row 1
        output_scrollbar = tk.Scrollbar(window)
        output_scrollbar.grid(row=1, column=3, rowspan=output_height, sticky='ns')

        self.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
        self.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

        # row 2
        self.gui_total_cycles_stringvar = tk.StringVar()
        self.gui_total_cycles_stringvar.set("Cycle #0")
        self.gui_total_cycles_lbl = tk.Label(window, textvariable=self.gui_total_cycles_stringvar)
        self.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

        speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
        speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

        self.gui_play_pause_button = tk.Button(window, text="", command=self.toggle_paused)
        self.gui_play_pause_button.grid(row=3, column=4, sticky='s')

        max_delay = 1000  # in milliseconds
        gui_delay_slider = tk.Scale(window, from_=max_delay, to=0)
        self.gui_delay_slider = gui_delay_slider
        self.gui_delay_slider.grid(row=3, column=5, sticky='ns')

        strings_pipe = self.gui_string_pipe

        def delay_slider_changed(event=None):
            strings_pipe.send(("delay", gui_delay_slider.get() / 1000))

        self.gui_delay_slider.bind('<ButtonRelease-1>',delay_slider_changed)
        self.gui_delay_slider.set(max_delay)
        delay_slider_changed() # set delay to max value


        # input GUI
        def input_clicked(event=None):
            """
                Callback when clicking button to send input
            """
            # put input into NARS input buffer
            userinput = input_field.get(index1=1.0, index2=tk.END)
            strings_pipe.send(("userinput", userinput)) # send user input to NARS
            input_field.delete(1.0, tk.END) # empty input field

        input_lbl = tk.Label(window, text="Input: ")
        input_lbl.grid(column=0, row=4)

        input_field = tk.Text(window, width=50, height=4)
        input_field.grid(column=1, row=4)
        input_field.focus()

        send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)  # send input when click button
        send_input_btn.grid(column=2, row=4)

        window.focus()

    def listbox_sentence_item_click_callback(self,event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            sentence_string = event.widget.get(index)
            self.gui_object_pipe.send(("getsentence", sentence_string, None))
            sentence = self.gui_object_pipe.recv()
            if sentence is not None:
                self.draw_sentence_internal_data(sentence)

    def draw_sentence_internal_data(self, sentence_to_draw):
        item_info_window = tk.Toplevel()
        item_info_window.title("Sentence Internal Data: " + sentence_to_draw[NARSGUI.KEY_STRING])
        is_array = sentence_to_draw[NARSGUI.KEY_IS_ARRAY]
        if is_array:
            item_info_window.geometry('1100x500')
        else:
            item_info_window.geometry('1000x500')

        object_listbox_width = 60
        object_listbox_height = 20

        rownum = 0

        # sentence
        label = tk.Label(item_info_window, text="Sentence: ")
        label.grid(row=rownum, column=0)

        label = tk.Label(item_info_window, text=sentence_to_draw[NARSGUI.KEY_STRING_NOID])
        label.grid(row=rownum, column=1)

        # sentence ID
        rownum += 1
        label = tk.Label(item_info_window, text="Sentence ID: ")
        label.grid(row=rownum, column=0)

        label = tk.Label(item_info_window, text=sentence_to_draw[NARSGUI.KEY_ID])
        label.grid(row=rownum, column=1)

        # sentence occurrence time
        rownum += 1
        label = tk.Label(item_info_window, text="Occurrence Time: ")
        label.grid(row=rownum, column=0)

        oc_time = sentence_to_draw[NARSGUI.KEY_OCCURRENCE_TIME]

        label = tk.Label(item_info_window, text=str("Eternal" if oc_time is None else oc_time))
        label.grid(row=rownum, column=1)

        # sentence type
        rownum += 1
        label = tk.Label(item_info_window, text="Sentence Type: ")
        label.grid(row=rownum, column=0)

        label = tk.Label(item_info_window, text=sentence_to_draw[NARSGUI.KEY_SENTENCE_TYPE])
        label.grid(row=rownum, column=1)

        # sentence type
        rownum += 1
        label = tk.Label(item_info_window, text="Derived By: ")
        label.grid(row=rownum, column=0)

        label = tk.Label(item_info_window, text=sentence_to_draw[NARSGUI.KEY_DERIVED_BY])
        label.grid(row=rownum, column=1)

        # blank
        rownum += 1
        label = tk.Label(item_info_window, text="")
        label.grid(row=rownum, column=1)

        # Listbox labels
        rownum += 1
        label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
        label.grid(row=rownum, column=0, columnspan=2)

        label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
        label.grid(row=rownum, column=2, columnspan=2)

        # Evidential base listbox
        evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                             width=object_listbox_width, font=('', 8))
        evidential_base_listbox.grid(row=rownum + 1, column=0, columnspan=2)

        for sentence in sentence_to_draw[NARSGUI.KEY_LIST_EVIDENTIAL_BASE]:
            evidential_base_listbox.insert(tk.END, str(sentence))
        evidential_base_listbox.bind("<<ListboxSelect>>",
                                     lambda event: self.listbox_sentence_item_click_callback(event))

        # Interacted sentences listbox
        interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                  width=object_listbox_width, font=('', 8))
        interacted_sentences_listbox.grid(row=rownum + 1, column=2, columnspan=2)
        for sentence in sentence_to_draw[NARSGUI.KEY_LIST_INTERACTED_SENTENCES]:
            interacted_sentences_listbox.insert(tk.END, str(sentence))
        interacted_sentences_listbox.bind("<<ListboxSelect>>",
                                          lambda event: self.listbox_sentence_item_click_callback(event))
        MAX_IMAGE_SIZE = 2000
        image_array = sentence_to_draw[NARSGUI.KEY_ARRAY_IMAGE]
        if is_array and image_array is not None:
            # reset image size to defaults
            self.gui_array_image_dimensions[0] = 300
            self.gui_array_image_dimensions[1] = 300

            # Percept elements label
            label = tk.Label(item_info_window, text="Array Visualization (scroll to zoom in/out)", font=('bold'))
            label.grid(row=rownum, column=4, columnspan=2)

            if not Config.ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS:
                """
                    Array - Draw entire image (faster)
                """
                image_array = image_array.T
                # create image frame
                image_frame = tk.Frame(item_info_window, width=MAX_IMAGE_SIZE, height=MAX_IMAGE_SIZE,
                                       name="array image frame")
                image_frame.grid(row=rownum + 1, column=4, columnspan=2, rowspan=2)

                # create image
                gui_array_image_dimensions = self.gui_array_image_dimensions

                # render = ImageTk.PhotoImage()
                img_container = tk.Label(image_frame, image=None)
                img_container.grid(row=rownum + 1, column=4, columnspan=2, rowspan=2)

                def zoom_image_array(event):
                    # zoom the image array depending on how the user scrolled
                    if event is None:
                        offset = 0  # initialize
                    else:
                        offset = 3 if event.delta > 0 else -3
                    pil_image = Image.fromarray(image_array)
                    gui_array_image_dimensions[0] += offset
                    if gui_array_image_dimensions[0] < 1: gui_array_image_dimensions[0] = 1
                    gui_array_image_dimensions[1] += offset
                    if gui_array_image_dimensions[1] < 1: gui_array_image_dimensions[1] = 1
                    pil_image = pil_image.resize(gui_array_image_dimensions, resample=Image.NEAREST)
                    render = ImageTk.PhotoImage(pil_image)
                    img_container.config(image=render)
                    img_container.image = render

                image_frame.bind_all("<MouseWheel>", zoom_image_array)
                zoom_image_array(None)
            else:
                """
                    Array - Draw Individual Cells (slower)
                """
                PIXEL_SIZE_PER_ELEMENT = 300 / image_array.shape[0]
                if PIXEL_SIZE_PER_ELEMENT < 1: PIXEL_SIZE_PER_ELEMENT = 1  # minimum size 1 pixel

                image_frame = tk.Frame(item_info_window, width=MAX_IMAGE_SIZE, height=MAX_IMAGE_SIZE,
                                       name="array image frame")
                image_frame.grid(row=rownum + 1, column=4, columnspan=2, rowspan=2)

                def zoom_image_array(event):
                    # zoom the image array depending on how the user scrolled
                    offset = 1 if event.delta > 0 else -1
                    for child in image_frame.winfo_children():
                        child.config(width=child.winfo_width() + offset,
                                     height=child.winfo_height() + offset)

                image_frame.bind_all("<MouseWheel>", zoom_image_array)

                def create_array_element_click_lambda(sentence):
                    return None #lambda: self.draw_sentence_internal_data(sentence) #todo

                # iterate over each element and draw a pixel for it
                if len(image_array.shape) == 2:
                    for (x,y), pixel_value in np.ndenumerate(image_array):
                        f = tk.Frame(image_frame, width=PIXEL_SIZE_PER_ELEMENT,
                                     height=PIXEL_SIZE_PER_ELEMENT)
                        f.grid(row=y, column=x, columnspan=1, rowspan=1)
                        f.rowconfigure(0, weight=1)
                        f.columnconfigure(0, weight=1)
                        f.grid_propagate(0)

                        color = from_rgb_to_tkinter_color((pixel_value, pixel_value, pixel_value))
                        element_string = sentence_to_draw[NARSGUI.KEY_ARRAY_ELEMENT_STRINGS][x,y]
                        button = tk.Button(f, bg=color,
                                           command=create_array_element_click_lambda(element_string))
                        button.config(relief='solid', borderwidth=0)
                        button.grid(sticky="NWSE")
                        CreateToolTip(button, text=(element_string))
                if len(image_array.shape) == 3:
                    #todo draw rgb
                    pass

            self.gui_array_image_frame = image_frame

    def listbox_datastructure_item_click_callback(self,event):
        """
            Presents a window describing the clicked data structure's item's internal data.
            Locks the interface until the window is closed.

            This function is called when the user clicks on an item in the internal data.
        """
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            item_string = event.widget.get(index)

            data_structure_name = ""
            if event.widget is self.gui_memory_listbox:
                ID = item_string[item_string.rfind(Global.Global.MARKER_ID_END) + len(Global.Global.MARKER_ID_END):item_string.find(
                    self.GUI_BUDGET_SYMBOL) - 1]  # remove ID and priority, concept term string is the key
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_memory_listbox)
            elif event.widget is self.gui_experience_buffer_listbox:
                ID = item_string[item_string.find(Global.Global.MARKER_ITEM_ID) + len(
                    Global.Global.MARKER_ITEM_ID):item_string.rfind(Global.Global.MARKER_ID_END)]
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_experience_buffer_listbox)
                ID = int(ID)
            else:
                # clicked concept within another concept
                ID = item_string
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_memory_listbox)
            self.gui_object_pipe.send(("getitem", ID, data_structure_name))
            item = self.gui_object_pipe.recv()

            if item is None:
                self.print_to_output("ERROR: could not get item with key: " + ID)
                return

            classname = item[NARSGUI.KEY_CLASS_NAME]
            assert classname == NARSMemory.Concept.__name__ or classname == NARSDataStructures.Task.__name__, "ERROR: Data Structure clickback only defined for Concept and Task"

            # window
            item_info_window = tk.Toplevel()
            item_info_window.title(classname + " Internal Data: " + item_string)
            item_info_window.geometry('1100x700')
            #item_info_window.grab_set()  # lock the other windows until this window is exited

            row_num = 0

            # name
            label = tk.Label(item_info_window, text=classname + " Name: ")
            label.grid(row=row_num, column=0)

            label = tk.Label(item_info_window, text=item[NARSGUI.KEY_OBJECT_STRING])
            label.grid(row=row_num, column=1)

            # term type
            row_num += 1
            label = tk.Label(item_info_window, text="Term Type: ")
            label.grid(row=row_num, column=0)

            label = tk.Label(item_info_window, text=item[NARSGUI.KEY_TERM_TYPE])
            label.grid(row=row_num, column=1)

            object_listbox_width = 60
            object_listbox_height = 20

            row_num += 1
            if classname == NARSMemory.Concept.__name__:
                label = tk.Label(item_info_window, text="", justify=tk.LEFT)
                label.grid(row=row_num, column=0)

                # Row 1
                # beliefs table listbox
                beliefs_capacity_text = "("+str(len(item[NARSGUI.KEY_LIST_BELIEFS])) + "/" + item[NARSGUI.KEY_CAPACITY_BELIEFS] +")"
                label = tk.Label(item_info_window, text="Beliefs " + beliefs_capacity_text, font=('bold'))
                label.grid(row=row_num, column=0, columnspan=2)

                belief_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                            font=('', 8))

                belief_listbox.grid(row=row_num+1, column=0, columnspan=2)
                for belief in item["ListBeliefs"]:
                    belief_listbox.insert(tk.END, belief)

                belief_listbox.bind("<<ListboxSelect>>", lambda event: self.listbox_sentence_item_click_callback(event))  # define callbac
                # desires table listbox
                desires_capacity_text = "("+str(len(item[NARSGUI.KEY_LIST_DESIRES])) + "/" + item[NARSGUI.KEY_CAPACITY_DESIRES] +")"
                label = tk.Label(item_info_window, text="Desires " + desires_capacity_text, font=('bold'))
                label.grid(row=row_num, column=2, columnspan=2)

                desire_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                            font=('', 8))
                desire_listbox.grid(row=row_num+1, column=2, columnspan=2)
                for desire in item[NARSGUI.KEY_LIST_DESIRES]:
                    desire_listbox.insert(tk.END, desire)
                desire_listbox.bind("<<ListboxSelect>>", lambda event: self.listbox_sentence_item_click_callback(event))  # define callback
                # Term Links listbox
                term_links_text = "(" + str(len(item[NARSGUI.KEY_LIST_TERM_LINKS])) + ")"
                label = tk.Label(item_info_window, text="Term Links " + term_links_text, font=('bold'))
                label.grid(row=row_num, column=4, columnspan=2)

                termlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                            font=('', 8))
                termlinks_listbox.grid(row=row_num+1, column=4, columnspan=2)
                for term_link in item[NARSGUI.KEY_LIST_TERM_LINKS]:
                    termlinks_listbox.insert(tk.END, term_link)
                termlinks_listbox.bind("<<ListboxSelect>>", lambda event: self.listbox_datastructure_item_click_callback(event))

                # Row 2 Listbox labels
                row_num += 2

                # Prediction Links Listbox
                prediction_links_text = "(" + str(len(item[NARSGUI.KEY_LIST_PREDICTION_LINKS])) + ")"
                label = tk.Label(item_info_window, text="Prediction Links " + prediction_links_text, font=('bold'))
                label.grid(row=row_num, column=0, columnspan=2)

                predictionlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                            font=('', 8))
                predictionlinks_listbox.grid(row=row_num+1, column=0, columnspan=2)
                for prediction_link in item[NARSGUI.KEY_LIST_PREDICTION_LINKS]:
                    predictionlinks_listbox.insert(tk.END, prediction_link)
                predictionlinks_listbox.bind("<<ListboxSelect>>", lambda event: self.listbox_datastructure_item_click_callback(event))

                # Explanation Links Listbox
                explanation_links_text = "(" + str(len(item[NARSGUI.KEY_LIST_EXPLANATION_LINKS])) + ")"
                label = tk.Label(item_info_window, text="Explanation Links " + explanation_links_text, font=('bold'))
                label.grid(row=row_num, column=2, columnspan=2)

                explanationlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                     width=object_listbox_width,
                                                     font=('', 8))
                explanationlinks_listbox.grid(row=row_num+1, column=2, columnspan=2)
                for explanation_link in item[NARSGUI.KEY_LIST_EXPLANATION_LINKS]:
                    explanationlinks_listbox.insert(tk.END, explanation_link)
                explanationlinks_listbox.bind("<<ListboxSelect>>",
                                             lambda event: self.listbox_datastructure_item_click_callback(event))

            elif classname == NARSDataStructures.Task.__name__:
                # Evidential base listbox
                label = tk.Label(item_info_window, text="Sentence: ", justify=tk.LEFT)
                label.grid(row=row_num, column=0)

                labelClickable = tk.Listbox(item_info_window, height=1)
                labelClickable.insert(tk.END, item["SentenceString"])
                labelClickable.grid(row=row_num, column=1)
                labelClickable.bind("<<ListboxSelect>>",
                                    lambda event: self.listbox_sentence_item_click_callback(event))

                row_num += 1
                label = tk.Label(item_info_window, text="", justify=tk.LEFT)
                label.grid(row=row_num, column=0)

                # Listbox labels
                row_num += 1

                # Evidential base listbox
                label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
                label.grid(row=row_num, column=0, columnspan=2)

                evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                     width=object_listbox_width, font=('', 8))
                evidential_base_listbox.grid(row=row_num+1, column=0, columnspan=2)
                for sentence in item["ListEvidentialBase"]:
                    evidential_base_listbox.insert(tk.END, sentence)
                evidential_base_listbox.bind("<<ListboxSelect>>", lambda event: self.listbox_sentence_item_click_callback(event))
                # Interacted sentences listbox
                label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
                label.grid(row=row_num, column=2, columnspan=2)

                interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                          width=object_listbox_width, font=('', 8))
                interacted_sentences_listbox.grid(row=row_num+1, column=2, columnspan=2)
                for sentence in item["ListInteractedSentences"]:
                    interacted_sentences_listbox.insert(tk.END, sentence)
                interacted_sentences_listbox.bind("<<ListboxSelect>>",
                                                  lambda event: self.listbox_sentence_item_click_callback(event))

    def get_data_structure_name_from_listbox(self,listbox):
        keys = list(self.dict_listboxes.keys())
        values = list(self.dict_listboxes.values())
        return keys[values.index(listbox)]

def start_gui(gui_use_internal_data, gui_use_interface, data_structure_names,data_structure_capacities,pipe_gui_objects,
                                            pipe_gui_strings):
    gui = NARSGUI()
    gui.execute_gui(gui_use_internal_data, gui_use_interface, data_structure_names,
                                            data_structure_capacities,
                                            pipe_gui_objects,
                                           pipe_gui_strings)


def from_rgb_to_tkinter_color(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb


# from https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.color = widget.cget('bg')
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.widget.config(bg="yellow",borderwidth=1)
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        self.widget.config(bg=self.color, borderwidth=0)
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)