import csv
import json
import math
import os
import socket
import threading
import time
import urllib.parse
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import requests
import urllib3
import urllib3.util.connection as urllib3_cn

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

AEROPORTS_PRESETS = {
    "TLS": {"nom": "TOULOUSE BLAGNAC (TLS)", "lat": 43.6290, "lon": 1.3638, "rayon": 90},
    "DXB": {"nom": "DUBAÏ DXB • APPROCHE TERRE (30L/30R)", "lat": 25.2150, "lon": 55.4350, "rayon": 65},
    "CDG": {"nom": "PARIS CHARLES DE GAULLE (CDG)", "lat": 49.0097, "lon": 2.5479, "rayon": 75},
    "LHR": {"nom": "LONDRES HEATHROW (LHR)", "lat": 51.4700, "lon": -0.4543, "rayon": 65},
    "JFK": {"nom": "NEW YORK JFK (JFK)", "lat": 40.6413, "lon": -73.7781, "rayon": 75},
    "SIN": {"nom": "SINGAPOUR CHANGI (SIN)", "lat": 1.3644, "lon": 103.9915, "rayon": 70}
}

ZONE_DEFAUT = "TLS"
INTERVALLE_SCAN_SEC = 5
DUREE_ACTIVITE_ZONE_SEC = 25
FICHIER_CSV = "avions.csv"
PORT = int(os.environ.get("PORT", 8000))

AVIONS_RARES_ICAO = {
    "A337": "AIRBUS BELUGAXL",
    "A3ST": "AIRBUS BELUGA",
    "A388": "SUPERJUMBO A380",
    "A35K": "AIRBUS A350-1000",
    "B748": "BOEING 747-8",
    "B744": "BOEING 747-400",
    "BLCF": "BOEING DREAMLIFFTER",
    "B779": "BOEING 777-9X",
    "A124": "ANTONOV AN-124",
    "A225": "ANTONOV AN-225",
    "C5M": "LOCKHEED C-5 GALAXY",
    "C17": "BOEING C-17 GLOBEMASTER",
    "A400": "AIRBUS A400M ATLAS",
    "K35R": "BOEING KC-135",
    "E3TF": "BOEING E-3 AWACS"
}

AEROPORTS_IATA = {
    "TLS": "Toulouse-Blagnac", "ORY": "Paris-Orly", "CDG": "Paris-CDG", "BVA": "Paris-Beauvais",
    "LYS": "Lyon-Saint-Exupéry", "MRS": "Marseille-Provence", "NCE": "Nice-Côte d'Azur",
    "BOD": "Bordeaux-Mérignac", "NTE": "Nantes-Atlantique", "SXB": "Strasbourg",
    "LIL": "Lille", "MPL": "Montpellier", "BIQ": "Biarritz", "PUF": "Pau", "PGF": "Perpignan",
    "RNS": "Rennes", "BES": "Brest", "FSC": "Figari", "AJA": "Ajaccio", "BIA": "Bastia", "CLY": "Calvi",
    "LHR": "Londres-Heathrow", "LGW": "Londres-Gatwick", "STN": "Londres-Stansted", "LTN": "Londres-Luton",
    "LCY": "Londres-City", "MAN": "Manchester", "BHX": "Birmingham", "EDI": "Édimbourg", "BRS": "Bristol",
    "DUB": "Dublin", "ORK": "Cork",
    "FRA": "Francfort", "MUC": "Munich", "BER": "Berlin", "DUS": "Düsseldorf", "HAM": "Hambourg", "CGN": "Cologne", "STR": "Stuttgart",
    "AMS": "Amsterdam-Schiphol", "EIN": "Eindhoven", "BRU": "Bruxelles", "CRL": "Charleroi", "LUX": "Luxembourg",
    "ZRH": "Zurich", "GVA": "Genève", "BSL": "Bâle-Mulhouse", "VIE": "Vienne",
    "MAD": "Madrid-Barajas", "BCN": "Barcelone", "PMI": "Palma de Majorque", "AGP": "Malaga",
    "ALC": "Alicante", "VLC": "Valence", "SVQ": "Séville", "BIO": "Bilbao", "IBZ": "Ibiza", "TFS": "Tenerife", "LPA": "Gran Canaria",
    "LIS": "Lisbonne", "OPO": "Porto", "FAO": "Faro",
    "FCO": "Rome-Fiumicino", "MXP": "Milan-Malpensa", "LIN": "Milan-Linate", "BGY": "Milan-Bergame",
    "VCE": "Venise", "NAP": "Naples", "BLQ": "Bologne", "CTA": "Catane", "PMO": "Palerme",
    "ATH": "Athènes", "SKG": "Thessalonique", "HER": "Héraklion", "CFU": "Corfou",
    "CPH": "Copenhague", "OSL": "Oslo", "ARN": "Stockholm", "HEL": "Helsinki", "KEF": "Reykjavik",
    "WAW": "Varsovie", "KRK": "Cracovie", "PRG": "Prague", "BUD": "Budapest", "OTP": "Bucarest", "BEG": "Belgrade", "ZAG": "Zagreb",
    "IST": "Istanbul", "SAW": "Istanbul-Sabiha", "AYT": "Antalya",
    "DXB": "Dubaï", "AUH": "Abou Dabi", "DOH": "Doha", "JED": "Djeddah", "RUH": "Riyad", "TLV": "Tel Aviv", "AMM": "Amman", "BEY": "Beyrouth",
    "CMN": "Casablanca", "RAK": "Marrakech", "AGA": "Agadir", "FEZ": "Fès", "TNG": "Tanger", "OUD": "Oujda",
    "ALG": "Alger", "ORN": "Oran", "CZL": "Constantine", "TUN": "Tunis", "DJE": "Djerba", "MIR": "Monastir", "CAI": "Le Caire",
    "DSS": "Dakar", "ABJ": "Abidjan", "RUN": "La Réunion", "MRU": "Maurice", "JNB": "Johannesburg", "ADD": "Addis-Abeba",
    "JFK": "New York-JFK", "EWR": "Newark", "BOS": "Boston", "IAD": "Washington", "ATL": "Atlanta", "MIA": "Miami",
    "ORD": "Chicago", "DFW": "Dallas", "IAH": "Houston", "LAX": "Los Angeles", "SFO": "San Francisco",
    "YUL": "Montréal", "YYZ": "Toronto", "YVR": "Vancouver",
    "GRU": "São Paulo", "GIG": "Rio de Janeiro", "EZE": "Buenos Aires", "BOG": "Bogota", "MEX": "Mexico", "CUN": "Cancún",
    "HND": "Tokyo-Haneda", "NRT": "Tokyo-Narita", "ICN": "Séoul", "PEK": "Pékin", "PVG": "Shanghai",
    "HKG": "Hong Kong", "SIN": "Singapour", "BKK": "Bangkok", "DEL": "New Delhi", "BOM": "Bombay", "SYD": "Sydney",
    "KUL": "Kuala Lumpur", "CGK": "Jakarta", "MNL": "Manille", "TPE": "Taipei", "HAN": "Hanoï", "SGN": "Hô Chi Minh-Ville",
    "XFW": "Hambourg-Finkenwerder (Airbus)", "CEQ": "Cannes", "LBG": "Paris-Le Bourget"
}

COMPAGNIES_ICAO = {
    "AFR": "Air France", "HOP": "Air France Hop", "TVF": "Transavia France",
    "FPO": "ASL Airlines France", "CRL": "Corsair", "FWI": "Air Caraïbes",
    "BFM": "French bee", "AEH": "Amelia", "TJT": "Twin Jet", "CCM": "Air Corsica",
    "AIB": "Airbus", "BGA": "Airbus Transport International",
    "BAW": "British Airways", "SHT": "British Airways", "CFE": "BA CityFlyer",
    "EZY": "easyJet", "EJU": "easyJet", "EZS": "easyJet",
    "EXS": "Jet2.com", "TOM": "TUI Airways", "VIR": "Virgin Atlantic", "LOG": "Loganair",
    "DLH": "Lufthansa", "CLH": "Lufthansa CityLine", "EWG": "Eurowings", "GWI": "Germanwings",
    "CFG": "Condor", "TUI": "TUI fly", "BOX": "AeroLogic", "GEC": "Lufthansa Cargo",
    "RYR": "Ryanair", "RUK": "Ryanair", "MAY": "Malta Air", "EIN": "Aer Lingus",
    "KLM": "KLM", "KLC": "KLM Cityhopper", "TRA": "Transavia", "MPH": "Martinair",
    "SWR": "Swiss International Air Lines", "EDW": "Edelweiss Air",
    "AUA": "Austrian Airlines", "BEL": "Brussels Airlines", "LGL": "Luxair",
    "IBE": "Iberia", "IBS": "Iberia Express", "VLG": "Vueling", "AEA": "Air Europa", "VOE": "Volotea",
    "TAP": "TAP Air Portugal", "ITY": "ITA Airways", "AZA": "Alitalia", "NOZ": "Neos", "BPA": "Blue Panorama",
    "SAS": "SAS Scandinavian Airlines", "NAX": "Norwegian", "NSZ": "Norwegian",
    "FIN": "Finnair", "ICE": "Icelandair", "WZZ": "Wizz Air", "WMT": "Wizz Air",
    "LOT": "LOT Polish Airlines", "CSA": "Czech Airlines", "TVS": "Smartwings",
    "BTI": "airBaltic", "ASL": "Air Serbia", "CTN": "Croatia Airlines", "ROT": "TAROM",
    "AEE": "Aegean Airlines", "OAL": "Olympic Air",
    "THY": "Turkish Airlines", "PGT": "Pegasus Airlines", "SXS": "SunExpress",
    "UAE": "Emirates", "QTR": "Qatar Airways", "ETD": "Etihad Airways",
    "SVA": "Saudia", "GFA": "Gulf Air", "OMA": "Oman Air", "KAC": "Kuwait Airways",
    "RJA": "Royal Jordanian", "MEA": "Middle East Airlines", "ELY": "El Al",
    "RAM": "Royal Air Maroc", "DAH": "Air Algérie", "TAR": "Tunisair", "MSR": "EgyptAir",
    "ETH": "Ethiopian Airlines", "KQA": "Kenya Airways", "SAA": "South African Airways",
    "MAU": "Air Mauritius", "REU": "Air Austral",
    "AAL": "American Airlines", "DAL": "Delta Air Lines", "UAL": "United Airlines",
    "JBU": "JetBlue", "ACA": "Air Canada", "TSC": "Air Transat", "WJA": "WestJet",
    "AMX": "Aeromexico", "AVA": "Avianca", "LAN": "LATAM Airlines", "TAM": "LATAM Brasil",
    "ANA": "All Nippon Airways", "JAL": "Japan Airlines", "KAL": "Korean Air", "AAR": "Asiana Airlines",
    "CPA": "Cathay Pacific", "SIA": "Singapore Airlines", "TGW": "Scoot", "SLK": "SilkAir",
    "THA": "Thai Airways", "EVA": "EVA Air",
    "CAL": "China Airlines", "CCA": "Air China", "CES": "China Eastern Airlines",
    "CSN": "China Southern Airlines", "CHH": "Hainan Airlines", "CXA": "XiamenAir",
    "AIC": "Air India", "VTI": "Vistara", "IGO": "IndiGo", "PIA": "Pakistan International Airlines",
    "HVN": "Vietnam Airlines", "MAS": "Malaysia Airlines", "AXM": "AirAsia", "GIA": "Garuda Indonesia",
    "QFA": "Qantas", "JST": "Jetstar", "ANZ": "Air New Zealand",
    "FDX": "FedEx Express", "UPS": "UPS Airlines", "BCS": "DHL", "GTI": "Atlas Air", "CLX": "Cargolux"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Origin": "https://www.flightradar24.com",
    "Referer": "https://www.flightradar24.com/"
}

base_avions = {}
if os.path.exists(FICHIER_CSV):
    with open(FICHIER_CSV, mode="r", encoding="utf-8-sig") as f:
        for ligne in csv.DictReader(f):
            code = ligne["icao"].strip().upper()
            if code not in base_avions or ligne.get("is_variant") == "0":
                base_avions[code] = {k.strip(): (v.strip() if v else "") for k, v in ligne.items() if k}

print(f"✅ Base CSV chargée ({len(base_avions)} modèles)")

cache_photos = {}
photos_en_cours = set()
historique_zones = {z: [] for z in AEROPORTS_PRESETS}
derniere_activite_zone = {z: 0.0 for z in AEROPORTS_PRESETS}
derniere_activite_zone[ZONE_DEFAUT] = time.time()

etats_radars = {
    z: {
        "statut": "vide",
        "maj_serveur": "",
        "zone_id": z,
        "zone": cfg["nom"],
        "nb_avions": 0,
        "historique": []
    }
    for z, cfg in AEROPORTS_PRESETS.items()
}

verrou = threading.Lock()
evenement_scan = threading.Event()

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

def formater_aeroport(code_iata):
    code = str(code_iata or "").strip().upper()
    if not code:
        return None
    nom = AEROPORTS_IATA.get(code)
    return {"code": code, "nom": f"{nom} ({code})" if nom else code}

def detecter_rarete(icao, indicatif):
    if icao in AVIONS_RARES_ICAO:
        return AVIONS_RARES_ICAO[icao]
    if indicatif.startswith(("AIB", "BGA")):
        return "VOL D'ESSAI / CONSTRUCTEUR AIRBUS"
    return ""

def enregistrer_historique(zone_id, vol, specs, heure):
    hist = historique_zones.setdefault(zone_id, [])
    modele_court = (specs.get("model") or vol["icao"]).strip()
    entree = {
        "hex": vol["hex"],
        "indicatif": vol["num_vol"] or vol["indicatif"],
        "compagnie": vol["compagnie"] or "",
        "modele": modele_court,
        "icao": vol["icao"],
        "heure": heure[:5],
        "rare": bool(vol["badge_rare"])
    }
    if hist and hist[0]["hex"] == vol["hex"]:
        hist[0].update(entree)
        return list(hist)

    hist[:] = [item for item in hist if item["hex"] != vol["hex"]]
    hist.insert(0, entree)
    del hist[6:]
    return list(hist)

def charger_photo_asynchrone(cle, immat, hex_code, modele, compagnie):
    try:
        res = None
        urls = []
        if immat and immat != "N/A":
            urls.append(f"https://api.planespotters.net/pub/photos/reg/{immat}")
        if hex_code:
            urls.append(f"https://api.planespotters.net/pub/photos/hex/{hex_code}")

        for u in urls:
            try:
                r = requests.get(u, timeout=2.5, verify=False)
                if r.status_code == 200:
                    photos = r.json().get("photos", [])
                    if photos:
                        p0 = photos[0]
                        src = (p0.get("thumbnail_large") or {}).get("src") or (p0.get("thumbnail") or {}).get("src")
                        if src:
                            res = {"url": src, "auteur": f"{p0.get('photographer', 'Spotter')} • {immat or hex_code.upper()} (Planespotters)"}
                            break
            except Exception:
                pass

        if not res and compagnie and modele:
            try:
                q = urllib.parse.quote(f"{compagnie} {modele} -cabin -interior -cockpit -logo")
                u = (
                    f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                    f"&gsrsearch=filetype:bitmap+{q}&gsrnamespace=6&gsrlimit=5"
                    f"&prop=imageinfo&iiprop=url|size|user&iiurlwidth=1920&format=json"
                )
                r = requests.get(u, headers={"User-Agent": "RadarApp/1.0"}, timeout=3.0, verify=False)
                if r.status_code == 200:
                    for page in r.json().get("query", {}).get("pages", {}).values():
                        info = page.get("imageinfo", [{}])[0]
                        w, h = info.get("width", 0), info.get("height", 0)
                        img_u = info.get("thumburl") or info.get("url")
                        if img_u and w >= 1000 and w > h * 1.15 and not img_u.lower().endswith((".svg", ".pdf", ".tif")):
                            res = {"url": img_u, "auteur": f"{info.get('user', 'Wikimedia')} • {compagnie}"}
                            break
            except Exception:
                pass

        if res:
            cache_photos[cle] = res
            with verrou:
                for etat in etats_radars.values():
                    if etat.get("vol", {}).get("hex") == hex_code:
                        etat["photo"] = res
    finally:
        photos_en_cours.discard(cle)

def obtenir_photo(immat, hex_code, modele, compagnie):
    cle = f"{hex_code}_{immat}_{modele}"
    if cle in cache_photos:
        return cache_photos[cle]
    if cle not in photos_en_cours and len(photos_en_cours) < 8:
        photos_en_cours.add(cle)
        threading.Thread(target=charger_photo_asynchrone, args=(cle, immat, hex_code, modele, compagnie), daemon=True).start()
    return None

def interroger_flightradar24(zone_cfg):
    lat, lon, rayon = zone_cfg["lat"], zone_cfg["lon"], zone_cfg["rayon"]
    dlat = rayon / 111.0
    dlon = rayon / (111.0 * math.cos(math.radians(lat)))
    bounds = f"{lat + dlat:.4f},{lat - dlat:.4f},{lon - dlon:.4f},{lon + dlon:.4f}"
    url = (
        f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js"
        f"?bounds={bounds}&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0"
    )
    t0 = time.time()
    r = requests.get(url, headers=HEADERS, timeout=4.0, verify=False)
    ms = round((time.time() - t0) * 1000)
    if r.status_code != 200:
        raise ValueError(f"FR24 HTTP {r.status_code}")

    data = r.json()
    avions = []
    for k, v in data.items():
        if not isinstance(v, list) or len(v) < 17:
            continue
        alt = int(v[4] or 0)
        if alt <= 0:
            continue
        lat_ac, lon_ac = float(v[1]), float(v[2])
        dist = distance_km(lat, lon, lat_ac, lon_ac)
        if dist > rayon:
            continue

        hex_code = str(v[0] or "").strip().lower()
        cap = int(v[3] or 0)
        spd = int(v[5] or 0)
        squawk = str(v[6] or "").strip()
        icao = str(v[8] or "").strip().upper()
        immat = str(v[9] or "").strip().upper()
        origine = formater_aeroport(v[11])
        destination = formater_aeroport(v[12])
        num_vol = str(v[13] or "").strip().upper()
        vario = int(v[15] or 0)
        indicatif = str(v[16] or "").strip() or num_vol or immat or hex_code.upper()
        compagnie_code = str(v[18] or "").strip().upper() if len(v) > 18 else indicatif[:3].upper()
        compagnie = COMPAGNIES_ICAO.get(compagnie_code) or COMPAGNIES_ICAO.get(indicatif[:3].upper(), "")
        badge_rare = detecter_rarete(icao, indicatif)

        avions.append({
            "hex": hex_code,
            "indicatif": indicatif,
            "num_vol": num_vol,
            "compagnie": compagnie,
            "immat": immat or "N/A",
            "icao": icao or "—",
            "squawk": squawk,
            "badge_rare": badge_rare,
            "origine": origine,
            "destination": destination,
            "lat": lat_ac,
            "lon": lon_ac,
            "altitude_ft": alt,
            "vitesse_kts": spd,
            "cap": cap,
            "taux_vertical": vario,
            "distance_km": dist
        })
    return avions, ms

def actualiser_zone(zone_id):
    zone_cfg = AEROPORTS_PRESETS[zone_id]
    heure = datetime.now().strftime("%H:%M:%S")
    try:
        candidats, ms = interroger_flightradar24(zone_cfg)
        if candidats:
            candidats.sort(key=lambda x: x["distance_km"])
            c = candidats[0]
            specs = dict(base_avions.get(c["icao"], {}))
            nom_complet = f"{specs.get('manufacturer', '')} {specs.get('model', c['icao'])}".strip()
            photo = obtenir_photo(c["immat"], c["hex"], nom_complet, c["compagnie"])

            vario = c["taux_vertical"]
            c["phase"] = "EN APPROCHE" if vario < -150 or c["altitude_ft"] < 4500 else ("MONTÉE" if vario > 250 else "PALIER")

            for suiv in candidats[1:4]:
                sp_s = base_avions.get(suiv["icao"], {})
                obtenir_photo(suiv["immat"], suiv["hex"], f"{sp_s.get('manufacturer', '')} {sp_s.get('model', suiv['icao'])}".strip(), suiv["compagnie"])

            with verrou:
                hist_maj = enregistrer_historique(zone_id, c, specs, heure)
                etats_radars[zone_id] = {
                    "statut": "actif",
                    "maj_serveur": heure,
                    "source_api": "FR24",
                    "zone_id": zone_id,
                    "zone": zone_cfg["nom"],
                    "nb_avions": len(candidats),
                    "vol": c,
                    "specs": specs,
                    "photo": photo,
                    "historique": hist_maj
                }
        else:
            with verrou:
                etats_radars[zone_id] = {
                    "statut": "vide",
                    "maj_serveur": heure,
                    "zone_id": zone_id,
                    "zone": zone_cfg["nom"],
                    "nb_avions": 0,
                    "historique": list(historique_zones.get(zone_id, []))
                }
    except Exception as e:
        print(f"❌ [{heure}] Erreur FR24 ({zone_id}) : {type(e).__name__}: {e}")

def boucle_radar():
    while True:
        debut = time.time()
        evenement_scan.clear()
        maintenant = time.time()

        with verrou:
            zones_actives = [
                z for z, ts in derniere_activite_zone.items()
                if (maintenant - ts) <= DUREE_ACTIVITE_ZONE_SEC
            ]
        if not zones_actives:
            zones_actives = [ZONE_DEFAUT]

        threads = []
        for z in zones_actives:
            t = threading.Thread(target=actualiser_zone, args=(z,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        ecoule = time.time() - debut
        attente = max(0.5, INTERVALLE_SCAN_SEC - ecoule)
        evenement_scan.wait(timeout=attente)

class RadarHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/zone":
            nouvelle_zone = params.get("id", [""])[0].strip().upper()
            if nouvelle_zone in AEROPORTS_PRESETS:
                with verrou:
                    etats_radars[nouvelle_zone]["maj_serveur"] = datetime.now().strftime("%H:%M:%S")
                    etats_radars[nouvelle_zone]["historique"] = list(historique_zones.get(nouvelle_zone, []))
                    derniere_activite_zone[nouvelle_zone] = time.time()
                evenement_scan.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "zone_id": nouvelle_zone}).encode("utf-8"))

        elif parsed.path == "/api/trafic":
            zone_req = params.get("zone", [ZONE_DEFAUT])[0].strip().upper()
            if zone_req not in AEROPORTS_PRESETS:
                zone_req = ZONE_DEFAUT

            declencher = False
            with verrou:
                derniere_activite_zone[zone_req] = time.time()
                etat = etats_radars[zone_req]
                if not etat.get("maj_serveur"):
                    declencher = True
                if etat.get("statut") == "actif":
                    v = etat["vol"]
                    s = etat.get("specs", {})
                    photo = obtenir_photo(v["immat"], v["hex"], f"{s.get('manufacturer', '')} {s.get('model', v['icao'])}".strip(), v.get("compagnie", ""))
                    if photo:
                        etat["photo"] = photo
                payload = json.dumps(etat).encode("utf-8")

            if declencher:
                evenement_scan.set()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        else:
            super().do_GET()

threading.Thread(target=boucle_radar, daemon=True).start()
print(f"🚀 Radar multi-zones actif sur le port {PORT}")
ThreadingHTTPServer(("0.0.0.0", PORT), RadarHandler).serve_forever()
