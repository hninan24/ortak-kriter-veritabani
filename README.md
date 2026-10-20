# Ortak Kriter Veritabanı VI

İsrail boykot listelerinin marka bazında birleştirilmiş veritabanı. Site: **https://hninan24.github.io/ortak-kriter-veritabani/**

Veritabanında 11 listeden toplanan 5.351 kuruluş var. Her kuruluş için şunlar gösterilir:

- listelerin hükmü,
- açıklama metni,
- kaynak bağlantısı,
- çatı şirket ilişkisi.

Kriter kodu yoktur. Bu sürümde kuruluşlar yalnızca listelerin hükmüne göre ayrılır.

## Listeler

| Liste | Kayıt |
|---|---:|
| Boykot Dedektifi (boykotdedektifi.com) | 2.556 |
| DBIO — Don't Buy Into Occupation (2025) | 1.218 |
| bykt.org | 1.167 |
| Abbott & Keefer | 687 |
| Who Profits | 472 |
| Kolay Boykot — Filistin İçin | 330 |
| Eczanede Boykot (ilaçlar, kök marka) | 316 |
| Bilinçli Tüketim | 296 |
| BM OHCHR A/HRC/63/20 (Liste A) | 219 |
| Investigate (AFSC) | 187 |
| AFSC — Gazze soykırımı şirketleri | 58 |

Metinler ve hükümler ilgili listelere aittir. Her kaydın yanında kaynağına giden bağlantı vardır.

Son güncelleme: 20 Ekim 2026. bykt 20 Ekim, Bilinçli Tüketim 18 Ekim verisine geçirildi (Lefties, Derimod ve Philips eklendi, 27 bykt gerekçesi güncellendi).

## Kaynak izleme

Listelerin çoğu canlı sitelerde değişiyor. `izleme/` klasöründeki betik bu siteleri GitHub Actions üzerinden her gün (Boykot Dedektifi ve Kolay Boykot'u her pazartesi) kontrol eder. Bir önceki kontrolden bu yana eklenen, çıkan, hükmü ya da gerekçesi değişen kayıtları raporlar ve [`izleme` etiketli Issue](https://github.com/hninan24/ortak-kriter-veritabani/issues?q=label%3Aizleme)'ya yazar. Değişiklikler veritabanına kendiliğinden işlenmez. Ayrıntı: [izleme/README.md](izleme/README.md).

## Öncelikli Boykot Listesi (ÖBL) nasıl hazırlanır

1. Siteyi açın. **Kuruluşlar** sekmesinde bir markanın sağındaki **“Öncelikli Boykot Listesine Ekle”** düğmesine basın. Marka, çatı şirketi ve çatının bütün alt markalarıyla birlikte listeye girer.
2. **Öncelikli Boykot Listesi** sekmesinde yalnızca çatı şirketler görünür; alt markalar kuruluşa tıklayınca açılan panelde listelenir. Yanlış eklediğiniz bir kuruluşu **“Listeden çıkar”** ile kaldırabilirsiniz.
3. Seçimleriniz **yalnızca kendi tarayıcınızda** saklanır. Başka bir tarayıcıda ya da cihazda görünmez. Tarayıcı verisini silerseniz liste de silinir.
4. Listeniz bitince ÖBL sekmesindeki **“Excel olarak dışa aktar”** düğmesine basın. Dosyayı gruba gönderin; listeler sonra birleştirilir.

Excel dosyasında şu sayfalar var:

- **Çatılar:** her çatı için listelerin hükmü ve seçtiğiniz marka.
- **Tüm kuruluşlar:** çatılar ve bütün alt markaları.
- **Açıklamalar:** listelerin metinleri ve bağlantıları.
- **Bilgi**

## Dosyalar

- `izleme/`: kaynak izleme betiği, anlık görüntüler ve raporlar.
- `index.html`: sitenin tamamı. Veri sayfanın içindedir. Dosyayı indirip internet olmadan da açabilirsiniz; bu durumda seçimleriniz o tarayıcının yerel belleğinde tutulur.
