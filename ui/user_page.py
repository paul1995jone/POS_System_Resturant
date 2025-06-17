# ui/user_page.py

import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageFilter
import os, tempfile, platform, csv,time, win32printing, win32api, threading
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
from utils.Shared_functions import record_daily_history_if_needed, execute_query, resource_path


def open_user_dashboard(root):
    root.withdraw()
    user_win = tk.Toplevel()
    user_win.title("Boikunther Adda - Billing")
    user_win.geometry("1200x600")
    user_win.configure(bg="gray")

    selected_filter = tk.StringVar(value="")  # "", "veg", or "nonveg"
    selected_filter.set("")  # Possible values: "", "veg", "non-veg", "stock-out"
    search_var = tk.StringVar()

    def open_stockout_window():
        stockout_win = tk.Toplevel(user_win)
        stockout_win.title("Mark Stock Out Items")
        stockout_win.geometry("850x600")
        stockout_win.configure(bg="white")

        tk.Label(stockout_win, text="Manage Item Stock", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

        main_frame = tk.Frame(stockout_win, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        avail_vars = {}
        stockout_vars = {}

        def create_section(parent, title, button_text, button_command):
            outer_frame = tk.Frame(parent, bg="white", bd=2, relief=tk.RIDGE)
            outer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            tk.Label(outer_frame, text=title, font=("Arial", 12, "bold"), bg="white").pack(pady=5)

            # --- Scrollable area setup ---
            scroll_frame_container = tk.Frame(outer_frame, bg="white")
            scroll_frame_container.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(scroll_frame_container, bg="white", highlightthickness=0)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(scroll_frame_container, orient=tk.VERTICAL, command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            canvas.configure(yscrollcommand=scrollbar.set)

            inner_frame = tk.Frame(canvas, bg="white")
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")

            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))

            inner_frame.bind("<Configure>", on_frame_configure)

            # Fix the width of the canvas to match the outer frame
            def on_outer_resize(event):
                canvas.itemconfig("all", width=event.width)

            canvas.bind("<Configure>", on_outer_resize)

            # --- Action button ---
            tk.Button(outer_frame, text=button_text,
                      bg="orange" if "Stock Out" in button_text else "green",
                      fg="black", font=("Arial", 11, "bold"),
                      command=button_command).pack(pady=10)

            return inner_frame

        # Create left and right scrollable sections
        avail_frame = create_section(main_frame, "Available Items", "Mark as Stock Out", lambda: mark_stock_out())
        out_frame = create_section(main_frame, "Stock Out Items", "Mark as Available", lambda: mark_stock_in())

        def load_items():
            avail_vars.clear()
            stockout_vars.clear()
            for widget in avail_frame.winfo_children():
                widget.destroy()
            for widget in out_frame.winfo_children():
                widget.destroy()

            available_items = execute_query("SELECT id, name FROM items WHERE is_available = 1 ORDER BY name",
                                            fetch=True)
            stockout_items = execute_query("SELECT id, name FROM items WHERE is_available = 0 ORDER BY name",
                                           fetch=True)

            for item_id, name in available_items:
                var = tk.BooleanVar()
                chk = tk.Checkbutton(avail_frame, text=name, variable=var, anchor="w", bg="white")
                chk.pack(fill=tk.X, padx=10, pady=2)
                avail_vars[item_id] = var

            for item_id, name in stockout_items:
                var = tk.BooleanVar()
                chk = tk.Checkbutton(out_frame, text=name, variable=var, anchor="w", bg="white")
                chk.pack(fill=tk.X, padx=10, pady=2)
                stockout_vars[item_id] = var

        def update_stock_status(selected_items, status):
            if not selected_items:
                msg = "Select items to mark as stock out." if status == 0 else "Select items to mark as available."
                messagebox.showwarning("No Selection", msg)
                return
            execute_query("UPDATE items SET is_available = ? WHERE id = ?",
                                 params=[(status, i) for i in selected_items], commit=True, many=True)
            load_items()
            update_item_display()

        def mark_stock_out():
            selected = [item_id for item_id, var in avail_vars.items() if var.get()]
            update_stock_status(selected, 0)

        def mark_stock_in():
            selected = [item_id for item_id, var in stockout_vars.items() if var.get()]
            update_stock_status(selected, 1)

        load_items()

    def reset_stockout_items():
        try:
            execute_query("UPDATE items SET is_available = 1 WHERE is_available = 0", commit=True)
            messagebox.showinfo("Success", "All stock out items are now available.")
            update_item_display()  # Refresh the UI
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset stock: {str(e)}")

    # =============== LEFT PANEL (Items) ===============
    left_frame = tk.Frame(user_win, width=300, bg="white")
    left_frame.pack(side=tk.LEFT, fill=tk.Y)
    tk.Label(left_frame, text="Today's item", font=("Arial", 16), bg="#f8f8f8").pack(pady=5)

    # === Row 1: STOCK BUTTONS ===
    stock_btn_frame = tk.Frame(left_frame, bg="white")
    stock_btn_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
    stockout_btn = tk.Button(stock_btn_frame, text="Stock Out", bg="#ffeeba", fg="black", width=12,
                             command=open_stockout_window)
    stockout_btn.pack(side=tk.LEFT, padx=2)

    reset_stock_btn = tk.Button(stock_btn_frame, text="Reset", bg="#dee2e6", fg="black", width=8,
                                command=reset_stockout_items)
    reset_stock_btn.pack(side=tk.RIGHT, padx=2)

    # === Row 2: VEG/NON-VEG BUTTONS ===
    filter_btn_frame = tk.Frame(left_frame, bg="white")
    filter_btn_frame.pack(fill=tk.X, padx=5, pady=(10, 0))

    veg_btn = tk.Button(filter_btn_frame, text="Veg", bg="#d4edda", fg="black", width=8,
                        command=lambda: set_filter("veg"))
    veg_btn.pack(side=tk.LEFT, padx=2)

    nonveg_btn = tk.Button(filter_btn_frame, text="Non-Veg", bg="#f8d7da", fg="black", width=8,
                           command=lambda: set_filter("non-veg"))
    nonveg_btn.pack(side=tk.LEFT, padx=2)

    # ---------- Search Entry  ----------
    search_frame = tk.Frame(left_frame, bg="white")
    search_frame.pack(fill=tk.X, padx=5, pady=(2, 5))

    search_entry = tk.Entry(search_frame, textvariable=search_var, width=25, fg="gray")
    search_entry.insert(0, "search")  # Set default placeholder
    search_entry.pack(fill=tk.X, expand=True)

    def clear_placeholder(event):
        if search_entry.get() == "search":
            search_entry.delete(0, tk.END)
            search_entry.config(fg="black")

    def add_placeholder(event):
        if search_entry.get() == "":
            search_entry.insert(0, "search")
            search_entry.config(fg="gray")

    search_entry.bind("<FocusIn>", clear_placeholder)
    search_entry.bind("<FocusOut>", add_placeholder)

    def update_item_display():
        # Function will be defined later
        pass

    def set_filter(filter_value):
        if selected_filter.get() == filter_value:
            selected_filter.set("")
        else:
            selected_filter.set(filter_value)
        update_filter_button_colors()
        update_item_display()

    def update_filter_button_colors():
        if selected_filter.get() == "veg":
            veg_btn.config(bg="#28a745", fg="white")  # Active veg: dark green
            nonveg_btn.config(bg="#f8d7da", fg="black")  # Inactive nonveg: light red
        elif selected_filter.get() == "nonveg":
            veg_btn.config(bg="#d4edda", fg="black")  # Inactive veg: light green
            nonveg_btn.config(bg="#c82333", fg="white")  # Active nonveg: dark red
        else:
            veg_btn.config(bg="#d4edda", fg="black")  # Both inactive
            nonveg_btn.config(bg="#f8d7da", fg="black")

    def on_search_change(*args):
        update_item_display()

    search_var.trace_add("write", on_search_change)

    canvas = tk.Canvas(left_frame, bg="white")
    scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scroll_frame.bind("<Configure>", on_configure)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Bind properly — bind to scroll_frame (child of canvas), not whole root
    scroll_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    scroll_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    # ===================== CENTER PANEL (Cart) =====================
    center_frame = tk.Frame(user_win, width=400, bg="#f8f8f8")
    center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(center_frame, text="Cart", font=("Arial", 16), bg="#f8f8f8").pack(pady=5)

    # Heading row
    heading_frame = tk.Frame(center_frame, bg="#d0d0d0")
    heading_frame.pack(fill=tk.X, padx=10)

    tk.Label(heading_frame, text="Item", font=("Arial", 12, "bold"), width=15, anchor="w", bg="#d0d0d0").grid(row=0,
                                                                                                              column=0,
                                                                                                              padx=2)
    tk.Label(heading_frame, text="Qty", font=("Arial", 12, "bold"), width=10, bg="#d0d0d0").grid(row=0, column=1,
                                                                                                 padx=2)
    tk.Label(heading_frame, text="Price/Unit", font=("Arial", 12, "bold"), width=10, bg="#d0d0d0").grid(row=0, column=2,
                                                                                                      padx=2)
    tk.Label(heading_frame, text="Extra Qty", font=("Arial", 12, "bold"), width=10, bg="#d0d0d0").grid(row=0, column=3,
                                                                                                       padx=2)
    tk.Label(heading_frame, text="Remove", font=("Arial", 12, "bold"), width=10, bg="#d0d0d0").grid(row=0, column=4,
                                                                                                    padx=2)

    # ========== CART SCROLLABLE SECTION ==========
    canvas_frame = tk.Frame(center_frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    cart_canvas = tk.Canvas(canvas_frame, bg="#f8f8f8", highlightthickness=0)
    cart_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    cart_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=cart_canvas.yview)
    cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    cart_canvas.configure(yscrollcommand=cart_scrollbar.set)

    # This frame holds all cart items
    cart_items_frame = tk.Frame(cart_canvas, bg="#f8f8f8")

    # This line attaches the cart_items_frame to the canvas
    cart_window = cart_canvas.create_window((0, 0), window=cart_items_frame, anchor="nw")

    # Ensure cart canvas resizes properly when new widgets are added
    def on_frame_configure(event):
        cart_canvas.configure(scrollregion=cart_canvas.bbox("all"))
        cart_canvas.itemconfig(cart_window, width=cart_canvas.winfo_width())

    cart_items_frame.bind("<Configure>", on_frame_configure)

    # Optional: Enable mousewheel scrolling
    def _on_mousewheel(event):
        cart_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    cart_canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Use this only once in your app

    cart = []

    def update_total():
        total = 0
        for item in cart:
            try:
                qty = int(item['qty_var'].get()) if item['qty_var'].get() != "5+" else int(item['custom_qty_var'].get())
            except ValueError:
                qty = 1
            subtotal = item['price'] * qty
            total += subtotal
        summary_label.config(text=f"Total: ₹{total}")

    def remove_from_cart(cart_item):
        cart.remove(cart_item)
        cart_item['frame'].destroy()
        update_total()

    def add_to_cart(item_id, name, price):
        # Helper to safely get quantity
        def get_quantity(item):
            try:
                if item['qty_var'].get() == "5+":
                    return int(item['custom_qty_var'].get())
                return int(item['qty_var'].get())
            except ValueError:
                return 1

        # Check if item is already in the cart
        for item in cart:
            if item['id'] == item_id:
                current_qty = get_quantity(item)
                new_qty = current_qty + 1

                if new_qty > 5:
                    item['qty_var'].set("5+")
                    item['custom_qty_var'].set(str(new_qty))
                    item['custom_qty_entry'].grid(row=0, column=3, padx=5)
                else:
                    item['qty_var'].set(str(new_qty))
                    item['custom_qty_entry'].grid_forget()

                update_total()
                return

        # ========== New Item ==========
        row = tk.Frame(cart_items_frame, bg="#f0f0f0")
        row.pack(fill=tk.X, pady=2)

        # Item name
        tk.Label(row, text=name, font=("Arial", 12), bg="#f0f0f0", anchor="w", width=15).grid(row=0, column=0, padx=2)

        qty_var = tk.StringVar(value="1")
        custom_qty_var = tk.StringVar(value="6")

        def on_dropdown_change(val):
            if val == "5+":
                custom_qty_entry.grid(row=0, column=3, padx=5)
            else:
                custom_qty_entry.grid_forget()
            update_total()

        qty_dropdown = tk.OptionMenu(row, qty_var, "1", "2", "3", "4", "5", "5+", command=on_dropdown_change)
        qty_dropdown.config(width=3)
        qty_dropdown.grid(row=0, column=1, padx=2)

        # Custom qty entry (for 5+)
        custom_qty_entry = tk.Entry(row, textvariable=custom_qty_var, width=4)
        custom_qty_entry.bind("<KeyRelease>", lambda e: update_total())
        custom_qty_entry.grid_forget()

        # Show unit price (not subtotal)
        unit_price_label = tk.Label(row, text=f"₹{price}", font=("Arial", 12), bg="#f0f0f0", width=10)
        unit_price_label.grid(row=0, column=2, padx=2)

        cart_item = {
            'id': item_id,
            'name': name,
            'price': price,
            'qty_var': qty_var,
            'custom_qty_var': custom_qty_var,
            'custom_qty_entry': custom_qty_entry,
            'frame': row
        }

        del_btn = tk.Button(row, text="❌", command=lambda: remove_from_cart(cart_item), bg="#ff4d4d", fg="white")
        del_btn.grid(row=0, column=4, padx=2)

        cart.append(cart_item)
        update_total()
        cart_canvas.update_idletasks()
    # =============== RIGHT PANEL (Summary & Checkout) ===============
    right_frame = tk.Frame(user_win, width=300, bg="#e0e0e0")
    right_frame.pack(side=tk.RIGHT, fill=tk.Y)

    tk.Label(right_frame, text="Summary", font=("Arial", 16), bg="#e0e0e0").pack(pady=10)
    summary_label = tk.Label(right_frame, text="Total: ₹0", font=("Arial", 14), bg="#e0e0e0")
    summary_label.pack(pady=10)

    # ======== Updating sales history========

    def update_item_history_csv(cart_items):
        today = datetime.now().strftime("%Y-%m-%d")
        csv_file = resource_path("item_history.csv")

        if not os.path.exists(csv_file):
            messagebox.showwarning("CSV Not Found",
                                   "Warning: item_history.csv not found.\nSale record will not be updated.")
            return

        try:
            with open(csv_file, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            messagebox.showerror("Read Error", f"Error reading {csv_file}: {e}")
            return

        if not rows:
            messagebox.showerror("File Error", "CSV file is empty or corrupted.")
            return

        headers = rows[0]
        try:
            date_index = headers.index("Date")
        except ValueError:
            messagebox.showerror("Header Error", "'Date' column not found in CSV.")
            return

        # Find today's row
        today_row_idx = next((i for i, row in enumerate(rows[1:], start=1)
                              if len(row) > date_index and row[date_index] == today), None)

        # If not found, call function to insert today's row and reload
        if today_row_idx is None:
            record_daily_history_if_needed()
            try:
                with open(csv_file, "r", newline="") as f:
                    rows = list(csv.reader(f))
            except Exception as e:
                messagebox.showerror("Reload Error", f"Error reloading {csv_file}: {e}")
                return
            today_row_idx = next((i for i, row in enumerate(rows[1:], start=1)
                                  if len(row) > date_index and row[date_index] == today), None)
            if today_row_idx is None:
                messagebox.showerror("Failed", "Unable to create today's row in item_history.csv.")
                return

        # Cache header-to-column mapping starting from column 4
        item_col_map = {name: idx for idx, name in enumerate(headers[4:], start=4)}

        for item in cart_items:
            name = item["name"]
            qty = item["quantity"]
            col_idx = item_col_map.get(name)
            if col_idx is not None:
                old_val = rows[today_row_idx][col_idx].strip() if len(rows[today_row_idx]) > col_idx else "0"
                try:
                    old_qty = int(old_val) if old_val else 0
                except ValueError:
                    old_qty = 0
                # Ensure the row is long enough
                while len(rows[today_row_idx]) <= col_idx:
                    rows[today_row_idx].append("")
                rows[today_row_idx][col_idx] = str(old_qty + qty)

        try:
            with open(csv_file, "w", newline="") as f:
                csv.writer(f).writerows(rows)
        except Exception as e:
            messagebox.showerror("Write Error", f"Error writing to {csv_file}: {e}")

    def checkout():
        if not cart:
            messagebox.showwarning("Empty Cart", "Please add items before checkout.")
            return

        total = 0
        now = datetime.now()
        receipt_lines = []
        receipt_lines.append("     BOIKUNTHER ADDA     ")
        receipt_lines.append("     BILL OF SUPPLY      ")
        receipt_lines.append(now.strftime("Date: %Y-%m-%d"))
        receipt_lines.append(now.strftime("Time: %H:%M:%S"))
        receipt_lines.append("-" * 32)
        receipt_lines.append("{:<12} {:>3}x{:>5} {:>6}".format("Item", "Qty", "Rate", "Total"))
        receipt_lines.append("-" * 32)

        history_cart = []
        for item in cart:
            try:
                qty = int(item['qty_var'].get()) if item['qty_var'].get() != "5+" else int(item['custom_qty_var'].get())
            except ValueError:
                qty = 1

            name = item['name'][:12]  # Trim name to 12 chars
            price = item['price']
            subtotal = price * qty
            total += subtotal
            receipt_lines.append("{:<12} {:>3}x{:>5} {:>6.0f}".format(name, qty, price, subtotal))

            history_cart.append({
                "name": item['name'],
                "quantity": qty
            })

        receipt_lines.append("-" * 32)
        receipt_lines.append("TOTAL: {:>22.0f}".format(total))
        receipt_lines.append("-" * 32)
        receipt_lines.append("   Thank You! Visit Again!   ")

        receipt_text = "\n".join(receipt_lines)

        # ✅ Show popup
        show_receipt_popup(receipt_text)

       # ✅ Save to a permanent temporary file (outside auto-deletion risk)
        try:
            # Manually create a temp path
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "boikunther_receipt.txt")

            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(receipt_text)
            time.sleep(1)
            # ✅ Print using Notepad
            os.system(f'notepad /p "{temp_path}"')

        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print receipt:\n{e}")

        # ✅ Update CSV
        update_item_history_csv(history_cart)

        # ✅ Clear cart
        for widget in cart_items_frame.winfo_children():
            widget.destroy()
        cart.clear()
        update_total()

    tk.Button(right_frame, text="Checkout", highlightbackground="red", bg="red", fg="Black", font=("Arial", 12, "bold"),
              width=20, command=checkout).pack(pady=20)

    def show_receipt_popup(receipt_text):
        popup = tk.Toplevel()
        popup.title("Receipt")
        popup.geometry("320x450")
        popup.configure(bg="white")
        popup.grab_set()

        text_box = tk.Text(popup, font=("Courier", 10), wrap=tk.NONE, bg="white", relief=tk.FLAT)
        text_box.insert(tk.END, receipt_text)
        text_box.config(state=tk.DISABLED)
        text_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(popup, bg="white")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Print", bg="green", fg="black", width=10,
                  command=lambda: [print_receipt(receipt_text), popup.destroy()]).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Save as PDF", bg="blue", fg="black", width=12,
                  command=lambda: [save_as_pdf(receipt_text), popup.destroy()]).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="OK", bg="gray", fg="black", width=8,
                  command=popup.destroy).grid(row=0, column=2, padx=5)

    def print_receipt(text):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as tmp:
                tmp.write(text)
                tmp_path = tmp.name

            system = platform.system()
            if system == "Windows":
                win32api.ShellExecute(
                    0,
                    "print",
                    tmp_path,
                    None,
                    ".",
                    0
                )
            elif system == "Darwin":  # macOS
                os.system(f"lp -o raw '{tmp_path}'")
            elif system == "Linux":
                os.system(f"lpr -o raw '{tmp_path}'")
            else:
                messagebox.showerror("Print Error", "Unsupported OS for printing.")

            # Delay file deletion
            def delayed_delete(path):
                time.sleep(15)
                try:
                    os.remove(path)
                except:
                    pass

            threading.Thread(target=delayed_delete, args=(tmp_path,)).start()

        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print:\n{str(e)}")

    def save_as_pdf(text):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        c = pdf_canvas.Canvas(file_path, pagesize=A4)
        text_obj = c.beginText(40, 800)
        text_obj.setFont("Courier", 12)

        for line in text.splitlines():
            text_obj.textLine(line)

        c.drawText(text_obj)
        c.showPage()
        c.save()

    # =============== Load Items from DB ===============
    image_refs = []
    filter_frame = tk.Frame(left_frame, bg="white")
    filter_frame.pack(pady=5)

    def update_item_display():
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        filter_cat = selected_filter.get()

        query = "SELECT id, name, price, category FROM items WHERE is_available = ?"
        params = (0,) if filter_cat == "stock-out" else (1,)

        all_items = execute_query(query, params=params, fetch=True)

        keyword = search_var.get().lower()
        if keyword == "search":
            keyword = ""

        filter_cat = selected_filter.get()

        filtered_items = []
        for item in all_items:
            item_id, name, price, category = item
            if (not filter_cat or category.lower() == filter_cat) and (keyword in name.lower()):
                filtered_items.append(item)

        def load_placeholder_image():
            img = Image.open(resource_path("images/Logo.png")).resize((100, 100))
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=2))
            return ImageTk.PhotoImage(blurred_img)

        image_refs.clear()
        photo = load_placeholder_image()  # Load once
        columns = 3
        for idx, (item_id, name, price, category) in enumerate(filtered_items):
            try:
                image_refs.append(photo)

                border_color = "green" if category.lower() == "veg" else "red"

                item_frame = tk.Frame(scroll_frame, bg="white", bd=2, relief=tk.RAISED,
                                      highlightbackground=border_color, highlightthickness=3)
                item_frame.grid(row=idx // columns, column=idx % columns, padx=10, pady=10, sticky="n")

                canvas_inner = tk.Canvas(item_frame, width=100, height=100, bd=0, highlightthickness=0)
                canvas_inner.pack()
                canvas_inner.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas_inner.create_text(50, 50, text=name, fill="black", font=("Helvetica", 15, "bold"), width=90)

                def click_handler(event, i=item_id, n=name, p=price):
                    add_to_cart(i, n, p)

                canvas_inner.bind("<Button-1>", click_handler)
                canvas_inner.image = photo

                tk.Label(item_frame, text=f"₹{price}", font=("Arial", 10, "bold"), bg="white").pack()

            except Exception as e:
                print(f"Failed to load image: {e}")

    def logout(win):
        user_win.destroy()
        root.deiconify()

    logout_btn = tk.Button(right_frame, text="Logout", bg="white", fg="black",
                           font=("Arial", 12, "bold"), width=20,
                           command=lambda: logout(user_win))
    logout_btn.pack(pady=10)

    user_win.protocol("WM_DELETE_WINDOW", logout)
    update_item_display()  # Show items immediately on login

    user_win.protocol("WM_DELETE_WINDOW", lambda: (user_win.destroy(), exit()))
