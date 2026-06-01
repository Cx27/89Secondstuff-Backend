[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Arch Linux](https://img.shields.io/badge/Arch%20Linux-33AADD?style=for-the-badge&logo=arch-linux&logoColor=white)](https://archlinux.org)
[![Zero Trust Security](https://img.shields.io/badge/Security-Zero%20Trust-red?style=for-the-badge)](https://en.wikipedia.org/wiki/Zero_trust_security_model)

---

## Summary & Arsitektur

**89Secondstuff-API** adalah engine backend kelas produksi (*production-ready*) tingkat tinggi yang dirancang khusus sebagai penggerak ekosistem platform *thrift clothing* **89Secondstuff**.

Engine ini secara fundamental mengadopsi dua prinsip rekayasa perangkat lunak modern:

1. **Decoupled Architecture:** Pemisahan mutlak secara fungsional antara lapisan *Frontend* (Astro Framework) dan *Backend* (FastAPI). Hubungan komunikasi keduanya dijalin secara murni melalui pertukaran data JSON via RESTful API Endpoints.
2. **Zero Trust Security Model & RBAC:** Sistem tidak pernah berasumsi bahwa sebuah request aman hanya karena berasal dari jaringan lokal atau akun tertentu. Setiap request ke rute terproteksi wajib melewati mekanisme inspeksi KTP Digital (*JWT Authentication Bearer Token*) dan divalidasi secara presisi berdasarkan hak akses peran (*Role-Based Access Control: Admin vs Buyer*).

---

## 1. Peta Koneksi & Arsitektur File (Mindmap)

Untuk memahami bagaimana roda-roda di dalam mesin ini saling berputar dan terhubung, berikut adalah tabel dekonstruksi relasi dan dependensi fungsional antar komponen file:

| Nama File | Peran Utama | Berinteraksi Dengan | Kenapa & Mengapa Didesain Begini? |
| :--- | :--- | :--- | :--- |
| **`database.py`** | **Kabel Busi & Konektor Utama** | File `.env`<br>PostgreSQL Engine | **Kenapa:** Mengisolasi seluruh konfigurasi dan instansiasi koneksi basis data.<br>**Mengapa:** Mengurangi risiko kebocoran data (*credential leakage*) di repositori publik dengan memanfaatkan variabel lingkungan (*environment variables*). |
| **`models.py`** | **Cetakan Beton Basis Data (ORM)** | `database.py` (Base class) | **Kenapa:** Mendefinisikan representasi fisik skema tabel (`users`, `products`, `bookings`) di PostgreSQL menggunakan SQLAlchemy.<br>**Mengapa:** Mentransformasikan baris data relasional database menjadi objek Python murni agar dapat diolah secara logis, lengkap dengan penetapan kolom `role`. |
| **`schemas.py`** | **Saringan & Gatekeeper JSON** | Pydantic BaseModel | **Kenapa:** Bertindak sebagai skema kontrak data untuk validasi input (*Request Payload*) dan penyaringan output (*Response Body*).<br>**Mengapa:** Memastikan tidak ada tipe data sampah yang masuk dan menjamin data sensitif (seperti `password_hash`) tidak akan pernah bocor keluar menuju sisi *frontend*. |
| **`auth.py`** | **Pabrik Token & Kriptografi** | `passlib` (bcrypt)<br>`python-jose` (JWT) | **Kenapa:** Memusatkan logika pengamanan kredensial, mulai dari *password hashing* hingga pencetakan *JWT Access Token*.<br>**Mengapa:** Menyediakan token terenkripsi simetris (HS256) berdurasi tetap, yang menanamkan parameter `role` di dalam payload-nya, untuk memverifikasi wewenang pengguna di setiap transaksi terproteksi. |
| **`crud.py`** | **Sang Pustakawan (Database Logic)** | `models.py`<br>`schemas.py`<br>`auth.py` | **Kenapa:** Menampung seluruh fungsi query manipulasi data mentah SQL (Create, Read, Update, Delete) dan logika fleksibel login.<br>**Mengapa:** Memisahkan urusan logika bisnis gudang (mekanisme penguncian inventaris dan auto-clean booking) dari lapisan routing, menjaga agar struktur endpoint tetap bersih. |
| **`main.py`** | **Resepsionis & Kawat Berduri API** | Semua File Internal Proyek<br>`StaticFiles` Engine | **Kenapa:** Titik masuk utama (*orchestrator*) seluruh aplikasi yang menangani inisialisasi FastAPI, konfigurasi CORS, pemetaan routing API, serta interseptor otorisasi hak akses.<br>**Mengapa:** Menjadi satu-satunya gerbang komunikasi seragam yang terekspos ke dunia luar untuk di-hit oleh *frontend* Astro. |
| **`uploads/`** | **Brankas Penyimpanan Gambar Fisik** | `main.py` (Static Directory) | **Kenapa:** Folder lokal yang ditunjuk khusus untuk menampung berkas biner media foto asli (.jpg/.png) barang thrift.<br>**Mengapa:** PostgreSQL sangat tidak efisien untuk menyimpan berkas biner berukuran besar; praktik terbaik adalah menyimpan file fisiknya di OS dan mencatat alamat URL-nya di database. |

---

## 2. Diagram Alir Logika Menjalar (Visual Request Flow)

ASCII flowchart berikut menggambarkan penjalaran data dari browser pengunjung, melewati kawat pertahanan *backend*, hingga berhasil terpatri di dalam basis data PostgreSQL:

```text
[ Astro Frontend / Browser User ]
               │
               │ (Kirim Request HTTP + Header 'Authorization: Bearer <token>')
               ▼
   [ main.py (Pintu Gerbang API) ]
               │
               ├───► Validasi CORS (Izinkan Lintas Origin)
               │
               ├───► Interseptor Satpam Token JWT ───► [ auth.py ]  (Bongkar KTP: Email + Role)
               │                                           │
               │                                           ▼ (Ambil Data Sub: Email)
               │                                      [ crud.py ] (Ambil User DB via email/username)
               │
               ├───► Pengecekan RBAC (Role-Based) ───► (Tolak jika Buyer akses rute Admin)
               │
               ├───► Saring Payload Data JSON ────────► [ schemas.py ]  (Cek Tipe Data Pydantic)
               │
               ▼ (Jika Lolos Seluruh Proteksi Zero Trust)
   [ crud.py (Otak Logika Bisnis Gudang) ]
               │
               ├───► Eksekusi Query Inventaris (Kunci Data / Auto-Clean System)
               │
               ▼ (Kombinasikan dengan Objek Struktur)
   [ models.py (Skema Relasional ORM) ]
               │
               ▼ (Salurkan Lewat Pipa SessionLocal)
   [ database.py (Konektor Pompa Data) ]
               │
               ▼
 [(🐘) PostgreSQL Database Server ] ◄─── [ Source of Truth (Status: Locked Permanen) ]
```

---

## 3. Skema Database (Model ORM)

### Tabel `users`

| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-increment primary key |
| `username` | String (Unique) | Username unik, wajib diisi |
| `email` | String (Unique) | Email unik, wajib diisi |
| `password_hash` | String | Hasil enkripsi bcrypt — tidak pernah disimpan plain |
| `role` | String | Default: `"buyer"`. Nilai valid: `"buyer"` / `"admin"` |
| `created_at` | DateTime | Timestamp otomatis saat register (UTC) |

### Tabel `products`

| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-increment primary key |
| `name` | String | Nama produk, wajib diisi |
| `description` | String | Deskripsi detail kondisi barang (opsional) |
| `price` | Float | Harga dalam Rupiah |
| `status` | String | Default: `"available"`. Nilai valid: `"available"` / `"reserved"` / `"sold"` |
| `image_url` | String | URL path gambar dari static server (opsional) |
| `created_at` | DateTime | Timestamp otomatis (UTC) |

### Tabel `bookings`

| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-increment primary key |
| `user_id` | Integer (FK → `users.id`) | Pemilik booking |
| `product_id` | Integer (FK → `products.id`) | Barang yang di-hold |
| `status` | String | Default: `"pending"`. Nilai valid: `"pending"` / `"confirmed"` / `"cancelled"` |
| `expires_at` | DateTime | Batas waktu booking — otomatis +2 jam dari waktu hold (UTC) |

---

## 4. Registrasi API Endpoint (Panduan Komunikasi Sisi Frontend / Astro Devs)

Semua interaksi API wajib menggunakan format konten **JSON** (kecuali `/login` yang memakai `multipart/form-data` dan `/admin/upload-image` yang memakai `multipart/form-data` untuk binary file), dan mengembalikan kode status HTTP standar sesuai aturan RESTful internasional.

---

###  A. Jalur Publik (Bebas Akses / Tanpa Token Keamanan)

#### 1. Register Akun Baru

- **Endpoint:** `POST /register`
- **Fungsi:** Mendaftarkan pengguna baru ke dalam sistem. Role otomatis diset sebagai `"buyer"`. Sistem menolak otomatis jika `username` **atau** `email` sudah terdaftar.
- **Request Body (JSON):**
  ```json
  {
    "username": "jagoanthrift",
    "email": "buyer.thrift@gmail.com",
    "password": "rahasiasuperaman"
  }
  ```
- **Response Sukses (`200 OK`):**
  ```json
  {
    "id": 1,
    "username": "jagoanthrift",
    "email": "buyer.thrift@gmail.com",
    "role": "buyer"
  }
  ```
- **Response Gagal (`400 Bad Request`):** Jika email atau username sudah terdaftar.
  ```json
  { "detail": "Email atau Username udah kedaftar dawg!" }
  ```

#### 2. Login & Penukaran KTP Digital (Token)

- **Endpoint:** `POST /login`
- **Fungsi:** Mengajukan kredensial untuk mendapatkan JWT Access Token. Mendukung input fleksibel — bisa menggunakan **Username ATAU Email**.
- **Request Body (Format: `multipart/form-data` — Wajib sesuai standar OAuth2):**
  - `username`: `jagoanthrift` atau `buyer.thrift@gmail.com`
  - `password`: `rahasiasuperaman`
- **Response Sukses (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
- **Catatan Implementasi:** Token JWT yang dihasilkan selalu terikat ke `email` user sebagai `sub` claim dan menyematkan `role` di dalamnya, berapapun identifier yang digunakan saat login. Token kedaluwarsa dalam **60 menit**.

#### 3. Tarik Etalase Katalog Aktif

- **Endpoint:** `GET /products`
- **Fungsi:** Mengambil daftar produk pakaian *thrift* yang siap dibeli oleh umum.
- **Radar Proteksi:** **Hanya memunculkan barang dengan status `"available"`**. Barang yang sedang dikunci (`reserved`) atau sudah laku (`sold`) otomatis disembunyikan agar etalase tetap steril bagi pembeli.
- **Response Sukses (`200 OK`):**
  ```json
  [
    {
      "id": 1,
      "name": "Jaket Vintage Carhartt Detroit",
      "description": "Size L, cond 9/10, faded mantap, minus kancing ujung kerah.",
      "price": 650000.0,
      "image_url": "http://127.0.0.1:8000/static/carhartt-detroit.jpg",
      "status": "available"
    }
  ]
  ```

---

###  B. Jalur Pembeli (Protected — Wajib Header `Authorization: Bearer <token>`)

#### 1. Lihat Riwayat Booking Sendiri

- **Endpoint:** `GET /bookings`
- **Fungsi:** Menarik daftar riwayat booking secara eksklusif hanya untuk User ID yang sedang login (Isolasi Privasi Pembeli — tidak bisa melihat booking orang lain).
- **Response Sukses (`200 OK`):**
  ```json
  [
    {
      "id": 3,
      "user_id": 1,
      "product_id": 5,
      "status": "pending"
    }
  ]
  ```

#### 2. Eksekusi Hold & Amankan Barang (Booking)

- **Endpoint:** `POST /bookings`
- **Fungsi:** Mengunci satu produk unik agar tidak bisa diambil orang lain selama masa tenggang transfer (2 jam).
- **Request Body (JSON):**
  ```json
  {
    "product_id": 1
  }
  ```
- **Response Sukses (`200 OK`):**
  ```json
  {
    "id": 3,
    "user_id": 1,
    "product_id": 1,
    "status": "pending"
  }
  ```
- **Alur Penanganan Transisi di Frontend (Astro JavaScript):**
  - **Skenario Tembus (`200 OK`):** Sistem sukses mengubah status barang menjadi `"reserved"`. JavaScript di Astro harus segera mengalihkan tab browser pengguna menuju tautan otomatis WhatsApp Admin:
    👉 `https://wa.me/628123456789?text=Halo%20min,%20gua%20udah%20hold%20Jaket%20Carhartt%20(ID:1).%20Ini%20bukti%20transfernya.`
  - **Skenario Tikungan (`400 Bad Request`):** Jika pembeli lain lebih dulu menekan tombol di milidetik yang lebih cepat, API mengembalikan error. Frontend Astro wajib membatalkan pengalihan ke WA dan menembakkan komponen *pop-up/toast* peringatan: `"Wah keduluan dawg! Barang ini sudah di-hold orang lain."`

---

###  C. Jalur Dewa / Admin (Protected — Mutlak Verifikasi `current_user.role == 'admin'`)

#### 1. Mata Dewa Gudang Total

- **Endpoint:** `GET /admin/products`
- **Fungsi:** Menarik manifes keseluruhan produk di gudang tanpa saringan status apapun. Admin bisa melacak barang yang sedang `available`, `reserved` (di-hold buyer), maupun `sold` (terjual). Data diurutkan dari ID terbaru (`DESC`).

#### 2. Tarik Antrean Transaksi Keseluruhan

- **Endpoint:** `GET /admin/bookings`
- **Fungsi:** Melihat manifes seluruh riwayat booking dari semua user di platform untuk mempermudah Admin mencocokkan nomor ID booking yang dikirim pembeli via WhatsApp dengan mutasi rekening bank. Data diurutkan dari ID terbaru (`DESC`).
- **Response Sukses (`200 OK`):**
  ```json
  [
    {
      "id": 3,
      "user_id": 1,
      "product_id": 1,
      "status": "pending"
    }
  ]
  ```

#### 3. Unggah Media Foto Produk (Tahap 1 — Tambah Produk)

- **Endpoint:** `POST /admin/upload-image`
- **Fungsi:** Mengirim berkas gambar fisik dari komputer lokal menuju server penyimpanan internal (`uploads/`).
- **Request Body (`multipart/form-data`):**
  - `file`: Binary berkas `.jpg` / `.jpeg` / `.png`
- **Response Sukses (`200 OK`):**
  ```json
  {
    "url": "http://127.0.0.1:8000/static/carhartt_detroit_HD.jpg"
  }
  ```
- **Validasi:** Hanya menerima `image/jpeg`, `image/jpg`, `image/png`. Format lain akan ditolak `400 Bad Request`.

#### 4. Inject Manifes Produk Baru (Tahap 2 — Tambah Produk)

- **Endpoint:** `POST /products`
- **Fungsi:** Memasukkan entri detail spesifikasi produk ke database.
- **Request Body (JSON):**
  ```json
  {
    "name": "Jaket Vintage Carhartt Detroit",
    "description": "Size L, cond 9/10, faded mantap, minus kancing ujung kerah.",
    "price": 650000.0,
    "image_url": "http://127.0.0.1:8000/static/carhartt_detroit_HD.jpg"
  }
  ```
- **Mekanisme Otomatisasi 2-Tembakan di Frontend:** Saat tombol "Simpan" ditekan pada panel admin Astro, *script* background wajib mengeksekusi dua pukulan beruntun: hit `/admin/upload-image` dulu → dapatkan string URL → pasang ke field `image_url` → baru hit `POST /products` dengan JSON lengkap.

#### 5. Fitur Anti-Typo & Koreksi Deskripsi Baju

- **Endpoint:** `PUT /admin/products/{product_id}`
- **Fungsi:** Melakukan pembaruan data tekstual (Nama, Deskripsi, Harga, URL Gambar) tanpa berisiko menyentuh, mereset, atau merusak kolom `status` transaksi yang sedang berjalan.
- **Request Body (JSON):** Sama dengan `POST /products`.
- **Response Gagal (`404 Not Found`):** Jika `product_id` tidak ditemukan.

#### 6. Ceklis Konfirmasi Hakim Garis (Update Status & Auto-Clean)

- **Endpoint:** `PATCH /admin/products/{product_id}/status?new_status=sold`
- **Fungsi:** Eksekusi validasi mutlak setelah Admin melakukan cek mutasi rekening bank.
- **Parameter Query:** `new_status` — nilai valid: `"sold"`, `"reserved"`, `"available"`.

| `new_status` | Efek di Database |
| :--- | :--- |
| `"sold"` | Barang digembok mati secara permanen. |
| `"reserved"` | Status dikunci manual oleh admin. |
| `"available"` | Barang dilepas kembali ke etalase + **auto-delete semua entri booking terkait** (*Garbage Cleaning*). |

---

## 5. Deep Dive Kebijakan Sistem (Prinsip Logika Mesin)

### ⚔️ Penaklukan Race Condition Melalui Inventory Locking

- **Kenapa Masalah Ini Muncul?** Karakteristik barang thrift adalah keunikan kuantitas (*Stok Tunggal / Only 1 Stock Available*). Apabila dua pembeli membuka katalog dan menekan tombol "Hold" secara serentak, potensi tabrakan alokasi sangatlah tinggi.
- **Mengapa Arsitektur Ini Aman?** Diselesaikan di level fundamental basis data relasional. Query di `crud.py` mengunci kriteria ketat:
  ```python
  .filter(Product.id == product_id, Product.status == "available")
  ```
  Request yang masuk lebih dulu akan langsung mengeksekusi update status ke `reserved` dan `db.commit()`. Request kedua yang mengantre tepat di belakangnya akan mendapati query bernilai `None` karena status sudah bukan `"available"`, sehingga otomatis terlempar keluar dengan pesan kegagalan.

### 🛡️ Smart Role-Based JWT Payload

Sistem *backend* menolak metode di mana *frontend* menebak-nebak *role* pengguna secara buta. Mesin `auth.py` menanamkan status `role` (`admin` atau `buyer`) di dalam JWT payload bersamaan dengan `email`:

```python
access_token = auth.create_access_token(data={"sub": user.email, "role": user.role})
```

*Frontend* wajib membedah token ini di sisi klien untuk mengatur logika perlindungan rute di level UI (sembunyikan tombol admin dari buyer), memastikan kondisi UI tersinkronisasi murni dengan *Source of Truth* dari server.

### 🔑 Fleksibilitas Login: Email atau Username

Sistem otentikasi mendukung login menggunakan **email** maupun **username** secara interchangeable. Fungsi `get_user_by_identifier()` di `crud.py` menggunakan query `OR` untuk mencari user:

```python
or_(models.User.email == identifier, models.User.username == identifier)
```

Meskipun begitu, JWT token yang diterbitkan **selalu menggunakan email** sebagai `sub` claim untuk konsistensi validasi di setiap request berikutnya.

### 🧹 Auto-Garbage Cleaning Transaksi Hangus

Saat Admin menemukan pembeli fiktif (*Hit and Run / Ghosting*) dan mereset status barang melalui `PATCH /admin/products/{id}/status?new_status=available`, sistem `crud.py` secara agresif akan mencari seluruh data booking yang terkait dengan ID barang tersebut dan langsung mengeksekusi `db.query(...).delete()`. Ini memastikan tabel `bookings` tetap bersih dan tidak dipenuhi riwayat transaksi bodong yang kedaluwarsa.

### Isolasi Tanggung Jawab Operasi Data (PUT vs PATCH)

- **Kenapa Harus Dipisah?** Mengikuti doktrin arsitektur bersih *Single Responsibility Principle*.
- **Mengapa Jika Dicampur Sangat Berbahaya?** Apabila fitur edit typo digabung dengan pengubahan status, maka saat Admin mengedit harga barang yang kebetulan sedang berada dalam masa kuncian (`reserved`), sistem berisiko besar ikut mereset atau tidak sengaja melepaskan kuncian barang ke pasar umum. Dengan pemisahan ini, benerin typo (PUT) dan eksekusi palang pintu transaksi (PATCH) berjalan di ruang terisolasi masing-masing.

### 🕐 Token Expiry & Waktu Booking

- **JWT Access Token:** Kedaluwarsa dalam **60 menit** (`ACCESS_TOKEN_EXPIRE_MINUTES = 60` di `auth.py`).
- **Booking Hold Timer:** Kedaluwarsa dalam **2 jam** dari waktu booking (`expires_at = now + timedelta(hours=2)`).
- Kedua nilai tersebut menggunakan timezone-aware `datetime` berbasis UTC untuk konsistensi antar server.

---

## 6. Daftar Paket Dependensi Komplit (Requirements)

Mesin ini membutuhkan beberapa pustaka eksternal Python agar seluruh fitur keamanan, manipulasi berkas, dan konektivitas database berjalan lancar:

| Package | Versi | Fungsi |
| :--- | :--- | :--- |
| `fastapi` | 0.136.3 | Framework inti pembuatan REST API berkecepatan tinggi |
| `uvicorn` | 0.48.0 | Web server ASGI berperforma tinggi untuk menjalankan FastAPI |
| `sqlalchemy` | 2.0.50 | Mesin utama ORM untuk menjembatani kode Python menjadi SQL |
| `psycopg2-binary` | 2.9.12 | Driver koneksi native untuk berkomunikasi dengan PostgreSQL |
| `passlib[bcrypt]` | 1.7.4 | Pustaka enkripsi bcrypt standar industri untuk *hashing* password |
| `python-jose[cryptography]` | 3.5.0 | Mesin enkripsi simetris untuk *signing* dan *decoding* JWT token |
| `python-multipart` | 0.0.29 | Ekstensi agar FastAPI mampu menangani upload file biner & form login |
| `python-dotenv` | 1.2.2 | Komponen pembaca berkas `.env` rahasia sistem (Zero Trust) |
| `pydantic` | 2.13.4 | Validasi data dan serialisasi schema (backbone `schemas.py`) |

**Satu Baris Command Instalasi (Eksekusi di dalam Virtual Environment):**

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary passlib[bcrypt] python-jose[cryptography] python-multipart python-dotenv
```

> **Catatan:** File `requirements.txt` sudah tersedia di root proyek untuk instalasi presisi versi menggunakan `pip install -r requirements.txt`.

---

## 7. Konfigurasi Environment (`.env`)

Buat file `.env` di root direktori proyek **sebelum** menjalankan server. Berikut adalah variabel yang wajib diisi:

```env
# Koneksi ke PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/nama_database

# Kunci rahasia JWT — ganti dengan string random yang panjang dan kuat!
SECRET_KEY=ganti_ini_dengan_string_random_yang_sangat_panjang_dan_aman
```

> ⚠️ **JANGAN PERNAH** commit file `.env` ke repositori publik. Pastikan `.env` sudah masuk ke dalam `.gitignore`.

---

## 8. The Boot Sequence (Panduan Instalasi & Menyalakan Mesin)

### Jalur A: Pengoperasian di Linux / Arch Linux (The Arch Way)

Buka emulator terminal, pastikan servis PostgreSQL sudah aktif, lalu eksekusi baris ini secara berurutan:

```bash
# 1. Masuk ke dalam direktori basis kode proyek backend
cd /home/cxz/89Secondstuff-Backend

# 2. Nyalakan dan masuk ke dalam ruang isolasi Virtual Environment Python
source venv/bin/activate

# 3. Nyalakan starter mesin server FastAPI dengan mode deteksi perubahan berkas otomatis
uvicorn main:app --reload
```

### Jalur B: Pengoperasian di Windows (Panduan Tim Frontend Devs)

Buka **Command Prompt (CMD)** atau **PowerShell**, arahkan ke folder proyek, dan eksekusi baris berikut:

```cmd
:: 1. Berpindah ke dalam direktori utama proyek backend
cd path\to\89Secondstuff-Backend

:: 2. Nyalakan sistem Virtual Environment Python versi Windows
venv\Scripts\activate

:: 3. Jalankan server lokal Uvicorn
uvicorn main:app --reload
```

### Persiapan Database (First-Time Setup)

Sebelum menjalankan server untuk pertama kali, pastikan database PostgreSQL sudah dibuat. Tabel `users`, `products`, dan `bookings` akan dibuat **otomatis** oleh SQLAlchemy saat server pertama kali dinyalakan melalui baris ini di `main.py`:

```python
models.Base.metadata.create_all(bind=engine)
```

---

## 9. Langkah Verifikasi Akhir (Swagger UI Testing)

Begitu terminal mengeluarkan log hijau pertanda server berhasil di-*binding* di alamat lokal, segera buka browser dan arahkan ke:

👉 **`http://127.0.0.1:8000/docs`**

Lakukan uji kelayakan operasional dengan menembak rute secara urut:

1. Daftarkan akun baru melalui `POST /register` (sertakan field `username`, `email`, `password`).
2. Promosikan akun tersebut menjadi admin secara manual via PostgreSQL client:
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'email_lu@domain.com';
   ```
3. Tukar token di rute `POST /login` menggunakan email atau username, lalu salin string `access_token`-nya.
4. Klik tombol **Authorize** di pojok kanan atas Swagger (ikon gembok), masukkan `Bearer <token_lu_tadi>`, lalu klik authorize.
5. Lakukan simulasi unggah gambar `.jpg` melalui `POST /admin/upload-image`. Jika merespon URL statis dan foto dapat dibuka di tab browser baru, maka mesin backend secara absolut dinyatakan:

** STATUS: ACTIVE / FLUID / PERFECT.**
