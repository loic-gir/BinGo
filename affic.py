import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import random
from itertools import cycle

# --- Palette de couleurs modernes ---
COLORS = {
    "primary": "#5A7EED",    # Bleu principal
    "secondary": "#91C4D7",  # Bleu clair
    "accent": "#4766F4",     # Bleu foncé
    "background": "#B6F3C9", # Vert très clair
    "text": "#2B2D42",       # Noir bleuté
    "error": "#D62246",      # Rouge
    "success": "#4CB944",    # Vert
    "warning": "#FF9F1C",    # Orange
    "white": "#FFFFFF",
    "light_bg": "#F5F5F5"
}

# --- Interface principale ---
fenetre = tk.Tk()
fenetre.title("Interface Station de Tri")
fenetre.geometry("800x480")
fenetre.configure(bg=COLORS["background"])

# Style global
style = ttk.Style()
style.configure("TFrame", background=COLORS["background"])
style.configure("TLabel", background=COLORS["background"], font=("Helvetica", 12), foreground=COLORS["text"])
style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground=COLORS["primary"])
style.configure("Bold.TLabel", font=("Helvetica", 12, "bold"))
style.configure("Error.TLabel", foreground=COLORS["error"])
style.configure("Success.TLabel", foreground=COLORS["success"])

# --- Frame principale ---
main_frame = tk.Frame(fenetre, bg=COLORS["background"])
main_frame.pack(fill="both", expand=True)

# Configuration de la grille principale
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# Dictionnaire pour stocker les frames
frames = {}

# Variables globales
dechet_type = tk.StringVar(value="En attente...")
dechet_icons = {
    "Papier / Carton": "icons/papier.png",
    "Plastique": "icons/plastique.png",
    "Métal": "icons/metal.png",
    "Verre": "icons/verre.png",
    "Non recyclable": "icons/non_recyclable.png",
}
dechets_interdits_icons = {
    "Liquides": "icons/liquide.png",
    "Batteries / Piles": "icons/batterie.png",
    "Déchets organiques": "icons/organique.png",
    "Déchets toxiques": "icons/toxique.png",
    "Déchets médicaux": "icons/medical.png",
    "Produits chimiques": "icons/chimique.png"
}
etats_systeme = cycle([
    "Prêt",
    "Détection en cours...",
    "Tri en cours...",
    "Déplacement du bras",
    "Erreur: objet non reconnu"
])

# Compteur de déchets 
class CompteurFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bd=2, relief="groove", bg=COLORS["light_bg"], padx=10, pady=10)

        self.nombre_trie = 0
        self.poids_total = 0.0

        # Style
        tk.Label(self, text="STATISTIQUES", font=("Helvetica", 14, "bold"), 
                bg=COLORS["light_bg"], fg=COLORS["primary"]).grid(row=0, columnspan=2, pady=5)

        # Label pour nombre trié
        tk.Label(self, text="Nombre trié:", font=("Helvetica", 12), 
                bg=COLORS["light_bg"]).grid(row=1, column=0, sticky="e", padx=5)
        self.label_trie = tk.Label(self, text="0", font=("Helvetica", 12, "bold"), 
                                 bg=COLORS["light_bg"], fg=COLORS["accent"])
        self.label_trie.grid(row=1, column=1, sticky="w", padx=5)

        # Label pour quantité jetée
        tk.Label(self, text="Quantité jetée:", font=("Helvetica", 12), 
                bg=COLORS["light_bg"]).grid(row=2, column=0, sticky="e", padx=5)
        self.label_poids = tk.Label(self, text="0.0 kg", font=("Helvetica", 12, "bold"), 
                                  bg=COLORS["light_bg"], fg=COLORS["accent"])
        self.label_poids.grid(row=2, column=1, sticky="w", padx=5)

    def ajouter_dechet(self, poids_kg):
        self.nombre_trie += 1
        self.poids_total += poids_kg
        self.label_trie.config(text=f"{self.nombre_trie}")
        self.label_poids.config(text=f"{self.poids_total:.2f} kg")

# Écran de veille
class VeilleScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["background"])
        
        # Conteneur principal centré
        container = tk.Frame(self, bg=COLORS["background"])
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Titre
        tk.Label(container, text="BinGo", font=("Helvetica", 24, "bold"), 
                bg=COLORS["background"], fg=COLORS["primary"]).pack(pady=(0, 20))

        # Contenu principal (logo + stats + déchets interdits)
        content_frame = tk.Frame(container, bg=COLORS["background"])
        content_frame.pack()

        # Partie gauche - Logo et compteur (inchangé)
        left_frame = tk.Frame(content_frame, bg=COLORS["background"])
        left_frame.pack(side="left", padx=20, pady=10)

        # Logo
        logo_frame = tk.Frame(left_frame, bg=COLORS["primary"], padx=10, pady=10, 
                            highlightbackground=COLORS["accent"], highlightthickness=2)
        logo_frame.pack(pady=(0, 20))
        
        self.logo_img = ImageTk.PhotoImage(Image.open("icons/logo.png").resize((120, 120)))
        logo_label = tk.Label(logo_frame, image=self.logo_img, bg=COLORS["primary"])
        logo_label.pack()
        logo_label.image = self.logo_img

        # Compteur
        self.compteur = CompteurFrame(left_frame)
        self.compteur.pack(fill="x")




        # Bouton de simulation
        self.sim_btn = ttk.Button(left_frame, text="Lancer Simulation", 
                                command=self.lancer_simulation)
        self.sim_btn.pack(pady=10, fill="x")




        # Partie droite - Déchets interdits avec bordure animée
        self.right_frame_container = tk.Frame(content_frame, bg=COLORS["background"])
        self.right_frame_container.pack(side="right", padx=20)
        
        # Charger le GIF animé
        self.border_gif = Image.open("icons/animated_border.gif")  # Téléchargez le GIF et mettez-le dans votre dossier
        self.gif_frames = []
        
        for frame in ImageSequence.Iterator(self.border_gif):
            # Redimensionner pour s'adapter à notre cadre
            frame = frame.resize((350, 300))
            self.gif_frames.append(ImageTk.PhotoImage(frame))
        
        self.current_frame = 0
        self.animation_cycle = cycle(self.gif_frames)
        
        # Canvas pour l'animation de bordure
        self.animated_canvas = tk.Canvas(self.right_frame_container, 
                                       width=350, height=300, 
                                       bg=COLORS["light_bg"], 
                                       highlightthickness=0)
        self.animated_canvas.pack()
        
        # Image de bordure
        self.border_img = self.animated_canvas.create_image(0, 0, 
                                                          anchor="nw", 
                                                          image=self.gif_frames[0])
        
        # Cadre intérieur pour le contenu
        self.inner_frame = tk.Frame(self.animated_canvas, 
                                  bg=COLORS["light_bg"], 
                                  padx=20, pady=20)
        self.animated_canvas.create_window(175, 150, window=self.inner_frame)
        
        # Titre
        tk.Label(self.inner_frame, text="DÉCHETS INTERDITS", 
                font=("Helvetica", 16, "bold"), 
                bg=COLORS["light_bg"], fg=COLORS["primary"]).pack(pady=10)
        
        # Liste avec icônes
        for item, icon in dechets_interdits_icons.items():
            item_frame = tk.Frame(self.inner_frame, bg=COLORS["light_bg"])
            item_frame.pack(fill="x", padx=10, pady=5)
            
            img = Image.open(icon).resize((30, 30))
            photo = ImageTk.PhotoImage(img)
            icon_label = tk.Label(item_frame, image=photo, bg=COLORS["light_bg"])
            icon_label.image = photo
            icon_label.pack(side="left", padx=(0, 10))
            
            tk.Label(item_frame, text=item, 
                    font=("Helvetica", 12), 
                    bg=COLORS["light_bg"], 
                    fg=COLORS["error"]).pack(side="left")
        
        # Démarrer l'animation
        self.animate_border()
        
        # Message d'attente
        self.msg_attente = tk.Label(container, 
                                  text="Veuillez déposer votre déchet dans le bac...", 
                                  font=("Helvetica", 14, "italic"), 
                                  bg=COLORS["background"], 
                                  fg=COLORS["text"])
        self.msg_attente.pack(pady=20)

    def animate_border(self):
        next_frame = next(self.animation_cycle)
        self.animated_canvas.itemconfig(self.border_img, image=next_frame)
        self.after(100, self.animate_border)  # 100ms entre chaque frame



    def lancer_simulation(self):
        start_simulation_cycle()



# Écran de résultat
class ResultatScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["background"])
        
        # Conteneur principal centré
        main_container = tk.Frame(self, bg=COLORS["background"])
        main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Cadre de résultat
        result_frame = tk.Frame(main_container, bg=COLORS["light_bg"], 
                              bd=2, relief="groove", padx=20, pady=20)
        result_frame.pack(pady=10, padx=20, ipadx=10, ipady=10)
        
        tk.Label(result_frame, text="RÉSULTAT DU TRI", 
                font=("Helvetica", 18, "bold"), 
                bg=COLORS["light_bg"], fg=COLORS["primary"]).pack(pady=10)

        # Icône du déchet
        self.icon_frame = tk.Frame(result_frame, bg=COLORS["light_bg"])
        self.icon_frame.pack(pady=10)
        
        self.icon_label = tk.Label(self.icon_frame, bg=COLORS["light_bg"])
        self.icon_label.pack()
        
        # Type détecté
        self.type_frame = tk.Frame(result_frame, bg=COLORS["light_bg"])
        self.type_frame.pack(pady=10)
        
        tk.Label(self.type_frame, text="Type détecté:", 
                font=("Helvetica", 14), 
                bg=COLORS["light_bg"]).pack(side="left")
        
        self.type_label = tk.Label(self.type_frame, 
                                 textvariable=dechet_type, 
                                 font=("Helvetica", 14, "bold"),
                                 bg=COLORS["light_bg"],
                                 fg=COLORS["accent"])
        self.type_label.pack(side="left", padx=10)

    def update_type_dechet(self, nom_type):
        dechet_type.set(nom_type)
        chemin = dechet_icons.get(nom_type)
        
        img = Image.open(chemin).resize((150, 150))
        photo = ImageTk.PhotoImage(img)
        self.icon_label.configure(image=photo)
        self.icon_label.image = photo

# Écran état système
class EtatSystemeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLORS["background"])

        # Conteneur principal centré
        main_container = tk.Frame(self, bg=COLORS["background"])
        main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Cadre d'état
        state_frame = tk.Frame(main_container, bg=COLORS["light_bg"], 
                              bd=2, relief="groove", padx=30, pady=30)
        state_frame.pack(pady=10, padx=20)

        # Titre
        tk.Label(state_frame, text="ÉTAT DU SYSTÈME", 
                font=("Helvetica", 14), 
                bg=COLORS["light_bg"], 
                fg=COLORS["text"]).pack()
        
        # Icône d'état
        self.state_icon = tk.Label(state_frame, 
                                  text="🔄", 
                                  font=("Helvetica", 48), 
                                  bg=COLORS["light_bg"])
        self.state_icon.pack(pady=10)

        # Message d'état
        self.state_label = tk.Label(state_frame, 
                                  text="Initialisation...", 
                                  font=("Helvetica", 18, "bold"),  # Police plus grande
                                  bg=COLORS["light_bg"], 
                                  fg=COLORS["primary"],  # Couleur d'accent
                                  pady=20,
                                  wraplength=300)  # Permet le retour à la ligne
        self.state_label.pack()

    def update_state(self, msg):
        self.state_label.config(text=msg)
        if "erreur" in msg.lower():
            self.state_icon.config(text="✗", fg=COLORS["error"])
            self.state_label.config(fg=COLORS["error"])
        elif "prêt" in msg.lower():
            self.state_icon.config(text="✓", fg=COLORS["success"])
            self.state_label.config(fg=COLORS["success"])
        else:
            self.state_icon.config(text="🔄", fg=COLORS["warning"])
            self.state_label.config(fg=COLORS["primary"])

# Fonctions de gestion des écrans
def show_frame(screen_class):
    frame = frames[screen_class]
    frame.tkraise()

def create_frames():
    for F in (VeilleScreen, ResultatScreen, EtatSystemeScreen):
        frame = F(main_frame, fenetre)
        frames[F] = frame
        frame.grid(row=0, column=0, sticky="nsew")

# Simulation
def start_simulation_cycle():
    type_choisi = random.choice(list(dechet_icons.keys()))
    
    show_frame(EtatSystemeScreen)
    frames[EtatSystemeScreen].update_state("Détection en cours...")
    fenetre.after(3000, lambda: frames[VeilleScreen].compteur.ajouter_dechet(0.5))
    
    fenetre.after(6000, lambda: [show_frame(ResultatScreen), 
                                frames[ResultatScreen].update_type_dechet(type_choisi)])
    
    fenetre.after(9000, lambda: [show_frame(EtatSystemeScreen), 
                                frames[EtatSystemeScreen].update_state("Tri en cours...")])
    
    fenetre.after(12000, lambda: show_frame(VeilleScreen))

# Initialisation
create_frames()
show_frame(VeilleScreen)

# Démarrer la simulation (décommenter pour tester)
fenetre.after(2000, start_simulation_cycle)

fenetre.mainloop()