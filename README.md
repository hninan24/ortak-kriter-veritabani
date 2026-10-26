# Boykot Çalışma Grubu Veritabanı

İsrail boykot listelerinin marka bazında birleştirilmiş veritabanı. Site: **https://hninan24.github.io/ortak-kriter-veritabani/**

Veritabanında 14 listeden toplanan 6.693 kuruluş var. Her kuruluş için şunlar gösterilir:

- listelerin hükmü,
- açıklama metni,
- kaynak bağlantısı,
- çatı şirket ilişkisi.

Kriter kodu yoktur. Bu sürümde kuruluşlar yalnızca listelerin hükmüne göre ayrılır.

## Listeler

| Liste | Kayıt |
|---|---:|
| Boykot Dedektifi (boykotdedektifi.com) | 2.556 |
| No Thanks — uygulamanın Level 1 ve Level 2 kayıtları | 2.188 |
| DBIO — Don't Buy Into Occupation (2025) | 1.218 |
| bykt.org | 1.167 |
| Boykot.co (yalnız “Boykot” durumundakiler) | 934 |
| Abbott & Keefer | 687 |
| Who Profits | 472 |
| Kolay Boykot — Filistin İçin | 330 |
| Eczanede Boykot (ilaçlar, kök marka) | 316 |
| Bilinçli Tüketim | 296 |
| BM OHCHR A/HRC/63/20 (Liste A) | 219 |
| Boycat — uygulamadaki “En iyi markalar” (Watermelon) | 199 |
| Investigate (AFSC) | 187 |
| AFSC — Gazze soykırımı şirketleri | 58 |

Metinler ve hükümler ilgili listelere aittir. Her kaydın yanında kaynağına giden bağlantı vardır.

Son güncelleme: 26 Ekim 2026. No Thanks uygulamasının 2.188 boykot kaydı eklendi (iOS uygulamasının 26 Ekim verisi): seviye (Level 1: Strong Connection to Israel, Level 2: Indirect Support for Israel), BDS işareti, uygulamadaki gerekçe metni ve kaynak bağlantıları. “Level 3: No Known Connection to Israel” markaları (3) alınmadı. Uygulamanın marka sayfası ve çatı alanı yok; 917 marka mevcut kuruluşlara bağlandı, 1.231'i yeni. Aynı adı taşıyan farklı markalar ayrı tutuldu (ör. Silk (Danone), Brisa (Coca-Cola), Tic Tac).

Aynı gün Boykot.co'nun “Boykot” durumundaki 934 markası eklendi (24 Ekim taraması; “Boykot değil” markalar alınmadı): sitedeki gerekçe metni, marka sayfası ve kanıt bağlantısı; 865'i mevcut kuruluşlara bağlandı, 29'u yeni. Metinler sitenin kendi metinleridir ve kaynak sayfasıyla birlikte verilir.

24 Ekim 2026: Boycat uygulamasının “En iyi markalar” listesi (199 marka) eklendi: uygulamadaki seviye (Official BDS Priority Campaign, Level 2, Level 3), research.boycat.io'daki gerekçe metni ve şirket sayfası; 116'sı mevcut kuruluşlara bağlandı, 82'si yeni. Ayrıntı panelinde çatının alt markalarından ve alt markanın çatısından devraldığı listeler de gösteriliyor. bykt'nin listeden çıkardığı Damla Minera “geri çekildi” olarak işaretlendi.

20 Ekim 2026: bykt 20 Ekim, Bilinçli Tüketim 18 Ekim verisine geçirildi: Lefties, Derimod ve Philips eklendi, 27 bykt gerekçesi güncellendi. Who Profits'in kaldırdığı Aldo ve SEMI kayıtları “geri çekildi” olarak işaretlendi.

## Kaynak izleme

Listelerin çoğu canlı sitelerde değişiyor. `izleme/` klasöründeki betik bu siteleri GitHub Actions üzerinden her gün (Boykot Dedektifi, Kolay Boykot ve Boykot.co'yu her pazartesi) kontrol eder. Bir önceki kontrolden bu yana eklenen, çıkan, hükmü ya da gerekçesi değişen kayıtları raporlar ve [`izleme` etiketli Issue](https://github.com/hninan24/ortak-kriter-veritabani/issues?q=label%3Aizleme)'ya yazar. Her değişiklik olay kaydına (`izleme/olaylar.json`) da girer ve sitenin **Güncellemeler** sekmesinde marka, liste, değişiklik türü ve tarihiyle görünür. Bir listenin geri çektiği kanıt silinmez, “geri çekildi” diye işaretlenir. Yeni veri veritabanına kendiliğinden işlenmez. Ayrıntı: [izleme/README.md](izleme/README.md).

## Öncelikli Boykot Listesi (ÖBL) nasıl hazırlanır

1. Siteyi açın. **Kuruluşlar** sekmesinde bir markanın sağındaki **“Öncelikli Boykot Listesine Ekle”** düğmesine basın. Marka, çatı şirketi ve çatının bütün alt markalarıyla birlikte listeye girer.
2. **Öncelikli Boykot Listesi** sekmesinde yalnızca çatı şirketler görünür; alt markalar kuruluşa tıklayınca açılan panelde listelenir. Yanlış eklediğiniz bir kuruluşu **“Listeden çıkar”** ile kaldırabilirsiniz.
3. Kampanya önceliği vermek istediğiniz çatının sağındaki **yıldıza** basın. Yıldız kırmızıya döner ve kuruluş listenin başındaki “Kampanya önceliği” bölümüne geçer. Yıldızsızlar, suçu sabit olduğu hâlde günlük tüketimde olmadığı için aşağıda kalır. Yıldızı kaldırmak için yeniden basın.
4. Seçimleriniz **yalnızca kendi tarayıcınızda** saklanır. Başka bir tarayıcıda ya da cihazda görünmez. Tarayıcı verisini silerseniz liste de silinir.
5. Listeniz bitince ÖBL sekmesindeki **“Excel olarak dışa aktar”** düğmesine basın. Dosyayı gruba gönderin; listeler sonra birleştirilir.

Excel dosyasında şu sayfalar var:

- **Kampanya:** yıldızladığınız çatılar, alt markalarının adlarıyla.
- **Çatılar:** her çatı için listelerin hükmü, seçtiğiniz marka ve kampanya önceliği.
- **Tüm kuruluşlar:** çatılar ve bütün alt markaları.
- **Açıklamalar:** listelerin metinleri ve bağlantıları.
- **Bilgi**

## Dosyalar

- `izleme/`: kaynak izleme betiği, anlık görüntüler ve raporlar.
- `index.html`: sitenin tamamı. Veri sayfanın içindedir. Dosyayı indirip internet olmadan da açabilirsiniz; bu durumda seçimleriniz o tarayıcının yerel belleğinde tutulur.
