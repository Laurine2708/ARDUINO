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
    "Joueur 1": 0,
    "Joueur 2": 0,
    "Joueur 3": 0,
    "Joueur 4": 0
}

joueur_actif = None
event_queue = queue.Queue()

player_names = {
    "1": "Joueur 1",
    "2": "Joueur 2",
    "3": "Joueur 3",
    "4": "Joueur 4"
}

# -------- TIMER --------
TIMER_MAX = 15
timer_value = TIMER_MAX
timer_running = False
paused = False
timer_job = None

# ---------------- QUESTIONS ----------------
try:
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)["questions"]
except:
    questions = []

index_question = 0

# ---------------- UI ----------------
root = tk.Tk()
root.title("QUIZ ARDUINO BUZZER")
root.geometry("1000x700")
root.configure(bg="#0f111a")

tk.Label(root, text="QUIZ ARDUINO BUZZER",
         font=("Arial", 26, "bold"),
         bg="#0f111a", fg="white").pack(pady=10)

question_label = tk.Label(root, text="", font=("Arial", 22),
                          bg="#0f111a", fg="#00d4ff", wraplength=800)
question_label.pack(pady=10)

answer_label = tk.Label(root, text="", font=("Arial", 16),
                        bg="#0f111a", fg="#aaaaaa", wraplength=800)
answer_label.pack(pady=5)

result_label = tk.Label(root, text="", font=("Arial", 18, "bold"),
                        bg="#0f111a", fg="white")
result_label.pack()

buzzer_label = tk.Label(root, text="", font=("Arial", 14),
                        bg="#0f111a", fg="#00ff99")
buzzer_label.pack()

timer_label = tk.Label(root, text="⏱ 15",
                       font=("Arial", 18, "bold"),
                       bg="#0f111a", fg="#ffaa00")
timer_label.pack()

# BARRE
canvas = tk.Canvas(root, width=600, height=25, bg="#222", highlightthickness=0)
canvas.pack(pady=10)
bar = canvas.create_rectangle(0, 0, 600, 25, fill="green")

# ---------------- PLAYERS UI ----------------
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

def get_color_and_score(t):
    if t >= 12:
        return "green", 5
    elif t >= 9:
        return "blue", 3
    elif t >= 6:
        return "yellow", 2
    elif t >= 1:
        return "red", 1
    return "gray", 0

# ---------------- TIMER FIX STABLE ----------------

def stop_timer():
    global timer_job
    if timer_job is not None:
        root.after_cancel(timer_job)
        timer_job = None

def update_timer():
    global timer_value, timer_running, timer_job

    if not timer_running or paused or joueur_actif is not None:
        return

    timer_label.config(text=f"⏱ {timer_value}")

    width = int((timer_value / TIMER_MAX) * 600)
    color, _ = get_color_and_score(timer_value)

    canvas.coords(bar, 0, 0, width, 25)
    canvas.itemconfig(bar, fill=color)

    if timer_value > 0:
        timer_value -= 1
        timer_job = root.after(1000, update_timer)
    else:
        timer_running = False
        result_label.config(text="⏱ TEMPS ÉCOULÉ", fg="orange")
        root.after(2000, next_question)

# ---------------- QUESTIONS ----------------

def set_question():
    global timer_value, timer_running, joueur_actif, paused

    stop_timer()

    joueur_actif = None
    paused = False
    pause_btn.config(text="⏸ PAUSE", bg="#ffaa00")

    if index_question < len(questions):
        q = questions[index_question]
        question_label.config(text=q["question"])
        answer_label.config(text=q["reponse"])
    else:
        question_label.config(text="FIN DU JEU")
        answer_label.config(text="")
        return

    result_label.config(text="")
    buzzer_label.config(text="")

    timer_value = TIMER_MAX
    timer_running = True
    update_timer()

def next_question():
    global index_question, timer_running

    stop_timer()
    timer_running = False

    index_question += 1
    set_question()

def reset_questions():
    global index_question, timer_running, joueur_actif

    stop_timer()

    index_question = 0
    timer_running = False
    joueur_actif = None

    set_question()

# ---------------- PAUSE ----------------

def toggle_pause():
    global paused, timer_running

    paused = not paused

    if paused:
        timer_running = False
        pause_btn.config(text="▶ REPRENDRE", bg="#00c853")
    else:
        timer_running = True
        pause_btn.config(text="⏸ PAUSE", bg="#ffaa00")
        update_timer()

# ---------------- BUZZ ----------------

def highlight_player(name):
    buzzer_label.config(text=f"{name} a buzzé !")

# ---------------- BOUTONS ----------------
btn_frame = tk.Frame(root, bg="#0f111a")
btn_frame.pack(pady=10)

pause_btn = tk.Button(btn_frame, text="⏸ PAUSE",
                      command=toggle_pause,
                      bg="#ffaa00", fg="black",
                      font=("Arial", 12, "bold"),
                      padx=20, pady=10)
pause_btn.grid(row=0, column=0, padx=10)

tk.Button(btn_frame, text="SUIVANT",
          command=next_question,
          bg="#00aaff", fg="white",
          font=("Arial", 12, "bold"),
          padx=20, pady=10).grid(row=0, column=1, padx=10)

tk.Button(btn_frame, text="RESET QUESTIONS",
          command=reset_questions,
          bg="#ff4d4d", fg="white",
          font=("Arial", 12, "bold"),
          padx=20, pady=10).grid(row=0, column=2, padx=10)

# ---------------- ARDUINO ----------------

def listen_arduino():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(2)

        while True:
            if ser.in_waiting:
                msg = ser.readline().decode(errors="ignore").strip()
                event_queue.put(msg)
    except:
        pass

def process_events():
    global joueur_actif, timer_running

    while not event_queue.empty():
        msg = event_queue.get()

        if paused:
            continue

        # BUZZ
        if msg.startswith("BUZZ:"):
            if not timer_running or joueur_actif is not None:
                continue

            num = msg.split(":")[1]
            joueur = player_names.get(num)

            joueur_actif = joueur
            timer_running = False
            stop_timer()
            highlight_player(joueur)

        # BONNE REPONSE
        elif msg == "true":
            if joueur_actif:
                _, pts = get_color_and_score(timer_value)
                players[joueur_actif] += pts
                update_scores()

            result_label.config(text="✔ BONNE RÉPONSE", fg="green")
            root.after(1500, next_question)

        # MAUVAISE REPONSE
        elif msg == "false":
            if joueur_actif:
                players[joueur_actif] -= 1
                update_scores()

            result_label.config(text="✖ MAUVAISE RÉPONSE", fg="red")
            joueur_actif = None
            timer_running = True
            update_timer()

    root.after(50, process_events)

# ---------------- START ----------------
threading.Thread(target=listen_arduino, daemon=True).start()

set_question()
update_scores()
process_events()

root.mainloop()