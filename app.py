import sys, os, base64, sqlite3, secrets, string, re
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- APPDATA FOLDER ----------
APP_NAME = "ZeroBreach"
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA")
if not LOCAL_APPDATA:
    LOCAL_APPDATA = os.path.expanduser("~")
DATA_PATH = os.path.join(LOCAL_APPDATA, APP_NAME)
os.makedirs(DATA_PATH, exist_ok=True)

KEY_FILE = os.path.join(DATA_PATH, "master.key")
SALT_FILE = os.path.join(DATA_PATH, "salt.bin")
DB_FILE = os.path.join(DATA_PATH, "passwords.db")
LOCK_FILE = os.path.join(DATA_PATH, "lock.dat")

# Resource path for PyInstaller
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

ICON_PATH = resource_path("ico.ico")

# ---------- SECURE KEY DERIVATION ----------
def load_salt():
    """Load salt from file, generate if missing"""
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()
    return None

def save_salt(salt: bytes):
    """Save salt to file securely"""
    with open(SALT_FILE, "wb") as f:
        f.write(salt)

def generate_key(master_password: str) -> bytes:
    """Generate secure key using PBKDF2 with salt"""
    salt = load_salt()
    if salt is None:
        salt = os.urandom(16)
        save_salt(salt)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return key

def save_key(key: bytes):
    with open(KEY_FILE, "wb") as f:
        f.write(key)

def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    return None

def encrypt(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(data.encode()).decode()

# ---------- DATABASE ----------
def create_db(key: bytes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            url TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database created/initialized")

def add_entry_db(username, password, url, comment, key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    encrypted_pw = encrypt(password, key)
    c.execute("INSERT INTO passwords (username, password, url, comment) VALUES (?, ?, ?, ?)",
              (username, encrypted_pw, url, comment))
    conn.commit()
    conn.close()
    logger.info(f"Entry added for {username}")

def get_entries_db(key):
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password, url, comment FROM passwords ORDER BY created_at DESC")
    data = []
    for row in c.fetchall():
        try:
            data.append((row[0], row[1], decrypt(row[2], key), row[3], row[4]))
        except Exception as e:
            logger.error(f"Decrypt error for entry {row[0]}: {e}")
            data.append((row[0], row[1], "DECRYPT ERROR", row[3], row[4]))
    conn.close()
    return data

def update_entry_db(entry_id, username, password, url, comment, key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    encrypted_pw = encrypt(password, key)
    c.execute("UPDATE passwords SET username=?, password=?, url=?, comment=? WHERE id=?",
              (username, encrypted_pw, url, comment, entry_id))
    conn.commit()
    conn.close()
    logger.info(f"Entry {entry_id} updated")

def delete_entry_db(entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM passwords WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    logger.info(f"Entry {entry_id} deleted")

# ---------- PASSWORD GENERATOR ----------
def generate_password(length=16, include_upper=True, include_lower=True, include_digits=True, include_symbols=True):
    """Generate secure random password with customizable options"""
    chars = ""
    if include_upper: chars += string.ascii_uppercase
    if include_lower: chars += string.ascii_lowercase
    if include_digits: chars += string.digits
    if include_symbols: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(chars) for _ in range(length))

# ---------- VALIDATION ----------
def validate_master_password(pwd):
    if len(pwd) < 8: return False
    if not re.search(r"[A-Z]", pwd): return False
    if not re.search(r"[a-z]", pwd): return False
    if not re.search(r"[0-9]", pwd): return False
    if not re.search(r"[!@#$%^&*()+\-~`;:'\",.<>?]", pwd): return False
    return True

# ---------- MASTER PASSWORD DIALOG ----------
class MasterPasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZeroBreach - Master Password")
        self.setFixedSize(400, 200)
        self.layout = QVBoxLayout()
        
        warning = QLabel("Master password mora imati:\n• Najmanje 8 karaktera\n• Veliko i malo slovo\n• Cifru\n• Specijalni karakter")
        warning.setStyleSheet("color:red; font-weight:bold; font-size:12px;")
        self.layout.addWidget(warning)
        
        self.label = QLabel("Unesite master password:")
        self.label.setStyleSheet("font-weight:bold; font-size:14px;")
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.textChanged.connect(self.validate_input)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setStyleSheet("background-color: #FFD700; color:black; font-weight:bold; padding:10px;")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pwd_input)
        self.layout.addWidget(self.btn_ok)
        self.setLayout(self.layout)

    def validate_input(self):
        self.btn_ok.setEnabled(validate_master_password(self.pwd_input.text()))

    def get_password(self):
        return self.pwd_input.text()

# ---------- ENTRY DIALOG ----------
class EntryDialog(QDialog):
    def __init__(self, key, entry_id=None):
        super().__init__()
        self.key = key
        self.entry_id = entry_id
        self.setWindowTitle("New Entry" if not entry_id else "Edit Entry")
        self.setFixedSize(500, 400)
        self.layout = QFormLayout()
        
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.show_pw = QPushButton("Show")
        self.show_pw.setCheckable(True)
        self.show_pw.clicked.connect(self.toggle_password)
        
        self.url = QLineEdit()
        self.comment = QTextEdit()
        self.comment.setMaximumHeight(80)
        
        self.layout.addRow("Username:", self.username)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.password)
        h_layout.addWidget(self.show_pw)
        self.layout.addRow("Password:", h_layout)
        self.layout.addRow("URL:", self.url)
        self.layout.addRow("Comment:", self.comment)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet("background-color:#FFD700; font-weight:bold; padding:8px;")
        self.btn_save.clicked.connect(self.save_entry)
        self.btn_gen = QPushButton("Generate Password")
        self.btn_gen.setStyleSheet("background-color:#4CAF50; color:white; padding:8px;")
        self.btn_gen.clicked.connect(self.generate_password)
        btn_layout.addWidget(self.btn_gen)
        btn_layout.addWidget(self.btn_save)
        self.layout.addRow(btn_layout)
        self.setLayout(self.layout)

        if self.entry_id:
            self.load_entry()

    def load_entry(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username,password,url,comment FROM passwords WHERE id=?", (self.entry_id,))
        row = c.fetchone()
        conn.close()
        if row:
            self.username.setText(row[0])
            self.password.setText(decrypt(row[1], self.key))
            self.url.setText(row[2])
            self.comment.setPlainText(row[3] or "")

    def toggle_password(self):
        if self.show_pw.isChecked():
            self.password.setEchoMode(QLineEdit.Normal)
            self.show_pw.setText("Hide")
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.show_pw.setText("Show")

    def generate_password(self):
        pw = generate_password(16)
        self.password.setText(pw)
        self.password.setEchoMode(QLineEdit.Normal)
        self.show_pw.setChecked(True)

    def save_entry(self):
        uname = self.username.text().strip()
        pw = self.password.text().strip()
        url = self.url.text().strip()
        comment = self.comment.toPlainText().strip()
        
        if not uname or not pw:
            QMessageBox.warning(self, "Error", "Username and Password are required!")
            return
        
        if self.entry_id:
            update_entry_db(self.entry_id, uname, pw, url, comment, self.key)
        else:
            add_entry_db(uname, pw, url, comment, self.key)
        self.accept()

# ---------- CHANGE MASTER PASSWORD ----------
class ChangeMasterDialog(QDialog):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.new_key = key
        self.setWindowTitle("Change Master Password")
        self.setFixedSize(400, 250)
        layout = QFormLayout()
        
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd1 = QLineEdit()
        self.new_pwd1.setEchoMode(QLineEdit.Password)
        self.new_pwd2 = QLineEdit()
        self.new_pwd2.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Old Password:", self.old_pwd)
        layout.addRow("New Password:", self.new_pwd1)
        layout.addRow("Confirm New:", self.new_pwd2)
        
        btn = QPushButton("Change")
        btn.setStyleSheet("background-color:#FFD700; font-weight:bold; padding:10px;")
        btn.clicked.connect(self.change_master)
        layout.addWidget(btn)
        self.setLayout(layout)

    def change_master(self):
        old_key = generate_key(self.old_pwd.text())
        saved_key = load_key()
        if saved_key != old_key:
            QMessageBox.warning(self, "Error", "Old password incorrect!")
            return
        if self.new_pwd1.text() != self.new_pwd2.text():
            QMessageBox.warning(self, "Error", "New passwords do not match!")
            return
        if not validate_master_password(self.new_pwd1.text()):
            QMessageBox.warning(self, "Error", "New password doesn't meet security requirements!")
            return
        
        new_key = generate_key(self.new_pwd1.text())
        entries = get_entries_db(old_key)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for e in entries:
            if e[2] != "DECRYPT ERROR":
                encrypted_pw = encrypt(e[2], new_key)
                c.execute("UPDATE passwords SET password=? WHERE id=?", (encrypted_pw, e[0]))
        conn.commit()
        conn.close()
        save_key(new_key)
        self.new_key = new_key
        QMessageBox.information(self, "Success", "Master password changed successfully!")
        self.accept()

# ---------- MAIN WINDOW ----------
class MainWindow(QMainWindow):
    def __init__(self, key):
        super().__init__()
        self.setWindowTitle("ZeroBreach - Secure Password Manager")
        try:
            self.setWindowIcon(QIcon(ICON_PATH))
        except:
            pass
        self.key = key
        self.resize(1200, 700)
        
        # STATUS BAR FIRST
        self.status_label = QLabel("Loading...")
        self.statusBar().addWidget(self.status_label)
        footer = QLabel("ZeroBreach © 2026 - Šamec Uglješa | PBKDF2 + Fernet Encryption")
        footer.setStyleSheet("background-color:#808080; color:white; padding:4px;")
        self.statusBar().addPermanentWidget(footer)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Search box
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search by username, URL or comment...")
        self.search_box.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)
        
        # Table - 6 columns total (ID hidden + 5 visible)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Password", "Show", "URL", "Comment"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Username
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # URL
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Comment
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        # HIDE ID COLUMN
        self.table.setColumnHidden(0, True)
        
        self.load_table()
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet("background-color: #003366; color: white; spacing: 5px;")
        self.addToolBar(toolbar)
        
        add_btn = QAction(QIcon.fromTheme("list-add", QIcon()), "Add", self)
        add_btn.triggered.connect(self.add_entry)
        edit_btn = QAction(QIcon.fromTheme("document-edit", QIcon()), "Edit", self)
        edit_btn.triggered.connect(self.edit_entry)
        del_btn = QAction(QIcon.fromTheme("edit-delete", QIcon()), "Delete", self)
        del_btn.triggered.connect(self.delete_entry)
        gen_btn = QAction(QIcon.fromTheme("document-new", QIcon()), "Generate", self)
        gen_btn.triggered.connect(self.generate_password)
        change_master = QAction(QIcon.fromTheme("preferences-system", QIcon()), "Change Master", self)
        change_master.triggered.connect(self.change_master)
        export_btn = QAction(QIcon.fromTheme("document-save-as", QIcon()), "Export", self)
        export_btn.triggered.connect(self.export_db)
        import_btn = QAction(QIcon.fromTheme("document-open", QIcon()), "Import", self)
        import_btn.triggered.connect(self.import_db)
        exit_btn = QAction(QIcon.fromTheme("application-exit", QIcon()), "Exit", self)
        exit_btn.triggered.connect(self.close)
        
        toolbar.addAction(add_btn)
        toolbar.addAction(edit_btn)
        toolbar.addAction(del_btn)
        toolbar.addAction(gen_btn)
        toolbar.addSeparator()
        toolbar.addAction(change_master)
        toolbar.addAction(export_btn)
        toolbar.addAction(import_btn)
        toolbar.addAction(exit_btn)

    def load_table(self):
        self.table.setRowCount(0)
        data = get_entries_db(self.key)
        for row_idx, row_data in enumerate(data):
            self.table.insertRow(row_idx)
            # Col 0: ID (hidden)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            # Col 1: Username
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            # Col 2: Password (masked)
            pw_item = QTableWidgetItem("🔒 *****")
            self.table.setItem(row_idx, 2, pw_item)
            # Col 3: Show button
            btn_show = QPushButton("👁 Show")
            btn_show.setStyleSheet("background-color: #FFD700; color:black; font-weight:bold; padding:4px;")
            btn_show.clicked.connect(lambda checked, r=row_idx: self.toggle_password(r))
            self.table.setCellWidget(row_idx, 3, btn_show)
            # Col 4: URL
            self.table.setItem(row_idx, 4, QTableWidgetItem(row_data[3] or ""))
            # Col 5: Comment (RESTORED!)
            self.table.setItem(row_idx, 5, QTableWidgetItem(row_data[4] or ""))
        
        self.table.resizeRowsToContents()
        self.status_label.setText(f"✅ Loaded {len(data)} entries")

    def filter_table(self):
        search_text = self.search_box.text().lower().strip()
        all_data = get_entries_db(self.key)
        
        self.table.setRowCount(0)
        matching_rows = 0
        
        for row_data in all_data:
            username = row_data[1].lower()
            url = (row_data[3] or "").lower()
            comment = (row_data[4] or "").lower()
            
            if search_text == "" or search_text in username or search_text in url or search_text in comment:
                self.table.insertRow(matching_rows)
                # Col 0: ID (hidden)
                self.table.setItem(matching_rows, 0, QTableWidgetItem(str(row_data[0])))
                # Col 1: Username
                self.table.setItem(matching_rows, 1, QTableWidgetItem(row_data[1]))
                # Col 2: Password
                pw_item = QTableWidgetItem("🔒 *****")
                self.table.setItem(matching_rows, 2, pw_item)
                # Col 3: Show button
                btn_show = QPushButton("👁 Show")
                btn_show.setStyleSheet("background-color: #FFD700; color:black; font-weight:bold; padding:4px;")
                btn_show.clicked.connect(lambda checked, r=matching_rows: self.toggle_password(r))
                self.table.setCellWidget(matching_rows, 3, btn_show)
                # Col 4: URL
                self.table.setItem(matching_rows, 4, QTableWidgetItem(row_data[3] or ""))
                # Col 5: Comment
                self.table.setItem(matching_rows, 5, QTableWidgetItem(row_data[4] or ""))
                matching_rows += 1
        
        self.table.resizeRowsToContents()
        self.status_label.setText(f"🔍 Found {matching_rows} of {len(all_data)} entries")

    def toggle_password(self, row):
        pw_item = self.table.item(row, 2)
        if pw_item.text() == "🔒 *****":
            all_data = get_entries_db(self.key)
            real_pw = all_data[row][2]
            pw_item.setText(real_pw)
        else:
            pw_item.setText("🔒 *****")

    def get_entry_id_from_row(self, row):
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def add_entry(self):
        dlg = EntryDialog(self.key)
        if dlg.exec_() == QDialog.Accepted:
            self.load_table()

    def edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an entry to edit!")
            return
        entry_id = self.get_entry_id_from_row(row)
        dlg = EntryDialog(self.key, entry_id)
        if dlg.exec_() == QDialog.Accepted:
            self.load_table()

    def delete_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select an entry to delete!")
            return
        entry_id = self.get_entry_id_from_row(row)
        username = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Delete entry '{username}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_entry_db(entry_id)
            self.load_table()

    def generate_password(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Password Generator")
        dlg.setFixedSize(400, 200)
        layout = QVBoxLayout()
        
        length_spin = QSpinBox()
        length_spin.setRange(8, 64)
        length_spin.setValue(16)
        
        gen_btn = QPushButton("Generate")
        pw_label = QLineEdit()
        pw_label.setEchoMode(QLineEdit.Password)
        copy_btn = QPushButton("Copy to Clipboard")
        
        def generate():
            pw = generate_password(length_spin.value())
            pw_label.setText(pw)
        
        gen_btn.clicked.connect(generate)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(pw_label.text()))
        generate()
        
        layout.addWidget(QLabel("Length:"))
        layout.addWidget(length_spin)
        layout.addWidget(gen_btn)
        layout.addWidget(pw_label)
        layout.addWidget(copy_btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def change_master(self):
        dlg = ChangeMasterDialog(self.key)
        if dlg.exec_() == QDialog.Accepted:
            self.key = dlg.new_key
            self.load_table()

    def export_db(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export Database", "", "Database Files (*.db)")
        if not fname: return
        
        private_key = Fernet.generate_key()
        fernet = Fernet(private_key)
        
        with open(DB_FILE, "rb") as f:
            data = f.read()
        encrypted_data = fernet.encrypt(data)
        with open(fname, "wb") as f:
            f.write(encrypted_data)
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Save Private Key")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🚨 IMPORTANT: Sačuvajte ovaj PRIVATE KEY!\nBez njega NEĆETE MOĆI otvoriti bazu!"))
        key_field = QLineEdit(private_key.decode())
        key_field.setReadOnly(True)
        layout.addWidget(key_field)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(key_field.text()))
        layout.addWidget(copy_btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def import_db(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Import Database", "", "Database Files (*.db)")
        if not fname: return
        
        while True:
            key_text, ok = QInputDialog.getText(self, "Private Key", 
                                              "Unesite privatni key za dekripciju:")
            if not ok: return
            if not key_text.strip():
                QMessageBox.warning(self, "Error", "Private key cannot be empty!")
                continue
            try:
                fernet = Fernet(key_text.encode())
                with open(fname, "rb") as f:
                    encrypted_data = f.read()
                data = fernet.decrypt(encrypted_data)
                with open(DB_FILE, "wb") as f:
                    f.write(data)
                QMessageBox.information(self, "Success", 
                                      "Database imported successfully!\nPlease restart the application.")
                self.close()
                return
            except Exception as e:
                logger.error(f"Import error: {e}")
                QMessageBox.warning(self, "Error", "Invalid private key or corrupted file!")

# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    if os.path.exists(LOCK_FILE):
        QMessageBox.critical(None, "Locked", "Aplikacija je trajno zaključana zbog 3 neuspešna pokušaja!")
        sys.exit(1)

    attempt = 0
    key = None
    while attempt < 3:
        master_dlg = MasterPasswordDialog()
        if master_dlg.exec_() == QDialog.Accepted:
            master_pwd = master_dlg.get_password()
            if not validate_master_password(master_pwd):
                QMessageBox.warning(None, "Error", "Master password ne zadovoljava sigurnosna pravila!")
                attempt += 1
                continue
            
            key = generate_key(master_pwd)
            saved_key = load_key()
            
            if saved_key is None:
                create_db(key)
                save_key(key)
                break
            elif saved_key == key:
                if not os.path.exists(DB_FILE):
                    create_db(key)
                break
            else:
                QMessageBox.warning(None, "Error", "Pogrešan master password!")
                attempt += 1
        else:
            sys.exit(0)
    else:
        with open(LOCK_FILE, "w") as f:
            f.write("locked due to 3 failed attempts")
        QMessageBox.critical(None, "Locked", "3 neuspešna pokušaja! Aplikacija je trajno zaključana!")
        sys.exit(1)

    main_win = MainWindow(key)
    main_win.show()
    sys.exit(app.exec_())
