import csv
import json
import math
import random
from pathlib import Path

class Government:
    tax_interval = 150
    initial_fiscal_health = 50.0
    tax_rate_zero_health = 0.30
    tax_rate_full_health = 0.10

    def __init__(self, reset_state = True):
        self.data_directory = Path(__file__).resolve().parent
        self.country_file = (self.data_directory.parent / "random_events" / "country-list.csv")
        self.state_file = self.data_directory / "government_state.json"
        self.players = {}

        with self.country_file.open("r", encoding = "utf-8", newline = "") as file:
            rows = csv.DictReader(file)
            self.countries = list(dict.fromkeys(row["country"].strip() 
                                                for row in rows if row.get("country") 
                                                and row["country"].strip()))

            if not self.countries:
                raise ValueError(f"Aucun pays trouvé dans {self.country_file}")

            self.fiscal_health = {country: self.initial_fiscal_health for country 
                                  in self.countries}

            self.regions_file = (self.data_directory.parent / "random_events" / "countries_regions.json")

            with self.regions_file.open("r", encoding = "utf-8") as file:
                countries_by_region = json.load(file)

            if not isinstance(countries_by_region, dict):
                raise ValueError(f"Format invalide : {self.regions_file}")

            self.countries_by_region = {region: [country for country in countries if country in self.fiscal_health] 
                                        for region, countries in countries_by_region.items()}

            if not reset_state and self.state_file.exists():
                self.load_state()

    def add_player(self, player_id):
        if player_id in self.players:
            return

        self.players[player_id] = {"country": random.choice(self.countries)}
        self.save_state()

    def get_tax_rate(self,country):
        if country not in self.fiscal_health:
            raise KeyError(f"Pays inconnu: {country!r}")

        health_ratio = self.fiscal_health[country] / 100
        return (self.tax_rate_zero_health + (self.tax_rate_full_health - self.tax_rate_zero_health) 
                * health_ratio)

    def load_state(self):
        with self.state_file.open("r", encoding = "utf-8") as file:
            state = json.load(file)

        if not isinstance(state, dict) or not isinstance(state.get("players"), dict):
            raise ValueError(f"État gouvernemental invalide: {self.state_file}")

        for player_id, player_state in state["players"].items():
            if (not isinstance(player_state, dict) or player_state.get("country") not in self.countries):
                raise ValueError(f"Pays invalide dans l'état gouvernemental pour {player_id!r}")

        saved_health = state.get("fiscal_health", {})
        if not isinstance(saved_health, dict):
            raise ValueError(f"Santé fiscale invalide: {self.state_file}")

        for country,health in saved_health.items():
            if(country not in self.fiscal_health or isinstance(health,bool) 
               or not isinstance(health, (int, float)) or not math.isfinite(health) 
               or not 0 <= health <= 100):
                raise ValueError(f"Santé fiscale invalide pour {country!r}")
            
            self.fiscal_health[country] = float(health)

        self.players = state["players"]

    def save_state(self):
        with self.state_file.open("w", encoding = "utf-8") as file:
            json.dump({"players": self.players, "fiscal_health": self.fiscal_health}, 
                      file, indent = 2, ensure_ascii = False)

    def adjust_health(self, value, minimum = 0.00, maximum = 100.0):
        return max(minimum, min(maximum, value))

    def random_fiscal_drift(self):
        for country, health in self.fiscal_health.items():
            direction = random.choice((-1, 0 ,1))
            amount = random.uniform(1, 3) if direction != 0 else 0.0

            self.fiscal_health[country] = self.adjust_health(health + direction * amount)

        self.save_state()


    def apply_global_event_impact(self, event):
        if not event or event.get("scope") != "global":
            return

        impact = event.get("impact", 0.0)
        if (isinstance(impact, bool) or not isinstance(impact, (int, float)) 
            or not math.isfinite(impact)):
            raise ValueError(f"Impact d'événement invalide : {impact!r}")

        variables = event.get("variables", {})
        if not isinstance(variables, dict):
            raise ValueError("Variables d'événement invalides")

        country = variables.get("country")
        region = variables.get("region")

        if country in self.fiscal_health:
            affected_countries = [country]
        elif region in self.countries_by_region:
            affected_countries = self.countries_by_region[region]
        else: return

        fiscal_change = impact * 12.0

        for affected_country in set(affected_countries):
            self.fiscal_health[affected_country] = self.adjust_health(self.fiscal_health[affected_country] + fiscal_change)

        self.save_state()