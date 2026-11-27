# TAVIO — Rekod Keputusan Penjanaan PDF

Tarikh rekod: 27 November 2026
Status: Rekod keputusan perbincangan pengguna
Skop: Susun atur PDF, preview, penjanaan PDF akhir, pengendalian ralat dan pengurusan fail PDF

## 1. Tujuan dan hubungan dengan spesifikasi laporan

Dokumen ini merekodkan keputusan tambahan yang dipersetujui selepas semakan dokumen `docs/report_template_v2.md` versi 2.1.

Dokumen ini ialah rekod keputusan tambahan, bukan pengganti keseluruhan spesifikasi templat laporan v2.1. Jika sesuatu keputusan di sini memperincikan atau mengubah keputusan terdahulu dalam v2.1, keputusan pengguna yang lebih baharu dalam rekod ini hendaklah dirujuk untuk semakan spesifikasi seterusnya.

Dokumen ini tidak memberi kebenaran untuk mengubah kod aplikasi, skema database, migration, solver atau modul lain. Pelaksanaan memerlukan tugasan dan kelulusan pembangunan yang berasingan.

## 2. Susun atur halaman dan saiz teks

1. Saiz teks yang telah disenaraikan dalam spesifikasi laporan ialah saiz default, bukan saiz tetap yang wajib digunakan dalam semua keadaan.
2. Saiz teks dan susun atur boleh dilaraskan secara fleksibel mengikut kepadatan kandungan.
3. Keutamaan reka bentuk ialah memastikan setiap jadual waktu individu bagi laporan Guru, Kelas, Bilik Khas dan Subjek muat dalam satu halaman A4 Landscape.
4. Pelarasan mesti mengekalkan kejelasan dan kebolehbacaan. Sistem hendaklah mengoptimumkan susun atur dan penggunaan ruang sebelum mengecilkan teks secara berlebihan.
5. Jika pengguna memilih beberapa rekod, satu fail PDF mengandungi beberapa halaman: satu halaman bagi setiap jadual individu yang dipilih.
6. Peraturan khusus Jadual Waktu Hari dalam spesifikasi v2.1 kekal: setiap hari bermula pada halaman baharu dan kandungan hari tersebut boleh bersambung ke halaman seterusnya jika diperlukan.

## 3. Jadual yang tidak dapat dimuatkan dengan jelas

1. Jika satu jadual individu masih tidak dapat dipaparkan dengan jelas dalam satu halaman selepas pelarasan susun atur dan saiz teks, TAVIO mesti menganggapnya sebagai ralat.
2. TAVIO memaparkan notifikasi yang menerangkan masalah paparan dan meminta pengguna membuat aduan kepada developer.
3. Jika pengguna memilih beberapa rekod dan sekurang-kurangnya satu jadual gagal melepasi pemeriksaan paparan, keseluruhan proses penjanaan PDF dibatalkan.
4. TAVIO tidak boleh menghasilkan PDF separa yang mengandungi hanya rekod yang berjaya.
5. Notifikasi ralat mesti menyenaraikan dengan jelas setiap jadual/rekod yang bermasalah, termasuk jenis laporan dan nama rekod yang berkaitan.
6. TAVIO tidak boleh menggugurkan atau memotong kandungan secara senyap untuk memaksa jadual muat.

Contoh kandungan notifikasi:

> **Penjanaan PDF dibatalkan**
>
> Satu atau lebih jadual waktu tidak dapat dipaparkan dengan jelas dalam satu halaman.
>
> Jadual bermasalah:
> - Jadual Waktu Guru — [nama guru]
> - Jadual Waktu Kelas — [nama kelas]
>
> Sila buat aduan kepada developer untuk pemeriksaan dan tindakan lanjut.

## 4. Pembetulan data dan penjanaan semula jadual waktu

1. Jika pengguna menemui kesilapan atau masalah dalam preview, pengguna boleh kembali ke bahagian pengurusan data dan jadual waktu.
2. Pengguna boleh membetulkan Master Data, Teacher Assignment dan maklumat berkaitan yang diperlukan.
3. Pengguna kemudian menjana semula jadual waktu sehingga proses penjanaan berjaya dan hasilnya boleh digunakan.
4. Selepas itu, pengguna kembali ke halaman Preview PDF untuk menghasilkan preview baharu berdasarkan jadual waktu terkini.
5. Pilihan laporan terdahulu dikekalkan secara automatik jika masih sah, supaya pengguna tidak perlu membuat semua pemilihan dari awal.
6. Pilihan yang tidak lagi sah akibat perubahan data atau versi perlu disahkan semula atau dipilih semula.
7. Jika Master Data, Teacher Assignment atau data lain yang mempengaruhi laporan berubah selepas preview dijana tetapi sebelum PDF akhir disimpan, preview terdahulu menjadi tidak sah. TAVIO tidak boleh menggunakan preview tersebut untuk menghasilkan PDF akhir.
8. Jika perubahan itu memerlukan jadual waktu dijana semula, pengguna mesti menyelesaikan penjanaan jadual waktu terlebih dahulu sebelum menghasilkan preview baharu.

## 5. Pengurusan fail Preview PDF sementara

1. Preview ialah fail PDF sementara sebenar yang disemak pengguna.
2. Apabila jadual waktu baharu berjaya dijana, TAVIO memadam fail Preview PDF lama secara automatik dan membersihkan rujukan kepada fail tersebut.
3. Preview lama tidak boleh digunakan semula selepas jadual waktu baharu dijana.
4. Jika fail preview lama sedang dibuka atau tidak dapat dipadam, TAVIO mengendalikan keadaan itu dengan selamat dan tetap menandakan preview lama sebagai tidak sah. Ia tidak boleh digunakan sebagai preview terkini.
5. Apabila aplikasi TAVIO ditutup secara normal, fail Preview PDF sementara bagi sesi tersebut dipadam dan rujukannya dibersihkan.
6. Jika aplikasi crash, komputer terpadam atau aplikasi tertutup secara luar jangka, TAVIO memeriksa dan membersihkan fail preview sementara yang tertinggal apabila aplikasi dibuka semula.
7. Pembersihan preview sementara tidak boleh menjejaskan mana-mana PDF akhir yang telah disimpan oleh pengguna.
8. Fail preview sementara hanya sah untuk sesi dan pilihan/data yang digunakan untuk menjana preview tersebut.

## 6. Hubungan Preview PDF dengan PDF akhir

1. Pengguna mesti menyemak Preview PDF sebelum menghasilkan PDF akhir.
2. Apabila pengguna menekan **JANA PDF**, TAVIO menggunakan fail Preview PDF yang sama tepat dan menyimpan/menyalinnya ke lokasi akhir yang dipilih pengguna.
3. TAVIO tidak menjana semula kandungan PDF daripada database ketika **JANA PDF** ditekan.
4. Jika fail preview hilang, rosak, tidak boleh dibaca atau tidak lagi sah, proses penjanaan PDF akhir disekat dan pengguna perlu menjana preview baharu.
5. PDF akhir mestilah sepadan tepat dengan preview yang telah disemak pengguna.

## 7. Nama fail PDF akhir

1. TAVIO mencadangkan nama fail secara automatik berdasarkan jenis laporan, skop/rekod yang dipilih dan tahun akademik.
2. Pengguna boleh mengubah nama fail sebelum menyimpan.
3. Nama fail mesti mematuhi sekatan nama fail Windows.
4. Contoh nama fail:
   - `Jadual_Guru_Ahmad_Ali_2026.pdf`
   - `Jadual_Kelas_5_Bestari_2026.pdf`
   - `Jadual_Bilik_Makmal_Sains_2026.pdf`
   - Untuk beberapa rekod: `Jadual_Guru_Sesi_Pagi_2026.pdf`
5. TAVIO tidak boleh menggantikan fail sedia ada secara senyap.

### 7.1 Nama fail yang telah wujud

Jika fail dengan nama yang sama telah wujud di lokasi destinasi, TAVIO memaparkan tiga tindakan:

- **GANTIKAN** — menggantikan fail sedia ada hanya selepas persetujuan/pengesahan pengguna.
- **SIMPAN SEBAGAI** — membolehkan pengguna menentukan nama atau lokasi lain.
- **BATAL** — membatalkan penyimpanan tanpa mengubah fail sedia ada.

## 8. Pengendalian kegagalan menyimpan PDF akhir

Jika PDF akhir gagal disimpan, contohnya disebabkan lokasi tidak tersedia, ruang storan tidak mencukupi, fail dikunci, kebenaran menulis tiada atau masalah sistem:

1. TAVIO memaparkan notifikasi kegagalan.
2. Punca kegagalan dipaparkan jika dapat dikenal pasti.
3. Pengguna boleh mencuba semula atau memilih lokasi penyimpanan lain.
4. Preview sementara dikekalkan selagi sesi aplikasi masih berjalan dan preview itu masih sah.
5. PDF hanya dianggap berjaya dijana selepas fail akhir benar-benar berjaya disimpan.
6. Kegagalan penyimpanan tidak boleh meninggalkan fail akhir separa yang dilaporkan sebagai berjaya.

## 9. Notifikasi selepas PDF berjaya dijana

Selepas PDF akhir berjaya disimpan, TAVIO memaparkan notifikasi yang mengandungi:

- Jenis laporan.
- Nama fail PDF.
- Lokasi folder penyimpanan.
- Bilangan halaman PDF.

Notifikasi menyediakan dua butang sahaja:

- **BUKA FOLDER** — membuka Windows File Explorer pada folder yang mengandungi PDF akhir.
- **TUTUP** — menutup notifikasi sahaja.

Tiada butang **BUKA PDF** diperlukan.

Contoh kandungan:

> **PDF BERJAYA DIJANA!**
>
> Jenis laporan: Jadual Waktu Guru
> Nama fail: Jadual_Guru_Sesi_Pagi_2026.pdf
> Lokasi: D:\TAVIO\Laporan\
> Bilangan halaman: 10
>
> [BUKA FOLDER] [TUTUP]

## 10. Status dan pemilikan PDF akhir

1. PDF akhir ialah dokumen bebas yang diuruskan oleh pengguna melalui Windows.
2. Selepas disimpan, TAVIO tidak boleh mengubah atau memadam PDF akhir secara automatik.
3. Pengguna bebas menyalin, memindahkan, menamakan semula atau memadam PDF akhir melalui Windows.
4. Pemadaman fail Preview PDF sementara tidak boleh menjejaskan PDF akhir.
5. TAVIO hanya menggantikan PDF akhir sedia ada jika pengguna memilih **GANTIKAN** dan mengesahkannya.
6. PDF akhir kekal walaupun pengguna menutup TAVIO, membuka ruang kerja lain atau memadam preview sementara.
7. Tiada fungsi sejarah penjanaan PDF atau pangkalan data khusus untuk merekod sejarah penjanaan diperlukan.

## 11. Had skop dan perkara yang perlu diselaraskan

1. Rekod ini tidak mengubah skema database atau peraturan foreign key sedia ada.
2. Perbincangan tentang pengguna memadam rekod Master Data yang tidak lagi diperlukan tidak bermaksud sistem boleh memadam rekod yang masih dirujuk secara paksa. Pelaksanaan pemadaman mesti mematuhi integriti hubungan data dan kekangan database sedia ada.
3. Fungsi SAVE AS/OPEN AS untuk pakej data TAVIO dan pengurusan beberapa ruang kerja dibincangkan secara berasingan. Ia bukan sebahagian daripada spesifikasi penjanaan PDF dalam dokumen ini.
4. Sebelum pembangunan, spesifikasi v2.1 dan rekod keputusan ini perlu diselaraskan supaya tiada peraturan lama yang bercanggah. Perubahan dokumen spesifikasi utama hendaklah dibuat selepas semakan dan kelulusan pengguna.
5. Tiada kod aplikasi, skema database atau migration diubah melalui rekod dokumentasi ini.

---
Dokumen ini merekodkan keputusan yang telah dipersetujui dalam perbincangan pengguna dan hendaklah digunakan sebagai rekod rujukan untuk penyelarasan spesifikasi laporan TAVIO yang seterusnya.
