# Database Migration v3 — Guru Kelas

**Status:** Kod migration dan ujian automatik telah disediakan; pengesahan ujian masih menunggu.  
**Skop pusingan ini:** Menambah medan Guru Kelas pada jadual classes melalui Database Migration v3.  
**Belum termasuk:** UI pengurusan Guru Kelas, validasi pada lapisan aplikasi dan integrasi laporan PDF.

## 1. Latar belakang dan keputusan reka bentuk

Audit skema mendapati jadual classes sebelum Migration v3 belum mempunyai medan untuk menyimpan Guru Kelas.

Jadual berkaitan:
- **classes** menyimpan rekod kelas, termasuk academic_year_id dan session_id.
- **teachers** menyimpan maklumat guru dan status is_active.
- **teacher_sessions** menghubungkan guru kepada tahun akademik dan sesi serta mempunyai status is_active.

Keputusan reka bentuk berikut telah dipersetujui:

1. Setiap kelas boleh mempunyai seorang Guru Kelas yang disimpan pada rekod kelas.
2. Guru Kelas dipilih daripada Master Data Guru dan mesti mempunyai keahlian sesi yang sah bagi tahun akademik serta sesi kelas berkenaan.
3. Guru Kelas boleh berbeza daripada guru yang mengajar kelas tersebut.
4. Seorang guru boleh ditetapkan sebagai Guru Kelas untuk lebih daripada satu kelas.
5. Kelas sedia ada tidak akan diberikan Guru Kelas secara automatik.
6. Jika guru atau keahlian sesinya dinyahaktifkan selepas penetapan, penetapan sedia ada dikekalkan. Preview dan cetakan Jadual Waktu Kelas perlu disekat sehingga penetapan digantikan dengan guru yang layak.
7. Tiada jadual, indeks atau trigger baharu dalam skop asas.
8. Perubahan skema menggunakan ALTER TABLE, bukan rebuild jadual classes.

## 2. Skema yang dilaksanakan

Migration v3 menambah medan berikut pada jadual classes:

| Medan | Jenis | Nullable | Tujuan |
|---|---|---:|---|
| class_teacher_id | INTEGER | Ya | Merujuk kepada ID guru yang ditetapkan sebagai Guru Kelas |

SQL migration:

    ALTER TABLE classes
    ADD COLUMN class_teacher_id INTEGER
    REFERENCES teachers(id) ON DELETE RESTRICT;

Peraturan skema:
- NULL dibenarkan supaya rekod kelas sedia ada kekal sah selepas migration.
- Foreign key merujuk kepada teachers(id).
- ON DELETE RESTRICT menghalang guru yang masih dirujuk sebagai Guru Kelas daripada dipadam secara fizikal.
- Penyahaktifan guru tidak memadam atau mengosongkan penetapan.

**Pengesahan keahlian sesi:** Foreign key terus kepada teachers(id) tidak memastikan guru mempunyai rekod teacher_sessions yang aktif bagi tahun akademik dan sesi kelas tersebut. Oleh itu, lapisan aplikasi mesti mengesahkan padanan academic_year_id, session_id, teacher_id serta status aktif pada rekod guru dan teacher_sessions sebelum penetapan disimpan. Pengesahan aplikasi ini belum dilaksanakan dalam pusingan migration v3 ini.

## 3. Butiran implementasi migration

Perubahan kod migration:
- SQL skema v3: **tavio/src/tavio/database/schema_v3.py**.
- Pendaftaran migration: **tavio/src/tavio/database/migrations.py**.
- Migration v3 didaftarkan selepas migration v2 dan menaik taraf PRAGMA user_version kepada 3.

Strategi yang digunakan ialah ALTER TABLE ADD COLUMN. Kolum baharu bersifat nullable dan tidak mempunyai nilai DEFAULT bukan NULL, maka pendekatan ini boleh digunakan tanpa rebuild jadual.

Kesan yang dijangka:
- Semua data kelas sedia ada dikekalkan.
- Rekod kelas sedia ada menerima nilai class_teacher_id = NULL.
- Tiada auto-assignment dibuat.
- Indeks, trigger dan struktur jadual lain tidak sepatutnya berubah akibat penambahan kolum ini.

## 4. Peraturan aplikasi yang perlu dibangunkan

Perkara berikut ialah keperluan untuk kerja susulan; ia **belum dilaksanakan** oleh migration v3 ini:

1. Paparkan pilihan Guru Kelas daripada guru yang aktif dan mempunyai rekod teacher_sessions aktif bagi tahun akademik serta sesi kelas berkenaan.
2. Benarkan seorang guru ditetapkan kepada lebih daripada satu kelas.
3. Simpan pilihan pada rekod classes yang berkenaan.
4. Apabila tahun akademik atau sesi kelas berubah, sahkan semula kelayakan Guru Kelas. Jika tidak lagi sepadan, minta pengguna memilih guru yang layak sebelum menyimpan perubahan.
5. Jika guru atau keahlian sesi dinyahaktifkan selepas penetapan, kekalkan ID penetapan. Paparkan amaran dan sekat preview/cetakan Jadual Waktu Kelas sehingga penetapan diganti.
6. Jika class_teacher_id masih NULL, sekat preview/cetakan dan nyatakan kelas yang belum mempunyai Guru Kelas.
7. Pada PDF, paparkan nama penuh Guru Kelas daripada Master Data Guru, bukan nama ringkasan.
8. Penetapan Guru Kelas tidak mengubah senarai guru mengajar, teaching assignments atau data jadual waktu.

## 5. Kesan terhadap rekod sedia ada

- Semua rekod kelas sedia ada dikekalkan.
- Nilai awal class_teacher_id bagi rekod sedia ada ialah NULL.
- Tiada guru ditetapkan secara automatik atau diteka daripada rekod pengajaran.
- Pengguna perlu melengkapkan penetapan Guru Kelas melalui fungsi aplikasi apabila fungsi tersebut dibangunkan.
- Migration tidak mengubah atau memadam data jadual waktu.

## 6. Ujian dan status pengesahan

### Ujian migration yang telah ditambah

Ujian berkaitan migration v3 telah ditulis dalam **tavio/tests/test_database.py**. Liputannya termasuk:
- Database baharu melalui migration sehingga versi 3.
- Naik taraf database v2 ke v3 dengan mengekalkan data sedia ada.
- Nilai class_teacher_id kekal NULL bagi rekod kelas lama.
- Jenis kolum, nullable, foreign key dan tindakan ON DELETE RESTRICT.
- Penolakan ID guru yang tidak wujud dan pemadaman guru yang masih dirujuk.
- Migration gagal yang perlu rollback tanpa menaikkan user_version atau meninggalkan kolum baharu.
- Pengulangan inisialisasi database tanpa mengaplikasikan migration sekali lagi.

**Penting:** Ujian tersebut telah ditulis tetapi belum dijalankan dan belum disahkan lulus. Keputusan pytest, Ruff serta pemeriksaan manual database masih belum tersedia.

### Ujian susulan selepas fungsi aplikasi dibangunkan

Perkara berikut belum diliputi sepenuhnya oleh ujian migration dan perlu diuji apabila fungsi berkaitan tersedia:
- Guru daripada tahun akademik atau sesi lain ditolak.
- Guru tidak aktif atau keahlian sesi tidak aktif tidak boleh dipilih.
- Penetapan kepada beberapa kelas dibenarkan.
- Penyahaktifan guru mengekalkan penetapan tetapi mencetuskan amaran/sekatan laporan.
- Pertukaran tahun atau sesi kelas mengesahkan semula kelayakan guru.
- Kelas tanpa Guru Kelas disekat daripada preview dan cetakan.
- PDF memaparkan nama penuh Guru Kelas yang betul dan tidak menyamakannya dengan guru mengajar.
- Preview atau cetakan tidak mengubah data database.

## 7. Skop yang tidak berubah

Perkara berikut kekal di luar skop Migration v3:
- UI pemilihan dan pengurusan Guru Kelas.
- Validasi keahlian teacher_sessions pada lapisan aplikasi.
- Pengendalian penetapan apabila guru atau keahlian sesi dinyahaktifkan.
- Integrasi Guru Kelas dalam laporan PDF Jadual Waktu Kelas.
- Penetapan Guru Kelas secara automatik.
- Perubahan kepada struktur guru mengajar atau solver.
- Perubahan kepada laporan selain keperluan Guru Kelas yang dinyatakan.

Tiada jadual, indeks atau trigger baharu ditambah dalam skop yang diluluskan. Sebarang peluasan skema memerlukan cadangan dan kelulusan berasingan.

## 8. Rekod kelulusan

Perkara berikut telah disemak dan dipersetujui sebelum implementasi:

1. Medan class_teacher_id ditambah pada jadual classes.
2. Foreign key terus kepada teachers(id) menggunakan ON DELETE RESTRICT, dengan validasi keahlian sesi pada lapisan aplikasi.
3. Rekod kelas sedia ada kekal dengan nilai NULL; tiada auto-assignment.
4. Guru yang dinyahaktifkan mengekalkan penetapan sedia ada, tetapi preview/cetakan perlu disekat sehingga penetapan diganti.
5. Tiada jadual, indeks atau trigger baharu dalam skop asas.
6. Migration dilaksanakan menggunakan ALTER TABLE, tanpa rebuild jadual classes.

---

## Ringkasan status

| Komponen | Status |
|---|---|
| Audit skema dan keputusan reka bentuk | Dipersetujui |
| Migration v3 — tambah classes.class_teacher_id | Kod disediakan |
| Pendaftaran migration dan naik taraf user_version | Kod disediakan |
| Ujian automatik migration v3 | Ditulis, belum dijalankan |
| Pengesahan pytest dan Ruff | Menunggu |
| Ujian manual database pada Windows | Menunggu |
| UI pemilihan Guru Kelas | Belum dibangunkan |
| Validasi guru dan teacher_sessions | Belum dibangunkan |
| Integrasi Guru Kelas dalam PDF Jadual Waktu Kelas | Belum dibangunkan |
