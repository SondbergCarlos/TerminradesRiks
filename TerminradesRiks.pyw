import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import requests
from bs4 import BeautifulSoup
import os
import json

def open_links_dropdown_focus(event=None):
    with open('open_links.json', 'r') as open_links_file:
        open_links_data = json.load(open_links_file)
    
    open_categories = list(open_links_data.keys())
    open_category_combobox['values'] = open_categories

def retrieve_explanation_dropdown_focus(event=None):
    with open('retrieve_explanation.json', 'r') as retrieve_explanation_file:
        retrieve_explanation_data = json.load(retrieve_explanation_file)
    
    retrieve_categories = list(retrieve_explanation_data.keys())
    retrieve_category_combobox['values'] = retrieve_categories

def retrieve(category_var, word_entry, result_text, save_checkbox, open_links, retrieve_explanation):
    category = category_var.get()
    word = word_entry.get()

    if category and word:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        
        if category in open_links:
            open_links_in_browser(word, open_links[category])
        elif category in retrieve_explanation:
            for site_info in retrieve_explanation[category]:
                result_text.insert(tk.END, f"Site: {site_info.get('name', '')}\n")
                result_text.insert(tk.END, f"Link: {site_info.get('link_prototype', '').format(word)}\n")
                meanings = search_meaning(word, [site_info])
                if meanings:
                    result_text.insert(tk.END, '\n'.join(meanings))
                else:
                    result_text.insert(tk.END, "No results found")
                result_text.insert(tk.END, "\n\n")
        else:
            result_text.insert(tk.END, "Invalid category")

        result_text.config(state=tk.DISABLED)

        if save_checkbox.get():
            save_to_file(word, result_text.get("1.0", tk.END))
    else:
        result_text.insert(tk.END, "Lūdzu izvēlaties sarakstu un ievadiet meklējamo vārdu")
        result_text.config(state=tk.DISABLED)

def open_links_in_browser(word, links_list):
    for link_info in links_list:
        if isinstance(link_info, dict) and 'link_prototype' in link_info:
            link_template = link_info['link_prototype']
            if isinstance(link_template, str):
                url = link_template.format(word)
                webbrowser.open(url)
            else:
                print(f"Invalid link template: {link_template}")
        else:
            print(f"Invalid link info: {link_info}")

def fetch_meaning(word, site_info_list):
    try:
        if isinstance(site_info_list, list) and site_info_list:
            site_info = site_info_list[0]
        else:
            return "Invalid site information"

        url = site_info.get("link_prototype", "").format(word)
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            if "id_prefix" in site_info:
                id_prefix = site_info["id_prefix"]
                meaning_elements = [soup.find("span", id=lambda x: x and x.startswith(id_prefix + str(i))) for i in range(100)]
                meanings = [element.get_text() for element in meaning_elements if element]

            else:
                meaning_elements = soup.find_all(site_info.get("section", ""), class_=site_info.get("class_name", ""))
                meanings = [element.get_text() for element in meaning_elements]

            if meanings:
                return '\n'.join(meanings)
            else:
                return f"No results from {site_info.get('name', '')}."

        else:
            return f"Failed to retrieve data from {site_info.get('name', '')}"
    except Exception as e:
        return str(e)

def search_meaning(word, site_list):
    word_to_search = word

    meanings = []
    for site_info in site_list:
        if isinstance(site_info, dict):  # Check if site_info is a dictionary
            meaning = fetch_meaning(word_to_search, [site_info])  # Wrap site_info in a list
            print(f"Site Name: {site_info.get('name', '')}")
            print(f"Link: {site_info.get('link_prototype', '').format(word_to_search)}")
            print(f"Meaning:")
            if meaning:
                print(meaning)
                meanings.append(meaning)
            else:
                print("No results found")
            print("\n")

    return meanings

def save_to_file(word, content):
    if not os.path.exists("results"):
        os.makedirs("results")

    file_path = os.path.join("results", f"{word}.txt")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        messagebox.showinfo("File Saved", f"Rezultāti saglabāti apakšmapē {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda saglabājot rezultātus: {str(e)}")

def add_site_to_json(file_path, category, data):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        json_data[category].append(data)

        with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=4)
        
        messagebox.showinfo("Success", "Avots veiksmīgi pievienots!")
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")

def add_site_to_open_links():
    site_name = open_links_site_name_entry.get()
    link_prototype = open_links_link_prototype_entry.get()
    selected_list = open_links_list_var.get()

    if site_name and link_prototype and selected_list:
        data = {
            "name": site_name,
            "link_prototype": link_prototype
        }
        add_site_to_json("open_links.json", selected_list, data)
    else:
        messagebox.showwarning("Warning", "Lūdzu aizpildiet visus nepieciešamos laukus.")

def add_site_to_retrieve_explanation():
    site_name = retrieve_explanation_site_name_entry.get()
    link_prototype = retrieve_explanation_link_prototype_entry.get()
    section = retrieve_explanation_section_entry.get()
    class_name = retrieve_explanation_class_name_entry.get()
    id_prefix = retrieve_explanation_id_prefix_entry.get()
    selected_list = retrieve_explanation_list_var.get()

    if class_name and id_prefix:
        messagebox.showerror("Error", "Ir nepieciešams tikai viens no Klases nosaukuma vai ID priekšdaļas")
        return

    if site_name and link_prototype and selected_list:
        if selected_list in retrieve_explanation:
            data = {"name": site_name, "link_prototype": link_prototype}
            if section:
                data["section"] = section
            if class_name:
                data["class_name"] = class_name
            elif id_prefix:
                data["id_prefix"] = id_prefix

            add_site_to_json("retrieve_explanation.json", selected_list, data)
        else:
            messagebox.showerror("Error", "Nederīgs izvēlētais saraksts")
    else:
        messagebox.showerror("Error", "Lūdzu aizpildiet visus nepieciešamos laukus.")

with open('open_links.json', 'r') as open_links_file:
    open_links = json.load(open_links_file)

with open('retrieve_explanation.json', 'r') as retrieve_explanation_file:
    retrieve_explanation = json.load(retrieve_explanation_file)

def add_new_list(list_name, category):
    if not list_name:
        messagebox.showwarning("Warning", "Lūdzu ievadiet jaunā saraksta nosaukumu.")
        return

    try:
        file_path = 'open_links.json' if category == 'open_links' else 'retrieve_explanation.json'
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        if list_name in json_data:
            messagebox.showwarning("Warning", f"Jau pastāv saraksts ar nosaukumu {list_name} .")
            return

        json_data[list_name] = []

        with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=4)

        messagebox.showinfo("Success", f"Veiksmīgi izveidots jauns saraksts '{list_name}' un tas ir pievienots kategorijai {category}!")
        
        if category == 'open_links':
            open_links_dropdown_focus()
        elif category == 'retrieve_explanation':
            retrieve_explanation_dropdown_focus()

    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")
        
def populate_item_fields(selected_list_name, selected_item_name, category):
    try:
        file_path = 'open_links.json' if category == 'open_links' else 'retrieve_explanation.json'
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        selected_list = json_data.get(selected_list_name, [])
        selected_item = next((item for item in selected_list if item.get('name') == selected_item_name), None)

        if selected_item:
            if category == 'open_links':
                open_links_site_name_entry.delete(0, tk.END)
                open_links_site_name_entry.insert(0, selected_item.get('name', ''))
                open_links_link_prototype_entry.delete(0, tk.END)
                open_links_link_prototype_entry.insert(0, selected_item.get('link_prototype', ''))
                open_links_list_combobox.set(selected_list_name)
            elif category == 'retrieve_explanation':
                retrieve_explanation_site_name_entry.delete(0, tk.END)
                retrieve_explanation_site_name_entry.insert(0, selected_item.get('name', ''))
                retrieve_explanation_link_prototype_entry.delete(0, tk.END)
                retrieve_explanation_link_prototype_entry.insert(0, selected_item.get('link_prototype', ''))
                retrieve_explanation_section_entry.delete(0, tk.END)
                retrieve_explanation_section_entry.insert(0, selected_item.get('section', ''))
                retrieve_explanation_class_name_entry.delete(0, tk.END)
                retrieve_explanation_class_name_entry.insert(0, selected_item.get('class_name', ''))
                retrieve_explanation_id_prefix_entry.delete(0, tk.END)
                retrieve_explanation_id_prefix_entry.insert(0, selected_item.get('id_prefix', ''))
                retrieve_explanation_list_combobox.set(selected_list_name)
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")

def modify_selected_item(selected_list_name, selected_item_name, category):
    try:
        file_path = 'open_links.json' if category == 'open_links' else 'retrieve_explanation.json'
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        selected_list = json_data.get(selected_list_name, [])
        selected_item_index = next((index for index, item in enumerate(selected_list) if item.get('name') == selected_item_name), None)

        if selected_item_index is not None:
            if category == 'open_links':
                selected_list[selected_item_index] = {
                    "name": open_links_site_name_entry.get(),
                    "link_prototype": open_links_link_prototype_entry.get()
                }
            elif category == 'retrieve_explanation':
                selected_list[selected_item_index] = {
                    "name": retrieve_explanation_site_name_entry.get(),
                    "link_prototype": retrieve_explanation_link_prototype_entry.get(),
                    "section": retrieve_explanation_section_entry.get(),
                    "class_name": retrieve_explanation_class_name_entry.get(),
                    "id_prefix": retrieve_explanation_id_prefix_entry.get()
                }

            json_data[selected_list_name] = selected_list

            with open(file_path, 'w') as file:
                json.dump(json_data, file, indent=4)

            messagebox.showinfo("Success", "Veiksmīgi pievienots jauns avots!")
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")

def populate_item_fields_on_select(event):
    selected_list_name = modify_list_combobox.get()
    selected_item_name = modify_item_combobox.get()
    category = 'open_links' if selected_list_name in open_categories else 'retrieve_explanation'
    populate_item_fields(selected_list_name, selected_item_name, category)

def load_items_of_selected_list(event):
    selected_list_name = modify_list_combobox.get()
    if selected_list_name in open_categories:
        modify_item_combobox['values'] = [item.get('name') for item in open_links.get(selected_list_name, [])]
    elif selected_list_name in retrieve_categories:
        modify_item_combobox['values'] = [item.get('name') for item in retrieve_explanation.get(selected_list_name, [])]
    else:
        modify_item_combobox['values'] = []

def delete_selected_item(selected_list_name, selected_item_name, category):
    try:
        file_path = 'open_links.json' if category == 'open_links' else 'retrieve_explanation.json'
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        selected_list = json_data.get(selected_list_name, [])
        selected_item_index = next((index for index, item in enumerate(selected_list) if item.get('name') == selected_item_name), None)

        if selected_item_index is not None:
            del selected_list[selected_item_index]

            json_data[selected_list_name] = selected_list

            with open(file_path, 'w') as file:
                json.dump(json_data, file, indent=4)

            messagebox.showinfo("Success", "Avots veiksmīgi izdzēsts!")
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")

def update_list_dropdown_values(selected_category):
    if selected_category == 'open_links':
        modify_list_combobox['values'] = open_categories
    elif selected_category == 'retrieve_explanation':
        modify_list_combobox['values'] = retrieve_categories

    modify_item_combobox['values'] = []

    populate_item_fields(selected_category, '', selected_category)

def update_item_dropdown_values(selected_list_name, category):
    if selected_list_name in open_categories:
        modify_item_combobox['values'] = [item.get('name') for item in open_links.get(selected_list_name, [])]
    elif selected_list_name in retrieve_categories:
        modify_item_combobox['values'] = [item.get('name') for item in retrieve_explanation.get(selected_list_name, [])]
    else:
        modify_item_combobox['values'] = []

    populate_item_fields(selected_list_name, '', category)

def delete_selected_list(selected_list_name, category):
    try:
        file_path = 'open_links.json' if category == 'open_links' else 'retrieve_explanation.json'
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        if selected_list_name in json_data:
            del json_data[selected_list_name]

            with open(file_path, 'w') as file:
                json.dump(json_data, file, indent=4)

            messagebox.showinfo("Success", "Saraksts veiksmīgi dzēsts!")
    except Exception as e:
        messagebox.showerror("Error", f"Kļūda: {e}")

# Saskarne
root = tk.Tk()
root.title("Terminrades rīks")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

open_links_tab = ttk.Frame(notebook)
retrieve_explanation_tab = ttk.Frame(notebook)
add_sites_tab = ttk.Frame(notebook)
add_new_list_tab = ttk.Frame(notebook)

notebook.add(open_links_tab, text='Atvērt Saites')
notebook.add(retrieve_explanation_tab, text='Iegūt Nozīmi')
notebook.add(add_sites_tab, text='Pievienot Avotus')
notebook.add(add_new_list_tab, text='Pievienot Avotu Sarakstus')

open_category_label = ttk.Label(open_links_tab, text="Kategorija:")
open_category_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

open_categories = list(open_links.keys())
open_category_var = tk.StringVar(open_links_tab)
open_category_combobox = ttk.Combobox(open_links_tab, textvariable=open_category_var, values=open_categories, state='readonly')
open_category_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
open_category_combobox.bind('<FocusIn>', open_links_dropdown_focus)
open_category_combobox.current(0)

open_word_label = ttk.Label(open_links_tab, text="Vārds:")
open_word_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

open_word_entry = ttk.Entry(open_links_tab)
open_word_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

open_retrieve_button = ttk.Button(open_links_tab, text="Atvērt Saites", command=lambda: retrieve(open_category_var, open_word_entry, open_result_text, save_to_file_checkbox, open_links, retrieve_explanation))
open_retrieve_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

open_result_text = scrolledtext.ScrolledText(open_links_tab, wrap=tk.WORD, width=40, height=10)
open_result_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

retrieve_category_label = ttk.Label(retrieve_explanation_tab, text="Kategorija:")
retrieve_category_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

retrieve_categories = list(retrieve_explanation.keys())
retrieve_category_var = tk.StringVar(retrieve_explanation_tab)
retrieve_category_combobox = ttk.Combobox(retrieve_explanation_tab, textvariable=retrieve_category_var, values=retrieve_categories, state='readonly')
retrieve_category_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
retrieve_category_combobox.bind('<FocusIn>', retrieve_explanation_dropdown_focus)
retrieve_category_combobox.current(0)

retrieve_word_label = ttk.Label(retrieve_explanation_tab, text="Vārds:")
retrieve_word_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

retrieve_word_entry = ttk.Entry(retrieve_explanation_tab)
retrieve_word_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

save_to_file_checkbox = tk.BooleanVar()
save_to_file_checkbutton = ttk.Checkbutton(retrieve_explanation_tab, text="Saglabāt rezultātus failā?", variable=save_to_file_checkbox)
save_to_file_checkbutton.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

retrieve_retrieve_button = ttk.Button(retrieve_explanation_tab, text="Meklēt", command=lambda: retrieve(retrieve_category_var, retrieve_word_entry, retrieve_result_text, save_to_file_checkbox, open_links, retrieve_explanation))
retrieve_retrieve_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

retrieve_result_text = scrolledtext.ScrolledText(retrieve_explanation_tab, wrap=tk.WORD, width=40, height=10)
retrieve_result_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

add_sites_frame = ttk.LabelFrame(add_sites_tab, text="Pievienot Saites")
add_sites_frame.grid(row=0, column=0, padx=10, pady=10)

open_links_frame = ttk.LabelFrame(add_sites_frame, text="Pievienot Avotu 'Atvērt Saites' Sarakstam")
open_links_frame.grid(row=0, column=0, padx=10, pady=10)

open_links_site_name_label = ttk.Label(open_links_frame, text="Avota Nosaukums:")
open_links_site_name_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
open_links_site_name_entry = ttk.Entry(open_links_frame)
open_links_site_name_entry.grid(row=0, column=1, padx=5, pady=5)

open_links_link_prototype_label = ttk.Label(open_links_frame, text="Saites Prototips:")
open_links_link_prototype_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
open_links_link_prototype_entry = ttk.Entry(open_links_frame)
open_links_link_prototype_entry.grid(row=1, column=1, padx=5, pady=5)

open_links_list_label = ttk.Label(open_links_frame, text="Avota Saraksts:")
open_links_list_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
open_links_list_var = tk.StringVar(open_links_frame)
open_links_list_combobox = ttk.Combobox(open_links_frame, textvariable=open_links_list_var, values=open_categories, state='readonly')
open_links_list_combobox.grid(row=2, column=1, padx=5, pady=5)
open_links_list_combobox.current(0)

open_links_add_button = ttk.Button(open_links_frame, text="Pievienot Avotu", command=add_site_to_open_links)
open_links_add_button.grid(row=3, columnspan=2, padx=5, pady=5)

retrieve_explanation_frame = ttk.LabelFrame(add_sites_frame, text="Pievienot Avotu 'Iegūt Nozīmi' Sarakstam")
retrieve_explanation_frame.grid(row=1, column=0, padx=10, pady=10)

retrieve_explanation_site_name_label = ttk.Label(retrieve_explanation_frame, text="Avota Nosaukums:")
retrieve_explanation_site_name_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_site_name_entry = ttk.Entry(retrieve_explanation_frame)
retrieve_explanation_site_name_entry.grid(row=0, column=1, padx=5, pady=5)

retrieve_explanation_link_prototype_label = ttk.Label(retrieve_explanation_frame, text="Saites Prototips:")
retrieve_explanation_link_prototype_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_link_prototype_entry = ttk.Entry(retrieve_explanation_frame)
retrieve_explanation_link_prototype_entry.grid(row=1, column=1, padx=5, pady=5)

retrieve_explanation_section_label = ttk.Label(retrieve_explanation_frame, text="Sadaļa:")
retrieve_explanation_section_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_section_entry = ttk.Entry(retrieve_explanation_frame)
retrieve_explanation_section_entry.grid(row=2, column=1, padx=5, pady=5)

retrieve_explanation_class_name_label = ttk.Label(retrieve_explanation_frame, text="Klases Nosaukums:")
retrieve_explanation_class_name_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_class_name_entry = ttk.Entry(retrieve_explanation_frame)
retrieve_explanation_class_name_entry.grid(row=3, column=1, padx=5, pady=5)

retrieve_explanation_id_prefix_label = ttk.Label(retrieve_explanation_frame, text="ID Priekšdaļa:")
retrieve_explanation_id_prefix_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_id_prefix_entry = ttk.Entry(retrieve_explanation_frame)
retrieve_explanation_id_prefix_entry.grid(row=4, column=1, padx=5, pady=5)

retrieve_explanation_list_label = ttk.Label(retrieve_explanation_frame, text="Avota Saraksts:")
retrieve_explanation_list_label.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
retrieve_explanation_list_var = tk.StringVar(retrieve_explanation_frame)
retrieve_explanation_list_combobox = ttk.Combobox(retrieve_explanation_frame, textvariable=retrieve_explanation_list_var, values=retrieve_categories, state='readonly')
retrieve_explanation_list_combobox.grid(row=5, column=1, padx=5, pady=5)
retrieve_explanation_list_combobox.current(0)

retrieve_explanation_add_button = ttk.Button(retrieve_explanation_frame, text="Pievienot Avotu", command=add_site_to_retrieve_explanation)
retrieve_explanation_add_button.grid(row=6, columnspan=2, padx=5, pady=5)

new_list_name_label = ttk.Label(add_new_list_tab, text="Jaunā Saraksta Nosaukums:")
new_list_name_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
new_list_name_entry = ttk.Entry(add_new_list_tab)
new_list_name_entry.grid(row=0, column=1, padx=5, pady=5)

new_list_category_label = ttk.Label(add_new_list_tab, text="Kategorija:")
new_list_category_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
new_list_category_var = tk.StringVar(add_new_list_tab)
new_list_category_combobox = ttk.Combobox(add_new_list_tab, textvariable=new_list_category_var, values=["open_links", "retrieve_explanation"], state='readonly')
new_list_category_combobox.grid(row=1, column=1, padx=5, pady=5)
new_list_category_combobox.current(0)

new_list_add_button = ttk.Button(add_new_list_tab, text="Izveidot Jaunu Sarakstu", command=lambda: add_new_list(new_list_name_entry.get(), new_list_category_var.get()))
new_list_add_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

modify_items_frame = ttk.LabelFrame(add_sites_tab, text="Labot Sarakstu")
modify_items_frame.grid(row=1, column=0, padx=10, pady=10)

modify_list_label = ttk.Label(modify_items_frame, text="Izvēlaties Sarakstu:")
modify_list_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
modify_list_var = tk.StringVar(modify_items_frame)
modify_list_combobox = ttk.Combobox(modify_items_frame, textvariable=modify_list_var, values=open_categories + retrieve_categories, state='readonly')
modify_list_combobox.grid(row=0, column=1, padx=5, pady=5)
modify_list_combobox.current(0)

modify_item_label = ttk.Label(modify_items_frame, text="Izvēlaties Avotu:")
modify_item_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
modify_item_var = tk.StringVar(modify_items_frame)
modify_item_combobox = ttk.Combobox(modify_items_frame, textvariable=modify_item_var, values=[], state='readonly')
modify_item_combobox.grid(row=1, column=1, padx=5, pady=5)

modify_item_combobox.bind('<<ComboboxSelected>>', populate_item_fields_on_select)

modify_item_button = ttk.Button(modify_items_frame, text="Labot Avotu", command=lambda: modify_selected_item(modify_list_combobox.get(), modify_item_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation'))
modify_item_button.grid(row=2, columnspan=2, padx=5, pady=5)

modify_list_combobox.bind('<<ComboboxSelected>>', load_items_of_selected_list)

delete_item_button = ttk.Button(modify_items_frame, text="Dzēst Avotu", command=lambda: delete_selected_item(modify_list_combobox.get(), modify_item_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation'))
delete_item_button.grid(row=3, columnspan=2, padx=5, pady=5)

delete_item_button.configure(command=lambda: [delete_selected_item(modify_list_combobox.get(), modify_item_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation'), update_item_dropdown_values(modify_list_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation')])

delete_list_button = ttk.Button(modify_items_frame, text="Dzēst Sarakstu", command=lambda: delete_selected_list(modify_list_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation'))
delete_list_button.grid(row=4, columnspan=2, padx=5, pady=5)

delete_list_button.configure(command=lambda: [delete_selected_list(modify_list_combobox.get(), 'open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation'), update_list_dropdown_values('open_links' if modify_list_combobox.get() in open_categories else 'retrieve_explanation')])

open_links_dropdown_focus()
retrieve_explanation_dropdown_focus()

root.mainloop()