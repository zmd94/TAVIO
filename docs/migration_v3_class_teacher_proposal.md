# Cadangan Migration v3 — Penetapan Guru Kelas

**Status:** Draf untuk semakan dan kelulusan  
**Skop:** Menyimpan seorang Guru Kelas bagi setiap rekod kelas  
**Penting:** Dokumen ini ialah cadangan sahaja. Tiada perubahan skema, migration, kod aplikasi atau data dibuat.

## 1. Latar belakang

Audit terhadap skema semasa mendapati jadual `classes` belum mempunyai medan untuk menetapkan Guru Kelas.

Jadual `classes` sedia ada mengandungi `academic_year_id`, `session_id`, `short_name`, `name`, `home_room_id` dan `is_active`, selain medan pengurusan rekod. Jadual `teachers` menyimpan maklumat guru dan status `is_active`. Jadual `teacher_sessions` menghubungkan guru kepada tahun akademik dan sesi serta mempunyai status `is_active`.

Keputusan fungsi yang telah dipersetujui:
- Setiap rekod kelas mempunyai seorang Guru Kelas.
- Guru Kelas dipilih daripada Master Data Guru.
- Penetapan disimpan pada rekod kelas.
- Tiada medan tahun akademik atau sesi tambahan diperlukan pada penetapan kerana kedua-duanya sudah terdapat pada rekod kelas.
- Guru Kelas boleh berbeza daripada guru yang mengajar kelas tersebut.
- Guru Kelas wajib ditetapkan sebelum preview atau cetakan Jadual Waktu Kelas.
- Jika guru yang ditetapkan dinyahaktifkan kemudian, penetapan tidak dipadam secara automatik; sistem perlu memberi amaran dan meminta penggantian sebelum preview/cetakan.

## 2. Cadangan struktur data

Cadangan medan baharu pada jadual `classes`:

| Medan | Jenis | Nullable | Tujuan |
|---|---|---:|---|
| `class_teacher_id` | INTEGER | Ya | Merujuk kepada ID guru yang ditetapkan sebagai Guru Kelas |

Nama medan dicadangkan sebagai `class_teacher_id` kerana jelas dan konsisten dengan penamaan hubungan ID dalam skema sedia ada.

### Foreign key

Cadangan asas:

```sql
class_teacher_id INTEGER,
FOREIGN KEY (class_teacher_id)
    REFERENCES teachers(id) ON DELETE RESTRICT
```

- `NULL` dibenarkan supaya rekod kelas sedia ada kekal sah selepas migration.
- `ON DELETE RESTRICT` menghalang rekod guru yang masih digunakan sebagai Guru Kelas daripada dipadam secara fizikal.
- Penyahaktifan guru tidak memadam atau mengosongkan penetapan.

**Perkara integriti sesi:** Hubungan terus kepada `teachers(id)` tidak memastikan guru mempunyai rekod keahlian yang aktif dalam `teacher_sessions` bagi tahun akademik dan sesi kelas tersebut. Oleh itu, servis aplikasi wajib mengesahkan padanan `academic_year_id`, `session_id`, `teacher_id` dan status aktif pada kedua-dua rekod guru dan `teacher_sessions` sebelum penetapan disimpan. Jika kelulusan memerlukan jaminan pada peringkat database juga, reka bentuk foreign key komposit dan keperluan rebuild jadual `classes` perlu dinilai sebagai pilihan berasingan sebelum migration; ia tidak termasuk secara automatik dalam cadangan asas ini.

## 3. Peraturan aplikasi

1. Paparkan pilihan Guru Kelas daripada guru yang aktif dan mempunyai rekod `teacher_sessions` aktif untuk tahun akademik serta sesi kelas berkenaan.
2. Benarkan satu guru ditetapkan kepada lebih daripada satu kelas; tiada peraturan unik satu guru untuk satu kelas dicadangkan.
3. Simpan pilihan pada rekod `classes` yang berkenaan.
4. Apabila kelas ditukar tahun akademik atau sesi, sahkan semula kelayakan Guru Kelas. Jika tidak lagi sepadan, minta pengguna memilih guru yang layak sebelum menyimpan perubahan.
5. Jika guru atau keahlian sesi dinyahaktifkan selepas penetapan, kekalkan ID penetapan untuk mengelakkan kehilangan sejarah. Paparkan amaran dan sekat preview/cetakan Jadual Waktu Kelas sehingga penetapan diganti dengan guru yang layak.
6. Jika `class_teacher_id` masih `NULL`, sekat preview/cetakan Jadual Waktu Kelas dan nyatakan kelas yang belum mempunyai Guru Kelas.
7. Nama Guru Kelas pada PDF menggunakan nama penuh daripada Master Data Guru, bukan nama ringkasan.
8. Penetapan Guru Kelas tidak mengubah senarai guru mengajar, teaching assignments atau data jadual waktu.

## 4. Kesan terhadap rekod sedia ada

- Semua rekod kelas sedia ada menerima nilai `NULL` pada medan baharu.
- Tiada guru akan ditetapkan secara automatik atau diteka daripada rekod pengajaran.
- Pengguna perlu melengkapkan penetapan Guru Kelas secara manual.
- Rekod dan medan kelas sedia ada mesti dikekalkan.
- Migration tidak boleh mengubah atau memadam data jadual waktu.

## 5. Strategi migration dan risiko SQLite

Penambahan medan nullable dengan foreign key pada SQLite perlu disahkan terhadap versi SQLite yang digunakan dan cara migration semasa dilaksanakan.

Dua pendekatan perlu dibandingkan sebelum pelaksanaan:
- **Tambah medan dengan ALTER TABLE:** hanya diterima jika kekangan foreign key yang diperlukan boleh ditambah dengan selamat dan disokong oleh versi SQLite aplikasi.
- **Rebuild jadual classes:** bina semula jadual dengan definisi lengkap, salin semua data, indeks dan kekangan, kemudian sahkan foreign key. Ini lebih kompleks dan berisiko, jadi tidak boleh dipilih tanpa audit skrip schema penuh, indeks, trigger, migration runner dan ujian pemulihan.

Tiada pendekatan migration dipilih dalam draf ini. Pelaksana mesti mengesahkan versi SQLite sebenar dan menguji migration pada salinan database v2 yang mengandungi data contoh serta data kelas sedia ada.

## 6. Pelan ujian yang diperlukan

### Migration dan integriti database
- Database baharu boleh dibina sehingga versi skema selepas migration.
- Database v2 sedia ada boleh dinaik taraf tanpa kehilangan rekod atau nilai kelas.
- Semua rekod kelas lama mempunyai `class_teacher_id = NULL`.
- `PRAGMA foreign_key_check` tidak melaporkan ralat.
- `PRAGMA integrity_check` mengembalikan `ok`.
- Backup sebelum migration boleh dipulihkan.
- Migration tidak menghasilkan perubahan pada jadual lain yang tidak berkaitan.

### Peraturan penetapan
- Guru aktif dengan `teacher_sessions` aktif bagi tahun dan sesi yang betul boleh ditetapkan.
- Guru daripada sesi atau tahun akademik lain ditolak.
- Guru tidak aktif atau keahlian sesi tidak aktif tidak boleh dipilih.
- Penetapan guru kepada beberapa kelas dibenarkan.
- Pemadaman fizikal guru yang masih dirujuk dihalang.
- Penyahaktifan guru tidak mengosongkan penetapan sedia ada, tetapi menghasilkan amaran/sekatan laporan.
- Pertukaran tahun atau sesi kelas mengesahkan semula kelayakan guru.

### Laporan Jadual Waktu Kelas
- Kelas tanpa Guru Kelas disekat daripada preview dan cetakan.
- Kelas dengan Guru Kelas aktif memaparkan nama penuh yang betul.
- Guru Kelas tidak disamakan dengan guru yang mengajar kelas.
- Semakan ini tidak mengubah data database ketika preview atau cetakan.

## 7. Perkara di luar skop

Cadangan ini tidak merangkumi:
- Jadual baharu, indeks baharu atau trigger baharu.
- Penetapan Guru Kelas secara automatik.
- Perubahan kepada struktur guru mengajar atau solver.
- Perubahan kepada laporan selain Jadual Waktu Kelas.
- Pelaksanaan UI atau migration sebenar.

Sebarang keperluan jadual, indeks atau trigger tambahan mesti dibentangkan sebagai perubahan berasingan dan mendapat kelulusan terlebih dahulu.

## 8. Keputusan yang diperlukan sebelum pelaksanaan

Sila semak dan sahkan perkara berikut:

1. Nama medan `class_teacher_id` dan lokasi pada jadual `classes`.
2. Foreign key terus kepada `teachers(id)` dengan `ON DELETE RESTRICT`, bersama pengesahan keahlian sesi pada lapisan aplikasi.
3. Nilai `NULL` untuk rekod kelas sedia ada; tiada auto-assign.
4. Guru yang dinyahaktifkan mengekalkan penetapan sedia ada tetapi menghalang preview/cetakan sehingga diganti.
5. Tiada jadual, indeks atau trigger baharu dalam skop cadangan asas.

**Status pelaksanaan:** Belum diluluskan dan belum dilaksanakan.
