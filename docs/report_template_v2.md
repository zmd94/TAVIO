# TAVIO — Spesifikasi Templat Laporan Jadual Waktu
Versi dokumen: 2.0
Status: Draf spesifikasi berdasarkan keputusan reka bentuk yang dipersetujui
Skop: Reka bentuk, susunan rekod, preview dan penjanaan lima jenis laporan jadual waktu

## 1. Tujuan dan kedudukan dokumen

Dokumen ini menghimpunkan keputusan reka bentuk terkini bagi lima jenis laporan jadual waktu TAVIO. Dokumen ini menjadi rujukan sebelum pembangunan modul preview, penjanaan dan cetakan laporan dimulakan.

Dokumen ini ialah kesinambungan perbincangan dalam `docs/report_template_v1.md`. Fail v1 dikekalkan sebagai rekod terdahulu dan tidak ditulis semula.

Laporan dijana daripada versi jadual waktu yang dipilih. Templat laporan bukan jadual waktu berasingan dan tidak memerlukan penduaan data jadual.

Dokumen ini merekodkan spesifikasi dan keputusan reka bentuk sahaja. Ia bukan arahan untuk terus mengubah kod atau skema database.

## 2. Prinsip umum

1. Semua laporan menggunakan data daripada versi jadual waktu yang sama yang dipilih secara jelas oleh pengguna.
2. Laporan tidak boleh mengambil data daripada autosave atau draf workspace.
3. Preview dan PDF akhir mesti menggunakan enjin serta susun atur PDF yang sama. Preview ialah paparan PDF sebenar yang akan dijana, bukan lakaran atau anggaran.
4. Proses preview dan penjanaan PDF tidak boleh mengubah data jadual waktu atau rekod database.
5. Pilihan Dengan Tandatangan atau Tanpa Tandatangan hanya memilih variasi templat; ia tidak mengubah konfigurasi Schedule Signatories.
6. Label tandatangan dan bahasa tarikh tandatangan mengikut bahasa yang dipilih dalam tetapan Schedule Signatories.
7. Semua nama ringkasan untuk Guru, Subjek, Kelas dan Bilik adalah mandatori dalam Master Data, termasuk rekod sedia ada.
8. Jangan menjana singkatan secara automatik. Semua nama ringkasan ditentukan dan diselenggara oleh pengguna melalui Master Data.
9. Dalam kotak/sel jadual, gunakan nama ringkasan bagi nama guru, subjek, kelas dan bilik.
10. Nama penuh digunakan pada tajuk utama atau bahagian pengenalan yang ditetapkan secara khusus.
11. Jangan tambah jadual, lajur, indeks, trigger atau migration database untuk memenuhi reka bentuk laporan tanpa audit skema dan kelulusan berasingan.
12. Jangan ubah skema database v1/v2 atau konfigurasi penandatangan sedia ada sebagai sebahagian daripada kerja dokumentasi ini.

## 3. Ringkasan lima jenis laporan

| Jenis laporan | Variasi templat | Ruang tandatangan |
|---|---|---|
| Jadual Waktu Guru | Dengan / Tanpa Tandatangan | Pilihan pengguna |
| Jadual Waktu Kelas | Dengan / Tanpa Tandatangan | Pilihan pengguna |
| Jadual Waktu Bilik Khas | Satu templat | Ada |
| Jadual Waktu Hari | Satu templat | Tiada |
| Jadual Waktu Subjek | Satu templat | Tiada |

## 4. Tetapan reka bentuk PDF umum

Tetapan berikut terpakai kepada kesemua lima jenis laporan:

- Saiz kertas: A4 Landscape.
- Margin: 8 mm pada semua sisi.
- Fon: Inter, dibenamkan (embedded) dalam PDF.
- Latar belakang putih dan teks hitam.
- Tajuk hari dan masa menggunakan kelabu yang sangat cerah.
- Tiada blok warna besar atau warna latar pekat.
- Garisan luar jadual: 0.8 pt.
- Garisan dalaman jadual: 0.4 pt.
- Logo sekolah, nama sekolah dan alamat berada di bahagian kiri atas setiap halaman.
- Jika logo sekolah tersedia dalam School Profile, gunakan logo tersebut.
- Jika logo sekolah tiada, gunakan logo rasmi TAVIO sebagai logo gantian. Logo TAVIO tidak disimpan sebagai logo sekolah dalam database.
- Jika logo sekolah dimuat naik kemudian, laporan seterusnya menggunakan logo sekolah secara automatik.
- Nama sekolah dan alamat mesti dibaca secara dinamik daripada School Profile; jangan hardcode contoh nama atau alamat.

### 4.1 Saiz teks rujukan

Saiz teks berikut telah dipersetujui untuk templat Jadual Waktu Guru dan menjadi rujukan asas gaya PDF:

| Elemen | Saiz |
|---|---:|
| Nama sekolah | 14 pt |
| Nama guru | 16 pt |
| Tajuk hari | 8 pt |
| Masa | 8 pt |
| Kandungan sel jadual | 8 pt |
| Ringkasan subjek | 8 pt |
| Ruang tandatangan | 9 pt |

Saiz khusus elemen lain dalam templat Kelas, Bilik Khas, Hari dan Subjek boleh diselaraskan dalam had reka bentuk yang sama, tetapi tidak boleh menyebabkan teks terlalu kecil sehingga sukar dibaca.

## 5. Peraturan nama penuh dan nama ringkasan

1. Rekod Master Data bagi kategori berikut mesti mempunyai nama penuh dan nama ringkasan:
   - Guru
   - Subjek
   - Kelas
   - Bilik
2. Syarat mandatori ini turut terpakai kepada rekod lama. Rekod lama yang belum mempunyai nama ringkasan perlu dilengkapkan.
3. Rekod baharu tidak boleh disimpan jika nama ringkasan belum diisi.
4. Tiada penjanaan singkatan secara automatik.
5. Semua kotak/sel jadual menggunakan nama ringkasan:
   - Nama guru → nama ringkasan guru.
   - Nama subjek → nama ringkasan subjek.
   - Nama kelas → nama ringkasan kelas.
   - Nama bilik → nama ringkasan bilik.
6. Tajuk utama atau bahagian pengenalan yang ditetapkan secara khusus boleh menggunakan nama penuh.
7. Jika rekod berkaitan belum memenuhi syarat nama ringkasan, sistem menyekat preview dan penjanaan laporan yang menggunakan rekod tersebut serta memaklumkan pengguna supaya Master Data dilengkapkan.

## 6. Pengiraan waktu dan ringkasan subjek

1. Jumlah waktu dikira berdasarkan bilangan slot pengajaran sebenar.
2. Rehat A dan Rehat B tidak dikira sebagai waktu pengajaran.
3. Satu sesi pengajaran yang meliputi dua slot berturut-turut dikira sebagai dua waktu.
4. Jika subjek yang sama berlaku dalam beberapa sesi berasingan pada hari yang sama, gabungkan semua slotnya dalam satu baris ringkasan subjek.
5. Jangan hasilkan baris berulang bagi subjek yang sama dalam ringkasan untuk guru atau kelas yang sama.
6. Semua pengiraan mesti berdasarkan versi jadual waktu yang dipilih, bukan anggaran atau data daripada versi lain.
7. Jumlah keseluruhan waktu dalam ringkasan kelas bertandatangan ialah jumlah slot pengajaran sebenar dan tidak termasuk rehat.

## 7. Pengatas dan templat Jadual Waktu Guru

### 7.1 Jadual Waktu Guru — Tanpa Tandatangan

Susunan pengatas khusus ini dikekalkan dan tidak boleh disatukan dengan pengatas versi bertandatangan:

1. Logo sekolah di bahagian kiri atas.
2. Nama sekolah dan alamat berada di bawah logo, sejajar ke kiri.
3. Nama penuh guru berada di tengah bahagian atas.
4. Tiada tajuk `JADUAL WAKTU GURU` atau tajuk tambahan.
5. Tiada garisan atau kotak pemisah tambahan antara pengatas dengan jadual.
6. Jadual bermula terus di bawah pengatas.

Kandungan:
- Jadual utama menggunakan ruang yang lebih luas.
- Lajur SUM memaparkan jumlah waktu mengikut hari.
- Tiada jadual ringkasan subjek di sebelah kanan.
- Tiada ruang Prepared By, Verified By atau tarikh tandatangan.

### 7.2 Jadual Waktu Guru — Dengan Tandatangan

Susunan pengatas berasingan berdasarkan gambar rujukan yang dipersetujui:

1. Logo sekolah di bahagian kiri atas.
2. Tajuk tepat `JADUAL WAKTU INDIVIDU` berada di tengah bahagian atas.
3. Nama sekolah berada di bawah tajuk, di bahagian tengah.
4. Alamat sekolah kekal di bawah logo di sebelah kiri.
5. Nama penuh guru berada di sebelah kanan, di bawah kawasan tajuk.
6. Tiada kotak atau garisan pemisah tambahan.
7. Jadual bermula di bawah pengatas.

Kandungan:
- Jadual utama disusun lebih kecil untuk menyediakan ruang jadual ringkasan subjek di sebelah kanan.
- Jadual ringkasan mempunyai kolum `SUBJEK / KELAS / WAKTU`.
- Nama subjek dan kelas dalam ringkasan menggunakan nama ringkasan.
- Ringkasan dijana daripada rekod pengajaran guru dalam versi jadual waktu yang dipilih.
- Sediakan ruang Prepared By, Verified By dan tarikh di bahagian bawah.
- Gunakan konfigurasi Schedule Signatories jenis `TEACHER`.

### 7.3 Pilihan variasi

Semasa menjana Jadual Waktu Guru, pengguna memilih Dengan Tandatangan atau Tanpa Tandatangan. Kedua-dua variasi mempunyai reka bentuk pengatas berbeza seperti yang dinyatakan di atas.

## 8. Pengatas dan templat Jadual Waktu Kelas

Kedua-dua variasi Jadual Waktu Kelas menggunakan pengatas yang sama, berdasarkan gambar rujukan kelas tanpa tandatangan:

1. Logo sekolah di bahagian kiri atas.
2. Nama penuh kelas dipaparkan besar di tengah bahagian atas.
3. Nama sekolah dan alamat berada di bawah logo, sejajar ke kiri.
4. Maklumat `GURU KELAS: [NAMA PENUH GURU]` berada di sebelah kanan, di atas jadual.
5. Tiada tajuk tambahan seperti `JADUAL WAKTU KELAS`.
6. Tiada kotak atau garisan pemisah tambahan.
7. Jadual bermula terus di bawah pengatas.
8. Nama kelas dan Guru Kelas dibaca secara dinamik daripada rekod berkaitan.

### 8.1 Jadual Waktu Kelas — Tanpa Tandatangan

- Jadual utama menggunakan ruang halaman yang lebih luas.
- Tiada jadual ringkasan guru di sebelah kanan.
- Tiada ruang Prepared By, Verified By atau tarikh tandatangan.

### 8.2 Jadual Waktu Kelas — Dengan Tandatangan

- Pengatas sama seperti variasi tanpa tandatangan.
- Jadual utama disusun lebih kecil.
- Jadual ringkasan berada di sebelah kanan jadual utama.
- Kolum ringkasan ialah `SUBJEK / GURU MENGAJAR / WAKTU`.
- Setiap subjek dipaparkan satu baris sahaja.
- Kolum GURU MENGAJAR menggunakan nama ringkasan guru daripada Master Data.
- Jika subjek diajar oleh beberapa guru, semua nama ringkasan guru disenaraikan dalam baris subjek yang sama.
- Padanan guru mesti berdasarkan guru yang benar-benar mengajar kelas bagi subjek berkenaan dalam versi jadual yang dipilih.
- Kolum WAKTU menjumlahkan semua slot pengajaran subjek tersebut.
- Baris terakhir memaparkan jumlah keseluruhan waktu.
- Sediakan ruang Prepared By, Verified By dan tarikh di bahagian bawah.
- Gunakan konfigurasi Schedule Signatories jenis `CLASS`.

### 8.3 Syarat Guru Kelas

1. Setiap kelas mesti mempunyai seorang Guru Kelas yang ditetapkan pada rekod kelas.
2. Guru Kelas dipilih daripada senarai guru Master Data yang berdaftar dan aktif.
3. Guru Kelas tidak semestinya guru yang mengajar kelas tersebut dalam jadual waktu.
4. Jika Guru Kelas belum ditetapkan, preview dan penjanaan Jadual Waktu Kelas disekat.
5. Sistem memaklumkan pengguna supaya menetapkan Guru Kelas terlebih dahulu.
6. Syarat ini terpakai kepada kedua-dua variasi Dengan Tandatangan dan Tanpa Tandatangan.
7. Penetapan Guru Kelas disimpan pada rekod kelas, bukan dipilih semula setiap kali laporan dijana.
8. Keputusan fungsi ialah seorang Guru Kelas bagi setiap rekod kelas. Tiada medan tahun akademik/sesi tambahan untuk penetapan ini dipersetujui kerana rekod kelas sudah terikat kepada tahun akademik/sesi.
9. Skema v2 yang diketahui belum mempunyai `classes.class_teacher_id`. Sebarang perubahan skema untuk menyimpan hubungan ini memerlukan audit skema, cadangan dan kelulusan berasingan sebelum migration dilaksanakan.

## 9. Jadual Waktu Bilik Khas

1. Satu templat sahaja, dengan ruang tandatangan.
2. Susun atur asas jadual menggunakan pendekatan Jadual Waktu Subjek.
3. Tajuk utama menggunakan nama penuh bilik khas.
4. Dalam kotak/sel jadual, gunakan nama ringkasan bilik, guru, kelas dan subjek apabila berkaitan.
5. Paparkan penggunaan bilik khas mengikut hari dan waktu.
6. Waktu rehat A dan B ditunjukkan mengikut struktur bell schedule, tetapi tidak dikira sebagai waktu pengajaran.
7. Sediakan ruang Prepared By, Verified By dan tarikh di bahagian bawah.
8. Gunakan konfigurasi Schedule Signatories jenis `SPECIAL_ROOM`.
9. Tiada variasi tanpa tandatangan dipersetujui.

## 10. Jadual Waktu Hari

1. Laporan memaparkan semua hari persekolahan secara automatik dalam satu fail PDF.
2. Hari ditentukan berdasarkan konfigurasi hari persekolahan: Isnin–Jumaat atau Ahad–Khamis. Jangan hardcode satu konfigurasi.
3. Setiap hari bermula pada halaman baharu.
4. Jika senarai kelas untuk satu hari terlalu panjang, jadual hari tersebut boleh bersambung ke halaman seterusnya.
5. Hari seterusnya tetap bermula pada halaman baharu.
6. Tajuk utama hanya memaparkan nama hari, contohnya `ISNIN`. Jangan tambah frasa `JADUAL WAKTU HARI`.
7. Pada halaman sambungan hari yang sama, tajuk hari dan kepala kolum waktu diulang.
8. Baris kelas disusun mengikut turutan yang telah ditetapkan dalam Master Data Kelas.
9. Kolum mendatar memaparkan slot/waktu daripada bell schedule yang dipilih, termasuk Rehat A dan Rehat B jika wujud.
10. Baris memaparkan nama ringkasan kelas.
11. Setiap sel memaparkan nama ringkasan subjek dan nama ringkasan guru.
12. Jika dua guru mengajar bersama, paparkan kedua-dua nama ringkasan guru.
13. Petak boleh digabungkan untuk pengajaran berterusan apabila data jadual membenarkannya.
14. Tiada ruang tandatangan.
15. Data dijana daripada versi jadual waktu yang dipilih, bukan disimpan sebagai jadual berasingan.

## 11. Jadual Waktu Subjek

1. Laporan memaparkan satu subjek merentasi semua hari persekolahan dalam satu fail PDF.
2. Tajuk utama menggunakan nama penuh subjek.
3. Baris menegak memaparkan hari persekolahan mengikut konfigurasi sesi (Isnin–Jumaat atau Ahad–Khamis).
4. Kolum mendatar memaparkan slot/waktu daripada bell schedule yang dipilih, termasuk Rehat A dan Rehat B jika wujud.
5. Dalam sel jadual, nama subjek, guru dan kelas menggunakan nama ringkasan.
6. Satu sel boleh mengandungi beberapa pasangan kelas/guru bagi subjek, hari dan waktu yang sama.
7. Setiap pasangan dipaparkan secara berasingan, contohnya:
   - `MARDHIAH — 4TH`
   - `ZULKEFLI — 5TF`
8. Jika satu kelas diajar oleh dua guru pada subjek, hari dan waktu yang sama, paparkan kedua-dua nama ringkasan guru bersama kelas berkenaan.
9. Sistem mesti memadankan setiap kelas dengan guru sebenar yang mengajar subjek tersebut pada hari dan waktu berkenaan. Jangan sekadar menyenaraikan semua guru yang mengajar subjek itu.
10. Tiada ruang tandatangan.
11. Data dijana daripada versi jadual waktu yang dipilih.

## 12. Ruang tandatangan dan pengesahan

### 12.1 Jenis laporan bertandatangan

Ruang tandatangan wujud pada:
- Jadual Waktu Guru — hanya variasi Dengan Tandatangan.
- Jadual Waktu Kelas — hanya variasi Dengan Tandatangan.
- Jadual Waktu Bilik Khas — satu-satunya variasi yang dipersetujui.

### 12.2 Kedudukan dan kandungan

- Prepared By / Disediakan Oleh berada di bahagian kiri.
- Verified By / Disahkan Oleh berada di bahagian tengah.
- Maklumat TARIKH berada di bahagian paling kanan, seperti gambar templat.
- Nama, jawatan dan nama sekolah penandatangan dipaparkan di bawah garisan tandatangan.
- Label Bahasa Melayu: `DISEDIAKAN OLEH` dan `DISAHKAN OLEH`.
- Label English: `PREPARED BY` dan `VERIFIED BY`.

### 12.3 Syarat wajib

1. Jika pengguna memilih templat yang mempunyai ruang tandatangan, tetapan Prepared By dan Verified By mesti lengkap terlebih dahulu.
2. Jika salah satu kosong, sistem menyekat preview dan penjanaan templat bertandatangan serta memaklumkan pengguna supaya melengkapkan tetapan.
3. Jika penandatangan yang telah ditetapkan dinyahaktifkan, templat bertandatangan disekat sehingga penandatangan aktif baharu dipilih.
4. Penandatangan baharu dipilih daripada pentadbir yang berdaftar dan aktif.
5. Prepared By dan Verified By mesti merupakan individu berbeza dalam kategori jenis jadual yang sama, mengikut peraturan Schedule Signatories sedia ada.
6. Templat tanpa tandatangan yang tersedia masih boleh digunakan jika pengguna tidak mahu menggunakan ruang tandatangan.
7. Tiada nama atau jawatan penandatangan boleh direka atau diisi secara automatik.

### 12.4 Bahasa tarikh

- Tarikh tandatangan mengikut bahasa label tandatangan yang dipilih.
- Tarikh dipaparkan dalam huruf besar.
- Contoh Bahasa Melayu: `26 NOVEMBER 2026`.
- Contoh Bahasa Inggeris: nama bulan menggunakan ejaan bahasa Inggeris, contohnya `26 NOVEMBER 2026`.
- Label TARIKH berada di bahagian paling kanan.
- Tarikh kuat kuasa di bawah jadual (jika templat berkenaan memaparkannya) kekal dalam Bahasa Melayu dan huruf besar, contohnya `26 NOVEMBER 2026`.

### 12.5 Perkara yang belum dimuktamadkan

Maksud sumber tarikh pada ruang tandatangan belum disahkan secara khusus: sama ada tarikh PDF dijana/dicetak atau tarikh tandatangan sebenar. Jangan membuat andaian sehingga perkara ini diputuskan.

## 13. Pemilihan versi jadual waktu dan tarikh kuat kuasa

### 13.1 Pemilihan versi

1. Sebelum menjana laporan, pengguna memilih Tahun Akademik, Sesi dan Versi Jadual Waktu.
2. Senarai versi ditapis berdasarkan Tahun Akademik dan Sesi yang dipilih.
3. Pengguna memilih versi secara jelas. Sistem tidak boleh menganggap versi bernombor paling tinggi sebagai versi rasmi atau aktif.
4. Jangan memilih versi secara automatik berdasarkan nombor versi, tarikh simpan atau tarikh kuat kuasa.
5. Semua laporan yang dijana dalam satu proses menggunakan ID versi jadual waktu yang sama.
6. Paparkan maklumat untuk membezakan versi, sekurang-kurangnya nombor versi dan nama versi. Jika tersedia, paparkan juga tarikh kuat kuasa dan tarikh simpan.
7. Jangan gunakan autosave atau draf workspace sebagai sumber laporan. Sumber laporan mestilah rekod versi yang disimpan dalam `timetable_versions`.

### 13.2 Tarikh kuat kuasa

1. Tarikh kuat kuasa diambil daripada `timetable_versions.effective_date` bagi versi yang dipilih.
2. Jangan menggantikan tarikh kuat kuasa dengan tarikh semasa, tarikh simpan atau tarikh cetakan.
3. Jika `effective_date` mempunyai nilai, paparkan tarikh tersebut pada bahagian templat yang telah ditetapkan.
4. Format tarikh kuat kuasa ialah Bahasa Melayu, huruf besar, contohnya `26 NOVEMBER 2026`.
5. Jika `effective_date` NULL, sistem memberi amaran bahawa tarikh kuat kuasa belum ditetapkan. Pengguna boleh membatalkan proses atau meneruskan tanpa tarikh kuat kuasa.
6. Sistem tidak boleh mereka atau mengisi tarikh kuat kuasa secara automatik.
7. Pemilihan, preview atau cetakan laporan tidak boleh mengubah `effective_date` atau mana-mana rekod database.

### 13.3 Batasan skema semasa

- Jadual `timetable_versions` mempunyai `version_number`, `version_name`, `effective_date` dan `saved_at`.
- Skema semasa tidak mempunyai penanda `is_active` atau `is_current`.
- Modul laporan tidak boleh mendakwa sesuatu versi sebagai versi rasmi/aktif tanpa fungsi pengurusan versi dan peraturan penetapan yang diluluskan.
- Tiada perubahan skema diperlukan untuk pemilihan versi secara manual.

## 14. Susunan rekod, fail PDF dan bilangan halaman

### 14.1 Satu fail untuk semua rekod

Setiap jenis laporan menjana satu fail PDF yang mengandungi semua rekod yang dipilih, bukan satu fail berasingan bagi setiap guru, kelas, subjek atau bilik.

### 14.2 Susunan rekod

Susunan rekod dalam PDF mengikut turutan yang ditetapkan dalam Master Data masing-masing:
- Guru mengikut turutan Master Data Guru.
- Kelas mengikut turutan Master Data Kelas.
- Subjek mengikut turutan Master Data Subjek.
- Bilik khas mengikut turutan Master Data Bilik.
- Hari mengikut konfigurasi hari persekolahan.

Jangan menyusun semula mengikut abjad secara automatik jika turutan Master Data telah ditetapkan.

### 14.3 Peraturan halaman

| Jenis laporan | Peraturan halaman |
|---|---|
| Jadual Waktu Guru | Seorang guru bagi setiap halaman; satu jadual mesti muat satu halaman |
| Jadual Waktu Kelas | Satu kelas bagi setiap halaman; satu jadual mesti muat satu halaman |
| Jadual Waktu Bilik Khas | Satu bilik bagi setiap halaman; satu jadual mesti muat satu halaman |
| Jadual Waktu Subjek | Satu subjek bagi setiap halaman; satu jadual mesti muat satu halaman |
| Jadual Waktu Hari | Satu hari bermula pada halaman baharu; hari tersebut boleh bersambung ke halaman seterusnya jika perlu |

Hanya Jadual Waktu Hari dibenarkan bersambung ke halaman lain. Bagi empat jenis laporan yang lain, kandungan jadual tidak boleh dipotong atau digugurkan untuk memenuhi had satu halaman. Laraskan susun atur secara dinamik dengan mengekalkan kebolehbacaan.

Jika Jadual Waktu Hari bersambung:
- Tajuk nama hari dan kepala kolum waktu diulang pada halaman sambungan.
- Kelas seterusnya disambung tanpa menggugurkan rekod.
- Hari persekolahan berikutnya tetap bermula pada halaman baharu.

### 14.4 Rekod atau slot kosong

- Rekod yang berkaitan tetap dipaparkan.
- Slot tanpa pengajaran dibiarkan kosong.
- Tiada rekod kelas, guru, subjek atau bilik digugurkan secara senyap.

### 14.5 Nombor halaman

Nombor halaman tidak perlu dipaparkan pada mana-mana laporan PDF TAVIO.

## 15. Pemilihan rekod sebelum preview

Bagi laporan Guru, Kelas, Subjek dan Bilik Khas, pengguna boleh memilih:

1. **Semua Rekod** — menjana semua rekod bagi kategori laporan yang dipilih.
2. **Rekod Tertentu** — pengguna memilih satu atau beberapa rekod sahaja.

Apabila Rekod Tertentu dipilih:
- Sistem memaparkan senarai rekod menggunakan checkbox.
- Pengguna boleh memilih atau membatalkan pilihan bagi beberapa rekod.
- Senarai mengikut turutan Master Data.
- Hanya rekod yang dipilih dimasukkan dalam fail PDF.
- Setiap rekod bermula pada halaman baharu, tertakluk kepada peraturan halaman dalam Seksyen 14.

Jadual Waktu Hari tidak memerlukan pemilihan rekod secara individu. Sistem menjana semua hari persekolahan yang dikonfigurasikan dalam satu fail PDF.

Tiada skrin ringkasan pengesahan tambahan diperlukan sebelum preview atau penjanaan PDF.

## 16. Aliran pengguna: Preview dan penjanaan PDF

Aliran yang dipersetujui:

1. Pilih Tahun Akademik, Sesi dan Versi Jadual Waktu.
2. Pilih jenis laporan.
3. Pilih variasi templat Dengan Tandatangan atau Tanpa Tandatangan jika jenis laporan mempunyai pilihan tersebut.
4. Pilih Semua Rekod atau Rekod Tertentu bagi laporan Guru, Kelas, Subjek atau Bilik Khas.
5. Tekan **PREVIEW PDF**.
6. Sistem menjalankan pengesahan syarat wajib yang berkaitan dan menjana preview menggunakan enjin PDF yang sama dengan PDF akhir.
7. Pengguna boleh menyemak halaman, mengezum dan bergerak antara halaman preview.
8. Jika preview berjaya, pengguna boleh menekan **JANA PDF** untuk menghasilkan fail akhir.

### 16.1 Tingkah laku Preview

- Preview ialah PDF sebenar yang dibina daripada pilihan dan data yang sama seperti PDF akhir.
- Preview bukan lakaran atau anggaran.
- Reka bentuk, fon, saiz kertas, margin, kandungan dan pemecahan halaman mesti sama dengan PDF akhir.
- Pengguna boleh menyemak semua halaman yang akan dijana.
- Preview tidak menyimpan atau mengubah data database.
- Jika syarat wajib tidak dipenuhi, preview disekat dan sistem memaparkan sebab serta tindakan yang perlu dibuat.
- Jika data atau pilihan berubah selepas preview, preview lama tidak boleh dianggap sah untuk pilihan baharu; sistem perlu menjana semula preview sebelum PDF akhir.
- Tiada halaman ringkasan pengesahan tambahan antara pemilihan rekod dengan Preview PDF.

### 16.2 Penjanaan PDF akhir

- Butang **JANA PDF** tersedia selepas preview berjaya dijana untuk pilihan semasa.
- PDF akhir mesti menggunakan sumber data, pilihan dan enjin susun atur yang sama seperti preview.
- Proses tidak boleh mengubah jadual waktu atau database.
- Pengguna tidak perlu menjana fail secara berasingan bagi setiap rekod.

## 17. Pengesahan dan sekatan sebelum preview/penjanaan

Sistem mesti menjalankan pengesahan yang berkaitan dengan jenis laporan dan rekod yang dipilih. Antara syarat wajib:

- Tahun akademik, sesi dan versi jadual waktu yang sah telah dipilih.
- Rekod yang dipilih wujud dalam versi jadual waktu tersebut.
- Nama ringkasan Guru, Subjek, Kelas dan Bilik yang berkaitan telah lengkap.
- Jadual Waktu Kelas: Guru Kelas mesti telah ditetapkan dan masih aktif.
- Templat bertandatangan: Prepared By dan Verified By mesti lengkap.
- Penandatangan yang dipilih mesti masih aktif.
- Prepared By dan Verified By mesti individu berbeza bagi jenis jadual yang sama.
- Logo sekolah menggunakan logo School Profile jika tersedia, jika tidak logo rasmi TAVIO sebagai gantian.
- Jika tarikh kuat kuasa NULL, beri amaran dan benarkan pengguna meneruskan tanpa tarikh atau membatalkan.

Jika pengesahan gagal, sistem mesti menerangkan rekod atau tetapan yang bermasalah dan tindakan yang perlu dibuat. Jangan menggugurkan rekod yang tidak lengkap secara senyap.

## 18. Pemetaan Schedule Signatories sedia ada

Skema database v2 mempunyai tiga jenis konfigurasi:

| Laporan | schedule_type |
|---|---|
| Jadual Waktu Guru | `TEACHER` |
| Jadual Waktu Kelas | `CLASS` |
| Jadual Waktu Bilik Khas | `SPECIAL_ROOM` |

Jadual Waktu Hari dan Jadual Waktu Subjek tidak memerlukan konfigurasi tandatangan.

Jangan tambah nilai `schedule_type` baharu untuk laporan Hari atau Subjek. Kekalkan peraturan Schedule Signatories sedia ada, termasuk Prepared By dan Verified By mesti berbeza dalam jenis jadual yang sama. Pentadbir yang sama boleh digunakan merentasi jenis jadual yang berlainan jika konfigurasi sedia ada membenarkannya.

## 19. Perkara yang masih belum dimuktamadkan

Perkara berikut tidak boleh diandaikan atau dilaksanakan tanpa keputusan lanjut:

1. **Tarikh tandatangan:** sumber tarikh belum diputuskan secara khusus — tarikh PDF dijana/dicetak atau tarikh tandatangan sebenar.
2. **Jadual Waktu Bilik Khas:** butiran visual penuh dan contoh susun atur khusus perlu disahkan, walaupun struktur asas seperti Jadual Waktu Subjek dan ruang tandatangan telah dipersetujui.
3. **Butiran saiz teks khusus:** saiz bagi elemen yang tidak disenaraikan dalam Seksyen 4.1 boleh diperincikan jika ujian visual menunjukkan keperluan.
4. **Pelaksanaan Guru Kelas:** hubungan pada rekod kelas memerlukan audit dan kelulusan perubahan skema berasingan kerana skema v2 yang diketahui belum mempunyai medan tersebut.

## 20. Had skop dan disiplin teknikal

Dokumen ini merekodkan spesifikasi laporan dan keperluan fungsinya sahaja. Ia bukan kebenaran untuk:
- mengubah skema database;
- menambah migration, jadual, lajur, indeks atau trigger;
- mengubah konfigurasi Schedule Signatories;
- mengubah solver atau enjin pembinaan jadual waktu;
- mengubah fungsi backup/restore;
- mengubah Master Data di luar keperluan yang telah diluluskan;
- membuat perubahan UI yang tidak berkaitan dengan aliran laporan.

Sebelum pembangunan:
1. Audit struktur projek dan skema database semasa.
2. Sahkan sumber data setiap jenis laporan.
3. Bentangkan cadangan teknikal bagi sebarang perubahan skema yang diperlukan.
4. Dapatkan kelulusan berasingan sebelum melaksanakan migration atau perubahan database.
5. Kekalkan skop kerja mengikut tugasan yang diluluskan dan uji pada Windows sebelum menganggap tugasan selesai.

---
Dokumen ini disediakan berdasarkan keputusan reka bentuk dan contoh templat yang telah dipersetujui dalam perbincangan TAVIO. Jika terdapat percanggahan dengan dokumen v1, keputusan yang lebih baharu dan dinyatakan secara jelas dalam dokumen v2 ini menjadi rujukan spesifikasi terkini.
