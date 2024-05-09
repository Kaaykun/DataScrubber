# Import libraries
import sys
sys.path.append('../src')

import os
basedir = os.path.dirname(__file__)

import tkinter as tk
import customtkinter as ck
from CTkMessagebox import CTkMessagebox
from src.cleaning_rawdata import main as clean_rawdata
from src.cleaning_customer import main as clean_customer
from src.cleaning_all_rawdata import main as clean_all
from src.create_readership import main as create_readership
from src.params import PUBLISHERS, CUSTOMERS

########################################################################################################################

ck.set_appearance_mode("light")
ck.set_default_color_theme("blue")

########################################################################################################################

class PrecleanRawData(ck.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Preclean Raw Data")
        self.wm_iconbitmap(os.path.join(basedir, 'assets', 'example.ico'))
        self.geometry(f"800x600+{parent.winfo_x()-150}+{parent.winfo_y()-100}")
        self.publisher = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        def combobox_callback(selected_publisher):
            self.publisher.set(selected_publisher)
            print("Selected Publisher:", self.publisher.get())

        self.combobox = ck.CTkComboBox(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            dropdown_font=("Arial", 20),
            values=list(PUBLISHERS.keys()),
            command=combobox_callback
        )
        self.combobox.pack(padx=20, pady=10)
        self.combobox.set("Select Publisher")

        self.button = ck.CTkButton(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            text="Clean Data",
            command=self.button_event
        )
        self.button.place(relx=0.5, rely=0.8, anchor="center")

    def show_busy_indicator(self):
        self.processing_label = ck.CTkLabel(
            master=self,
            text="Processing...",
            font=("Arial", 20)
        )
        self.processing_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()  # Force update to display the label

    def remove_busy_indicator(self):
        self.processing_label.destroy()

    def button_event(self):
        try:
            self.show_busy_indicator()  # Show busy indicator before processing
            self.update_idletasks()  # Force update to display the busy indicator
            clean_rawdata(self.publisher.get())
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Success",
                message="Data was cleaned successfully.",
                font=("Arial", 20),
                icon="check",
                option_1="OK")
        except KeyError:
            error_message = "Please select a publisher and try again."
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {error_message}",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
        except Exception as e:
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {repr(e)}, please contact an admin.",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
            
########################################################################################################################

class CleanCustomerData(ck.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Clean Customer Data")
        self.wm_iconbitmap(os.path.join(basedir, 'assets', 'example.ico'))
        self.geometry(f"800x600+{parent.winfo_x()-150}+{parent.winfo_y()-100}")

        self.publisher = tk.StringVar()
        self.customer = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        def combobox_callback_publisher(selected_publisher):
            self.publisher.set(selected_publisher)
            print("Selected Publisher:", self.publisher.get())

        def combobox_callback_customer(selected_customer):
            self.customer.set(selected_customer)
            print("Selected Customer:", self.customer.get())

        self.create_combobox("Select Publisher", 0.1, PUBLISHERS, combobox_callback_publisher)
        self.create_combobox("Select Customer", 0.2, CUSTOMERS, combobox_callback_customer)

    def create_combobox(self, text, rely, value, command):
        self.combobox = ck.CTkComboBox(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            dropdown_font=("Arial", 20),
            values=list(value.keys()),
            command=command
        )
        self.combobox.pack(padx=20, pady=10)
        self.combobox.place(relx=0.5, rely=rely, anchor="center")
        self.combobox.set(f"Select {text}")

        self.button = ck.CTkButton(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            text="Clean Data",
            command=self.button_event
        )
        self.button.place(relx=0.5, rely=0.8, anchor="center")

    def show_busy_indicator(self):
        self.processing_label = ck.CTkLabel(
            master=self,
            text="Processing...",
            font=("Arial", 20)
        )
        self.processing_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()  # Force update to display the label

    def remove_busy_indicator(self):
        self.processing_label.destroy()

    def button_event(self):
        try:
            self.show_busy_indicator()  # Show busy indicator before processing
            self.update_idletasks()  # Force update to display the busy indicator
            clean_customer(self.publisher.get(), self.customer.get())
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Success",
                message="Data was cleaned successfully.",
                font=("Arial", 20),
                icon="check",
                option_1="OK")
        except KeyError:
            error_message = "Please select a publisher and try again."
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {error_message}",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
        except Exception as e:
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {repr(e)}, please contact an admin.",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
            
########################################################################################################################

class CleanAll(ck.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Clean Data for all Publishers and Customers")
        # self.wm_iconbitmap()
        # self.after(300, lambda: self.iconphoto(False, parent.icon_path))
        self.wm_iconbitmap(os.path.join(basedir, 'assets', 'example.ico'))
        self.geometry(f"800x600+{parent.winfo_x()-150}+{parent.winfo_y()-100}")
        self.publisher = tk.StringVar()

        self.create_widgets()
        self.create_label()

    def create_label(self):
        self.label = ck.CTkLabel(
            master=self,
            text="This cleaning process takes multiple minutes.",
            font=("Arial", 24)
        )
        self.label.place(relx=0.5, rely=0.7, anchor="center")

    def create_widgets(self):
        self.button = ck.CTkButton(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            text="Clean Data",
            command=self.button_event
        )
        self.button.place(relx=0.5, rely=0.8, anchor="center")

    def show_busy_indicator(self):
        self.processing_label = ck.CTkLabel(
            master=self,
            text="Processing...",
            font=("Arial", 20)
        )
        self.processing_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()  # Force update to display the label

    def remove_busy_indicator(self):
        self.processing_label.destroy()

    def button_event(self):
        try:
            self.show_busy_indicator()  # Show busy indicator before processing
            self.update_idletasks()  # Force update to display the busy indicator
            clean_all()
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Success",
                message="Data was cleaned successfully.",
                font=("Arial", 20),
                icon="check",
                option_1="OK")
        except KeyError:
            error_message = "Please select a publisher and try again."
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {error_message}",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
        except Exception as e:
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {repr(e)}, please contact an admin.",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")

########################################################################################################################

class CreateReadership(ck.CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Create Readership File for all Customers")
        self.wm_iconbitmap(os.path.join(basedir, 'assets', 'example.ico'))
        self.geometry(f"800x600+{parent.winfo_x()-150}+{parent.winfo_y()-100}")

        self.create_widgets()

    def create_widgets(self):
        self.button = ck.CTkButton(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            text="Create Readership Files",
            command=self.button_event
        )
        self.button.place(relx=0.5, rely=0.8, anchor="center")

    def show_busy_indicator(self):
        self.processing_label = ck.CTkLabel(
            master=self,
            text="Processing...",
            font=("Arial", 20)
        )
        self.processing_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()  # Force update to display the label

    def remove_busy_indicator(self):
        self.processing_label.destroy()

    def button_event(self):
        try:
            self.show_busy_indicator()  # Show busy indicator before processing
            self.update_idletasks()  # Force update to display the busy indicator
            create_readership()
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Success",
                message="Readership Files created successfully.",
                font=("Arial", 20),
                icon="check",
                option_1="OK")
        except KeyError:
            error_message = "Something went wrong. Please check the Clean Files and try again."
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {error_message}",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")
        except Exception as e:
            self.remove_busy_indicator()
            CTkMessagebox(
                title="Error",
                message=f"An error occurred: {repr(e)}, please contact an admin.",
                font=("Arial", 20),
                icon="cancel",
                option_1="OK")

########################################################################################################################

class App(ck.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wm_iconbitmap(os.path.join(basedir, 'assets', 'example.ico'))

        self.title("DataScrubber")
        self.geometry("500x400")

        self.create_widgets()

        self.toplevel_window = None

    def create_widgets(self):
        self.create_button("Clean specific Publisher", 0.2, self.open_preclean_raw_data)
        self.create_button("Clean specifc Customer", 0.4, self.open_clean_customer_data)
        self.create_button("Clean all Publishers & Customers", 0.6, self.open_clean_raw_all)
        self.create_button("Create Readership File for all Customers", 0.8, self.open_create_readership)

    def create_button(self, text, rely, command):
        button = ck.CTkButton(
            master=self,
            width=400,
            height=40,
            font=("Arial", 20),
            text=text,
            command=command
        )
        button.place(relx=0.5, rely=rely, anchor="center")

    def open_preclean_raw_data(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = PrecleanRawData(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it

    def open_clean_customer_data(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = CleanCustomerData(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it

    def open_clean_raw_all(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = CleanAll(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it
            
    def open_create_readership(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = CreateReadership(self) # create window if its None or destroyed
        else:
            self.toplevel_window.focus() # if window exists focus it

app = App()
app.mainloop()
