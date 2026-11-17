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
        self.grid_rowconfigure(2, weight =1)

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

        self.figure, self.axis = plt.subplots(figsize = (8, 4), facecolor = "#181a20")
        self.canvas = FigureCanvasTkAgg(self.figure, master = self)
        self.canvas.get_tk_widget().grid(row = 2, column = 0, padx = 18, 
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
        
