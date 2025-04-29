import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
import csv
from datetime import datetime
import platform
import subprocess
import barcode 
from barcode.writer import ImageWriter
import firebase_admin
from firebase_admin import credentials, firestore
import threading
import time
import sys
import os

firebaseSuccess = False
def resource_path(relative_path):
    try:
        # PyInstaller'da temp klasörü
        base_path = sys._MEIPASS
    except Exception:
        # Normal çalıştırma
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def initializeFirebase():
    global firebaseSuccess, db
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(resource_path("firebase-key.json"))
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        testDoc = db.collection("tryConnection").document("ping")
        testDoc.set({"time": datetime.now()})
        firebaseSuccess = True

    except Exception as e:
        print("Firebase connection failed:", e)
        firebaseSuccess = False

def showConnectionError():
    errorWin = tk.Toplevel()
    errorWin.title("Bağlantı Hatası")
    errorWin.geometry("400x200")
    errorWin.configure(bg="#ffdddd")

    tk.Label(errorWin, text="Firebase bağlantısı sağlanamadı.", font=("Arial", 12, "bold"), bg="#ffdddd", fg="red").pack(pady=20)
    tk.Label(errorWin, text="Lütfen internet bağlantınızı kontrol edin.", bg="#ffdddd").pack(pady=10)
    tk.Button(errorWin, text="Tamam", command=lambda: window.destroy(), bg="white").pack(pady=20)

def showSplashScreen():
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    splash.geometry("400x250+500+250")
    splash.configure(bg="#ffffff")
    splash.protocol("WM_DELETE_WINDOW", lambda: None)

    try:
        splashImg = Image.open(resource_path("splash.png")).resize((350, 200))
        splashTk = ImageTk.PhotoImage(splashImg)
        tk.Label(splash, image=splashTk, bg="#ffffff").pack()
        splash.image = splashTk
    except:
        tk.Label(splash, text="Barkod Uygulaması", font=("Helvetica", 18, "bold"), bg="#ffffff").pack(pady=30)

    tk.Label(splash, text="Barkod sistemi başlatılıyor...", font=("Arial", 11), bg="#ffffff", fg="#555555").pack(pady=10)

    def tryConnection():
        nonlocal splash
        startTime = datetime.now()

        thread = threading.Thread(target=initializeFirebase)
        thread.start()
        thread.join(timeout=10)

        elapsed = (datetime.now() - startTime).total_seconds()
        remaining = max(0, 4 - elapsed)
        time.sleep(remaining)

        window.after(0, splash.destroy)
        if firebaseSuccess:
            window.deiconify()
        else:
            showConnectionError()

    threading.Thread(target=tryConnection).start()

window = tk.Tk()
window.withdraw()
showSplashScreen()

try:
    window.iconbitmap("barkodlogo.ico")
except:
    pass
window.title("Barkod Uygulaması")
window.state('zoomed') 

style = ttk.Style()
style.theme_use("default")

# Satırlar arasında çizgi görünmesi için grid özelliğini açıyoruz
style.configure("Treeview", 
    background="#ffffff",
    foreground="black",
    rowheight=25,
    fieldbackground="#ffffff",
    bordercolor="#c0c0c0",
        font=('Segoe UI', 10),
    borderwidth=1

)

style.map("Treeview", background=[('selected', '#cce5ff')])
style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'), relief="flat")

# Alternatif satır renklendirme (çizgi etkisi)
tree_tag_config = {
    "oddrow": {"background": "#f2f2f2"},
    "evenrow": {"background": "#ffffff"}
}
# Satır çizgilerini açık hale getir
style.layout("Treeview", [
    ('Treeview.treearea', {'sticky': 'nswe'})
])

# Genel ayarlar
queueFile = "queueNumber.txt"
csvFile = "dataRecord.csv"
barcodeFolder = "barcodes"
columns = [
    "Sıra No", "Teslim Eden", "Arıza", "Teslim Alan", "İlgili Personel",
    "Cihaz Tipi", "Marka/Model", "Teslim Tarihi", "Durum", "Açıklama"
]

if not os.path.exists(barcodeFolder):
    os.makedirs(barcodeFolder)
lastBarcodePath = ""

def getQueueNumber():
    if os.path.exists(queueFile):
        with open(queueFile, "r") as f:
            return int(f.read())
    return 1

def incrementQueueNumber(nextNumber):
    with open(queueFile, "w") as f:
        f.write(str(nextNumber))

def saveToFirebase(data):
    doc_ref = db.collection("barcode").document(data["Sıra No"])
    doc_ref.set(data)

def createBarcode():
    if not entry_gonderen.get().strip():
        messagebox.showwarning("Eksik Bilgi", "Lütfen 'Teslim Eden' alanını doldurunuz.")
        return

    global lastBarcodePath
    queueNumber = getQueueNumber()
    barcodeData = f"{datetime.now().strftime('%Y%m%d')}-{queueNumber}"

    data = {
        "Sıra No": str(queueNumber),
        "Teslim Eden": entry_gonderen.get(),
        "Arıza": entry_ariza.get(),
        "Teslim Alan": entry_teslim.get(),
        "İlgili Personel": entry_personel.get(),
        "Cihaz Tipi": entry_tip.get(),
        "Marka/Model": entry_model.get(),
        "Teslim Tarihi": dateEntry.get() if dateVar.get() and dateEntry.get().strip() else datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "Durum": entry_durum.get(),
        "Açıklama": entry_aciklama.get()
    }

    # Barkod görseli oluşturma
    barcodePath = os.path.join(barcodeFolder, f"BARCODE_{queueNumber}")
    code128 = barcode.get("code128", barcodeData, writer=ImageWriter())  
    filename = code128.save(barcodePath)

    # Barkodu tkinter'da göster
    img_open = Image.open(filename).resize((300, 100))
    img_tk = ImageTk.PhotoImage(img_open)
    barcodeLabel.config(image=img_tk)
    barcodeLabel.image = img_tk

    lastBarcodePath = filename
    saveToCsv(data)
    saveToFirebase(data)
    incrementQueueNumber(queueNumber + 1)
    tree.insert("", tk.END, values=[data[col] for col in columns])
    messagebox.showinfo("Başarılı", f"{queueNumber} numaralı barkod oluşturuldu.")


def barcodePrint():
    if not lastBarcodePath:
        messagebox.showwarning("Uyarı", "Henüz bir barkod oluşturulmadı.")
        return
    try:
        if platform.system() == "Windows":
            os.startfile(lastBarcodePath, "print")
        else:
            subprocess.run(["lp", lastBarcodePath])
        messagebox.showinfo("Yazdırılıyor", "Barkod yazıcıya gönderildi.")
    except Exception as e:
        messagebox.showerror("Hata", f"Yazdırma hatası: {str(e)}")

def printBarcodeSelectedRow():
    selected = tree.focus()
    if not selected:
         messagebox.showwarning("Uyarı", "Bir kayıt seçin.")

    data = tree.item(selected)["values"]
    queueNumber = data[0]
    barcodePath = os.path.join(barcodeFolder, f"Barkod_{ queueNumber}.png")
    if not os.path.exists(barcodePath):
        messagebox.showerror("Hata", "Barkod görseli bulunamadı.")
        return
    try:
        if platform.system() == "Windows":
            os.startfile(barcodePath, "print")
        else:
            subprocess.run(["lp", barcodePath])
        messagebox.showinfo("Yazdırılıyor", f"{ queueNumber} numaralı barkod yazdırılıyor.")
    except Exception as e:
        messagebox.showerror("Hata", str(e))

def saveToCsv(data):
    yeni = not os.path.exists(csvFile)
    with open(csvFile, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if yeni:
            writer.writeheader()
        writer.writerow(data)

def rewriteCsv(allData):
    with open(csvFile, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(allData)

def loadDataCsv():
    if os.path.exists(csvFile):
        with open(csvFile, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                tree.insert("", tk.END, values=[row.get(col, "") for col in columns], tags=(tag,))

def searchRecords():
    searcTerm = searchEntry.get().strip().lower()
    for row in tree.get_children():
        tree.delete(row)

    if not searcTerm:
        loadDataCsv()
        return

    with open(csvFile, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            satir = [row.get(col, "").lower() for col in columns]
            if any(searcTerm in hucre for hucre in satir):
                tree.insert("", tk.END, values=[row.get(col, "") for col in columns])

def createBarcodeFromFile(data):
    queueNumber = getQueueNumber()
    data["Sıra No"] = str( queueNumber)
    data["Teslim Tarihi"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    barcodePath = os.path.join(barcodeFolder, f"Barkod_{ queueNumber}.png")
    barcode.make("\n".join([f"{k}: {v}" for k, v in data.items()])).save(barcodePath)

    saveToCsv(data)
    saveToFirebase(data)
    incrementQueueNumber( queueNumber + 1)
    tree.insert("", tk.END, values=[data[col] for col in columns])
    messagebox.showinfo("Yeni Barkod", f"{ queueNumber} numaralı yeni barkod oluşturuldu.")

def orderModel():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Uyarı", "Bir kayıt seçin.")
        return
    data = tree.item(selected)["values"]

    window = tk.Toplevel()
    window.title("Kaydı Düzenle")
    window.geometry("500x600")

    entry_map = {}
    for i, col in enumerate(columns):
        tk.Label(window, text=col).pack()
        ent = tk.Entry(window, width=50)
        ent.pack()
        ent.insert(0, data[i])
        if col == "Sıra No":
            ent.config(state="disabled")
        entry_map[col] = ent

    def justSave():
        newData = [entry_map[col].get() for col in columns]
        tree.item(selected, values=newData)
        allData = [dict(zip(columns, tree.item(row)["values"])) for row in tree.get_children()]
        rewriteCsv(allData)
        saveToFirebase(dict(zip(columns, newData)))
        window.destroy()
        messagebox.showinfo("Güncellendi", "Kayıt başarıyla güncellendi.")

    def saveAndNewBarcode():
        yeni_data = {col: entry_map[col].get() for col in columns if col != "Sıra No"}
        createBarcodeFromFile(yeni_data)
        window.destroy()
    btn_kaydet_frame = tk.Frame(window, bg="#f5f5f5")
    btn_kaydet_frame.pack(pady=10)

    tk.Button(
        btn_kaydet_frame,
        text="Kaydet",
        command=justSave,
        bg="#1e88e5", fg="white"
    ).pack(side="left")

    tk.Button(
        btn_kaydet_frame,
        image=help_tk,
        command=lambda: messagebox.showinfo("Yardım", "Bu buton seçili kaydı günceller."),
        bg="#f5f5f5",
        activebackground="#f5f5f5",
        highlightthickness=0,
        bd=0,
        relief="flat"
    ).pack(side="left", padx=5)

    btn_barcode_frame = tk.Frame(window, bg="#f5f5f5")
    btn_barcode_frame.pack(pady=5)

    tk.Button(
        btn_barcode_frame,
        text="Kaydet ve Barkod Oluştur",
        command=saveAndNewBarcode,
        bg="#1e88e5", fg="white"
    ).pack(side="left")

    tk.Button(
        btn_barcode_frame,
        image=help_tk,
        command=lambda: messagebox.showinfo("Yardım", "Bu buton güncellenmiş veriyle yeni bir barkod oluşturur."),
        bg="#f5f5f5",
        activebackground="#f5f5f5",
        highlightthickness=0,
        bd=0,
        relief="flat"
    ).pack(side="left", padx=5)

    

# sekmeli yapı
tab = ttk.Notebook(window)
barcode_frame = tk.Frame(tab)
try:
    bg_img = ImageTk.PhotoImage(Image.open(resource_path("background.png")).resize((1000, 700)))
    bg_label = tk.Label(barcode_frame, image=bg_img)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    barcode_frame.bg_img = bg_img
except:
    barcode_frame.configure(bg="#eef5fc")

history_frame = tk.Frame(tab)
searchBox = tk.Frame(history_frame, bg="#eef5fc")
searchBox.pack(pady=5)
searchEntry = tk.Entry(searchBox, width=50)
searchEntry.pack(side="left", padx=5)
tk.Button(searchBox, text="Ara", command=searchRecords, bg="#43a047", fg="white").pack(side="left")


tab.add(barcode_frame, text="Barkod Oluştur")

tab.add(history_frame, text="Geçmiş")
tab.pack(expand=True, fill="both")

# Barkod form alanları
def nemInput(parent, label):
    tk.Label(parent, text=label).pack()
    entry = tk.Entry(parent, width=40)
    entry.pack()
    return entry

entry_gonderen = nemInput(barcode_frame, "Teslim Eden:")
entry_ariza = nemInput(barcode_frame, "Arıza:")
entry_teslim = nemInput(barcode_frame, "Teslim Alan:")
entry_personel = nemInput(barcode_frame, "İlgili Personel:")
entry_tip = nemInput(barcode_frame, "Cihaz Tipi:")
entry_model = nemInput(barcode_frame, "Marka/Model:")
entry_durum = nemInput(barcode_frame, "Durum:")
entry_aciklama = nemInput(barcode_frame, "Açıklama:")

# Tarih seçme kutusu ve giriş alanı
dateVar = tk.BooleanVar()
dateCheckbox = tk.Checkbutton(barcode_frame, text="Tarihi kendim seçmek istiyorum", variable=dateVar, command=lambda: dateEntry.config(state="normal" if dateVar.get() else "disabled"))
dateCheckbox.pack()

dateEntry = tk.Entry(barcode_frame, width=40, state="disabled")
dateEntry.insert(0, "GG.AA.YYYY")
dateEntry.pack(pady=5)


tk.Button(barcode_frame, text="Barkod Oluştur", command=createBarcode).pack(pady=10)
tk.Button(barcode_frame, text="Son Barkodu Yazdır", command=barcodePrint).pack(pady=5)
barcodeLabel = tk.Label(barcode_frame)
barcodeLabel.pack(pady=10)

# Görseli yükle (öncesinde tanımlanmalı)
help_img = Image.open(resource_path("help_icon.png")).resize((20, 20), resample=Image.LANCZOS)
help_tk = ImageTk.PhotoImage(help_img)

# Geçmiş sekmesi
tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=25)
tree.pack(padx=10, pady=10, fill="both", expand=True)
tree.tag_configure("oddrow", background="#f2f2f2")
tree.tag_configure("evenrow", background="#ffffff")


for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=120)




# --- Düzenle Buton Grubu ---
btnOrderFrame = tk.Frame(history_frame, bg="#eef5fc")
btnOrderFrame.pack(pady=5)

tk.Button(
    btnOrderFrame,
    text="Düzenle",
    command=orderModel,
    bg="#1e88e5", fg="white"
).pack(side="left")

tk.Button(
    btnOrderFrame,
    image=help_tk,
    command=lambda: messagebox.showinfo("Yardım", "Listeden seçilen kaydı düzenlemenizi veya yeni barkod oluşturmanızı sağlar."),
    bg="#eef5fc",
    activebackground="#eef5fc",     # <- Bu satır çok önemli
    highlightthickness=0,
    bd=0,
    relief="flat"
).pack(side="left", padx=5)

# --- Barkod Yazdır Buton Grubu ---
btnPrintFrame = tk.Frame(history_frame, bg="#eef5fc")
btnPrintFrame.pack(pady=5)

tk.Button(
    btnPrintFrame,
    text="Barkod Yazdır",
    command=printBarcodeSelectedRow,
    bg="#1e88e5", fg="white"
).pack(side="left")

tk.Button(
    btnPrintFrame,
    image=help_tk,
    command=lambda: messagebox.showinfo("Yardım", "Listede seçilen satıra ait barkod görselini yazıcıya gönderir."),
    bg="#eef5fc",
    activebackground="#eef5fc",   
    highlightthickness=0,           
    bd=0,
    relief="flat"
).pack(side="left", padx=5)
# Yardım ikonu referansını kaybetmemek için
history_frame.help_tk = help_tk

# Çift tıklama ile yazdırma
tree.bind("<Double-1>", lambda e: printBarcodeSelectedRow())

# CSV'den kayıtları yükle
loadDataCsv()

def showErrorScreen():
    error_win = tk.Toplevel()
    error_win.title("Bağlantı Hatası")
    error_win.geometry("400x200")
    error_win.configure(bg="#ffdddd")

    tk.Label(error_win, text="Firebase bağlantısı sağlanamadı.", font=("Arial", 12, "bold"), bg="#ffdddd", fg="red").pack(pady=20)
    tk.Label(error_win, text="Lütfen internet bağlantınızı kontrol edin.", bg="#ffdddd").pack(pady=10)

    tk.Button(error_win, text="Tamam", command=lambda: window.destroy(), bg="white").pack(pady=20)


window.mainloop()