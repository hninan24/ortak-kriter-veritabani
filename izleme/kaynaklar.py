"""Kaynak sitelerin çekicileri ve normalleştiricileri.

Her kaynak `cek(onceki)` ile güncel durumu alır ve ortak biçimde döndürür:
    {"kayitlar": {kimlik: kayit}, "parmak_izi": str|None, "meta": {...}, "uyarilar": [...]}
ya da parmak izi önceki kontrolle aynıysa {"degismedi": True, "parmak_izi": ...}.

Kayıt alanları (hepsi isteğe bağlı): ad, hukum, kapsam (Ortak Kriter Veritabanı'nın aldığı hükümlerden biri mi), cati,
metin (gerekçe/açıklama), kaynaklar (kanıt bağlantıları), url, ek (kaynağa özgü diğer alanlar).
`normalle_*` işlevleri hem canlı çekimde hem de ilk anlık görüntüyü yerel dışa aktarımlardan kurarken kullanılır; böylece
ikisi aynı biçimde karşılaştırılır.
"""
import datetime as dt
import hashlib
import html as H
import json
import random
import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0 Safari/537.36")
_yerel = threading.local()


class KaynakHatasi(Exception):
    pass


def oturum():
    if not hasattr(_yerel, "s"):
        _yerel.s = requests.Session()
        _yerel.s.headers.update({"User-Agent": UA, "Accept-Language": "tr,en;q=0.8"})
    return _yerel.s


def al(url, deneme=5, bekle=5, kabul=(200,), **kw):
    """GET; geçici hatalarda artan beklemeyle yeniden dener. 404 gibi kabul edilen kodlar dışındakilerde hata verir."""
    son = None
    for i in range(deneme):
        try:
            r = oturum().get(url, timeout=60, **kw)
            if r.status_code in kabul or r.status_code == 404:
                return r
            son = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            son = type(e).__name__
        time.sleep(min(120, bekle * 2 ** i))
    raise KaynakHatasi(f"{url}: {son}")


def sayfa_metni(url, **kw):
    """Sayfanın metni; satır sonları \\n'e çevrilir (yerel dışa aktarımlar dosyadan okunduğu için öyle)."""
    return al(url, **kw).text.replace("\r\n", "\n").replace("\r", "\n")


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def tekil(xs):
    return list(dict.fromkeys(x.strip() for x in xs if isinstance(x, str) and x.strip()))


def bos(x):
    x = (x or "").strip() if isinstance(x, str) else x
    return x or None


def kayit(ad, hukum=None, kapsam=True, cati=None, metin=None, kaynaklar=(), url=None, *, tarih=None, eklenme=None, **ek):
    """tarih / eklenme: kaydın listedeki son güncelleme ve eklenme tarihi (biliniyorsa). Karşılaştırmaya girmez, yalnız
    olay tarihinde kullanılır."""
    r = {"ad": bos(ad), "hukum": bos(hukum), "kapsam": bool(kapsam), "cati": bos(cati), "metin": bos(metin),
         "kaynaklar": tekil(kaynaklar), "url": bos(url), "tarih": bos(tarih), "eklenme": bos(eklenme)}
    ek = {k: v for k, v in ek.items() if v not in (None, "", [], {})}
    if ek:
        r["ek"] = ek
    return {k: v for k, v in r.items() if v not in (None, [])}


# ===================================================================== bykt.org
BYKT_META = "https://firebasestorage.googleapis.com/v0/b/boykot-listesi-e7b96.firebasestorage.app/o/brands.json"
BYKT_DURUM = {"red": "Kesin Boykot", "orange": "İnsafa Bağlı", "green": "Alınabilir"}


def bykt_url(ad):
    s = re.sub(r"[\W_]+", "-", ad.strip().replace("İ", "i").lower()).strip("-")
    return "https://bykt.org/marka/" + urllib.parse.quote(s)


def _fb_tarih(u):
    if isinstance(u, dict) and "_seconds" in u:
        return dt.datetime.fromtimestamp(u["_seconds"], dt.timezone(dt.timedelta(hours=3))).date().isoformat()
    return None


def normalle_bykt(veri):
    out = {}
    for b in veri:
        ad = (b.get("name") or "").strip()
        if not ad:
            continue
        out[b["id"]] = kayit(ad, BYKT_DURUM.get(b.get("status"), b.get("status")), b.get("status") in ("red", "orange"),
                             b.get("parentCompany"), b.get("reason"),
                             [s.get("url") for s in (b.get("reasonSources") or [])], bykt_url(ad),
                             tarih=_fb_tarih(b.get("updatedAt")), eklenme=_fb_tarih(b.get("createdAt")))
    return out


def cek_bykt(onceki):
    meta = al(BYKT_META).json()
    iz = meta.get("md5Hash")
    if not iz:
        raise KaynakHatasi("bykt: dosya bilgisi okunamadı")
    if iz == onceki.get("parmak_izi"):
        return {"degismedi": True, "parmak_izi": iz}
    veri = al(BYKT_META + "?alt=media").json()
    return {"kayitlar": normalle_bykt(veri), "parmak_izi": iz, "meta": {"dosya_guncelleme": meta.get("updated")}}


# ===================================================================== Bilinçli Tüketim
BT_URL = "https://api.bilinclituketim.com/data/snapshot.json"


def normalle_bt(d):
    B = {b["id"]: b for b in d["all_brands"]}
    goster = {b["id"] for b in d["brands"]}
    derece = {r["rate"]: r["name"] for r in d["rates"]}

    def kok(b):
        while b.get("parent") in B:
            b = B[b["parent"]]
        return b

    out = {}
    for b in B.values():
        k = kok(b)
        ust = B.get(b.get("parent"))
        out[str(b["id"])] = kayit(
            b["name"], derece.get(b["rate"]) or f"Listede değil ({b['rate']})",
            k["rate"] in (1, 2, 3) and k["id"] in goster, ust["name"] if ust else None, b.get("explanation"),
            list(b.get("other_links") or []) + list(b.get("image_links") or []),
            "https://bilinclituketim.com/brand/" + b["key"], tarih=(b.get("date_updated") or "")[:10],
            eklenme=(b.get("date_added") or "")[:10], sitede="Evet" if b["id"] in goster else "Hayır")
    return out


def cek_bt(onceki):
    r = al(BT_URL)
    d = r.json()
    iz = d.get("version") or sha(r.content)
    if iz == onceki.get("parmak_izi"):
        return {"degismedi": True, "parmak_izi": iz}
    return {"kayitlar": normalle_bt(d), "parmak_izi": iz, "meta": {"uretim": d.get("generated_at")}}


# ===================================================================== Boykot Dedektifi
BD = "https://boykotdedektifi.com"
BD_KAPSAM = ("Boykot", "İkincil Boykot", "Şüpheli")
URL_RE = re.compile(r'https?://[^\s<>"\'\)\]]+')


def _para_text(el):
    """Paragrafları satır olarak koruyarak düz metin (yerel tarayıcının parse.py'siyle aynı)."""
    if el is None:
        return ""
    el = BeautifulSoup(str(el), "html.parser")
    for br in el.find_all("br"):
        br.replace_with("\n")
    for td in el.find_all(["td", "th"]):
        td.insert_after(" | ")
    for b in el.find_all(["tr", "p", "li", "blockquote", "figure", "div", "h1", "h2", "h3", "h4", "h5", "h6"]):
        b.insert_before("\n")
        b.insert_after("\n")
    t = el.get_text("").replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", x).strip() for x in t.split("\n")]
    return "\n".join(x for x in lines if x)


def bd_ayristir(raw, slug):
    soup = BeautifulSoup(raw, "html.parser")
    main = soup.find("main")
    canon = soup.find("link", rel="canonical")
    m = re.search(r"-(\d+)$", slug)
    rec = {"id": int(m.group(1)) if m else None, "slug": slug, "url": canon["href"] if canon else ""}
    h1 = main.find("h1")
    sp = h1.find("span")
    if sp:
        sp.extract()
    rec["marka"] = h1.get_text(" ", strip=True)
    badge = main.select_one(".status-badge-premium")
    rec["durum"] = badge.get_text(" ", strip=True) if badge else ""
    parent = h1.find_next_sibling("p")
    rec["cati_sirket"] = parent.get_text(" ", strip=True) if parent else ""
    alert = main.select_one("div.alert")
    body = alert.select_one("div.text-muted") if alert else None
    rec["gerekce"] = _para_text(body)
    links = []
    if body:
        links += [a["href"].strip() for a in body.find_all("a", href=True)]
        links += [i["src"].strip() for i in body.find_all("img", src=True)]
        links += [u.rstrip(".,;:") for u in URL_RE.findall(body.get_text(" "))]
    rec["gerekce_linkleri"] = tekil(links)
    rec["kanit"] = [a["href"] for a in main.select("a.btn-brand-primary") if "Kan" in a.get_text() and a.get("href")]
    return rec


def normalle_bd(markalar):
    return {str(r["id"]): kayit(r["marka"], r["durum"], r["durum"] in BD_KAPSAM, r.get("cati_sirket"), r.get("gerekce"),
                                list(r.get("kanit") or []) + list(r.get("gerekce_linkleri") or []), r.get("url"))
            for r in markalar if r.get("id") is not None}


def cek_bd(onceki, isci=3):
    sm = al(BD + "/site-haritasi").text
    yollar = sorted(set(re.findall(r'href="(/b/[^"]+)"', sm)))
    eski = onceki.get("kayitlar") or {}
    if len(yollar) < 0.8 * max(len(eski), 1000):
        raise KaynakHatasi(f"Boykot Dedektifi: site haritasında yalnız {len(yollar)} marka (önceki {len(eski)})")
    recs, alinamayan, yok = [], [], []
    kilit = threading.Lock()

    def getir(p):
        for i in range(5):
            try:
                r = oturum().get(BD + p, timeout=60)
                if r.status_code == 200 and "<main" in r.text:
                    rec = bd_ayristir(r.text.replace("\r\n", "\n").replace("\r", "\n"), p.split("/b/", 1)[1].replace("/", "_"))
                    with kilit:
                        recs.append(rec)
                    time.sleep(0.3 + random.random() * 0.4)
                    return
                if r.status_code == 404:
                    with kilit:
                        yok.append(p)
                    return
            except requests.RequestException:
                pass
            time.sleep(min(120, 5 * 2 ** i))
        with kilit:
            alinamayan.append(p)

    with ThreadPoolExecutor(isci) as ex:
        list(ex.map(getir, yollar))
    if len(alinamayan) > 0.05 * len(yollar):
        raise KaynakHatasi(f"Boykot Dedektifi: {len(alinamayan)}/{len(yollar)} marka sayfası alınamadı")
    yeni = normalle_bd(recs)
    uyari = []
    if alinamayan:
        # alınamayan sayfaların önceki kaydı korunur (kalkmış sayılmaz)
        ids = {re.search(r"-(\d+)$", p).group(1) for p in alinamayan if re.search(r"-(\d+)$", p)}
        for i in ids:
            if i in eski:
                yeni[i] = eski[i]
        uyari.append(f"{len(alinamayan)} marka sayfası alınamadı; önceki kayıtları korundu")
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True, ensure_ascii=False)),
            "meta": {"site_haritasi": len(yollar)}, "uyarilar": uyari}


# ===================================================================== Kolay Boykot
KB = "https://www.kolayboykot.com/"
KB_KATEGORI = {843: "filistin-icin", 844: "boykot-farkinda", 845: "boykot-kararli", 846: "boykot-oncu",
               847: "boykot-iradeli", 848: "boykot-mucahit"}


def _kb_text(node):
    if node is None:
        return ""
    for br in node.find_all("br"):
        br.replace_with("\n")
    for p in node.find_all("p"):
        p.append("\n")
    t = H.unescape(node.get_text(" "))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    return re.sub(r"\n{2,}", "\n", t).strip()


def _kb_kartlar(h):
    out = []
    for parca in h.split('<div class="card-product style-8"')[1:]:
        m = re.search(r'href="https://www\.kolayboykot\.com/marka/([^"]+)"', parca)
        if not m:
            continue
        etiket = re.search(r'<div class="on-sale-item[^"]*"[^>]*>\s*([^<]*?)\s*</div>', parca)
        ad = re.search(r'class="title link">\s*([^<]*?)\s*</a>', parca)
        out.append((m.group(1), etiket.group(1) if etiket else "", H.unescape(ad.group(1)) if ad else ""))
    return out


def kb_marka(h):
    s = BeautifulSoup(h, "html.parser")
    rozet = [_kb_text(b) for b in s.select(".kb-brand-badges .kb-badge")]
    sec = s.select_one("#neden-boykot")
    return {"rozet_durum": rozet[0].replace("🚫", "").strip() if rozet else "",
            "gerekce": _kb_text(sec.select_one(".announcement-box")) if sec else ""}


def normalle_kb(markalar):
    return {r["slug"]: kayit(r["ad"], r.get("seviye"), True, None, r.get("gerekce"), (), r.get("url"),
                             durum=r.get("rozet_durum"))
            for r in markalar}


def cek_kb(onceki):
    kartlar = {}
    for cid, slug in KB_KATEGORI.items():
        s = 1
        while True:
            h = sayfa_metni(f"{KB}{slug}-c-{cid}?s={s}")
            k = _kb_kartlar(h)
            if not k:
                break
            for ms, etiket, ad in k:
                kartlar.setdefault(cid, []).append((ms, etiket, ad))
            s += 1
            time.sleep(0.3)
    if not kartlar.get(843):
        raise KaynakHatasi("Kolay Boykot: Filistin İçin listesi okunamadı")
    seviye = {ms: etiket for cid, ks in kartlar.items() if cid != 843 for ms, etiket, _ in ks}
    fil = {}
    for ms, _, ad in kartlar[843]:
        fil.setdefault(ms, ad)
    markalar = []

    def getir(ms):
        r = al(f"{KB}marka/{ms}")
        d = kb_marka(r.text.replace("\r\n", "\n").replace("\r", "\n")) if r.status_code == 200 else {}
        return dict(slug=ms, ad=fil[ms], seviye=seviye.get(ms, ""), url=f"{KB}marka/{ms}", **d)

    with ThreadPoolExecutor(3) as ex:
        markalar = list(ex.map(getir, fil))
    yeni = normalle_kb(markalar)
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True, ensure_ascii=False)),
            "meta": {"marka": len(yeni)}}


# ===================================================================== Eczanede Boykot
EB = "https://eczanedeboykot.com"
EB_TOHUM = ["bayer", "pfizer", "teva", "novartis", "msd", "organon", "merck", "johnson"]


def _eb_text(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _eb_kart(li, body):
    k = {"durum": "boykot" if "is-boycott" in li else ("boykot değil" if "is-clear" in li else li)}
    m = re.search(r"<strong>(.*?)</strong>", body, re.S)
    k["ad"] = _eb_text(m.group(1)) if m else ""
    m = re.search(r'<strong><a href="([^"]+)"', body)
    k["link"] = H.unescape(m.group(1)) if m else ""
    m = re.search(r'<a class="manufacturer-link" href="([^"]+)"[^>]*>(.*?)</a>', body, re.S)
    k["firma"] = _eb_text(m.group(2)) if m else ""
    k["firma_link"] = H.unescape(m.group(1)) if m else ""
    if not m:
        m = re.search(r"<small>(.*?)</small>", body, re.S)
        k["firma"] = _eb_text(m.group(1)) if m else ""
    m = re.search(r'data-boycott-manufacturer="([^"]*)"', body)
    k["boykot_firmasi"] = H.unescape(m.group(1)) if m else ""
    return k


def _eb_kartlar(t, ana=False):
    """Sonuç bölümündeki ilaç kartları. ana=True: yalnız her grubun ana listesi (yerel tarayıcıdaki firma sayfası okuması
    gibi; eşdeğer ve ATC bölümleri hariç)."""
    s = t[t.find('<section class="site-shell search-results"'):]
    if '<aside class="medical-warning"' in s:
        s = s[:s.find('<aside class="medical-warning"')]
    if ana:
        s = "".join(re.split(r'<header class="equivalent-group-heading">\s*<div>\s*<h4>', a)[0]
                    for a in re.findall(r'<article class="equivalent-group">(.*?)</article>', s, re.S))
    return [_eb_kart(a, b) for a, b in re.findall(r'<li class="drug-status-card([^"]*)">(.*?)</li>', s, re.S)]


def _eb_ana(t):
    firmalar = []
    for attrs, body in re.findall(r"<button([^>]*data-company-evidence[^>]*)>(.*?)</button>", t, re.S):
        a = dict((k, H.unescape(v)) for k, v in re.findall(r'(data-company-[a-z-]+)="([^"]*)"', attrs))
        m = re.search(r"data-company-full-reason[^>]*>(.*?)</", body, re.S)
        firmalar.append({"firma": a.get("data-company-name", ""),
                         "gerekce": H.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""})
    m = re.search(r'<time datetime="([^"]+)"', t)
    return firmalar, (m.group(1) if m else "")


def normalle_eb(firmalar, urunler, liste_tarihi):
    out = {f"firma:{f['firma']}": kayit(f["firma"], "Boykot firması", True, None, f.get("gerekce"), (), EB + "/tr")
           for f in firmalar}
    for u in urunler:
        out[u["link"]] = kayit(u["ad"], "Boykot", True, u.get("firma"), None, (), EB + u["link"])
    out["_liste"] = kayit("Sitedeki liste güncelleme tarihi", None, True, url=EB + "/tr", tarih=liste_tarihi)
    return out


def cek_eb(onceki):
    def sayfa(url):
        t = sayfa_metni(url)
        time.sleep(1)
        return t

    ana = sayfa(EB + "/tr")
    firmalar, tarih = _eb_ana(ana)
    if not firmalar:
        raise KaynakHatasi("Eczanede Boykot: ana sayfada boykot firması okunamadı")
    ureticiler = {}
    for q in EB_TOHUM + [f["firma"].lower() for f in firmalar]:
        for k in _eb_kartlar(sayfa(EB + "/tr?q=" + urllib.parse.quote(q))):
            if k["boykot_firmasi"]:
                link = k["firma_link"] if k["firma"] == k["boykot_firmasi"] and k["firma_link"] else ""
                if link or k["boykot_firmasi"] not in ureticiler:
                    ureticiler[k["boykot_firmasi"]] = EB + link if link else (
                        EB + "/tr?company=" + urllib.parse.quote(k["boykot_firmasi"], safe=""))
    urunler = {}
    for ad, url in sorted(ureticiler.items()):
        t = sayfa(url)
        if not tarih:                      # liste güncelleme tarihi arama/firma sayfalarının başlığında
            m = re.search(r'<time datetime="([^"]+)"', t)
            tarih = m.group(1) if m else ""
        for k in _eb_kartlar(t, ana=True):
            if k["durum"] == "boykot" and k["link"]:
                urunler[k["link"]] = k
    if len(urunler) < 100:
        raise KaynakHatasi(f"Eczanede Boykot: yalnız {len(urunler)} boykot ürünü okundu")
    yeni = normalle_eb(firmalar, urunler.values(), tarih)
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True, ensure_ascii=False)),
            "meta": {"uretici": sorted(ureticiler), "urun": len(urunler)}}


# ===================================================================== Who Profits
WP = "https://www.whoprofits.org/companies?page={}"
IBRANICE = re.compile(r"[\u0590-\u05ff\u0600-\u06ff]")


def _wp_ad(t):
    t = H.unescape(re.sub(r"<[^>]+>", " ", t))
    m = IBRANICE.search(t)
    return re.sub(r"\s+", " ", t[:m.start()] if m else t).strip(" (")


def cek_wp(onceki):
    """Şirket dizini (site haritası eski: silinmiş sayfalar var, bazı şirketler yok). Son sayfadan sonra dizin başa döner."""
    eski = onceki.get("kayitlar") or {}
    gor = {}
    for p in range(1, 80):
        L = re.findall(r'<a[^>]*href="https://www\.whoprofits\.org/companies/company/(\d+)\?[^"]*"[^>]*>(.*?)</a>',
                       al(WP.format(p)).text, re.S)
        if not [i for i, _ in L if i not in gor]:
            break
        for i, ad in L:
            gor.setdefault(i, _wp_ad(ad))
        time.sleep(1)
    if len(gor) < 0.8 * max(len(eski), 300):
        raise KaynakHatasi(f"Who Profits: dizinde yalnız {len(gor)} şirket okundu")
    yeni = {i: eski.get(i) or kayit(gor[i], None, True, None, None, (), f"https://www.whoprofits.org/companies/company/{i}")
            for i in sorted(gor, key=int)}
    return {"kayitlar": yeni, "parmak_izi": sha(",".join(sorted(gor))), "meta": {"sirket": len(gor)}}


# ===================================================================== AFSC Gazze
AFSC = "https://afsc.org/gaza-genocide-companies"


def normalle_afsc(t):
    s = BeautifulSoup(t, "html.parser")
    out = {}
    for it in s.select("div.item[data-uri]"):
        ad = it.select_one("h3.big-title")
        bilgi = {}
        for d in it.select(".details-holder .details"):
            k, v = d.select_one(".detail-label"), d.select_one(".small-title")
            if k and v:
                bilgi[k.get_text(strip=True).rstrip(":")] = v.get_text(" ", strip=True)
        rt = it.select_one(".offcanvas-item-content .block-richtext")
        metin = re.sub(r"[ \t\xa0]+", " ", rt.get_text("\n")).strip() if rt else ""
        metin = re.sub(r"\s*\n\s*", "\n", metin)
        linkler = [a["href"] for a in rt.select("a[href]")] if rt else []
        uri = it["data-uri"]
        out[uri] = kayit(ad.get_text(" ", strip=True) if ad else uri, None, True, None, metin, linkler,
                         "https://afsc.org" + uri, tur=bilgi.get("Type"), ulke=bilgi.get("Location"),
                         kategori=bilgi.get("Category"))
    return out


def cek_afsc(onceki):
    yeni = normalle_afsc(sayfa_metni(AFSC))
    if len(yeni) < 20:
        raise KaynakHatasi(f"AFSC: sayfada yalnız {len(yeni)} şirket okundu")
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True, ensure_ascii=False)),
            "meta": {"sirket": len(yeni)}}


# ===================================================================== DBIO
DBIO = "https://dontbuyintooccupation.org/dbio-data-2025/"


def dosya_kaydi(ad, icerik, url):
    return kayit(ad, None, True, None, None, (), url, sha256=sha(icerik), boyut=len(icerik))


def cek_dbio(onceki):
    t = al(DBIO).text
    urls = tekil(re.findall(r'sourceFile\s*=\s*"([^"]+\.csv)"', t))
    if not urls:
        raise KaynakHatasi("DBIO: veri sayfasında CSV bağlantısı bulunamadı")
    yeni = {}
    for u in urls:
        ad = u.rsplit("/", 1)[-1]
        yeni[ad] = dosya_kaydi(ad, al(u).content, u)
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True)), "meta": {"dosya": len(yeni)}}


# ===================================================================== AFSC Investigate
INV = "https://investigate.info/downloads"


def cek_inv(onceki):
    t = al(INV).text
    urls = tekil(re.findall(r'href="(https?://[^"]+\.(?:xlsx|csv|zip))"', t))
    if not urls:
        raise KaynakHatasi("Investigate: indirme sayfasında veri dosyası bulunamadı")
    yeni = {}
    for u in urls:
        ad = u.rsplit("/", 1)[-1]
        yeni[ad] = dosya_kaydi(ad, al(u).content, u)
    return {"kayitlar": yeni, "parmak_izi": sha(json.dumps(yeni, sort_keys=True)), "meta": {"dosya": len(yeni)}}


# ===================================================================== Abbott & Keefer
AK_SM = "https://directory.abbottandkeefer.com/sitemap.xml"


def cek_ak(onceki):
    xml = al(AK_SM).text
    urls = sorted(set(re.findall(r"<loc>(https://directory\.abbottandkeefer\.com/brand-entry/[^<]+)</loc>", xml)))
    eski = onceki.get("kayitlar") or {}
    if len(urls) < 0.8 * max(len(eski), 500):
        raise KaynakHatasi(f"Abbott & Keefer: site haritasında yalnız {len(urls)} marka")
    yeni, n = {}, 0
    for u in urls:
        slug = u.rsplit("/", 1)[-1]
        if slug in eski:
            yeni[slug] = eski[slug]
            continue
        ad = slug.replace("-", " ")
        if n < 60:                         # yeni sayfaların adı sayfa başlığından (toplu değişimde ilk 60)
            n += 1
            m = re.search(r"<title>(.*?)</title>", al(u).text, re.S)
            ad = re.sub(r"\s*[|–-]\s*Abbott.*$", "", H.unescape(m.group(1)).strip()) if m else ad
            time.sleep(1)
        yeni[slug] = kayit(ad, None, True, None, None, (), u)
    return {"kayitlar": yeni, "parmak_izi": sha(",".join(urls)), "meta": {"marka": len(urls)}}


# ===================================================================== kayıt defteri
# siklik: "gunluk" kaynaklar her gün, "haftalik" olanlar yalnız tam taramada (pazartesi) kontrol edilir.
# birim: raporda kayıtların adı.
KAYNAKLAR = {
    "bykt": dict(ad="bykt.org", site="https://bykt.org", cek=cek_bykt, siklik="gunluk", birim="marka",
                 kapsam="Kesin Boykot ve İnsafa Bağlı"),
    "bt": dict(ad="Bilinçli Tüketim", site="https://bilinclituketim.com", cek=cek_bt, siklik="gunluk", birim="marka",
               kapsam="çatısı 1–3 çarpılı ve sitede listelenen markalar"),
    "bd": dict(ad="Boykot Dedektifi", site="https://boykotdedektifi.com", cek=cek_bd, siklik="haftalik", birim="marka",
               kapsam="Boykot, İkincil Boykot ve Şüpheli"),
    "kb": dict(ad="Kolay Boykot (Filistin İçin)", site="https://www.kolayboykot.com/filistin-icin-c-843", cek=cek_kb,
               siklik="haftalik", birim="marka", kapsam="listenin tamamı"),
    "eb": dict(ad="Eczanede Boykot", site="https://eczanedeboykot.com/tr", cek=cek_eb, siklik="gunluk", birim="ilaç",
               kapsam="boykot firmaları ve ürünleri"),
    "wp": dict(ad="Who Profits", site="https://www.whoprofits.org", cek=cek_wp, siklik="gunluk", birim="şirket",
               kapsam="şirket dizini (yalnız eklenen ve çıkan şirketler izlenir)"),
    "afsc": dict(ad="AFSC Gazze listesi", site=AFSC, cek=cek_afsc, siklik="gunluk", birim="şirket",
                 kapsam="listenin tamamı"),
    "dbio": dict(ad="DBIO", site=DBIO, cek=cek_dbio, siklik="gunluk", birim="veri dosyası",
                 kapsam="veri sayfasındaki CSV dosyaları"),
    "inv": dict(ad="AFSC Investigate", site="https://investigate.info", cek=cek_inv, siklik="gunluk",
                birim="veri dosyası", kapsam="indirme sayfasındaki veri seti"),
    "ak": dict(ad="Abbott & Keefer", site="https://directory.abbottandkeefer.com", cek=cek_ak, siklik="gunluk",
               birim="marka", kapsam="marka dizini (yalnız eklenen ve çıkan markalar izlenir)"),
}
