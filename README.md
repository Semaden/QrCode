**QR/Barkod Tabanlı Cihaz Takip Sistemi**

Bu proje, bilgisayar ve benzeri cihazların tamir, mail kurulumu, Netsis kurulumu gibi işlem süreçlerini kolay takip edebilmek amacıyla staj yaptığım kurumda doğan anlık ihtiyaca yönelik geliştirilmiştir.

Ilk aşamada QR kod ile bir sistem kurulmuş, fakat herkesin telefonuyla QR kod okuyabilmesi nedeniyle güvenlik endişesi oluşmuş ve bu nedenle proje, barkod tabanlı el terminali ile okuma yapabilecek şekilde güncellenmiştir.



**Proje İçeriği**

✔️ QR Kod Üretimi

✔️ Barkod (Code128) Üretimi

✔️ Firebase Firestore'a veri kayıt

✔️ CSV dosyasına kayıt

✔️ Tkinter tabanlı grafik arayüz

✔️ Splash ekranı ile güzel başlangıç

✔️ Yardım ikonları ve detaylı kullanıcı deneyimi

✔️ Firebase bağlantı kontrol mekanizması

✔️ PyInstaller ile çıktı alarak .exe dosyasına dönüşütürülebilme



**Kullanılan Teknolojiler**

Python 3.8+

Tkinter

Pillow (PIL)

Pyrebase / firebase_admin

python-barcode

PyInstaller



**Kurulum**

Gerekli paketleri yükleyin:

pip install pillow firebase-admin python-barcode pyinstaller

Firebase için bir proje oluşturun ve bir Service Account Key indirin.

Dosya yapınız şu şekilde olmalı:

```
.
|— background.png
|— help_icon.png
|— logo.ico
|— splash.png
|— veri_kaydi.csv (veya dataRecord.csv)
|— queueNumber.txt
|— qr_ureticisi.py (veya barcode_ureticisi.py)
|— firebase-key.json 
|— qr_codes/ (klasör)(veya barcodes
```



**Projenin .EXE Formatına Çevrilmesi**

```
pyinstaller --noconsole --onefile --name "İŞ Takip Uygulaması" \
--add-data "splash.png;." \
--add-data "logo.ico;." \
--add-data "background.png;." \
--add-data "help_icon.png;." \
--add-data "firebase-key.json;." \
--add-data "dataRecord.csv;." \
--add-data "queueNumber.txt;." \
--add-data "qr_codes;qr_codes" \
--icon=logo.ico qr_ureticisi.py
```
