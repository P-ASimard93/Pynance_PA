import math
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GovernmentView(ctk.CTkFrame):
    def __init__(self, master, controller, engine):
        super().__init__(master, fg_color = "#0b0e11")
        self.controller = controller
        self.engine = engine

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(3, weight =1)

        header = ctk.CTkFrame(self, fg_color = "#181a20", corner_radius = 8)
        header.grid(row = 0, column = 0, padx = 18, pady = (18,10), sticky = "ew")

        ctk.CTkLabel(header, text = "GOUVERNEMENT", text_color = "#0ecb81", 
                     font = ("Arial", 12, "bold")).pack(anchor = "w", padx = 18, 
                                                        pady = (12,2))

        ctk.CTkLabel(header, text = "Situation fiscale", text_color = "#eaecef", 
                     font = ("Arial", 24, "bold")).pack(anchor = "w", padx = 18, 
                                                        pady = (0,12))

        self.country_label = ctk.CTkLabel(self, text = "", text_color = "#eaecef", 
                                          font = ("Arial", 16, "bold"))
        self.country_label.grid(row = 1, column = 0, padx = 24, pady = 12, 
                                sticky = "w")

        self.grid_rowconfigure(3, weight = 1)

        self.bribe_panel = ctk.CTkFrame(self, fg_color = "#181a20", corner_radius = 8)
        self.bribe_panel.grid(row = 2, column = 0, padx = 18, pady = 10, sticky = "ew")
        self.bribe_panel.grid_columnconfigure(0, weight = 1)

        self.influence_label = ctk.CTkLabel(self.bribe_panel, text = "Influence politique: 0 / 100", 
                                            text_color = "#eaecef", font = ("Arial", 14, "bold"))
        self.influence_label.pack(anchor = "w", padx = 16, pady = (12, 4))

        ctk.CTkLabel(self.bribe_panel, text = "Coût : 10 000 $ par point d'influence", 
                     text_color = "#848e9c").pack(anchor = "w", padx = 16, pady = (0,8))

        self.bribe_entry = ctk.CTkEntry(self.bribe_panel, placeholder_text = "Montant de pot-de-vin")
        self.bribe_entry.pack(fill = "x", padx = 16, pady = (0, 8))

        self.bribe_button = ctk.CTkButton(self.bribe_panel, text = "Payer un pot-de-vin", 
                                          command = self.submit_bribe)
        self.bribe_button.pack(anchor = "w", padx = 16, pady = (0, 8))

        self.bribe_status = ctk.CTkLabel(self.bribe_panel, text = "", text_color = "#848e9c")
        self.bribe_status.pack(anchor = "w", padx = 16, pady = (0, 12))

        self.risk_label = ctk.CTkLabel(self.bribe_panel, text = "Risque de détection : 0 / 100", 
                                       text_color = "#eaecef")
        self.risk_label.pack(anchor = "w", padx = 16, pady = (0, 8))

        self.cover_button = ctk.CTkButton(self.bribe_panel, text = "Couvrir mes traces - 100 000 $", 
                                          command = self.cover_traces)
        self.cover_button.pack(anchor = "w", padx = 16, pady = (0, 8))

        self.tax_havens_label = ctk.CTkLabel(self.bribe_panel, text = "", 
                                             text_color = "#848e9c", wraplength = 900)
        self.tax_havens_label.pack(anchor = "w", padx = 16, pady = (8, 4))

        self.offshore_balance_label = ctk.CTkLabel(self.bribe_panel, text = "Solde cachée : 0,00 $", 
                                                        text_color = "#eaecef")
        self.offshore_balance_label.pack(anchor = "w", padx = 16, pady = (0,4))

        self.offshore_entry = ctk.CTkEntry(self.bribe_panel, placeholder_text = "Montant à transférer")
        self.offshore_entry.pack(fill = "x", padx = 16, pady = (0, 8))

        offshore_buttons = ctk.CTkFrame(self.bribe_panel, fg_color = "transparent")
        offshore_buttons.pack(anchor = "w", padx = 16, pady = (0, 8))

        ctk.CTkButton(offshore_buttons, text = "Déposer", command = lambda: self.transfer_offshore("deposit_offshore")).pack(side = "left", padx = (0, 8))

        ctk.CTkButton(offshore_buttons, text = "Retirer", command = lambda: self.transfer_offshore("withdraw_offshore")).pack(side = "left")

        self.offshore_status = ctk.CTkLabel(self.bribe_panel, text = "", text_color = "#848e9c")
        self.offshore_status.pack(anchor = "w", padx = 16, pady = (0, 12))

        self.figure, self.axis = plt.subplots(figsize = (8, 4), facecolor = "#181a20")
        self.canvas = FigureCanvasTkAgg(self.figure, master = self)
        self.canvas.get_tk_widget().grid(row = 3, column = 0, padx = 18, 
                                         pady = (0, 18), sticky = "nsew")

        self.refresh()

    def refresh(self):
        state = self.engine.database.get("government_state")
        if not isinstance(state, dict):
            state = {}

        players = state.get("players", {})
        fiscal_health = state.get("fiscal_health", {})
        fiscal_history = state.get("fiscal_history", {})

        player_state = players.get(self.engine.username, {})
        country = (player_state.get("country") if isinstance(player_state, dict)
                    else None)

        tax_havens = state.get("tax_haven_countries", [])
        if not isinstance(tax_havens, list):
            tax_havens = []

        tax_rate = self.engine.government.offshore_tax_rate
        self.tax_havens_label.configure( text = f"Paradis fiscaux ({tax_rate:.1%} par prélèvement) : {', '.join(tax_havens)}")

        offshore_cash = player_state.get("offshore_cash", 0.0)
        self.offshore_balance_label.configure(text = f"Solde cachée : {offshore_cash:,.2f} $")

        influence = player_state.get("political_influence", 0.0)
        self.influence_label.configure(text = f"Influence politique : {influence:.1f} / 100")

        risk = player_state.get("bribe_risk", 0.0)
        self.risk_label.configure(text = f"Risque de détection : {risk:.1f} / 100")

        health = fiscal_health.get(country) if country else None
        history = fiscal_history.get(country, []) if country else []

        if (isinstance(health, bool) or not isinstance(health, (int, float)) or not math.isfinite(health)):
            self.country_label.configure(text = "Aucune donnée gouvernementale disponible.")
        else:
            government = self.engine.government
            tax_rate = government.tax_rate_zero_health + (government.tax_rate_full_health 
                                                          - government.tax_rate_zero_health) * (health/100)

            self.country_label.configure(text = (f"Pays : {country} --- Santé fiscale : {health:.1f} / 100 --- Taux de taxe : {tax_rate:.1%}"))

        valid_history = [value for value in history if isinstance(value, (int,float)) 
                         and not isinstance(value,bool) and math.isfinite(value)]

        self.axis.clear()
        self.axis.set_facecolor("#181a20")
        self.axis.tick_params(colors = "#eaecef")

        for spine in self.axis.spines.values():
            spine.set_color("#363c4e")

        if valid_history:
            self.axis.plot(range(len(valid_history)), valid_history, color = "#0ecb81", 
                           linewidth = 2)

        self.axis.set_xlim(0, max(1, len(valid_history) - 1))
        self.axis.set_ylim(0,100)
        self.axis.set_xlabel("Temps (1 point = 10 itérations)", color = "#eaecef")
        self.axis.set_ylabel("Santé fiscale", color = "#eaecef")
        self.axis.set_title(f"Évolution de la santé fiscale - {country or 'pays inconnu'}", color = "#eaecef")
        self.axis.grid(True, color = "#363c4e", alpha = 0.5)

        self.canvas.draw_idle()

    def submit_bribe(self):
        try:
            amount = float(self.bribe_entry.get())
        except ValueError:
            self.bribe_status.configure(text = "Entre un montant valide.")
            return

        if not math.isfinite(amount) or amount <= 0:
            self.bribe_status.configure(text = "Le montant doit être positif.")
            return

        accepted = self.engine.request_bank_action("bribe", amount)

        if not accepted:
            self.bribe_status.configure(text = "Demande refusée: vérifie ton solde et ton plafond d'influence")
            return

        if self.engine.hosting:
            self.bribe_status.configure(text = "Pot-de-vin payé.")
            self.bribe_entry.delete(0, "end")
            self. refresh()
        else:
            self.bribe_status.configure(text = "Demande envoyée à l'hôte.")

    def cover_traces(self):
        accepted = self.engine.request_bank_action("cover_traces")

        if not accepted:
            self.bribe_status.configure(text = "Couverture refusée : vérifie ton solde et ton risque.")
        elif self.engine.hosting:
            self.bribe_status.configure(text = "Traces couvertes.")
            self.refresh()
        else:
            self.bribe_status.configure(text = "Demande envoyée à l'hôte.")

    def transfer_offshore(self, action):
        try:
            amount = float(self.offshore_entry.get())
        except ValueError:
            self.offshore_status.configure(text = "Entre un montant valide")
            return

        if not math.isfinite(amount) or amount <= 0:
            self.offshore_status.configure(text = "Le montant doit être positif.")
            return

        accepted = self.engine.request_bank_action(action, amount)

        if not accepted:
            self.offshore_status.configure(text = "Transfert refusé : vérifie ton solde.")
        elif self.engine.hosting:
            label = "Dépôt effectué." if action == "deposit_offshore" else "Retrait effectué."
            self.offshore_status.configure(text = label)
            self.offshore_entry.delete(0, "end")
            self.refresh()
        else:
            self.offshore_status.configure(text = "Demande envoyée à l'hôte")