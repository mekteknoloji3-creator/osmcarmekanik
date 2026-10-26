"""
OSM CAR MEKANİK - Web sitesi (sadece Python, ek paket gerekmez)

Çalıştırmak için: PyCharm'da bu dosyaya sağ tık > Run 'main'
Tarayıcı otomatik açılır: http://localhost:8000
Değişiklik yapınca kaydet, Stop/Run yap, tarayıcıda F5'e bas.
"""
import datetime
import gzip
import html
import mimetypes
from pathlib import Path
from urllib.parse import quote, unquote
import json
import http.server
import socketserver
import webbrowser

# =====================================================================
# BURAYI DÜZENLE: yazılar, telefon, adres, hizmetler
# =====================================================================
MARKA_1 = "OSM CAR"
MARKA_2 = "MEKANİK"
USTA = "OSMAN BULUT"
SLOGAN = "Aracınız Emin Ellerde"          # üstteki büyük slogan
ALT_SLOGAN = "Doğru Bakım, Güvenli Yol"   # sayfanın en altındaki slogan
ACIKLAMA = "Motor, alt takım, yağ ve antifriz değişimi, genel bakım ve onarım. Sivas'ta güvenle gelebileceğiniz sanayi ustası."

TELEFON = "0552 856 12 48"                # ekranda görünen
TELEFON_NO = "905528561248"               # arama/WhatsApp için: başında 90, boşluksuz
ADRES = "Gültepe Mah. 51. Sanayi Sokak No: 10 T, Sivas / Merkez"
SAATLER = ["Pazartesi – Cumartesi: 08.30 – 18.30", "Pazar: Kapalı"]   # saatleri kendine göre değiştir
HARITA = "https://www.google.com/maps/search/?api=1&query=G%C3%BCltepe+Mah.+51.+Sanayi+Sokak+10+Sivas"

# Renkler (kartvizitten)
RENK_SIYAH = "#0c0c0d"
RENK_KIRMIZI = "#e5311f"
RENK_TURUNCU = "#f59a00"

HIZMETLER = [
    ("Motor Mekanik", "Motor bakım, onarım, triger, conta ve kafa işleri. Parça seçimini sizinle konuşuruz."),
    ("Alt Takım", "Amortisör, rotil, rotbaşı, salıncak, helezon yayı ve yürüyen aksam kontrolü."),
    ("Yağ Değişimi", "Motor yağı ve filtre değişimi. Aracınıza uygun yağı birlikte seçeriz."),
    ("Antifriz Değişimi", "Soğutma sistemi kontrolü, antifriz değişimi, radyatör ve hortum bakımı."),
    ("Genel Bakım ve Onarım", "Periyodik bakım, fren sistemi, arıza tespit ve mevsim öncesi kontrol."),
]

# (belirti, olası neden başlığı, açıklama)
BELIRTILER = [
    ("Motor lambası yanıyor", "Motor hata kodu var",
     "Sensör, ateşleme ya da yakıt sistemi kaynaklı olabilir. Kontrolde nedeni net görürüz."),
    ("Tak tak sesi geliyor", "Alt takım elemanı gevşemiş olabilir",
     "Çukurda ya da virajda ses geliyorsa rotil, salıncak burcu veya amortisör üstü rulmanı kontrol edilmeli."),
    ("Araç bir yöne çekiyor", "Rot-balans ya da lastik sorunu",
     "Ön düzen bozulmuş, lastik basıncı farklı ya da aksam aşınmış olabilir."),
    ("Motor ısınıyor", "Soğutma sistemi arızası",
     "Antifriz eksikliği, termostat, radyatör ya da su pompası olabilir. Aracı çalıştırmadan getirmeniz iyi olur."),
    ("Direksiyon titriyor", "Balans ya da fren diski",
     "Hız arttıkça titriyorsa balans, frende titriyorsa disk eğriliği olabilir."),
    ("Fren sesi çıkarıyor", "Balata aşınmış olabilir",
     "Fren yaparken ıslık ya da sürtme sesi balatanın bittiğini gösterebilir. Geç kalmadan baktırın."),
    ("Egzozdan duman çıkıyor", "Yağ, yakıt veya soğutma kaynaklı olabilir",
     "Mavi duman yağ yakmayı, siyah duman fazla yakıtı, beyaz duman soğutma suyu sorununu düşündürür. Kontrol gerekir."),
    ("Yağ lambası yandı", "Yağ basıncı düşük olabilir",
     "Aracı hemen durdurup motoru kapatın. Yağ seviyesine bakın, lamba sönmüyorsa aracı çalıştırmadan bize getirin."),
]

ACILIS, KAPANIS = "08:30", "18:30"   # çalışma saatleri (yukarıdaki SAATLER ile aynı olsun)
KAPALI_GUNLER = [0]                  # 0 = Pazar, 6 = Cumartesi (kapalı olan günleri yaz)
INSTAGRAM = ""                       # örnek: "https://instagram.com/osmcarmekanik" (boşsa görünmez)
SITE_ADRESI = ""                     # internete koyunca buraya adres yaz, örnek: "https://osmcar.com"

# Neden biz? (kendi işine uygun olanları bırak, diğerlerini sil/değiştir)
NEDEN = [
    ("Önce teşhis", "Arızayı tespit eder, ne yapılacağını ve fiyatı işe başlamadan söyleriz."),
    ("Eski parçayı gösteririz", "Değişen parçayı size teslim eder, neden değiştiğini anlatırız."),
    ("Doğru parça", "Aracınıza uygun parçayı birlikte seçeriz."),
    ("Sanayide, ulaşımı kolay", "Gültepe 51. Sanayi Sokak'tayız, aracınızı bırakıp işinize gidebilirsiniz."),
]

SSS = [
    ("Randevu şart mı?", "Hayır, gelebilirsiniz. Ama yoğunluk için önce aramanız veya WhatsApp'tan yazmanız iyi olur."),
    ("Fiyatı önceden öğrenebilir miyim?", "Arıza belli ise telefonda yaklaşık fiyat söyleriz. Kesin fiyat araç görüldükten sonra verilir."),
    ("Kendi parçamı getirebilir miyim?", "Parçayı görüp uygunsa takarız. Ayrıntı için bizi arayın."),
    ("Araç ne kadar sürede çıkar?", "İşe göre değişir. Yağ ve antifriz gibi işler kısa sürer, motor işleri daha uzun sürebilir."),
]

# YORUM HAVUZU: müşterilerin gerçek ve onaylı yorumlarını biriktir. Site her hafta havuzdaki en iyi (4-5 yıldız)
# yorumlardan YORUM_SAYISI kadarını gösterir, hafta değişince seçim de değişir. Yorumları sen onaylarsın.
# Gerçek yorumları (isim, yorum, yıldız) şeklinde ekle. Yıldız 1-5, yazmazsan 5.
YORUMLAR = []   # örnek: [("Ahmet K.", "Aracımı çok güzel yaptılar, teşekkürler.", 5)]

CEKICI_NO = ""        # çekici/yol yardım için ayrı numara varsa yaz (başında 90). Boşsa ana numara aranır
GOOGLE_YORUM = ""     # Google Haritalar yorum linkin varsa yapıştır (boşsa buton görünmez)
YAG_ARALIK = 10000    # yağ değişimi aralığı (km) - hesaplayıcı bunu kullanır
ANTIFRIZ_ARALIK = 60000   # antifriz değişimi aralığı (km)

# Sayfanın arasında çıkan sloganlar (istediğini değiştir, ekle, sil)
SLOGANLAR = [
    "Aracınız Emin Ellerde",
    "Sesini dinler, sorununu buluruz",
    "Önce teşhis, sonra fiyat",
    "Doğru Bakım, Güvenli Yol",
    "Sanayide usta işi",
    "Her kilometrede güven",
    "Yolun açık, motorun sağlam olsun",
    "Arıza küçükken gel, cebin büyümesin",
    "Motorun sesi bizden sorulur",
    "Güvenle bırak, rahatça al",
    "Önce ses, sonra çözüm",
    "Sivas sanayinin usta eli",
    "Yağın, antifrizin, frenin: bizde tamam",
    "Yolda kalma, bize uğra",
    "Aracına usta eli değsin",
    "Bakımın zamanı gelince biz buradayız",
]

EPOSTA = ""           # örnek: "osmcar@gmail.com" (boşsa görünmez)
TIKTOK = ""           # örnek: "https://tiktok.com/@osmcarmekanik" (boşsa görünmez)
# Instagram adresini yukarıdaki INSTAGRAM satırına yaz.
# GÖRSELLER: main.py'nin yanındaki "gorseller" klasörüne fotoğraf (jpg/png/webp) at, site otomatik "Çalışmalarımızdan kareler" bölümünü açar.
# Hızlı açılması için fotoğrafları telefonda küçültüp (yaklaşık 1000-1200 piksel genişlik) at.

YORUM_SAYISI = 10     # sitede aynı anda görünecek yorum sayısı (her hafta yenisi seçilir)
DEMO_YORUM = False    # True yaparsan sadece YERLEŞİMİ görmek için "ÖRNEK" etiketli boş kartlar çıkar (gerçek sitede kapalı kalsın)
DUYURU = ""           # sayfanın en üstünde sarı şerit olarak çıkar. Örnek: "Kış bakımı: antifriz kontrolü ücretsiz" (boşsa görünmez)
HAKKINDA = "Osman Bulut, Sivas Gültepe 51. Sanayi Sokak'ta motor, alt takım ve genel bakım işleri yapıyor. Aracınızı bırakırken sorununuzu dinler, ne yapılacağını anlatır."

# "Aracın hazır mı?" kontrol listesi
LISTE = ["Yağ ve yağ filtresi", "Antifriz seviyesi", "Akü", "Fren balataları", "Lastik basıncı ve diş derinliği",
         "Silecek ve cam suyu", "Far, stop ve sinyal lambaları"]

PORT = 8000
# =====================================================================
# Aşağısı sayfayı oluşturur, değiştirmen gerekmez
# =====================================================================

# Rehbere kaydet QR kodu (kişi kartı: Osman Bulut, 0552 856 12 48, adres).
# Telefon numarasını değiştirirsen bu QR eski numarada kalır, bana yaz yenisini yapayım.
QR_PATH = "M2 2h7v1h-7zM12 2h3v1h-3zM16 2h3v1h-3zM20 2h1v1h-1zM22 2h3v1h-3zM26 2h3v1h-3zM31 2h4v1h-4zM36 2h4v1h-4zM42 2h1v1h-1zM44 2h7v1h-7zM2 3h1v1h-1zM8 3h1v1h-1zM10 3h2v1h-2zM13 3h2v1h-2zM18 3h8v1h-8zM28 3h1v1h-1zM31 3h2v1h-2zM35 3h1v1h-1zM39 3h4v1h-4zM44 3h1v1h-1zM50 3h1v1h-1zM2 4h1v1h-1zM4 4h3v1h-3zM8 4h1v1h-1zM10 4h1v1h-1zM13 4h2v1h-2zM16 4h3v1h-3zM22 4h1v1h-1zM25 4h1v1h-1zM28 4h1v1h-1zM30 4h3v1h-3zM34 4h1v1h-1zM36 4h2v1h-2zM41 4h2v1h-2zM44 4h1v1h-1zM46 4h3v1h-3zM50 4h1v1h-1zM2 5h1v1h-1zM4 5h3v1h-3zM8 5h1v1h-1zM12 5h3v1h-3zM21 5h2v1h-2zM27 5h3v1h-3zM31 5h1v1h-1zM33 5h1v1h-1zM35 5h1v1h-1zM37 5h1v1h-1zM39 5h1v1h-1zM41 5h1v1h-1zM44 5h1v1h-1zM46 5h3v1h-3zM50 5h1v1h-1zM2 6h1v1h-1zM4 6h3v1h-3zM8 6h1v1h-1zM10 6h1v1h-1zM13 6h1v1h-1zM15 6h3v1h-3zM22 6h1v1h-1zM24 6h9v1h-9zM34 6h2v1h-2zM44 6h1v1h-1zM46 6h3v1h-3zM50 6h1v1h-1zM2 7h1v1h-1zM8 7h1v1h-1zM10 7h1v1h-1zM12 7h1v1h-1zM14 7h1v1h-1zM20 7h2v1h-2zM24 7h1v1h-1zM28 7h3v1h-3zM35 7h1v1h-1zM37 7h4v1h-4zM44 7h1v1h-1zM50 7h1v1h-1zM2 8h7v1h-7zM10 8h1v1h-1zM12 8h1v1h-1zM14 8h1v1h-1zM16 8h1v1h-1zM18 8h1v1h-1zM20 8h1v1h-1zM22 8h1v1h-1zM24 8h1v1h-1zM26 8h1v1h-1zM28 8h1v1h-1zM30 8h1v1h-1zM32 8h1v1h-1zM34 8h1v1h-1zM36 8h1v1h-1zM38 8h1v1h-1zM40 8h1v1h-1zM42 8h1v1h-1zM44 8h7v1h-7zM10 9h1v1h-1zM13 9h1v1h-1zM17 9h4v1h-4zM24 9h1v1h-1zM28 9h3v1h-3zM32 9h1v1h-1zM34 9h5v1h-5zM40 9h3v1h-3zM2 10h2v1h-2zM5 10h1v1h-1zM8 10h2v1h-2zM13 10h1v1h-1zM15 10h1v1h-1zM18 10h1v1h-1zM20 10h1v1h-1zM22 10h10v1h-10zM33 10h1v1h-1zM36 10h1v1h-1zM38 10h3v1h-3zM42 10h1v1h-1zM44 10h3v1h-3zM48 10h2v1h-2zM3 11h2v1h-2zM6 11h2v1h-2zM9 11h1v1h-1zM11 11h1v1h-1zM13 11h3v1h-3zM23 11h1v1h-1zM26 11h1v1h-1zM29 11h1v1h-1zM34 11h1v1h-1zM37 11h1v1h-1zM39 11h1v1h-1zM46 11h3v1h-3zM50 11h1v1h-1zM8 12h2v1h-2zM12 12h2v1h-2zM16 12h3v1h-3zM22 12h3v1h-3zM26 12h3v1h-3zM33 12h2v1h-2zM38 12h1v1h-1zM42 12h4v1h-4zM47 12h1v1h-1zM50 12h1v1h-1zM2 13h1v1h-1zM6 13h2v1h-2zM9 13h2v1h-2zM13 13h5v1h-5zM19 13h1v1h-1zM21 13h1v1h-1zM26 13h1v1h-1zM29 13h2v1h-2zM33 13h3v1h-3zM38 13h1v1h-1zM41 13h1v1h-1zM43 13h1v1h-1zM46 13h1v1h-1zM50 13h1v1h-1zM2 14h1v1h-1zM7 14h3v1h-3zM12 14h1v1h-1zM14 14h1v1h-1zM16 14h1v1h-1zM18 14h4v1h-4zM24 14h1v1h-1zM26 14h2v1h-2zM29 14h3v1h-3zM33 14h2v1h-2zM37 14h2v1h-2zM41 14h1v1h-1zM45 14h2v1h-2zM48 14h3v1h-3zM3 15h1v1h-1zM5 15h1v1h-1zM9 15h1v1h-1zM12 15h1v1h-1zM14 15h1v1h-1zM18 15h1v1h-1zM20 15h2v1h-2zM24 15h1v1h-1zM30 15h1v1h-1zM33 15h2v1h-2zM36 15h1v1h-1zM41 15h2v1h-2zM46 15h4v1h-4zM2 16h3v1h-3zM8 16h2v1h-2zM15 16h3v1h-3zM20 16h1v1h-1zM27 16h2v1h-2zM31 16h2v1h-2zM35 16h1v1h-1zM37 16h4v1h-4zM43 16h2v1h-2zM46 16h3v1h-3zM50 16h1v1h-1zM3 17h1v1h-1zM5 17h3v1h-3zM9 17h7v1h-7zM17 17h1v1h-1zM19 17h1v1h-1zM22 17h1v1h-1zM28 17h4v1h-4zM36 17h1v1h-1zM38 17h5v1h-5zM46 17h2v1h-2zM50 17h1v1h-1zM4 18h1v1h-1zM6 18h3v1h-3zM15 18h2v1h-2zM19 18h3v1h-3zM24 18h3v1h-3zM31 18h2v1h-2zM34 18h2v1h-2zM37 18h3v1h-3zM41 18h1v1h-1zM44 18h7v1h-7zM2 19h3v1h-3zM11 19h1v1h-1zM13 19h1v1h-1zM22 19h2v1h-2zM25 19h2v1h-2zM28 19h1v1h-1zM30 19h2v1h-2zM33 19h2v1h-2zM37 19h1v1h-1zM39 19h2v1h-2zM43 19h1v1h-1zM45 19h1v1h-1zM48 19h3v1h-3zM2 20h2v1h-2zM5 20h1v1h-1zM7 20h2v1h-2zM10 20h4v1h-4zM15 20h1v1h-1zM17 20h2v1h-2zM23 20h2v1h-2zM27 20h2v1h-2zM31 20h1v1h-1zM34 20h1v1h-1zM37 20h3v1h-3zM41 20h1v1h-1zM43 20h2v1h-2zM46 20h1v1h-1zM50 20h1v1h-1zM2 21h1v1h-1zM5 21h1v1h-1zM9 21h1v1h-1zM16 21h1v1h-1zM21 21h2v1h-2zM24 21h2v1h-2zM28 21h2v1h-2zM31 21h1v1h-1zM33 21h1v1h-1zM36 21h3v1h-3zM47 21h2v1h-2zM2 22h1v1h-1zM4 22h1v1h-1zM6 22h5v1h-5zM15 22h2v1h-2zM18 22h1v1h-1zM20 22h5v1h-5zM26 22h1v1h-1zM28 22h3v1h-3zM32 22h2v1h-2zM35 22h2v1h-2zM38 22h1v1h-1zM41 22h1v1h-1zM44 22h1v1h-1zM47 22h1v1h-1zM50 22h1v1h-1zM2 23h4v1h-4zM10 23h1v1h-1zM14 23h2v1h-2zM19 23h5v1h-5zM26 23h2v1h-2zM29 23h2v1h-2zM34 23h1v1h-1zM39 23h1v1h-1zM41 23h1v1h-1zM45 23h1v1h-1zM47 23h1v1h-1zM49 23h1v1h-1zM2 24h2v1h-2zM6 24h6v1h-6zM15 24h1v1h-1zM18 24h3v1h-3zM24 24h9v1h-9zM36 24h2v1h-2zM39 24h2v1h-2zM42 24h5v1h-5zM48 24h3v1h-3zM3 25h2v1h-2zM6 25h1v1h-1zM10 25h2v1h-2zM13 25h1v1h-1zM15 25h1v1h-1zM19 25h1v1h-1zM21 25h2v1h-2zM24 25h1v1h-1zM28 25h3v1h-3zM32 25h2v1h-2zM35 25h1v1h-1zM38 25h2v1h-2zM42 25h1v1h-1zM46 25h2v1h-2zM49 25h1v1h-1zM2 26h1v1h-1zM4 26h1v1h-1zM6 26h1v1h-1zM8 26h1v1h-1zM10 26h1v1h-1zM12 26h2v1h-2zM16 26h2v1h-2zM19 26h2v1h-2zM24 26h1v1h-1zM26 26h1v1h-1zM28 26h5v1h-5zM34 26h6v1h-6zM41 26h2v1h-2zM44 26h1v1h-1zM46 26h2v1h-2zM49 26h2v1h-2zM2 27h3v1h-3zM6 27h1v1h-1zM10 27h1v1h-1zM12 27h3v1h-3zM16 27h4v1h-4zM21 27h1v1h-1zM24 27h1v1h-1zM28 27h1v1h-1zM30 27h1v1h-1zM34 27h1v1h-1zM36 27h2v1h-2zM42 27h1v1h-1zM46 27h2v1h-2zM50 27h1v1h-1zM2 28h2v1h-2zM5 28h6v1h-6zM12 28h3v1h-3zM17 28h2v1h-2zM20 28h2v1h-2zM23 28h6v1h-6zM30 28h2v1h-2zM33 28h2v1h-2zM38 28h3v1h-3zM42 28h5v1h-5zM49 28h2v1h-2zM2 29h1v1h-1zM4 29h3v1h-3zM12 29h2v1h-2zM21 29h1v1h-1zM23 29h3v1h-3zM28 29h4v1h-4zM33 29h1v1h-1zM36 29h7v1h-7zM49 29h1v1h-1zM3 30h2v1h-2zM6 30h3v1h-3zM10 30h2v1h-2zM15 30h3v1h-3zM20 30h4v1h-4zM25 30h1v1h-1zM27 30h3v1h-3zM34 30h1v1h-1zM37 30h3v1h-3zM42 30h1v1h-1zM46 30h2v1h-2zM4 31h2v1h-2zM9 31h1v1h-1zM11 31h4v1h-4zM16 31h1v1h-1zM23 31h1v1h-1zM27 31h1v1h-1zM33 31h2v1h-2zM37 31h2v1h-2zM40 31h1v1h-1zM42 31h2v1h-2zM46 31h1v1h-1zM3 32h2v1h-2zM6 32h1v1h-1zM8 32h7v1h-7zM19 32h1v1h-1zM22 32h3v1h-3zM26 32h3v1h-3zM30 32h1v1h-1zM34 32h2v1h-2zM38 32h1v1h-1zM40 32h1v1h-1zM42 32h3v1h-3zM46 32h1v1h-1zM48 32h3v1h-3zM5 33h1v1h-1zM7 33h1v1h-1zM10 33h3v1h-3zM14 33h4v1h-4zM19 33h1v1h-1zM21 33h1v1h-1zM23 33h2v1h-2zM29 33h1v1h-1zM31 33h2v1h-2zM34 33h2v1h-2zM38 33h1v1h-1zM40 33h2v1h-2zM45 33h1v1h-1zM47 33h4v1h-4zM2 34h1v1h-1zM6 34h1v1h-1zM8 34h1v1h-1zM10 34h1v1h-1zM14 34h1v1h-1zM18 34h3v1h-3zM22 34h3v1h-3zM26 34h1v1h-1zM29 34h2v1h-2zM32 34h1v1h-1zM36 34h1v1h-1zM38 34h3v1h-3zM43 34h2v1h-2zM47 34h1v1h-1zM49 34h2v1h-2zM2 35h1v1h-1zM10 35h2v1h-2zM16 35h1v1h-1zM20 35h1v1h-1zM23 35h2v1h-2zM30 35h2v1h-2zM35 35h1v1h-1zM37 35h1v1h-1zM42 35h3v1h-3zM50 35h1v1h-1zM2 36h5v1h-5zM8 36h1v1h-1zM13 36h1v1h-1zM23 36h1v1h-1zM25 36h1v1h-1zM27 36h2v1h-2zM30 36h1v1h-1zM33 36h2v1h-2zM36 36h2v1h-2zM39 36h7v1h-7zM48 36h1v1h-1zM50 36h1v1h-1zM9 37h1v1h-1zM11 37h1v1h-1zM13 37h3v1h-3zM17 37h1v1h-1zM20 37h2v1h-2zM23 37h4v1h-4zM29 37h2v1h-2zM33 37h1v1h-1zM37 37h2v1h-2zM40 37h4v1h-4zM45 37h2v1h-2zM50 37h1v1h-1zM7 38h3v1h-3zM11 38h5v1h-5zM17 38h1v1h-1zM19 38h4v1h-4zM24 38h7v1h-7zM32 38h1v1h-1zM34 38h5v1h-5zM44 38h1v1h-1zM46 38h1v1h-1zM48 38h1v1h-1zM50 38h1v1h-1zM3 39h2v1h-2zM6 39h2v1h-2zM13 39h1v1h-1zM17 39h3v1h-3zM21 39h1v1h-1zM23 39h2v1h-2zM27 39h2v1h-2zM33 39h1v1h-1zM36 39h1v1h-1zM38 39h2v1h-2zM41 39h1v1h-1zM43 39h1v1h-1zM45 39h1v1h-1zM47 39h1v1h-1zM49 39h1v1h-1zM3 40h1v1h-1zM7 40h2v1h-2zM10 40h3v1h-3zM14 40h1v1h-1zM16 40h1v1h-1zM18 40h2v1h-2zM21 40h2v1h-2zM25 40h2v1h-2zM31 40h5v1h-5zM41 40h2v1h-2zM44 40h2v1h-2zM48 40h1v1h-1zM50 40h1v1h-1zM3 41h3v1h-3zM9 41h1v1h-1zM12 41h2v1h-2zM20 41h3v1h-3zM25 41h1v1h-1zM28 41h4v1h-4zM34 41h1v1h-1zM36 41h3v1h-3zM41 41h3v1h-3zM45 41h1v1h-1zM47 41h1v1h-1zM49 41h2v1h-2zM2 42h3v1h-3zM8 42h2v1h-2zM11 42h1v1h-1zM13 42h1v1h-1zM15 42h3v1h-3zM19 42h3v1h-3zM24 42h6v1h-6zM32 42h3v1h-3zM36 42h3v1h-3zM42 42h5v1h-5zM10 43h1v1h-1zM12 43h1v1h-1zM19 43h1v1h-1zM22 43h1v1h-1zM24 43h1v1h-1zM28 43h1v1h-1zM30 43h2v1h-2zM34 43h2v1h-2zM42 43h1v1h-1zM46 43h2v1h-2zM49 43h2v1h-2zM2 44h7v1h-7zM10 44h1v1h-1zM13 44h2v1h-2zM16 44h9v1h-9zM26 44h1v1h-1zM28 44h2v1h-2zM31 44h4v1h-4zM37 44h1v1h-1zM40 44h1v1h-1zM42 44h1v1h-1zM44 44h1v1h-1zM46 44h2v1h-2zM50 44h1v1h-1zM2 45h1v1h-1zM8 45h1v1h-1zM15 45h1v1h-1zM17 45h1v1h-1zM21 45h1v1h-1zM23 45h2v1h-2zM28 45h2v1h-2zM32 45h1v1h-1zM34 45h1v1h-1zM36 45h2v1h-2zM39 45h4v1h-4zM46 45h1v1h-1zM48 45h1v1h-1zM2 46h1v1h-1zM4 46h3v1h-3zM8 46h1v1h-1zM11 46h4v1h-4zM18 46h1v1h-1zM20 46h3v1h-3zM24 46h7v1h-7zM32 46h1v1h-1zM36 46h1v1h-1zM38 46h1v1h-1zM40 46h7v1h-7zM48 46h1v1h-1zM50 46h1v1h-1zM2 47h1v1h-1zM4 47h3v1h-3zM8 47h1v1h-1zM10 47h2v1h-2zM14 47h1v1h-1zM19 47h1v1h-1zM21 47h1v1h-1zM24 47h2v1h-2zM27 47h1v1h-1zM33 47h1v1h-1zM35 47h1v1h-1zM37 47h3v1h-3zM42 47h2v1h-2zM47 47h2v1h-2zM50 47h1v1h-1zM2 48h1v1h-1zM4 48h3v1h-3zM8 48h1v1h-1zM12 48h1v1h-1zM15 48h2v1h-2zM18 48h3v1h-3zM23 48h7v1h-7zM33 48h2v1h-2zM36 48h1v1h-1zM43 48h1v1h-1zM46 48h1v1h-1zM48 48h1v1h-1zM2 49h1v1h-1zM8 49h1v1h-1zM10 49h7v1h-7zM18 49h1v1h-1zM21 49h1v1h-1zM26 49h5v1h-5zM35 49h1v1h-1zM37 49h4v1h-4zM43 49h1v1h-1zM46 49h1v1h-1zM2 50h7v1h-7zM10 50h2v1h-2zM13 50h1v1h-1zM16 50h5v1h-5zM23 50h2v1h-2zM29 50h3v1h-3zM34 50h1v1h-1zM36 50h1v1h-1zM39 50h1v1h-1zM41 50h2v1h-2zM44 50h1v1h-1zM46 50h1v1h-1zM48 50h3v1h-3z"

CSS = """
:root{--black:@SIYAH@;--red:@KIRMIZI@;--gold:@TURUNCU@;--grey:#17171a;--line:#2a2a2e;--muted:#a9a9b0;
--head:"Barlow Condensed","Arial Narrow",sans-serif;--body:"Barlow",Arial,sans-serif;--script:"Caveat","Segoe Script",cursive}
*{box-sizing:border-box;margin:0}
html{scroll-behavior:smooth}
body{font-family:var(--body);background:var(--black);color:#fff;line-height:1.6}
a{color:inherit}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:var(--head);line-height:1}
h2{font-size:clamp(34px,6vw,54px);font-weight:800;text-transform:uppercase;margin-bottom:26px}
h2 i{font-style:normal;color:var(--red)}
section{padding:64px 0}
:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
header{background:rgba(12,12,13,.95);position:sticky;top:0;z-index:5;border-bottom:2px solid var(--red)}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:58px}
.logo{font-family:var(--head);font-size:26px;font-weight:800;text-decoration:none;letter-spacing:.02em}
.logo b{color:var(--red)}
nav a{margin-left:18px;text-decoration:none;font-weight:500;font-size:15px}
nav a:hover{color:var(--gold)}
@media(max-width:620px){nav a.hide{display:none}}

.hero{position:relative;overflow:hidden;padding:70px 0 84px;background:
 linear-gradient(115deg,transparent 62%,var(--red) 62%,var(--red) 64%,transparent 64%,transparent 67%,var(--red) 67%,var(--red) 68%,transparent 68%),var(--black)}
.hero h1{font-size:clamp(76px,19vw,190px);font-weight:800;letter-spacing:.01em;text-transform:uppercase}
.hero .alt{display:block;font-size:clamp(26px,6vw,56px);font-weight:700;letter-spacing:.45em;color:var(--red);margin:6px 0 4px}
.hero .usta{font-family:var(--head);font-size:clamp(18px,3vw,26px);letter-spacing:.3em;color:var(--muted)}
.slogan{font-family:var(--script);font-weight:700;font-size:clamp(36px,7vw,64px);color:var(--gold);margin:22px 0 8px;transform:rotate(-2deg);transform-origin:left}
.hero p{max-width:46ch;color:#d8d8dc;font-size:18px;margin-bottom:28px}
.btn{display:inline-block;padding:14px 26px;font-weight:700;text-decoration:none;border-radius:4px;margin:0 10px 10px 0}
.btn.main{background:var(--red)}
.btn.ghost{border:2px solid #fff}
.btn:hover{filter:brightness(1.15)}

.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.svc{background:var(--grey);padding:22px;border-left:5px solid var(--red)}
.svc h3{font-size:28px;margin-bottom:8px;text-transform:uppercase}
.svc p{color:var(--muted)}

.diag{background:var(--grey);border:1px solid var(--line);padding:24px}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 20px}
.chip{font:600 15px var(--body);padding:10px 16px;border:2px solid var(--red);background:transparent;color:#fff;border-radius:999px;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--red)}
.result{border-left:6px solid var(--gold);padding:6px 0 6px 16px;min-height:80px}
.result h3{font-size:28px;margin-bottom:4px}
.result p{color:#d8d8dc}

.konum{background:var(--grey);border-top:2px solid var(--red)}
.konum .big{font-family:var(--script);font-weight:700;font-size:clamp(54px,12vw,110px);color:var(--gold);line-height:1;margin-bottom:12px}
.konum address{font-style:normal;font-size:20px;margin-bottom:6px}
.konum .saat{color:var(--muted);margin-bottom:22px}
.qr{display:flex;gap:24px;align-items:center;flex-wrap:wrap;margin-top:8px}
.qr svg{width:210px;height:210px;border-radius:8px;background:#fff}
.qr h3{font-size:32px;text-transform:uppercase;margin-bottom:6px}
.qr p{color:var(--muted);max-width:30ch}
.qr .tel{font-family:var(--head);font-size:38px;font-weight:800;color:#fff;text-decoration:none}

footer{text-align:center;padding:36px 20px 44px;border-top:2px solid var(--red)}
footer .slogan{margin:0 0 6px;transform:none;font-size:clamp(34px,6vw,52px)}
footer small{color:var(--muted)}
.durum{display:inline-block;margin:0 0 14px;padding:6px 14px;border-radius:999px;font-weight:600;font-size:15px;border:2px solid var(--line);background:var(--grey)}
.durum i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;background:var(--muted)}
.durum.acik i{background:#2ecc71}.durum.kapali i{background:var(--red)}
.neden .svc{border-left-color:var(--gold)}
.form{display:grid;gap:14px;background:var(--grey);padding:24px;border:1px solid var(--line);max-width:640px}
.form label{display:grid;gap:6px;font-weight:600}
.form input,.form textarea{font:inherit;padding:12px;border:2px solid var(--line);background:var(--black);color:#fff;border-radius:4px}
.form input:focus,.form textarea:focus{border-color:var(--red);outline:none}
details{background:var(--grey);border-left:5px solid var(--red);margin-bottom:10px;padding:14px 18px}
summary{font-weight:600;cursor:pointer;font-size:18px}
details p{color:var(--muted);margin-top:8px}
.yorum{background:var(--grey);padding:20px;border-left:5px solid var(--gold)}
.yorum b{display:block;margin-top:8px;color:var(--gold)}
.harita{width:100%;height:300px;border:0;border-radius:6px;margin:22px 0;filter:grayscale(.4) invert(.92) contrast(.9)}
.btn.sm{background:var(--grey);border:2px solid var(--line);cursor:pointer;font:700 16px var(--body);color:#fff}
.ust{position:fixed;right:14px;bottom:90px;z-index:8;width:44px;height:44px;border-radius:50%;border:0;background:var(--red);color:#fff;font-size:20px;cursor:pointer;display:none}
body{padding-bottom:78px}
.bar{display:grid;grid-template-columns:repeat(4,1fr);position:fixed;left:0;right:0;bottom:0;z-index:9;background:var(--black);border-top:2px solid var(--red);padding:8px 8px calc(8px + env(safe-area-inset-bottom,0px));gap:8px}
.bar a{margin:0;text-align:center;text-decoration:none;font-weight:700;padding:12px 2px;border-radius:6px;background:var(--grey);font-size:14px}
.bar a.ara{background:var(--red)}.bar a.cek{background:var(--gold);color:#000}
@media(min-width:760px){.bar{left:50%;right:auto;transform:translateX(-50%);width:640px;border:2px solid var(--red);border-bottom:0;border-radius:10px 10px 0 0}}
.fon{position:fixed;inset:0;display:grid;place-items:center;font-family:var(--head);font-weight:800;font-size:clamp(90px,22vw,260px);letter-spacing:.05em;color:#fff;opacity:.035;transform:rotate(-12deg);pointer-events:none;z-index:0;white-space:nowrap;overflow:hidden}
main,footer{position:relative;z-index:1}
.bant{background:var(--red);color:#fff;text-align:center;padding:12px 20px;transform:skewY(-1.2deg);margin:22px 0;overflow:hidden}
.bant.g{background:var(--gold);color:#000}
.bant span{display:inline-block;transform:skewY(1.2deg);font-family:var(--script);font-weight:700;font-size:clamp(26px,5vw,40px)}
.form select{font:inherit;padding:12px;border:2px solid var(--line);background:var(--black);color:#fff;border-radius:4px}
.form input[type=file]{padding:10px}
.yildiz{color:var(--gold);letter-spacing:3px;font-size:20px}
.yorum p{margin-top:6px;color:#e3e3e6}
.adimlar{list-style:none;padding:0;display:grid;gap:12px;max-width:680px;margin-bottom:22px}
.adimlar li{display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:center;background:var(--grey);padding:14px 16px;border-left:5px solid var(--gold)}
.adimlar b{font-family:var(--head);font-size:30px;color:var(--gold)}
.acil{background:var(--red);padding:38px 0;text-align:center}
.acil h2{margin-bottom:8px}.acil h2 i{color:#000}
.acil .btn{background:#000;margin-top:14px;font-size:20px}
.duyuru{background:var(--gold);color:#000;text-align:center;padding:9px 14px;font-weight:700}
.ozet{font-size:24px;margin:-8px 0 18px;line-height:1.3}
.ornek{display:inline-block;margin-left:8px;color:var(--muted);font-size:12px;border:1px solid var(--line);padding:0 6px}
.form label.isaret{display:flex;gap:12px;align-items:center;font-weight:500;font-size:18px}
.isaret input{width:22px;height:22px;accent-color:var(--red)}
.hak{display:grid;gap:10px;max-width:60ch}
.hak .isim{font-family:var(--script);font-weight:700;font-size:clamp(46px,9vw,80px);color:var(--gold);line-height:1}
.ikon{width:44px;height:44px;color:var(--red);margin-bottom:10px}
.dis{position:absolute;right:-70px;top:30px;width:min(70vw,440px);color:var(--red);opacity:.16;pointer-events:none}
.hero .wrap{position:relative}
.donen{font-family:var(--head);font-size:clamp(20px,4vw,30px);font-weight:700;letter-spacing:.06em;text-transform:uppercase;min-height:1.4em;margin:6px 0 14px;transition:opacity .4s}
.galeri{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.galeri img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:4px;border:1px solid var(--line);background:var(--grey)}
html{overflow-x:clip;-webkit-text-size-adjust:100%}
body{overflow-x:clip}
a,button,summary,label{touch-action:manipulation}
[hidden]{display:none!important}
.form{grid-template-columns:minmax(0,1fr)}
.form input,.form textarea,.form select{width:100%;min-width:0;font-size:16px}
nav a{padding:12px 4px}
summary{padding:8px 0}
.bar a{min-height:48px;display:flex;align-items:center;justify-content:center}
.acil button.btn{border:0;cursor:pointer;font:700 18px var(--body);color:#fff;margin-left:8px}
#konum-not{margin-top:8px;min-height:1.4em}
.logo,nav a{white-space:nowrap}
.slogan{line-height:1.05}
.hero h1{font-size:clamp(60px,17vw,190px)}
@media(max-width:420px){.logo{font-size:22px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

JS = """
const veri = @VERI@;
const cfg = @CFG@;
(function(){
  var d = new Date(), g = d.getDay(), dk = d.getHours()*60 + d.getMinutes();
  function dakika(t){ var a = t.split(':'); return +a[0]*60 + +a[1]; }
  var acik = cfg.kapaliGunler.indexOf(g) < 0 && dk >= dakika(cfg.acilis) && dk < dakika(cfg.kapanis);
  var el = document.getElementById('durum');
  el.className = 'durum ' + (acik ? 'acik' : 'kapali');
  el.innerHTML = '<i></i>' + (acik ? 'Şu an açığız · ' + cfg.kapanis + "'e kadar" : 'Şu an kapalıyız · ' + cfg.acilis + "'de açılıyoruz");
  var ust = document.getElementById('ust');
  window.addEventListener('scroll', function(){ ust.style.display = window.scrollY > 600 ? 'block' : 'none'; });
  ust.addEventListener('click', function(){ window.scrollTo({top:0, behavior:'smooth'}); });
  var NL = String.fromCharCode(10);
  function metin(satirlar){ return satirlar.filter(Boolean).join(NL); }
  function wa(m){ window.open('https://wa.me/' + cfg.no + '?text=' + encodeURIComponent(m), '_blank'); }
  document.getElementById('teklif-form').addEventListener('submit', async function(ev){
    ev.preventDefault();
    var f = ev.target, not = document.getElementById('form-not');
    var m = metin(['Merhaba, ben ' + f.ad.value + '.', 'Araç: ' + f.arac.value, f.plaka.value ? 'Plaka: ' + f.plaka.value : '', 'Sorun: ' + f.sorun.value, 'Uğrama zamanı: ' + f.zaman.value, 'Fiyat/randevu bilgisi alabilir miyim?']);
    var dosyalar = [].slice.call(f.foto.files).concat([].slice.call(f.ses.files));
    if (dosyalar.length && navigator.canShare && navigator.canShare({files: dosyalar})) {
      try { await navigator.share({files: dosyalar, text: m}); not.textContent = "Açılan ekranda WhatsApp'ı seç ve " + cfg.tel + " numarasına gönder."; } catch (x) {}
      return;
    }
    wa(m);
    if (dosyalar.length) not.textContent = "WhatsApp açıldı. Fotoğraf veya sesi sohbette ataç simgesinden ekle.";
  });
  document.getElementById('yorum-form').addEventListener('submit', function(ev){
    ev.preventDefault();
    var f = ev.target;
    wa(metin(['Yorum bırakmak istiyorum.', 'Ad: ' + f.ad.value, 'Puan: ' + f.puan.value + '/5', 'Yorum: ' + f.yorum.value]));
  });
  function kmHesap(){
    var su = +document.getElementById('km-su').value, out = document.getElementById('km-sonuc'), h = '';
    if (!su) { out.textContent = 'Şu anki kilometreni yaz.'; return; }
    [['km-yag', cfg.yag, 'Yağ değişimi'], ['km-ant', cfg.ant, 'Antifriz değişimi']].forEach(function(x){
      var son = +document.getElementById(x[0]).value;
      if (!son) return;
      var kalan = son + x[1] - su, k = Math.abs(kalan).toLocaleString('tr-TR');
      h += '<p><b>' + x[2] + ':</b> ' + (kalan > 0 ? k + ' km kaldı' : k + ' km geçti, zamanı gelmiş') + '</p>';
    });
    out.innerHTML = h || 'Son değişimin kilometresini de yaz.';
  }
  ['km-su', 'km-yag', 'km-ant'].forEach(function(id){ document.getElementById(id).addEventListener('input', kmHesap); });
  document.getElementById('harita-ac').addEventListener('click', function(){
    var fr = document.createElement('iframe');
    fr.className = 'harita'; fr.title = 'Harita'; fr.src = this.dataset.src;
    document.getElementById('harita-kutu').replaceChildren(fr);
  });
  var kutular = [].slice.call(document.querySelectorAll('.isaret input'));
  function listeGuncelle(){
    var n = kutular.filter(function(k){ return k.checked; }).length;
    document.getElementById('liste-sonuc').textContent = n + ' / ' + kutular.length + ' işaretli' + (n === kutular.length ? ' - Harika, aracın bakımlı görünüyor.' : '');
  }
  kutular.forEach(function(k){ k.addEventListener('change', listeGuncelle); });
  listeGuncelle();
  document.getElementById('liste-gonder').addEventListener('click', function(){
    var eksik = kutular.filter(function(k){ return !k.checked; }).map(function(k){ return '- ' + k.value; });
    wa(metin(['Merhaba, aracım için şunları kontrol ettirmek istiyorum:'].concat(eksik.length ? eksik : ['Genel bakım kontrolü istiyorum.'])));
  });
  var dn = document.getElementById('donen'), si = 1;
  dn.textContent = cfg.sloganlar[si];
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    setInterval(function(){
      dn.style.opacity = 0;
      setTimeout(function(){ si = (si + 1) % cfg.sloganlar.length; dn.textContent = cfg.sloganlar[si]; dn.style.opacity = 1; }, 400);
    }, 3500);
  }
  document.getElementById('konum-gonder').addEventListener('click', function(){
    var not = document.getElementById('konum-not');
    if (!navigator.geolocation) { not.textContent = 'Telefonun konum özelliği kullanılamıyor, bizi arayın.'; return; }
    not.textContent = 'Konum alınıyor...';
    navigator.geolocation.getCurrentPosition(function(k){
      wa(metin(['Yolda kaldım, yardım lazım.', 'Konumum: https://maps.google.com/?q=' + k.coords.latitude + ',' + k.coords.longitude]));
      not.textContent = '';
    }, function(){ not.textContent = 'Konum alınamadı. İzin verip tekrar dene ya da bizi ara.'; });
  });
  var kurEv, kurBtn = document.getElementById('kur');
  window.addEventListener('beforeinstallprompt', function(ev){ ev.preventDefault(); kurEv = ev; kurBtn.hidden = false; });
  kurBtn.addEventListener('click', function(){ if (kurEv) kurEv.prompt(); });
  if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(function(){}); }
  var pay = document.getElementById('paylas');
  pay.addEventListener('click', function(){
    if (navigator.share) { navigator.share({title: cfg.marka, text: cfg.marka + ' - ' + cfg.tel, url: location.href}); }
    else { navigator.clipboard.writeText(location.href); pay.textContent = 'Link kopyalandı'; }
  });
})();
const sonuc = document.getElementById('sonuc');
document.querySelectorAll('.chip').forEach(function(btn, i){
  btn.addEventListener('click', function(){
    document.querySelectorAll('.chip').forEach(function(c){ c.setAttribute('aria-pressed','false'); });
    btn.setAttribute('aria-pressed','true');
    sonuc.innerHTML = '<h3></h3><p></p>';
    sonuc.querySelector('h3').textContent = veri[i][0];
    sonuc.querySelector('p').textContent = veri[i][1];
  });
});
"""


GALERI = Path(__file__).parent / "gorseller"
RESIM_UZANTI = (".jpg", ".jpeg", ".png", ".webp")


def _ikon(ic):
    return ('<svg class="ikon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ic}</svg>')


IKONLAR = [_ikon(x) for x in (
    '<path d="M3 9h3V6h6v3h3l2 2v6H6l-3-3z"/><path d="M18 11h3v4h-3"/>',
    '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5"/><path d="M12 4v5.5M12 14.5V20M4 12h5.5M14.5 12H20"/>',
    '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    '<path d="M12 3v18M4.2 7.5l15.6 9M19.8 7.5l-15.6 9"/>',
    '<circle cx="12" cy="12" r="3.5"/><circle cx="12" cy="12" r="8" stroke-dasharray="3.1 3.1"/>')]


def galeri_dosyalari():
    if not GALERI.is_dir():
        return []
    return sorted(f.name for f in GALERI.iterdir() if f.suffix.lower() in RESIM_UZANTI)


def haftalik_yorumlar():
    """Havuzdaki en iyi yorumlardan her hafta YORUM_SAYISI tanesini seçer."""
    puan = lambda y: y[2] if len(y) > 2 else 5
    havuz = [tuple(y) for y in YORUMLAR]
    if not havuz and DEMO_YORUM:
        return [(f"Örnek Müşteri {i}", "Buraya gerçek müşteri yorumu gelecek.", 5, "ornek") for i in range(1, YORUM_SAYISI + 1)]
    iyiler = sorted([y for y in havuz if puan(y) >= 4], key=lambda y: -puan(y)) or havuz
    if len(iyiler) <= YORUM_SAYISI:
        return iyiler
    hafta = datetime.date.today().isocalendar()[1]
    bas = (hafta * YORUM_SAYISI) % len(iyiler)
    return (iyiler[bas:] + iyiler[:bas])[:YORUM_SAYISI]


def sayfa_olustur() -> str:
    e = html.escape
    hizmetler = "".join(
        f'<article class="svc">{IKONLAR[i % len(IKONLAR)]}<h3>{e(a)}</h3><p>{e(y)}</p></article>'
        for i, (a, y) in enumerate(HIZMETLER))
    butonlar = "".join(
        f'<button class="chip" type="button" aria-pressed="false">{e(b[0])}</button>' for b in BELIRTILER)
    veri = json.dumps([[b[1], b[2]] for b in BELIRTILER], ensure_ascii=False)
    css = (CSS.replace("@SIYAH@", RENK_SIYAH).replace("@KIRMIZI@", RENK_KIRMIZI)
              .replace("@TURUNCU@", RENK_TURUNCU))
    js = JS.replace("@VERI@", veri)
    saatler = "<br>".join(e(s) for s in SAATLER)
    marka = f"{MARKA_1} {MARKA_2}"
    neden = "".join(f'<article class="svc"><h3>{e(a)}</h3><p>{e(y)}</p></article>' for a, y in NEDEN)
    sss = "".join(f"<details><summary>{e(a)}</summary><p>{e(y)}</p></details>" for a, y in SSS)
    def bant(i):
        return f'<div class="bant{" g" if i % 2 else ""}"><span>{e(SLOGANLAR[i % len(SLOGANLAR)])}</span></div>'

    def yorum_kart(y):
        yil = y[2] if len(y) > 2 else 5
        ornek = '<small class="ornek">ÖRNEK</small>' if len(y) > 3 else ""
        return (f'<blockquote class="yorum"><span class="yildiz">{"★" * yil}</span>'
                f'<p>{e(y[1])}</p><b>{e(y[0])}</b>{ornek}</blockquote>')
    secili = haftalik_yorumlar()
    kartlar = "".join(yorum_kart(y) for y in secili) or '<p style="color:var(--muted)">Henüz yorum yok. İlk yorumu sen yaz.</p>'
    puanlar = [(y[2] if len(y) > 2 else 5) for y in YORUMLAR]
    ort = f"{sum(puanlar) / len(puanlar):.1f}".replace(".", ",") if puanlar else ""
    ozet = (f'<p class="ozet"><span class="yildiz">★</span> <b>{ort}</b> / 5 · {len(puanlar)} yorum'
            f'<br><small style="color:var(--muted)">Bu hafta öne çıkan yorumlar</small></p>') if puanlar else ""
    liste = "".join(f'<label class="isaret"><input type="checkbox" value="{e(x)}"> {e(x)}</label>' for x in LISTE)
    duyuru = f'<div class="duyuru">{e(DUYURU)}</div>' if DUYURU else ""
    google = f'<a class="btn sm" href="{e(GOOGLE_YORUM)}" target="_blank" rel="noopener">Google yorumu yaz</a>' if GOOGLE_YORUM else ""
    cekici = CEKICI_NO or TELEFON_NO
    sosyal_liste = [("Instagram", INSTAGRAM), ("TikTok", TIKTOK), ("E-posta", f"mailto:{EPOSTA}" if EPOSTA else "")]
    sosyal = "".join(f'<a class="btn sm" href="{e(u)}" target="_blank" rel="noopener">{e(ad)}</a>' for ad, u in sosyal_liste if u)
    eposta_yazi = f'<p style="margin-bottom:18px">E-posta: <a href="mailto:{e(EPOSTA)}">{e(EPOSTA)}</a></p>' if EPOSTA else ""
    galeri = ""
    dosyalar = galeri_dosyalari()
    if dosyalar:
        resimler = "".join(f'<img src="/gorseller/{quote(d)}" alt="{e(marka)} çalışma fotoğrafı" loading="lazy">' for d in dosyalar)
        galeri = (f'<section id="galeri"><div class="wrap"><h2>Çalışmalarımızdan <i>kareler</i></h2>'
                  f'<div class="galeri">{resimler}</div></div></section>')
    ld = json.dumps({"@context": "https://schema.org", "@type": "AutoRepair", "name": marka,
                     "telephone": "+" + TELEFON_NO, "address": {"@type": "PostalAddress",
                     "streetAddress": ADRES, "addressLocality": "Sivas", "addressCountry": "TR"},
                     "openingHours": f"Mo-Sa {ACILIS}-{KAPANIS}", "url": SITE_ADRESI or None}, ensure_ascii=False)
    cfg = json.dumps({"acilis": ACILIS, "kapanis": KAPANIS, "kapaliGunler": KAPALI_GUNLER,
                      "no": TELEFON_NO, "marka": marka, "tel": TELEFON, "yag": YAG_ARALIK, "ant": ANTIFRIZ_ARALIK, "sloganlar": SLOGANLAR})
    harita_gomulu = "https://maps.google.com/maps?q=" + quote(ADRES) + "&output=embed"
    js = js.replace("@CFG@", cfg)

    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>{e(marka)} | Sivas Sanayi - Motor, Alt Takım, Bakım</title>
<meta name="theme-color" content="{RENK_SIYAH}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{e(MARKA_1)}">
<meta name="description" content="{e(marka)} - Sivas sanayi. {e(ACIKLAMA)}">
<script type="application/ld+json">{ld}</script>
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&family=Caveat:wght@700&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&family=Caveat:wght@700&display=swap"></noscript>
<style>{css}</style></head>
<body>
<div class="fon" aria-hidden="true">{e(USTA)}</div>
{duyuru}
<header><div class="wrap">
  <a class="logo" href="#">{e(MARKA_1)} <b>{e(MARKA_2)}</b></a>
  <nav><a class="hide" href="#ariza">Arıza Rehberi</a><a class="hide" href="#hizmetler">Hizmetler</a><a class="hide" href="#teklif">Teklif Al</a><a href="#konum">Konum</a></nav>
</div></header>
<main>
<section class="hero">
  <svg class="dis" viewBox="0 0 200 200" aria-hidden="true"><circle cx="100" cy="100" r="78" fill="none" stroke="currentColor" stroke-width="26" stroke-dasharray="10.2 10.2"/><circle cx="100" cy="100" r="62" fill="none" stroke="currentColor" stroke-width="12"/><circle cx="100" cy="100" r="22" fill="none" stroke="currentColor" stroke-width="10"/></svg>
  <div class="wrap">
  <h1>{e(MARKA_1)}</h1>
  <span class="alt">{e(MARKA_2)}</span>
  <span class="usta">{e(USTA)}</span>
  <div style="margin-top:18px"><span id="durum" class="durum"></span></div>
  <div class="slogan">{e(SLOGAN)}</div>
  <div class="donen" id="donen" aria-hidden="true"></div>
  <p>{e(ACIKLAMA)}</p>
  <a class="btn main" href="tel:+{TELEFON_NO}">Hemen Ara: {e(TELEFON)}</a>
  <a class="btn ghost" href="https://wa.me/{TELEFON_NO}" target="_blank" rel="noopener">WhatsApp'tan Yaz</a>
</div></section>

{bant(0)}
<section id="hakkinda" style="padding-bottom:0"><div class="wrap"><div class="hak">
  <span class="isim">{e(USTA.title())}</span><p style="font-size:19px;color:#d8d8dc">{e(HAKKINDA)}</p></div></div></section>
<section class="neden"><div class="wrap"><h2>Neden <i>biz?</i></h2>
  <div class="grid">{neden}</div></div></section>

<section id="hizmetler" style="padding-top:0"><div class="wrap"><h2>Neler <i>yapıyoruz</i></h2>
  <div class="grid">{hizmetler}</div></div></section>

{galeri}
{bant(1)}
<section id="ariza" style="padding-top:0"><div class="wrap"><h2>Aracında <i>ne oluyor?</i></h2>
  <div class="diag"><p>Belirtiyi seç, olası nedeni gör. Kesin teşhis için araç servise gelmeli.</p>
  <div class="chips">{butonlar}</div>
  <div class="result" id="sonuc" aria-live="polite"><h3>Bir belirti seç</h3><p>Sonuç burada görünecek.</p></div></div>
</div></section>

{bant(6)}
<section id="liste"><div class="wrap"><h2>Aracın <i>hazır mı?</i></h2>
  <div class="form"><p>Son zamanlarda kontrol ettirdiklerini işaretle.</p>
    {liste}
    <div class="result" id="liste-sonuc" aria-live="polite">0 işaretli</div>
    <button class="btn main" id="liste-gonder" type="button" style="border:0;cursor:pointer;font-size:17px">İşaretlemediklerim için WhatsApp'tan yaz</button>
  </div></div></section>

<section id="km"><div class="wrap"><h2>Bakıma ne kadar <i>kaldı?</i></h2>
  <div class="form">
    <label>Şu anki kilometre<input id="km-su" type="number" inputmode="numeric" min="0" placeholder="Örnek: 125000"></label>
    <label>Son yağ değişimi kilometresi<input id="km-yag" type="number" inputmode="numeric" min="0"></label>
    <label>Son antifriz değişimi kilometresi<input id="km-ant" type="number" inputmode="numeric" min="0"></label>
    <div class="result" id="km-sonuc" aria-live="polite">Kilometreyi yaz, hesaplayalım.</div>
    <small style="color:var(--muted)">Yağ için {YAG_ARALIK:,} km, antifriz için {ANTIFRIZ_ARALIK:,} km üzerinden hesaplanır. Aracına göre değişebilir, emin olmak için bize sor.</small>
  </div></div></section>

<section id="durum-bolum"><div class="wrap"><h2>Aracım <i>ne durumda?</i></h2>
  <ol class="adimlar">
    <li><b>1</b><span>Aracını getirirsin, sorununu dinleriz.</span></li>
    <li><b>2</b><span>Teşhis yapılır, fiyat işe başlamadan söylenir.</span></li>
    <li><b>3</b><span>Onayından sonra işe başlarız.</span></li>
    <li><b>4</b><span>Parça değişirken fotoğraf çeker, WhatsApp'tan sana göndeririz.</span></li>
    <li><b>5</b><span>Aracın hazır olunca haber veririz.</span></li>
  </ol>
  <a class="btn main" href="https://wa.me/{TELEFON_NO}?text=Merhaba%2C%20arac%C4%B1m%C4%B1n%20durumunu%20sormak%20istiyorum.%20Plaka%3A%20" target="_blank" rel="noopener">Aracımın durumunu sor</a>
</div></section>

{bant(2)}
<section id="teklif"><div class="wrap"><h2>Fiyat / randevu <i>al</i></h2>
  <form class="form" id="teklif-form">
    <label>Adınız<input name="ad" required autocomplete="name"></label>
    <label>Araç marka ve model<input name="arac" required placeholder="Örnek: Renault Clio 2015"></label>
    <label>Plaka (isteğe bağlı)<input name="plaka" autocomplete="off"></label>
    <label>Sorun nedir?<textarea name="sorun" rows="3" required placeholder="Örnek: Çukurda tak tak sesi geliyor"></textarea></label>
    <label>Ne zaman uğramak istersin?<select name="zaman"><option>Bugün</option><option>Yarın</option><option>Bu hafta</option><option>Fark etmez</option></select></label>
    <label>Gösterge paneli (arıza lambası) fotoğrafı - isteğe bağlı<input type="file" name="foto" accept="image/*" multiple></label>
    <label>Motordan gelen ses kaydı - isteğe bağlı<input type="file" name="ses" accept="audio/*"></label>
    <button class="btn main" type="submit" style="border:0;cursor:pointer;font-size:17px">WhatsApp'tan Gönder</button>
    <small id="form-not" style="color:var(--muted)">Butona basınca bilgiler WhatsApp mesajı olarak hazır gelir, sen sadece gönderirsin.</small>
  </form></div></section>

{bant(7)}
<section class="acil"><div class="wrap">
  <h2>Yolda mı <i>kaldın?</i></h2>
  <p>Mesai dışında da ara, yol yardımı ve çekici için yönlendirelim.</p>
  <a class="btn" href="tel:+{cekici}">Acil Yol Yardım: Hemen Ara</a>
  <button class="btn" id="konum-gonder" type="button">Konumumu WhatsApp'tan gönder</button>
  <p id="konum-not" aria-live="polite"></p>
</div></section>

{bant(8)}
<section id="sss" style="padding-top:0"><div class="wrap"><h2>Sık sorulan <i>sorular</i></h2>{sss}</div></section>
{bant(3)}
<section id="yorumlar"><div class="wrap"><h2>Müşteriler <i>diyor ki</i></h2>
  {ozet}<div class="grid">{kartlar}</div>
  <form class="form" id="yorum-form" style="margin-top:24px">
    <h3>Sen de yorum yaz</h3>
    <label>Adın<input name="ad" required autocomplete="name"></label>
    <label>Puan<select name="puan"><option value="5">5 yıldız</option><option value="4">4 yıldız</option><option value="3">3 yıldız</option><option value="2">2 yıldız</option><option value="1">1 yıldız</option></select></label>
    <label>Yorumun<textarea name="yorum" rows="3" required></textarea></label>
    <button class="btn main" type="submit" style="border:0;cursor:pointer;font-size:17px">Yorumu Gönder</button>
    <small style="color:var(--muted)">Yorumun WhatsApp ile Osman Usta'ya gider. Onaylanınca sitede görünür.</small>{google}
  </form></div></section>
{bant(4)}
<section class="konum" id="konum"><div class="wrap">
  <div class="big">Sivas'tayız</div>
  <address>{e(ADRES)}</address>
  <p class="saat">{saatler}</p>{eposta_yazi}
  <a class="btn main" href="{e(HARITA)}" target="_blank" rel="noopener">Yol Tarifi Al</a>
  <a class="btn sm" href="/osman-bulut.vcf" download>Rehbere Kaydet</a>
  <button class="btn sm" id="paylas" type="button">Siteyi Paylaş</button>{sosyal}
  <div id="harita-kutu" style="margin:22px 0"><button class="btn sm" id="harita-ac" type="button" data-src="{e(harita_gomulu)}">Haritayı sayfada göster</button></div>
  <div class="qr">
    <svg viewBox="-4 -4 61 61" role="img" aria-label="Rehbere kaydetmek için QR kod" shape-rendering="crispEdges">
      <path d="{QR_PATH}" fill="#000"/></svg>
    <div>
      <h3>Rehberden ulaşın</h3>
      <p>Telefonun kamerasıyla okut, numaramız rehberine kaydolsun.</p>
      <a class="tel" href="tel:+{TELEFON_NO}">{e(TELEFON)}</a>
    </div>
  </div>
</div></section>
</main>
<footer>
  {bant(5)}
  <div class="slogan">{e(ALT_SLOGAN)}</div>
  <button class="btn sm" id="kur" type="button" hidden>Uygulama gibi ekle</button><br>
  <small>© {e(marka)} · {e(USTA.title())}</small>
</footer>
<button class="ust" id="ust" type="button" aria-label="Yukarı çık">↑</button>
<nav class="bar" aria-label="Hızlı erişim">
  <a class="ara" href="tel:+{TELEFON_NO}">Ara</a>
  <a href="https://wa.me/{TELEFON_NO}" target="_blank" rel="noopener">WhatsApp</a>
  <a href="{e(HARITA)}" target="_blank" rel="noopener">Yol Tarifi</a>
  <a class="cek" href="tel:+{cekici}">Çekici</a>
</nav>
<script>{js}</script>
</body></html>"""


# Çevrimdışı destek: internet gidince son açılan sayfa gösterilir (https veya localhost'ta çalışır)
SW_JS = """self.addEventListener('install', function(){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(clients.claim()); });
self.addEventListener('fetch', function(e){
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(function(r){
    var c = r.clone(); caches.open('osm-v1').then(function(x){ x.put(e.request, c); }); return r;
  }).catch(function(){ return caches.match(e.request); }));
});"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/manifest.json":
            tur, icerik = "application/manifest+json", json.dumps({
                "name": f"{MARKA_1} {MARKA_2}", "short_name": MARKA_1, "start_url": "/",
                "display": "standalone", "background_color": RENK_SIYAH, "theme_color": RENK_SIYAH,
                "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}]}).encode("utf-8")
        elif self.path == "/osman-bulut.vcf":
            tur = "text/vcard; charset=utf-8"
            icerik = (f"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:{USTA.title()} - {MARKA_1} {MARKA_2}\r\n"
                      f"ORG:{MARKA_1} {MARKA_2}\r\nTEL;TYPE=CELL:+{TELEFON_NO}\r\n"
                      f"ADR;TYPE=WORK:;;{ADRES};Sivas;;;Türkiye\r\nEND:VCARD\r\n").encode("utf-8")
        elif self.path.startswith("/gorseller/"):
            dosya = GALERI / Path(unquote(self.path[len("/gorseller/"):])).name
            if dosya.suffix.lower() not in RESIM_UZANTI or not dosya.is_file():
                self.send_error(404)
                return
            tur, icerik = mimetypes.guess_type(dosya.name)[0] or "image/jpeg", dosya.read_bytes()
        elif self.path == "/sw.js":
            tur, icerik = "text/javascript", SW_JS.encode("utf-8")
        elif self.path == "/icon.svg":
            tur, icerik = "image/svg+xml", (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="18" fill="{RENK_SIYAH}"/>'
                f'<rect y="70" width="100" height="6" fill="{RENK_KIRMIZI}"/>'
                f'<text x="50" y="58" font-family="Arial Narrow,Arial,sans-serif" font-weight="800" font-size="38" text-anchor="middle" fill="#fff">OSM</text></svg>'
            ).encode("utf-8")
        else:
            tur, icerik = "text/html; charset=utf-8", sayfa_olustur().encode("utf-8")  # her istekte yeniden oluşur
        kabul = "gzip" in self.headers.get("Accept-Encoding", "")
        sikistir = kabul and (not tur.startswith("image/") or tur == "image/svg+xml")
        if sikistir:
            icerik = gzip.compress(icerik, 6)
        self.send_response(200)
        self.send_header("Content-Type", tur)
        if sikistir:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(icerik)))
        self.end_headers()
        self.wfile.write(icerik)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    GALERI.mkdir(exist_ok=True)   # fotoğrafları buraya at
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Site çalışıyor: http://localhost:{PORT}  (durdurmak için Stop)")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()
