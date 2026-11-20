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
    fiscal_history_limit = 200
    bribe_cost_per_influence = 10000.0
    max_political_influence = 100.0
    bribe_risk_per_10k = 5.0
    bribe_risk_growth_per_check = 0.1
    cover_traces_cost = 100000.0
    cover_traces_reduction = 10.0
    tax_haven_count = 5
    offshore_tax_rate = 0.075

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

            if len(self.countries) <= self.tax_haven_count:
                raise ValueError("Il faut plus de pays que le nombre de paradis fiscaux.")

            self.tax_haven_countries = random.sample(self.countries, self.tax_haven_count)

            self.fiscal_health = {country: self.initial_fiscal_health for country 
                                  in self.countries}

            self.fiscal_history = {country: [health] for country, health in self.fiscal_health.items()}

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

        available_countries = [country for country in self.countries if country not in self.tax_haven_countries]

        self.players[player_id] = {"country": random.choice(available_countries),
                                   "offshore_cash": 0.0, 
                                   "political_influence": 0.0,
                                   "bribe_risk": 0.0}
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

        saved_havens = state.get("tax_haven_countries")
                
        if saved_havens is None:
            occupied_countries = {player.get("country") for player in state["players"].values() 
                                if isinstance(player,dict) and player.get("country") in self.countries}
            available_havens = [country for country in self.countries if country not in occupied_countries]
            if len(available_havens) < self.tax_haven_count:
                raise ValueError("Impossible de choisir les paradis fiscaux")
                
            saved_havens = random.sample(available_havens, self.tax_haven_count)
                
        if ( not isinstance(saved_havens, list) or len(saved_havens) != self.tax_haven_count or any(country not in self.countries for country in saved_havens) or len(set(saved_havens)) != self.tax_haven_count):
            raise ValueError("Liste de paradis fiscaux invalide.")
                
        self.tax_haven_countries = saved_havens

        for player_id, player_state in state["players"].items():   
            if (not isinstance(player_state, dict) or player_state.get("country") not in self.countries):
                raise ValueError(f"Pays invalide dans l'état gouvernemental pour {player_id!r}")

            influence = player_state.get("political_influence", 0.0)

            if( isinstance(influence,bool) or not isinstance(influence, (int, float)) 
            or not math.isfinite(influence) or not 0 <= influence <= self.max_political_influence):
                raise ValueError(f"Influence politique invalide pour {player_id!r}")

            player_state["political_influence"] = float(influence)

            risk = player_state.get("bribe_risk", 0.0)

            if (isinstance(risk,bool) or not isinstance(risk, (int, float)) 
                or not math.isfinite(risk) or not 0 <= risk <= 100):
                raise ValueError(f"Risque de corruption invalide pour {player_id!r}")

            player_state["bribe_risk"] = float(risk)

            offshore_cash = player_state.get("offshore_cash", 0.0)
            if(isinstance(offshore_cash, bool) or not isinstance(offshore_cash, (int, float)) or not math.isfinite(offshore_cash) or offshore_cash < 0):
                raise ValueError(f"Solde cachée invaliude pour {player_id!r}")

            player_state["offshore_cash"] = float(offshore_cash)

            if(not isinstance(player_state, dict) or player_state.get("country") not in self.countries or player_state.get("country") in self.tax_haven_countries):
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

        saved_history = state.get("fiscal_history", {})

        if not isinstance(saved_history, dict):
            raise ValueError("Historique fiscal invalide")

        for country in self.countries:
            values = saved_history.get(country)

            if values is None:
                self.fiscal_history[country] = [self.fiscal_health[country]]
                continue

            if not isinstance(values, list):
                raise ValueError(f"Historique fiscal invalide pour {country!r}")

            valid_values = []
            for value in values:
                if (isinstance(value,bool) or not isinstance(value, (int, float)) 
                    or not math.isfinite(value) 
                    or not 0 <= value <= 100):
                    raise ValueError(f"Valeur d'historique invalide pour {country!r}")
                valid_values.append(float(value))

            self.fiscal_history[country] = (valid_values[-self.fiscal_history_limit:] 
                                            or [self.fiscal_health[country]])




        self.players = state["players"]

    def save_state(self):
        with self.state_file.open("w", encoding = "utf-8") as file:
            json.dump({"players": self.players, 
                       "fiscal_health": self.fiscal_health, 
                       "fiscal_history": self.fiscal_history,
                       "tax_haven_countries": self.tax_haven_countries}, 
                       file, indent = 2, ensure_ascii = False)

    def adjust_health(self, value, minimum = 0.00, maximum = 100.0):
        return max(minimum, min(maximum, value))

    def random_fiscal_drift(self):
        for country, health in self.fiscal_health.items():
            direction = random.choice((-1, 0 ,1))
            amount = random.uniform(1, 10) if direction != 0 else 0.0

            self.fiscal_health[country] = self.adjust_health(health + direction * amount)

        self.record_fiscal_history()


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
        else: 
            affected_countries = []

        fiscal_change = impact * 12.0

        for affected_country in set(affected_countries):
            self.fiscal_health[affected_country] = self.adjust_health(self.fiscal_health[affected_country] + fiscal_change)

        self.record_fiscal_history()

    def record_fiscal_history(self):
        for country, health in self.fiscal_health.items():
            history = self.fiscal_history.setdefault(country, [])
            history.append(health)
            del history[:-self.fiscal_history_limit]

        self.save_state()

    def apply_bribe(self, player_id, amount):
        player_state = self.players.get(player_id)
        if player_state is None:
            return False

        influence = player_state.get("political_influence")
        if (isinstance(amount,bool) or not isinstance(amount, (int, float)) 
            or not math.isfinite(amount) or amount <= 0 or isinstance(influence,bool) 
            or not isinstance(influence, (int, float)) or not math.isfinite(influence) 
            or influence < 0 or influence > self.max_political_influence):
            return False

        influence_gain = amount / self.bribe_cost_per_influence
        if influence + influence_gain > self.max_political_influence:
            return False

        risk = player_state.get("bribe_risk", 0.0)
        risk_gain = amount / self.bribe_cost_per_influence * self.bribe_risk_per_10k

        player_state["political_influence"] = influence + influence_gain
        player_state["bribe_risk"] = min(100.0, risk + risk_gain)
        self.save_state()
        return True

    def advance_bribe_risk(self):
        caught_players = []

        for player_id, player_state in self.players.items():
            risk = player_state.get("bribe_risk", 0.0)
            if risk <= 0:
                continue

            risk = min(100.0, risk + self.bribe_risk_growth_per_check)
            player_state["bribe_risk"] = risk

            if random.random() < risk / 100:
                caught_players.append(player_id)

        self.save_state()
        return caught_players

    def cover_bribe_traces(self, player_id):
        player_state = self.players.get(player_id)
        if player_state is None:
            return False

        risk = player_state.get("bribe_risk", 0.0)
        if(isinstance(risk, bool) or not isinstance(risk, (int, float)) or not math.isfinite(risk) 
           or risk <= 0):
            return False

        player_state["bribe_risk"] = max(0.0, risk - self.cover_traces_reduction)
        self.save_state()
        return True