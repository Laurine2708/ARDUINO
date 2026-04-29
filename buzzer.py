import tkinter as tk
import serial
import threading
import time
import json
import queue

# ---------------- CONFIG ----------------
PORT = "COM10"
BAUDRATE = 9600

# ---------------- DATA ----------------
players = {
    "Joueur1": 0,
    "Joueur2": 0,
    "Joueur3": 0,
    "Joueur4": 0
}

points = [5, 3, 2, 1]
tentative = 0
joueur_actif = None
bonne_reponse = False

player_names = {
    "1": "Joueur1",
    "2": "Joueur2",
    "3": "Joueur3",
    "4": "Joueur4"
}

event_queue = queue.Queue()

# ---------------- QUESTIONS ----------------
try:
    with open("questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        questions = data["questions"]
except Exception as e:
    print("Erreur JSON :", e)
    questions = []

index_question = 0

# ---------------- UI ----------------
root = tk.Tk()
root.title("QUIZ ARDUINO BUZZER")
root.geometry("1000x650")
root.configure(bg="#0f111a")

tk.Label(root, text="QUIZ ARDUINO BUZZER",
         font=("Arial", 26, "bold"),
         bg="#0f111a", fg="white").pack(pady=10)

# QUESTION
question_frame = tk.Frame(root, bg="#1b1f2a",
                          highlightthickness=2,
                          highlightbackground="#2c3142")
question_frame.pack(pady=20, ipadx=25, ipady=25)

question_label = tk.Label(question_frame, text="",
                          font=("Arial", 24, "bold"),
                          bg="#1b1f2a", fg="#00d4ff",
                          wraplength=700)
question_label.pack()

answer_label = tk.Label(question_frame, text="",
                        font=("Arial", 18, "italic"),
                        bg="#1b1f2a", fg="#aaaaaa",
                        wraplength=700)
answer_label.pack(pady=10)

# RESULT
result_label = tk.Label(root, text="",
                        font=("Arial", 20, "bold"),
                        bg="#0f111a", fg="white")
result_label.pack(pady=5)

# BUZZ
buzzer_label = tk.Label(root, text="",
                        font=("Arial", 16, "bold"),
                        bg="#0f111a", fg="#00ff99")
buzzer_label.pack(pady=5)

# PLAYERS
frame_players = tk.Frame(root, bg="#0f111a")
frame_players.pack(pady=25)

player_frames = {}

def create_card(name, col):
    card = tk.Frame(frame_players, bg="#1b1f2a",
                    width=200, height=140,
                    highlightthickness=2,
                    highlightbackground="#2c3142")
    card.grid(row=0, column=col, padx=15)
    card.pack_propagate(False)

    tk.Label(card, text=name,
             font=("Arial", 14, "bold"),
             bg="#1b1f2a", fg="white").pack(pady=10)

    score = tk.Label(card, text="0",
                     font=("Arial", 28, "bold"),
                     bg="#1b1f2a", fg="#00ff99")
    score.pack()

    player_frames[name] = {"card": card, "score": score}

for i, p in enumerate(players):
    create_card(p, i)

# ---------------- LOGIQUE ----------------

def update_scores():
    for p in players:
        player_frames[p]["score"].config(text=str(players[p]))

def set_question():
    global tentative, bonne_reponse, joueur_actif

    tentative = 0
    bonne_reponse = False
    joueur_actif = None

    if index_question < len(questions):
        question_label.config(text=questions[index_question]["question"])
        answer_label.config(text=questions[index_question]["reponse"])
    else:
        question_label.config(text="FIN DU JEU")
        answer_label.config(text="")

    result_label.config(text="", bg="#0f111a")
    buzzer_label.config(text="")

def highlight_player(name):
    for p in player_frames:
        player_frames[p]["card"].config(highlightbackground="#2c3142")

    if name in player_frames:
        player_frames[name]["card"].config(highlightbackground="#00d4ff")

    buzzer_label.config(text=f"{name} a buzzé !")

def reset_game():
    global index_question, tentative, joueur_actif

    for p in players:
        players[p] = 0

    index_question = 0
    tentative = 0
    joueur_actif = None

    update_scores()
    set_question()

def next_question():
    global index_question
    index_question += 1
    set_question()

# ---------------- BOUTONS ----------------
btn_frame = tk.Frame(root, bg="#0f111a")
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="RESET",
          command=reset_game,
          bg="#ff4d4d", fg="white",
          font=("Arial", 12, "bold"),
          padx=20, pady=10).grid(row=0, column=0, padx=10)

tk.Button(btn_frame, text="QUESTION SUIVANTE",
          command=next_question,
          bg="#00aaff", fg="white",
          font=("Arial", 12, "bold"),
          padx=20, pady=10).grid(row=0, column=1, padx=10)

# ---------------- ARDUINO ----------------

def listen_arduino():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)
        print("Arduino connecté")

        while True:
            if ser.in_waiting > 0:
                msg = ser.readline().decode(errors="ignore").strip()
                event_queue.put(msg)

    except Exception as e:
        print("Erreur série:", e)

# ---------------- EVENT HANDLER ----------------

def process_events():
    global joueur_actif, tentative, bonne_reponse

    while not event_queue.empty():
        msg = event_queue.get()
        print("Event:", msg)

        # BUZZ
        if msg.startswith("BUZZ:"):
            num = msg.split(":")[1].strip()
            joueur = player_names.get(num, num)

            joueur_actif = joueur
            highlight_player(joueur)

        # BONNE REPONSE
        elif msg == "true":
            if joueur_actif and joueur_actif in players:
                if tentative == 0:
                    players[joueur_actif] += 5
                else:
                    players[joueur_actif] += points[min(tentative-1, len(points)-1)]

                update_scores()

            result_label.config(text="✔ BONNE RÉPONSE",
                                bg="green", fg="white")

            bonne_reponse = True

            root.after(1500, lambda: result_label.config(text="", bg="#0f111a"))
            root.after(2000, next_question)

        # MAUVAISE REPONSE
        elif msg == "false":
            if joueur_actif and joueur_actif in players:
                players[joueur_actif] -= 1
                update_scores()

            result_label.config(text="✖ MAUVAISE RÉPONSE",
                                bg="red", fg="white")

            tentative += 1
            joueur_actif = None

            root.after(1500, lambda: result_label.config(text="", bg="#0f111a"))

    root.after(50, process_events)

# ---------------- START ----------------
threading.Thread(target=listen_arduino, daemon=True).start()

set_question()
update_scores()
process_events()

print("Interface prête")
root.mainloop()