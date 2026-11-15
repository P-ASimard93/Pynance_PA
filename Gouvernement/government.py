import csv
import json
import random
from pathlib import Path

class Government:
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

            if not reset_state and self.state_file.exists():
                self.load_state()

    def add_player(self, player_id):
        if player_id in self.players:
            return

        self.players[player_id] = {"country": random.choice(self.countries)}
        self.save_state()

    def load_state(self):
        with self.state_file.open("r", encoding = "utf-8") as file:
            state = json.load(file)

        if not isinstance(state, dict) or not isinstance(state.get("players"), dict):
            raise ValueError(f"État gouvernemental invalide: {self.state_file}")

        for player_id, player_state in state["players"].items():
            if (not isinstance(player_state, dict) or player_state.get("country") not in self.countries):
                raise ValueError(f"Pays invalide dans l'état gouvernemental pour {player_id!r}")

        self.players = state["players"]

    def save_state(self):
        with self.state_file.open("w", encoding = "utf-8") as file:
            json.dump({"players": self.players}, file, indent = 2, ensure_ascii = False)
            

