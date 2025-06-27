import json
from pathlib import Path

JSON_PATH = Path(__file__).parent / "data" / "BesoinNet.json"


def load_irrigation_data():
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {JSON_PATH.absolute()}")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_irrigation(culture: str, type_sol: str, saison: str, type_irrigation: str):
    try:
        data = load_irrigation_data()
        print("✅ Fichier JSON chargé avec succès")
        print("👉 Exemple d’entrée chargée :", data[0])

        entry = next(
            (item for item in data
             if item["Culture"] == culture
             and item["Type de sol"] == type_sol
             and item["Saison"] == saison),
            None
        )


        if not entry:
            raise ValueError(f"Combinaison non trouvée pour: Culture={culture}, Type de sol={type_sol}, Saison={saison}")

        besoin_quotidien = entry["Besoin quotidien (m³/ha/jour)"]
        frequence = entry["Fréquence d'irrigation (par semaine)"]

        if type_irrigation == "goutte_a_goutte":
            besoin_brut = besoin_quotidien / 0.90
        elif type_irrigation == "aspersion":
            besoin_brut = besoin_quotidien / 0.70
        elif type_irrigation == "gravitaire":
            besoin_brut = besoin_quotidien / 0.50
        else:
            raise ValueError("Type d'irrigation invalide.")

        besoin_par_seance = (besoin_brut * 7) / frequence

        return {
            "culture": culture,
            "type_sol": type_sol,
            "saison": saison,
            "type_irrigation": type_irrigation,
            "frequence_irrigation": frequence,
            "besoin_brut": besoin_brut,
            "besoin_par_seance": besoin_par_seance,
            "irrigation_necessaire": True
        }


    except FileNotFoundError as e:
        raise ValueError(f"Erreur de fichier : {str(e)}")
    except KeyError as e:
        raise ValueError(f"Clé manquante dans le fichier JSON : {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur lors du calcul de l'irrigation : {str(e)}")
