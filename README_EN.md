# ZeroBreach 🔐  
### Version 1.0 – Local • Zero-Knowledge • Enterprise Encryption

<p align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue)
![UI](https://img.shields.io/badge/UI-PyQt5-green)
![Cryptography](https://img.shields.io/badge/crypto-cryptography%2046.0.5-darkred)
![Encryption](https://img.shields.io/badge/Encryption-AES--128-red)
![Security](https://img.shields.io/badge/Security-Zero--Knowledge-black)
![Storage](https://img.shields.io/badge/Storage-Local--Only-orange)
![License](https://img.shields.io/badge/License-GPLv3-brightgreen)

</p>

---

## 🛡 About the Project

**ZeroBreach** is a local password manager with enterprise-grade encryption that securely stores your passwords on your computer.

Its zero-knowledge architecture means that **no one except you with the master password can access the data**.

The application is 100% local, written in Python with a PyQt5 interface, offering a secure alternative to cloud-based password managers.

---

## 🎯 Intended For

- 👤 Individuals who want complete control over their data  
- 🏢 Small businesses that don’t trust cloud solutions  
- 🔐 Security enthusiasts seeking enterprise-level encryption without a subscription  
- 💻 Developers who want an open-source alternative to commercial managers  

---

## ❓ Why ZeroBreach?

### Issues with Cloud Managers

- Hacks (e.g., LastPass 2022)  
- GDPR complications  
- Vendor lock-in  
- Subscription costs €3–5/month (36–60€/year)  
- You must trust a third party with your sensitive data  

---

## 🚀 Key Advantages

- 🖥 **LOCAL** – Data never leaves your device  
- 💰 **FREE** – No subscription required  
- 🔑 **CONTROL** – You own the encryption key  
- 👁 **OPEN-SOURCE** – Every line of code can be verified  

---

## 📊 ZeroBreach vs Popular Password Managers

| Feature | ZeroBreach | Bitwarden | LastPass | 1Password | KeePass |
|---------|------------|-----------|----------|-----------|---------|
| 🚫 100% Offline | ✅ | ❌ Cloud | ❌ Cloud | ❌ Cloud | ✅ (legacy UI) |
| 💰 Completely Free Forever | ✅ €0 | ❌ €10/year | ❌ €36/year | ❌ €36/year | ✅ |
| 🔧 Size (~100MB) | ✅ 100MB | ❌ | ❌ | ❌ | ❌ |
| ⚙️ Custom PBKDF2 (100k iter) | ✅ Bank-level | ❌ Standard | ❌ | ❌ | ❌ |
| 🎨 Modern PyQt5 Fusion UI | ✅ 2026 look | ❌ Web-based | ❌ Web-based | ✅ | ❌ XP look |
| 🔍 Instant Search (SQLite) | ✅ <50ms | ❌ | ❌ | ✅ | ❌ |
| 🧹 Auto Re-encrypt | ✅ Change master = instant | ❌ Manual | ❌ | ❌ | ❌ |
| 🔒 3-attempt HARD LOCK | ✅ Persistent lock.dat | ❌ Soft lock | ❌ | ❌ | ❌ |
| 📝 Comment Column (searchable) | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 🏗 Technical Architecture

![ZeroBreach UI](tehnicka_arhitektura.png)

---

## 📷 Application Screenshot

![ZeroBreach UI](ss.png)

---

## 🔐 Security Model

Master Password → PBKDF2 (100,000 iterations + 16B salt) → master.key → Fernet (AES-128) → SQLite database

### Security Features

- PBKDF2 – 100,000 iterations  
- 16-byte salt (`salt.bin`)  
- SHA256 key derivation  
- AES-128 encryption (Fernet)  
- 3 incorrect attempts → PERMANENT lock (`lock.dat`)  
- Without `master.key` → DATA IS UNREADABLE (even by the author)  
- No cloud sync  

---

## 🔄 Application Life-Cycle

1. Installation → Set Master Password → Empty database  
2. Add passwords → Daily usage  
3. Backup → Export DB + Private Key  
4. Migration → Copy folder to a new computer  
5. Recovery → Import DB + Private Key  

---

## ⭐ Unique Values

- Data never leaves your computer  
- Free forever  
- Bank-grade protection (PBKDF2 100k)  
- Instant search – zero lag  
- Single `.exe` build  
- Full transparency  

---

## ⚙ Functionalities

### ➕ Add / Edit Password

1. Click **Add** or **Edit**  
2. Enter: Username*, Password*, URL, Comment  
3. Click **Generate Password**  
4. Click **Save**

---

### 🔎 Search

- Searches Username, URL, and Comment  
- Real-time filtering  
- Status indicator: `🔍 Found X of Y entries`

---

### 👁 Show Password

1. Click **👁 Show**  
2. Password appears instead of `🔒 *****`  
3. Click again to hide  

---

### 🔑 Change Master Password

1. Tools → Change Master Password  
2. Enter old password  
3. Enter new password (twice)  
4. Automatic re-encryption of all data  

---

### 📤 Export / Import

#### Export

1. Click **Export DB**  
2. ALWAYS save the PRIVATE KEY  
3. Without the key → data permanently lost  

#### Import

1. Click **Import DB**  
2. Select `.db` file  
3. Enter PRIVATE KEY  
4. Restart the application  

---

## 🛡 Security

### Master Password

- 3 incorrect attempts = PERMANENT lock  
- PBKDF2 (100,000 iterations)  
- SHA256 key derivation  
- 16-byte salt  

### Data

- AES-128 encryption  
- Local SQLite database  
- Automatic re-encryption on password change  

---

## 💾 Backup Strategy

1. Regularly export the DB  
2. Store PRIVATE KEY securely (USB + offline backup)  
3. Test import on another machine  

---

## 🧠 Preventive Measures

| Frequency | Action |
|-----------|--------|
| DAILY | Test "Show" on 2–3 passwords |
| WEEKLY | Export DB |
| MONTHLY | Test Import |
| EVERY TIME | Backup PRIVATE KEY |
| NEVER | Change master password without backup |

---

## 🧩 Common Issues & Solutions

| Issue | Solution |
|-------|---------|
| DECRYPT ERROR | Wrong master password or corrupted DB |
| Application locked | Delete `lock.dat` |
| Search not working | Restart the application |
| Import fails | Check PRIVATE KEY |

---

## 📁 Folder Structure


C:\Users[User]\AppData\Local\ZeroBreach\

master.key → PBKDF2-derived key (32B)
salt.bin → Salt (16B)
passwords.db → Encrypted database
lock.dat → Lock file


---

## ⚠ Reset (Lose All Data)

1. Delete the entire ZeroBreach folder  
2. Launch the application → fresh installation  

---

## 📜 License

This project is released under the **GPLv3** license.  
If you use or modify the code, you must retain authorship and release changes under the same license.

---

> 🔐 Security First. Privacy Always.  
> Zero Knowledge Means Zero Trust.
