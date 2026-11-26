# TAVIO — Spesifikasi Templat Laporan Jadual Waktu
Versi dokumen: 1.1  
Status: Draf spesifikasi berdasarkan keputusan reka bentuk yang telah dipersetujui  
Skop: Reka bentuk dan tingkah laku lima jenis laporan jadual waktu

## 1. Tujuan
Dokumen ini menghimpunkan keputusan reka bentuk bagi lima jenis laporan jadual waktu TAVIO. Ia menjadi rujukan sebelum pembangunan modul penjanaan dan cetakan laporan dimulakan.

Laporan dijana daripada data jadual waktu sedia ada. Templat laporan bukan jadual waktu berasingan dan tidak memerlukan penduaan data jadual.

## 2. Prinsip umum
1. Semua laporan menggunakan data jadual waktu yang sama dan dijana secara automatik.
2. Pilihan variasi templat dibuat ketika pengguna hendak menjana atau mencetak laporan, bukan melalui perubahan data jadual waktu.
3. Pilihan Dengan Tandatangan atau Tanpa Tandatangan tidak mengubah konfigurasi Schedule Signatories.
4. Label tandatangan menggunakan bahasa yang dipilih dalam tetapan Schedule Signatories:
   - English: PREPARED BY / VERIFIED BY
   - Bahasa Melayu: DISEDIAKAN OLEH / DISAHKAN OLEH
5. Jangan tambah jadual, lajur, indeks, trigger atau migration database untuk memenuhi reka bentuk laporan tanpa spesifikasi dan kelulusan berasingan.
6. Jangan ubah skema database v1/v2 atau konfigurasi penandatangan sedia ada sebagai sebahagian daripada kerja dokumentasi ini.

## 3. Ringkasan lima jenis laporan

| Jenis laporan | Variasi templat | Ruang tandatangan |
|---|---|---|
| Jadual Waktu Guru | Dengan / Tanpa Tandatangan | Pilihan pengguna ketika cetakan |
| Jadual Waktu Kelas | Dengan / Tanpa Tandatangan | Pilihan pengguna ketika cetakan |
| Jadual Waktu Bilik Khas | Templat bertandatangan | Ada |
| Jadual Waktu Hari | Satu templat | Tiada |
| Jadual Waktu Subjek | Satu templat | Tiada |

## 4. Jadual Waktu Guru

### 4.1 Kandungan asas
- Logo sekolah di bahagian kiri atas.
- Nama dan alamat sekolah.
- Nama penuh guru sebagai tajuk utama.
- Jadual waktu guru mengikut hari Isnin hingga Jumaat.
- Lajur waktu/period termasuk Rehat A dan Rehat B.
- Kod ringkas mata pelajaran dalam petak jadual.
- Singkatan kelas dalam petak jadual.
- Petak boleh digabungkan untuk pengajaran berterusan.
- Tarikh berkuat kuasa di bahagian bawah seperti dalam contoh templat.

### 4.2 Variasi Tanpa Tandatangan
- Jadual utama menggunakan kawasan halaman yang lebih luas.
- Kekalkan lajur SUM untuk jumlah waktu mengikut hari.
- Tiada jadual rumusan subjek di sebelah kanan.
- Tiada ruang DISEDIAKAN OLEH, DISAHKAN OLEH atau tarikh tandatangan.

### 4.3 Variasi Dengan Tandatangan
- Jadual utama disusun lebih kecil bagi menyediakan ruang untuk jadual rumusan subjek di sebelah kanan.
- Jadual rumusan subjek hanya dipaparkan dalam variasi ini.
- Jadual rumusan mempunyai maklumat SUBJEK, KELAS dan WAKTU.
- Rumusan dijana daripada rekod pengajaran guru dalam jadual waktu.
- Sediakan ruang DISEDIAKAN OLEH, DISAHKAN OLEH dan TARIKH di bahagian bawah.
- Gunakan nama pentadbir berdasarkan konfigurasi Schedule Signatories jenis TEACHER.
- Jangan mereka nama penandatangan jika konfigurasi belum ditetapkan.

### 4.4 Pilihan ketika cetakan
Semasa menjana atau mencetak Jadual Waktu Guru, pengguna memilih Dengan Tandatangan atau Tanpa Tandatangan. Pilihan ini hanya menentukan templat laporan yang digunakan.

## 5. Jadual Waktu Kelas

### 5.1 Kandungan asas
- Nama kelas sebagai tajuk utama.
- Nama Guru Kelas di bahagian atas sebelah kanan.
- Jadual waktu Isnin hingga Jumaat.
- Lajur waktu/period termasuk Rehat A dan Rehat B.
- Setiap petak menunjukkan kod ringkas mata pelajaran dan singkatan nama guru yang mengajar.
- Petak boleh digabungkan untuk pengajaran berterusan.
- Jika dua guru mengajar bersama, paparkan kedua-dua singkatan nama guru.
- Nama Guru Kelas dipaparkan dalam format: GURU KELAS: NAMA GURU.

### 5.2 Variasi Tanpa Tandatangan
- Jadual utama menggunakan kawasan halaman yang lebih luas.
- Nama Guru Kelas tetap dipaparkan.
- Tiada jadual rumusan Guru Mengajar di sebelah kanan.
- Tiada ruang DISEDIAKAN OLEH, DISAHKAN OLEH atau tarikh tandatangan.

### 5.3 Variasi Dengan Tandatangan
- Jadual utama disusun lebih kecil untuk menyediakan ruang jadual rumusan di sebelah kanan.
- Jadual rumusan mempunyai lajur SUBJEK, GURU MENGAJAR dan WAKTU.
- Setiap rekod rumusan memadankan subjek dengan guru yang benar-benar mengajar kelas tersebut.
- Paparkan jumlah keseluruhan waktu dalam rumusan.
- Nama Guru Kelas tetap dipaparkan.
- Sediakan ruang DISEDIAKAN OLEH, DISAHKAN OLEH dan TARIKH di bahagian bawah.
- Gunakan konfigurasi Schedule Signatories jenis CLASS.
- Jangan mereka nama penandatangan jika konfigurasi belum ditetapkan.

### 5.4 Pilihan ketika cetakan
Semasa menjana atau mencetak Jadual Waktu Kelas, pengguna memilih Dengan Tandatangan atau Tanpa Tandatangan. Pilihan ini hanya menentukan templat laporan yang digunakan.

## 6. Tetapan Guru Kelas

### 6.1 Keperluan fungsi
1. Setiap kelas yang didaftarkan boleh ditetapkan seorang Guru Kelas.
2. Pengguna memilih Guru Kelas daripada senarai guru yang telah didaftarkan dalam Master Data.
3. Tetapan disimpan mengikut kelas.
4. Guru Kelas tidak semestinya guru yang mengajar kelas tersebut dalam jadual waktu.
5. Pengguna boleh mengubah tetapan apabila berlaku pertukaran Guru Kelas.
6. Jika belum ditetapkan, laporan tidak boleh memaparkan nama rekaan; paparkan keadaan kosong yang jelas atau maklumkan pengguna sebelum cetakan mengikut keputusan UX kemudian.

### 6.2 Paparan laporan
Nama Guru Kelas dipaparkan di bahagian atas sebelah kanan Jadual Waktu Kelas dengan format GURU KELAS: NAMA GURU.

### 6.3 Skop teknikal
Fungsi pengurusan Guru Kelas perlu diletakkan dalam pengurusan data kelas atau aliran Master Data yang sesuai. Reka bentuk penyimpanan dan perubahan skema belum diluluskan dalam dokumen ini. Semak skema semasa dahulu dan bentangkan cadangan sebelum sebarang migration atau perubahan database.

## 7. Jadual Waktu Bilik Khas
1. Gunakan susun atur asas seperti Jadual Waktu Subjek.
2. Paparkan penggunaan bilik khas mengikut hari dan waktu.
3. Jadual merangkumi hari Isnin hingga Jumaat dan lajur waktu termasuk Rehat A serta Rehat B, selaras dengan struktur templat subjek.
4. Sediakan ruang DISEDIAKAN OLEH, DISAHKAN OLEH dan TARIKH di bahagian bawah.
5. Gunakan konfigurasi Schedule Signatories sedia ada jenis SPECIAL_ROOM.
6. Buat masa ini hanya templat bertandatangan dipersetujui; tiada pilihan tanpa tandatangan ditetapkan.
7. Jangan tambah jenis schedule_type baharu. Skema v2 sedia ada sudah mempunyai SPECIAL_ROOM.

## 8. Jadual Waktu Hari
1. Laporan memaparkan keseluruhan jadual semua kelas bagi satu hari persekolahan yang dipilih.
2. Nama laporan ialah Jadual Waktu Hari.
3. Baris di sebelah kiri memaparkan singkatan nama kelas, contohnya 4TA, 4TF, 4TH dan 4TK.
4. Lajur mendatar memaparkan waktu/period termasuk Rehat A dan Rehat B.
5. Setiap petak memaparkan singkatan mata pelajaran dan singkatan nama guru.
6. Jika dua guru mengajar bersama, paparkan kedua-dua singkatan nama guru.
7. Petak boleh digabungkan apabila pengajaran berterusan.
8. Data dijana daripada jadual waktu sedia ada, bukan disimpan sebagai jadual berasingan.
9. Tiada ruang tandatangan dan tiada konfigurasi Schedule Signatories diperlukan.

## 9. Jadual Waktu Subjek
1. Laporan memaparkan satu mata pelajaran merentasi hari dan waktu persekolahan.
2. Tajuk utama ialah nama mata pelajaran.
3. Baris menegak memaparkan hari Isnin hingga Jumaat.
4. Lajur mendatar memaparkan waktu/period termasuk Rehat A dan Rehat B.
5. Satu petak boleh mengandungi beberapa pasangan guru-kelas.
6. Setiap pasangan dipaparkan secara berasingan, contohnya:
   - MARDHIAH — 4TH
   - ZULKEFLI — 5TF
7. Jika satu kelas diajar oleh dua guru bagi subjek, hari dan waktu yang sama, paparkan kedua-dua guru bersama kelas berkenaan.
8. Sistem mesti memadankan setiap kelas dengan guru sebenar yang mengajar subjek tersebut pada hari dan waktu berkenaan. Jangan sekadar menyenaraikan semua guru yang mengajar subjek itu.
9. Data dijana daripada jadual waktu sedia ada.
10. Tiada ruang tandatangan.

## 10. Konfigurasi Schedule Signatories sedia ada
Skema database v2 mempunyai tiga jenis konfigurasi: TEACHER, CLASS dan SPECIAL_ROOM.

Pemetaan:
- Jadual Waktu Guru → TEACHER
- Jadual Waktu Kelas → CLASS
- Jadual Waktu Bilik Khas → SPECIAL_ROOM

Jadual Waktu Hari dan Jadual Waktu Subjek tidak memerlukan konfigurasi tandatangan. Jangan tambah nilai schedule_type baharu untuk kedua-dua laporan ini.

Prepared By dan Verified By mesti kekal mengikut peraturan Schedule Signatories sedia ada, termasuk peraturan bahawa kedua-dua pentadbir bagi satu jenis jadual adalah berbeza.


## 11. Pemilihan versi jadual waktu dan tarikh kuat kuasa

### 11.1 Pemilihan versi
1. Sebelum menjana laporan, pengguna mesti memilih Tahun Akademik, Sesi dan Versi Jadual Waktu.
2. Senarai versi ditapis berdasarkan Tahun Akademik dan Sesi yang dipilih. Hanya versi yang benar-benar wujud bagi kombinasi tersebut boleh dipilih.
3. Pengguna memilih versi secara jelas. Sistem tidak boleh menganggap versi bernombor paling tinggi sebagai versi rasmi atau aktif.
4. Jangan memilih versi secara automatik berdasarkan nombor versi, tarikh simpan atau tarikh kuat kuasa.
5. Semua laporan yang dijana dalam satu proses hendaklah menggunakan ID versi jadual waktu yang sama.
6. Paparkan maklumat yang membantu pengguna membezakan versi, sekurang-kurangnya nombor versi dan nama versi. Jika tersedia, paparkan juga tarikh kuat kuasa dan tarikh simpan.
7. Jangan gunakan autosave atau draf workspace sebagai sumber laporan. Sumber laporan mestilah rekod versi yang disimpan dalam `timetable_versions`.

### 11.2 Tarikh kuat kuasa
1. Tarikh kuat kuasa laporan diambil daripada `timetable_versions.effective_date` bagi versi yang dipilih.
2. Jangan menggantikan tarikh kuat kuasa dengan tarikh semasa, tarikh simpan atau tarikh cetakan.
3. Jika `effective_date` mempunyai nilai, paparkan tarikh tersebut pada bahagian templat yang telah ditetapkan.
4. Jika `effective_date` NULL, sistem mesti memberi amaran bahawa tarikh kuat kuasa belum ditetapkan. Pengguna boleh membatalkan proses atau meneruskan cetakan tanpa tarikh kuat kuasa; sistem tidak boleh mereka atau mengisi tarikh secara automatik.
5. Pemilihan atau cetakan laporan tidak boleh mengubah `effective_date` atau mana-mana rekod database.

### 11.3 Batasan skema semasa
- Jadual `timetable_versions` mempunyai `version_number`, `version_name`, `effective_date` dan `saved_at`.
- Skema semasa tidak mempunyai penanda `is_active` atau `is_current`.
- Oleh itu, modul laporan tidak boleh mendakwa sesuatu versi sebagai versi rasmi/aktif melainkan fungsi pengurusan versi dan peraturan penetapannya dibangunkan serta diluluskan kemudian.
- Tiada perubahan skema atau migration diperlukan untuk melaksanakan pemilihan manual ini.

## 12. Perkara yang perlu diperincikan sebelum pembangunan
1. Saiz kertas, orientasi, margin, fon, saiz teks dan skala cetakan akhir bagi setiap templat.
2. Tingkah laku apabila logo sekolah atau Guru Kelas belum ditetapkan.
3. Format tepat nama ringkas guru dan kelas yang digunakan dalam setiap laporan.
4. Kaedah pengiraan dan paparan jumlah waktu bagi jadual rumusan.
5. Tingkah laku apabila data terlalu padat untuk satu halaman, termasuk pemecahan halaman atau pelarasan skala.
6. Paparan jika konfigurasi penandatangan kosong.
7. Butiran tepat templat Jadual Waktu Bilik Khas dan contoh visual akhir.
8. Aliran pemilihan hari, subjek, guru, kelas atau bilik khas sebelum laporan dijana.

Jangan membuat andaian senyap tentang perkara yang belum diputuskan. Bentangkan pilihan untuk kelulusan sebelum mengunci tingkah laku.

## 13. Had skop dokumen
Dokumen ini merekodkan reka bentuk laporan dan keperluan fungsinya sahaja. Ia bukan kebenaran untuk:
- mengubah skema database;
- menambah migration, jadual, lajur, indeks atau trigger;
- membangunkan atau mengubah solver;
- membangunkan keseluruhan Master Data yang belum dipersetujui;
- menukar konfigurasi Schedule Signatories;
- mengubah fungsi backup/restore;
- membuat perubahan reka bentuk UI yang tidak berkaitan.

Sebarang perubahan database atau peluasan skop perlu dibentangkan dan diluluskan secara berasingan.

---
Dokumen ini disediakan berdasarkan contoh templat dan keputusan reka bentuk yang telah dipersetujui dalam perbincangan TAVIO.