import csv
import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 10000))

ZONES = {
    "TLS": {
        "nom": "Toulouse-Blagnac (TLS)",
        "lat": 43.6291,
        "lon": 1.3638,
        "rayon_km": 22.0
    },
    "DXB": {
        "nom": "Dubaï International (DXB)",
        "lat": 25.2532,
        "lon": 55.3657,
        "rayon_km": 25.0
    },
    "CDG": {
        "nom": "Paris-Charles de Gaulle (CDG)",
        "lat": 49.0097,
        "lon": 2.5479,
        "rayon_km": 25.0
    },
    "LHR": {
        "nom": "Londres-Heathrow (LHR)",
        "lat": 51.4700,
        "lon": -0.4543,
        "rayon_km": 25.0
    },
    "JFK": {
        "nom": "New York-JFK (JFK)",
        "lat": 40.6413,
        "lon": -73.7781,
        "rayon_km": 28.0
    },
    "SIN": {
        "nom": "Singapour-Changi (SIN)",
        "lat": 1.3644,
        "lon": 103.9915,
        "rayon_km": 25.0
    }
}

COMPAGNIES_OACI = {
    "AFR": "Air France",
    "EZY": "easyJet",
    "EJU": "easyJet Europe",
    "EZS": "easyJet Switzerland",
    "RYR": "Ryanair",
    "DLH": "Lufthansa",
    "BAW": "British Airways",
    "UAE": "Emirates",
    "FDB": "flydubai",
    "QTR": "Qatar Airways",
    "ETD": "Etihad Airways",
    "IBE": "Iberia",
    "VLG": "Vueling",
    "TAP": "TAP Air Portugal",
    "KLM": "KLM Royal Dutch Airlines",
    "SWR": "SWISS",
    "AZA": "ITA Airways",
    "THY": "Turkish Airlines",
    "VOE": "Volotea",
    "TOW": "Air Caraïbes",
    "CRL": "Corsair",
    "TVF": "Transavia France",
    "TRA": "Transavia",
    "AAL": "American Airlines",
    "DAL": "Delta Air Lines",
    "UAL": "United Airlines",
    "JBU": "JetBlue Airways",
    "ACA": "Air Canada",
    "SIA": "Singapore Airlines",
    "CPA": "Cathay Pacific",
    "ANA": "All Nippon Airways",
    "JAL": "Japan Airlines",
    "QFA": "Qantas",
    "AIB": "Airbus Industrie (Essais)",
    "BGA": "Airbus Transport International (Beluga)",
    "GAF": "German Air Force",
    "CTM": "Armée de l'Air et de l'Espace",
    "RRR": "Royal Air Force",
    "RCH": "US Air Force (AMC)",
    "UPS": "UPS Airlines",
    "FDX": "FedEx Express",
    "BCS": "DHL Air",
    "GEC": "Lufthansa Cargo",
    "CLX": "Cargolux"
}

COORDS_AEROPORTS = {
    "TLS": (43.6291, 1.3638, "Toulouse (TLS)"),
    "CDG": (49.0097, 2.5479, "Paris CDG"),
    "ORY": (48.7262, 2.3652, "Paris Orly"),
    "NCE": (43.6584, 7.2159, "Nice (NCE)"),
    "LYS": (45.7256, 5.0811, "Lyon (LYS)"),
    "MRS": (43.4393, 5.2214, "Marseille (MRS)"),
    "BOD": (44.8283, -0.7156, "Bordeaux (BOD)"),
    "NTE": (47.1532, -1.6107, "Nantes (NTE)"),
    "LHR": (51.4700, -0.4543, "Londres LHR"),
    "LGW": (51.1537, -0.1821, "Londres LGW"),
    "STN": (51.8850, 0.2350, "Londres STN"),
    "FRA": (50.0379, 8.5622, "Francfort (FRA)"),
    "MUC": (48.3537, 11.7750, "Munich (MUC)"),
    "AMS": (52.3105, 4.7683, "Amsterdam (AMS)"),
    "MAD": (40.4983, -3.5676, "Madrid (MAD)"),
    "BCN": (41.2974, 2.0833, "Barcelone (BCN)"),
    "FCO": (41.8003, 12.2389, "Rome FCO"),
    "ZRH": (47.4582, 8.5555, "Zurich (ZRH)"),
    "GVA": (46.2370, 6.1092, "Genève (GVA)"),
    "BRU": (50.9010, 4.4856, "Bruxelles (BRU)"),
    "LIS": (38.7756, -9.1354, "Lisbonne (LIS)"),
    "IST": (41.2753, 28.7519, "Istanbul (IST)"),
    "DXB": (25.2532, 55.3657, "Dubaï (DXB)"),
    "AUH": (24.4330, 54.6511, "Abu Dhabi (AUH)"),
    "DOH": (25.2731, 51.6081, "Doha (DOH)"),
    "JFK": (40.6413, -73.7781, "New York JFK"),
    "EWR": (40.6895, -74.1745, "Newark (EWR)"),
    "LAX": (33.9416, -118.4085, "Los Angeles (LAX)"),
    "ORD": (41.9742, -87.9073, "Chicago ORD"),
    "YUL": (45.4706, -73.7408, "Montréal (YUL)"),
    "YYZ": (43.6777, -79.6248, "Toronto (YYZ)"),
    "SIN": (1.3644, 103.9915, "Singapour (SIN)"),
    "HKG": (22.3080, 113.9185, "Hong Kong (HKG)"),
    "HND": (35.5494, 139.7798, "Tokyo HND"),
    "NRT": (35.7720, 140.3929, "Tokyo NRT"),
    "ICN": (37.4602, 126.4407, "Séoul ICN"),
    "SYD": (-33.9399, 151.1753, "Sydney (SYD)"),
    "DEL": (28.5562, 77.1000, "New Delhi (DEL)"),
    "BOM": (19.0896, 72.8656, "Mumbai (BOM)"),
    "CMN": (33.3675, -7.5898, "Casablanca (CMN)"),
    "RAK": (31.6069, -8.0363, "Marrakech (RAK)"),
    "TUN": (36.8510, 10.2272, "Tunis (TUN)"),
    "ALG": (36.6910, 3.2154, "Alger (ALG)")
}

BASE_AVIONS = {}
CACHE_PHOTOS = {}
CACHE_DETAILS_VOLS = {}
ETAT_PAR_ZONE = {}
ZONE_ACTIVE_SERVEUR = "TLS"
LOCK_ETAT = threading.Lock()


def charger_base_csv():
    if not os.path.exists("avions.csv"):
        print("⚠️ Fichier avions.csv introuvable.")
        return
    with open("avions.csv", mode="r", encoding="utf-8-sig") as f:
        lecteur = csv.DictReader(f)
        for ligne in lecteur:
            code = (ligne.get("icao") or ligne.get("ICAO") or ligne.get("type") or "").strip().upper()
            if code:
                BASE_AVIONS[code] = {k.strip(): (v.strip() if v else "") for k, v in ligne.items() if k}
    print(f"✅ Base CSV chargée : {len(BASE_AVIONS)} modèles d'appareils.")


def distance_haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def decoder_compagnie(indicatif):
    if not indicatif or len(indicatif) < 3:
        return ""
    prefixe = indicatif[:3].upper()
    return COMPAGNIES_OACI.get(prefixe, "")


def detecter_badge_rare(icao, indicatif, immat):
    icao_u = (icao or "").upper()
    ind_u = (indicatif or "").upper()
    imm_u = (immat or "").upper()

    if icao_u in ("A3ST", "A337"):
        return "AIRBUS BELUGA XL / ST"
    if icao_u == "A388":
        return "SUPERJUMBO AIRBUS A380"
    if icao_u in ("A124", "A225", "B748", "B744", "C17", "C5M", "A400"):
        return f"GÉANT / MILITAIRE ({icao_u})"
    if ind_u.startswith("AIB") or ind_u.startswith("BGA"):
        return "VOL D'ESSAI / TRANSPORT AIRBUS"
    if imm_u.startswith("F-WW") or imm_u.startswith("F-WX") or imm_u.startswith("D-AUB"):
        return "PROTOTYPE / ESSAI CONSTRUCTEUR"
    return ""


def determiner_phase(altitude_ft, taux_vertical, distance_km):
    if altitude_ft <= 150 and distance_km <= 4.0:
        return "AU SOL / PISTE"
    if taux_vertical < -300 or (altitude_ft < 6500 and distance_km < 16.0):
        return "EN APPROCHE"
    if taux_vertical > 400:
        return "MONTÉE"
    return "CROISIÈRE / TRANSIT"


def obtenir_photo(immat, icao):
    cle = f"{immat}_{icao}"
    if cle in CACHE_PHOTOS:
        return CACHE_PHOTOS[cle]

    headers = {"User-Agent": "RadarApprocheLive/1.0"}
    urls_a_tester = []
    if immat and immat != "N/A":
        urls_a_tester.append(f"https://api.planespotters.net/pub/photos/reg/{urllib.parse.quote(immat)}")
    if icao and icao != "N/A":
        urls_a_tester.append(f"https://api.planespotters.net/pub/photos/type/{urllib.parse.quote(icao)}")

    for url in urls_a_tester:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                photos = data.get("photos", [])
                if photos:
                    p = photos[0]
                    src = (p.get("thumbnail_large") or {}).get("src") or (p.get("thumbnail") or {}).get("src")
                    if src:
                        res = {"url": src, "auteur": p.get("photographer", "Planespotters.net")}
                        CACHE_PHOTOS[cle] = res
                        return res
        except Exception:
            continue

    CACHE_PHOTOS[cle] = None
    return None


def obtenir_details_vol_fr24(flight_id):
    if not flight_id:
        return {}
    maintenant = time.time()
    if flight_id in CACHE_DETAILS_VOLS:
        entree = CACHE_DETAILS_VOLS[flight_id]
        if maintenant - entree["ts"] < 180:
            return entree["data"]

    url = f"https://data-live.flightradar24.com/clickhandler/?version=1.5&flight={urllib.parse.quote(str(flight_id))}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            airport = raw.get("airport") or {}
            orig = airport.get("origin") or {}
            dest = airport.get("destination") or {}
            time_info = raw.get("time") or {}
            sched = time_info.get("scheduled") or {}
            est = time_info.get("estimated") or {}
            aircraft_info = raw.get("aircraft") or {}

            eta_ts = est.get("arrival") or sched.get("arrival") or None

            details = {
                "orig_code": (orig.get("code") or {}).get("iata", ""),
                "orig_nom": (orig.get("position") or {}).get("region", {}).get("city") or orig.get("name") or "",
                "orig_lat": (orig.get("position") or {}).get("latitude"),
                "orig_lon": (orig.get("position") or {}).get("longitude"),
                "dest_code": (dest.get("code") or {}).get("iata", ""),
                "dest_nom": (dest.get("position") or {}).get("region", {}).get("city") or dest.get("name") or "",
                "dest_lat": (dest.get("position") or {}).get("latitude"),
                "dest_lon": (dest.get("position") or {}).get("longitude"),
                "eta_ts": eta_ts,
                "age": aircraft_info.get("age", "")
            }
            CACHE_DETAILS_VOLS[flight_id] = {"ts": maintenant, "data": details}
            return details
    except Exception:
        return {}


def calculer_progression_et_eta(lat_av, lon_av, vitesse_kts, orig_iata, dest_iata, details):
    orig_lat = details.get("orig_lat")
    orig_lon = details.get("orig_lon")
    dest_lat = details.get("dest_lat")
    dest_lon = details.get("dest_lon")

    if (orig_lat is None or orig_lon is None) and orig_iata in COORDS_AEROPORTS:
        orig_lat, orig_lon, _ = COORDS_AEROPORTS[orig_iata]
    if (dest_lat is None or dest_lon is None) and dest_iata in COORDS_AEROPORTS:
        dest_lat, dest_lon, _ = COORDS_AEROPORTS[dest_iata]

    pct = None
    dist_restante_km = None

    if dest_lat is not None and dest_lon is not None:
        dist_restante_km = round(distance_haversine(lat_av, lon_av, float(dest_lat), float(dest_lon)))
        if orig_lat is not None and orig_lon is not None:
            dist_totale = distance_haversine(float(orig_lat), float(orig_lon), float(dest_lat), float(dest_lon))
            if dist_totale > 10:
                avancement = max(0.0, min(1.0, 1.0 - (dist_restante_km / dist_totale)))
                pct = round(avancement * 100)

    eta_ts = details.get("eta_ts")
    if not eta_ts and dist_restante_km is not None and vitesse_kts and vitesse_kts > 60:
        vitesse_kmh = vitesse_kts * 1.852
        secondes_restantes = (dist_restante_km / vitesse_kmh) * 3600 + 480
        eta_ts = int(time.time() + secondes_restantes)

    return {"pct": pct, "dist_restante_km": dist_restante_km}, eta_ts


def interroger_fr24(zone_id):
    z = ZONES.get(zone_id, ZONES["TLS"])
    lat_c, lon_c, rayon_km = z["lat"], z["lon"], z["rayon_km"]
    delta_lat = (rayon_km / 111.0) * 1.35
    delta_lon = (rayon_km / (111.0 * max(0.2, math.cos(math.radians(lat_c))))) * 1.35

    bounds = f"{lat_c + delta_lat:.4f},{lat_c - delta_lat:.4f},{lon_c - delta_lon:.4f},{lon_c + delta_lon:.4f}"
    url = f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds={bounds}&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=0&estimated=1&maxage=14400&gliders=0&stats=0"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=6) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    avions_detectes = []
    for fid, val in data.items():
        if not isinstance(val, list) or len(val) < 17:
            continue
        hex_code = str(val[0] or fid).upper()
        lat = float(val[1] or 0)
        lon = float(val[2] or 0)
        cap = float(val[3] or 0)
        alt_ft = int(val[4] or 0)
        spd_kts = int(val[5] or 0)
        squawk = str(val[6] or "")
        icao = str(val[8] or "N/A").upper()
        immat = str(val[9] or "N/A").upper()
        orig_iata = str(val[11] or "").upper()
        dest_iata = str(val[12] or "").upper()
        num_vol = str(val[13] or "").upper()
        v_rate = int(val[15] or 0)
        indicatif = str(val[16] or num_vol or immat or hex_code).strip().upper()

        dist = distance_haversine(lat_c, lon_c, lat, lon)
        if dist > rayon_km:
            continue

        compagnie = decoder_compagnie(indicatif)
        phase = determiner_phase(alt_ft, v_rate, dist)
        badge_rare = detecter_badge_rare(icao, indicatif, immat)
        specs = BASE_AVIONS.get(icao, {})

        origine_obj = None
        if orig_iata:
            nom_o = COORDS_AEROPORTS[orig_iata][2] if orig_iata in COORDS_AEROPORTS else orig_iata
            origine_obj = {"code": orig_iata, "nom": nom_o}

        dest_obj = None
        if dest_iata:
            nom_d = COORDS_AEROPORTS[dest_iata][2] if dest_iata in COORDS_AEROPORTS else dest_iata
            dest_obj = {"code": dest_iata, "nom": nom_d}

        vol_obj = {
            "flight_id": fid,
            "hex": hex_code,
            "indicatif": indicatif,
            "num_vol": num_vol,
            "compagnie": compagnie,
            "icao": icao,
            "immat": immat,
            "lat": lat,
            "lon": lon,
            "distance_km": round(dist, 2),
            "altitude_ft": alt_ft,
            "vitesse_kts": spd_kts,
            "cap": cap,
            "taux_vertical": v_rate,
            "squawk": squawk,
            "phase": phase,
            "badge_rare": badge_rare,
            "origine": origine_obj,
            "destination": dest_obj,
            "progression": {"pct": None, "dist_restante_km": None},
            "eta_ts": None,
            "age": ""
        }
        avions_detectes.append({"vol": vol_obj, "specs": specs})

    avions_detectes.sort(key=lambda x: x["vol"]["distance_km"])

    for item in avions_detectes[:5]:
        v = item["vol"]
        details = obtenir_details_vol_fr24(v["flight_id"])
        if details.get("orig_code") or details.get("orig_nom"):
            code_o = details.get("orig_code") or (v["origine"]["code"] if v["origine"] else "")
            nom_o = details.get("orig_nom") or (COORDS_AEROPORTS[code_o][2] if code_o in COORDS_AEROPORTS else code_o)
            if code_o or nom_o:
                v["origine"] = {"code": code_o, "nom": f"{nom_o} ({code_o})" if code_o and code_o not in nom_o else nom_o}

        if details.get("dest_code") or details.get("dest_nom"):
            code_d = details.get("dest_code") or (v["destination"]["code"] if v["destination"] else "")
            nom_d = details.get("dest_nom") or (COORDS_AEROPORTS[code_d][2] if code_d in COORDS_AEROPORTS else code_d)
            if code_d or nom_d:
                v["destination"] = {"code": code_d, "nom": f"{nom_d} ({code_d})" if code_d and code_d not in nom_d else nom_d}

        o_code = v["origine"]["code"] if v["origine"] else ""
        d_code = v["destination"]["code"] if v["destination"] else ""
        prog, eta_ts = calculer_progression_et_eta(v["lat"], v["lon"], v["vitesse_kts"], o_code, d_code, details)
        v["progression"] = prog
        v["eta_ts"] = eta_ts
        if details.get("age"):
            v["age"] = details["age"]

    return avions_detectes


def boucle_radar():
    global ETAT_PAR_ZONE
    while True:
        with LOCK_ETAT:
            zone_a_scanner = ZONE_ACTIVE_SERVEUR
        try:
            avions = interroger_fr24(zone_a_scanner)
            horodatage = datetime.now().strftime("%H:%M:%S")
            with LOCK_ETAT:
                ETAT_PAR_ZONE[zone_a_scanner] = {
                    "avions": avions,
                    "maj": horodatage,
                    "source": "FR24 LIVE"
                }
        except Exception as e:
            print(f"⚠️ Erreur scan {zone_a_scanner}: {e}")
        time.sleep(5)


class RadarHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def envoyer_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def servir_fichier(self, chemin_local, content_type, extra_headers=None):
        try:
            with open(chemin_local, "rb") as f:
                contenu = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(contenu)))
            self.end_headers()
            self.wfile.write(contenu)
        except FileNotFoundError:
            self.send_error(404, "Fichier introuvable")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        chemin = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if chemin in ("/", "/index.html"):
            self.servir_fichier("index.html", "text/html; charset=utf-8")
            return

        if chemin == "/manifest.json":
            self.servir_fichier("manifest.json", "application/manifest+json; charset=utf-8")
            return

        if chemin == "/sw.js":
            self.servir_fichier("sw.js", "application/javascript; charset=utf-8", {"Service-Worker-Allowed": "/"})
            return

        if chemin == "/icon.svg":
            self.servir_fichier("icon.svg", "image/svg+xml")
            return

        if chemin == "/api/zone":
            global ZONE_ACTIVE_SERVEUR
            nouvelle_zone = (params.get("id", ["TLS"])[0] or "TLS").upper()
            if nouvelle_zone in ZONES:
                with LOCK_ETAT:
                    ZONE_ACTIVE_SERVEUR = nouvelle_zone
                try:
                    avions = interroger_fr24(nouvelle_zone)
                    horodatage = datetime.now().strftime("%H:%M:%S")
                    with LOCK_ETAT:
                        ETAT_PAR_ZONE[nouvelle_zone] = {
                            "avions": avions,
                            "maj": horodatage,
                            "source": "FR24 LIVE"
                        }
                except Exception:
                    pass
                self.envoyer_json({"ok": True, "zone_id": nouvelle_zone})
            else:
                self.envoyer_json({"ok": False, "erreur": "Zone inconnue"}, 400)
            return

        if chemin == "/api/trafic":
            zone_id = (params.get("zone", [ZONE_ACTIVE_SERVEUR])[0] or "TLS").upper()
            if zone_id not in ZONES:
                zone_id = "TLS"
            hex_cible = (params.get("hex", [""])[0] or "").upper()

            with LOCK_ETAT:
                ZONE_ACTIVE_SERVEUR = zone_id
                snapshot = ETAT_PAR_ZONE.get(zone_id)

            if not snapshot:
                try:
                    avions = interroger_fr24(zone_id)
                    snapshot = {
                        "avions": avions,
                        "maj": datetime.now().strftime("%H:%M:%S"),
                        "source": "FR24 LIVE"
                    }
                    with LOCK_ETAT:
                        ETAT_PAR_ZONE[zone_id] = snapshot
                except Exception:
                    snapshot = {"avions": [], "maj": datetime.now().strftime("%H:%M:%S"), "source": "FR24 LIVE"}

            liste_avions = snapshot.get("avions", [])
            if not liste_avions:
                self.envoyer_json({
                    "statut": "vide",
                    "zone_id": zone_id,
                    "zone_nom": ZONES[zone_id]["nom"],
                    "nb_avions": 0,
                    "maj_serveur": snapshot.get("maj", ""),
                    "source_api": snapshot.get("source", "FR24 LIVE"),
                    "liste_avions": []
                })
                return

            cible = None
            verrouille = False
            if hex_cible:
                for item in liste_avions:
                    if item["vol"]["hex"] == hex_cible:
                        cible = item
                        verrouille = True
                        break

            if not cible:
                cible = liste_avions[0]

            vol_cible = cible["vol"]
            specs_cible = cible["specs"]
            photo = obtenir_photo(vol_cible["immat"], vol_cible["icao"])

            self.envoyer_json({
                "statut": "actif",
                "zone_id": zone_id,
                "zone_nom": ZONES[zone_id]["nom"],
                "nb_avions": len(liste_avions),
                "verrouille": verrouille,
                "maj_serveur": snapshot.get("maj", ""),
                "source_api": snapshot.get("source", "FR24 LIVE"),
                "vol": vol_cible,
                "specs": specs_cible,
                "photo": photo,
                "liste_avions": liste_avions
            })
            return

        self.send_error(404, "Endpoint inconnu")


if __name__ == "__main__":
    charger_base_csv()
    thread_scan = threading.Thread(target=boucle_radar, daemon=True)
    thread_scan.start()
    serveur = ThreadingHTTPServer(("0.0.0.0", PORT), RadarHandler)
    print(f"🚀 Radar multi-zones actif sur le port {PORT}")
    serveur.serve_forever()
