# ☀️ SunERP Professional v3.0

**SunERP Professional** is a high-performance, modern ERP and Inventory Management System designed for warehouse operations. It combines the ease of **Excel** with the speed of **SQLite** and a stunning **Python CustomTkinter** interface.

---

## 🚀 Quick Setup Guide

Follow these steps to get the software running on your computer in less than 2 minutes.

### 1. Prerequisites
Ensure you have **Python 3.10 or higher** installed. You can download it from [python.org](https://www.python.org/).

### 2. Install Dependencies
Open your terminal (PowerShell or Command Prompt) in the project folder and run:
```powershell
pip install customtkinter openpyxl reportlab matplotlib pandas pillow
```

### 3. Initialize & Launch
Run the application using the following command:
```powershell
$env:PYTHONPATH = "."
python src/main.py
```

### 4. Default Credentials
- **Username:** `admin`
- **Password:** `admin123`

---

## 📖 Documentation Index

| Document | Purpose | Audience |
|:---|:---|:---|
| **[User Guide](USER_GUIDE.md)** | How to use every feature (POS, Analytics, Exports) | End Users / Staff |
| **[Developer Guide](DEVELOPER_DEEP_DIVE.md)** | Code walkthrough, FIFO logic, and database architecture | Developers / IT |
| **[System Design](SYSTEM_DESIGN.md)** | Technical specs, schema, and security model | System Architects |

---

## ✨ Key Features

- **Modern POS System:** Fast checkout with real-time stock validation and discount support.
- **FIFO Inventory Math:** Professional-grade cost and profit tracking based on the oldest stock batches.
- **Real-time Analytics:** KPI cards, sales trends, and dead stock reporting.
- **Automated Safety:** Every transaction creates an Excel backup and an entry in the secure audit log.
- **Migration System:** Export your entire history to a ZIP archive and restore it on another machine.
- **Role-Based Access:** Secure login for Admins, Managers, and Cashiers.

---

## 🛠️ Troubleshooting

- **"Excel file not found":** Ensure `SunERP_Master_Database.xlsx` is in the root folder.
- **UI looks blurry:** This usually happens on high-DPI screens. CustomTkinter automatically scales, but you can adjust the `WINDOW_SIZE` in `src/core/config.py`.
- **Database errors:** Use **Settings > Database > Re-sync from Excel** to rebuild your local cache.

---

## 📜 License
Developed for Sun Warehouse Operations. All rights reserved.
