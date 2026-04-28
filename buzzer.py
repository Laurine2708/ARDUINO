import tkinter as tk
import serial
import threading
import time
import queue

# ---------------- CONFIG ----------------
PORT = "COM4"
BAUDRATE = 9600

# ---------------- DATA ----------------
players = {
    "Joueur 1": 0,
    "Joueur 2": 0,
    "Joueur 3": 0,
    "Joueur 4": 0
}

points = [5, 3, 2, 1]
tentative = 0
joueur_actif = None
bonne_reponse = False

questions = [
    "La Terre est plate ?",
    "Python est un langage de programmation ?",
    "Le Soleil est une planète ?"
]
index_question = 0

# file pour communication thread -> GUI
serial_queue = queue.Queue()

# ---------------- UI ----------------
root = tk.Tk()
root.title("QUIZ ARDUINO BUZZER")
root.geometry("1000x650")
root.configure(bg="#0f111a")

title = tk.Label(
    root,
    text="QUIZ ARDUINO BUZZER",
    font=("Arial", 26, "bold"),
    bg="#0f111a",
    fg="white"
)
title.pack(pady=10)

question_label = tk.Label(
    root,
    text="",
    font=("Arial", 22, "bold"),
    bg="#0f111a",
    fg="#00d4ff"
)
question_label.pack(pady=10)

buzzer_label = tk.Label(
    root,
    text="",
    font=("Arial", 16, "bold"),
    bg="#0f111a",
    fg="#00ff99"
)
buzzer_label.pack(pady=5)

result_label = tk.Label(
    root,
    text="",
    font=("Arial", 18, "bold"),
    width=30
)
result_label.pack(pady=10)

# ---------------- JOUEURS ----------------
frame_players = tk.Frame(root, bg="#0f111a")
frame_players.pack(pady=25)

player_frames = {}

def create_card(name, col):
    card = tk.Frame(
        frame_players,
        bg="#1b1f2a",
        width=200,
        height=140,
        highlightthickness=2,
        highlightbackground="#2c3142"
    )
    card.grid(row=0, column=col, padx=15)
    card.pack_propagate(False)

    tk.Label(
        card,
        text=name,
        font=("Arial", 14, "bold"),
        bg="#1b1f2a",
        fg="white"
    ).pack(pady=10)

    score = tk.Label(
        card,
        text="0",
        font=("Arial", 28, "bold"),
        bg="#1b1f2a",
        fg="#00ff99"
    )
    score.pack()

    player_frames[name] = {
        "card": card,
        "score": score
    }

create_card("Joueur 1", 0)
create_card("Joueur 2", 1)
create_card("Joueur 3", 2)
create_card("Joueur 4", 3)

# ---------------- LOGIQUE ----------------
def update_scores():
    for p in players:
        player_frames[p]["score"].config(text=str(players[p]))

def set_question():
    global tentative, bonne_reponse, joueur_actif
    if index_question < len(questions):
        question_label.config(text=questions[index_question])
    else:
        question_label.config(text="FIN DU JEU")
    tentative = 0
    bonne_reponse = False
    joueur_actif = None
    result_label.config(text="", bg="#0f111a")
    buzzer_label.config(text="")
    for p in player_frames:
        player_frames[p]["card"].config(highlightbackground="#2c3142")

def highlight_player(name):
    for p in player_frames:
        player_frames[p]["card"].config(highlightbackground="#2c3142")
    player_frames[name]["card"].config(highlightbackground="#00d4ff")
    buzzer_label.config(text=f"{name} a buzzé !")

def reset_game():
    global index_question, joueur_actif, tentative, bonne_reponse
    for p in players:
        players[p] = 0
    index_question = 0
    tentative = 0
    joueur_actif = None
    bonne_reponse = False
    update_scores()
    set_question()
    result_label.config(text="", bg="#0f111a")
    buzzer_label.config(text="RESET")

def next_question():
    global index_question
    index_question += 1
    set_question()

# ---------------- BOUTONS ----------------
btn_frame = tk.Frame(root, bg="#0f111a")
btn_frame.pack(pady=15)

def btn(text, color, cmd):
    return tk.Button(
        btn_frame,
        text=text,
        command=cmd,
        font=("Arial", 12, "bold"),
        bg=color,
        fg="white",
        relief="flat",
        padx=20,
        pady=10
    )

btn("RESET", "#ff4d4d", reset_game).grid(row=0, column=0, padx=10)
btn("QUESTION SUIVANTE", "#00aaff", next_question).grid(row=0, column=1, padx=10)

# ---------------- ARDUINO ----------------
def process_serial_message(msg):
    global joueur_actif, tentative, bonne_reponse

    if msg in players:
        joueur_actif = msg
        highlight_player(msg)

    elif msg == "true":
        if joueur_actif and not bonne_reponse:
            score = points[min(tentative, len(points) - 1)]
            players[joueur_actif] += score
            update_scores()
            result_label.config(text=f"BONNE RÉPONSE +{score}", bg="green")
            bonne_reponse = True

    elif msg == "false":
        if joueur_actif and not bonne_reponse:
            result_label.config(text="MAUVAISE RÉPONSE", bg="red")
            tentative += 1
            joueur_actif = None
            if tentative >= 4:
                result_label.config(text="PERSONNE N'A TROUVÉ", bg="gray")

def listen_arduino():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        while True:
            if ser.in_waiting > 0:
                msg = ser.readline().decode(errors="ignore").strip()
                if msg:
                    serial_queue.put(msg)
    except Exception as e:
        serial_queue.put(f"ERROR:{e}")

def poll_serial_queue():
    while not serial_queue.empty():
        msg = serial_queue.get()

        if msg.startswith("ERROR:"):
            result_label.config(text=msg[6:], bg="red")
        else:
            process_serial_message(msg)

    root.after(50, poll_serial_queue)

threading.Thread(target=listen_arduino, daemon=True).start()
root.after(50, poll_serial_queue)

# INIT
set_question()
update_scores()
root.mainloop()