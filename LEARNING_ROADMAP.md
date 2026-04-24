# 🚀 Python Learning Roadmap: From Beginner to Pro

This project, **SunERP Professional**, is a "gold mine" for learning real-world Python. Instead of just reading the code, follow this step-by-step roadmap to level up your skills from **Beginner** to **Intermediate** and **Advanced**.

---

## 🌱 Level 1: The Beginner (The Basics)
*Goal: Understand how data is stored and how logic flows.*

### 1. Variables & Dictionaries
- **Where to look:** `src/core/config.py`
- **What to study:** See how the `COLORS` and `SHORTCUTS` dictionaries are used to store settings in one central place.
- **Exercise:** Change the `accent` color and the `WINDOW_SIZE`. Observe how the whole app changes.

### 2. File Operations & Strings
- **Where to look:** `src/core/safety.py`
- **What to study:** Look at how `os.path.join` and `shutil.copy2` are used to manage files and folders safely.
- **Exercise:** Add a new print statement inside `create_backup()` that says exactly which file was backed up.

### 3. Basic Functions & Imports
- **Where to look:** `src/main.py`
- **What to study:** See how classes are imported from other files and how the `if __name__ == "__main__":` block starts the app.

---

## 📈 Level 2: The Intermediate (Data & UI)
*Goal: Master Object-Oriented Programming (OOP) and external libraries.*

### 1. Classes & Inheritance
- **Where to look:** `src/ui/views/dashboard.py` and `src/ui/app.py`
- **What to study:** Notice how every "View" (Dashboard, Sales, etc.) **inherits** from `ctk.CTkFrame`. This is a core OOP concept.
- **Exercise:** Create a simple new file `test_ui.py` and try to create a single `ctk.CTkButton` that changes its own text when clicked.

### 2. Working with Data (Pandas & SQL)
- **Where to look:** `src/core/database.py`
- **What to study:** Look at `execute_query`. It uses `pandas` to turn SQL results into a "DataFrame" (a programmable table).
- **Exercise:** Open the `sqlite3` CLI or a browser tool and run `SELECT * FROM products`. Then, try to write a query that only shows products in the "Grains" category.

### 3. List Comprehensions & Loops
- **Where to look:** `src/core/inventory_manager.py` (the `get_low_stock_items` method).
- **What to study:** See how loops are used to filter through data quickly.

---

## 🔥 Level 3: The Advanced (Architecture & Algorithms)
*Goal: Understand complex business logic and system design.*

### 1. Algorithmic Thinking (FIFO)
- **Where to look:** `src/core/inventory_manager.py` → `calculate_fifo_cogs()`
- **The Challenge:** This is the most complex part of the app. It tracks which specific "batch" of a product was sold first.
- **Study Tip:** Draw it on paper. If you have 2 batches of 10 items, and you sell 15, how does the code "consume" 10 from Batch A and 5 from Batch B?

### 2. Multi-Persistence (SQLite + Excel)
- **Where to look:** `src/core/database.py` → `write_sale()`
- **What to study:** Notice how the system writes to **two different places** at once. One for speed (SQLite) and one for permanent storage (Excel).
- **Advanced Concept:** Think about "Concurrency". What happens if two people try to write to the Excel file at the exact same time? (This is why we have the `SafetyManager`).

### 3. Security & Hashing
- **Where to look:** `src/core/auth.py`
- **What to study:** See how `hashlib.sha256` is used. We never store the actual password, only the "fingerprint" (hash). This is how professional websites work.

---

## 🛠️ The "Ultimate Learning" Method

Don't just read—**BREAK IT.**

1.  **Delete a line:** Delete a comma in `config.py`. See what error Python gives you. Learning to read errors is the #1 skill of a pro.
2.  **Add a Feature:** Try to add a "Phone Number" field to the `users` table. You'll have to change:
    -   The SQL table creation in `database.py`.
    -   The UI form in `settings.py`.
    -   The logic in `auth.py`.
3.  **Refactor:** Take a long function and try to split it into two smaller, cleaner functions.

---

## 🎯 Final Advice
Python is not a set of rules to memorize; it's a **toolset** to build things. You have the whole toolset in your hands now. Use this project as your playground!

**Keep coding, keep breaking things, and keep learning.** 🚀
