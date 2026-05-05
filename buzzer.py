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

player_names = {
    "1": "Joueur 1",
    "2": "Joueur 2",
    "3": "Joueur 3",
    "4": "Joueur 4"
}

joueur_actif = None
event_queue = queue.Queue()

# ---------------- TIMER ----------------
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
wrong_attempts = 0

# ---------------- UI ----------------
root = tk.Tk()
root.title("QUIZ ARDUINO BUZZER")
root.geometry("1200x700")
root.configure(bg="#0f111a")

# ================= LEFT =================
left_frame = tk.Frame(root, bg="#0f111a")
left_frame.pack(side="left", fill="both", expand=True)

# ================= RIGHT =================
right_frame = tk.Frame(root, bg="#1b1f2a", width=250)
right_frame.pack(side="right", fill="y")

# ---------------- TITLE ----------------
tk.Label(left_frame, text="QUIZ ARDUINO BUZZER",
         font=("Arial", 26, "bold"),
         bg="#0f111a", fg="white").pack(pady=10)

# ---------------- QUESTION ----------------
question_frame = tk.Frame(left_frame, bg="#1b1f2a",
                          highlightthickness=2,
                          highlightbackground="#2c3142")
question_frame.pack(pady=20, ipadx=25, ipady=25)

question_label = tk.Label(question_frame, text="",
                          font=("Arial", 24, "bold"),
                          bg="#1b1f2a", fg="#00d4ff",
                          wraplength=600)
question_label.pack()

answer_label = tk.Label(question_frame, text="",
                        font=("Arial", 18),
                        bg="#1b1f2a", fg="#aaaaaa",
                        wraplength=600)
answer_label.pack(pady=10)

result_label = tk.Label(left_frame, text="",
                        font=("Arial", 20, "bold"),
                        bg="#0f111a", fg="white")
result_label.pack(pady=5)

buzzer_label = tk.Label(left_frame, text="",
                        font=("Arial", 16, "bold"),
                        bg="#0f111a", fg="#00ff99")
buzzer_label.pack(pady=5)

timer_label = tk.Label(left_frame, text="⏱ 15",
                       font=("Arial", 18, "bold"),
                       bg="#0f111a", fg="#ffaa00")
timer_label.pack(pady=5)

# ---------------- BAR ----------------
canvas = tk.Canvas(left_frame, width=500, height=25, bg="#222", highlightthickness=0)
canvas.pack(pady=10)
bar = canvas.create_rectangle(0, 0, 500, 25, fill="green")

# ---------------- PROPOSITIONS ----------------
choices_frame = tk.Frame(left_frame, bg="#0f111a")
choices_frame.pack(pady=10)

choice_labels = []

def show_choices(propositions):
    for w in choice_labels:
        w.destroy()
    choice_labels.clear()

    for p in propositions:
        lbl = tk.Label(choices_frame,
                       text=p,
                       font=("Arial", 14, "bold"),
                       bg="#1b1f2a",
                       fg="white",
                       width=35,
                       pady=5)
        lbl.pack(pady=3)
        choice_labels.append(lbl)

def show_choices_progressive():
    q = questions[index_question]
    props = q["propositions"]

    remaining = max(1, 4 - wrong_attempts)
    show_choices(props[:remaining])

# ---------------- PLAYERS ----------------
frame_players = tk.Frame(left_frame, bg="#0f111a")
frame_players.pack(pady=20)

player_frames = {}

def create_card(name, col):
    card = tk.Frame(frame_players, bg="#1b1f2a",
                    width=180, height=120,
                    highlightthickness=2,
                    highlightbackground="#2c3142")
    card.grid(row=0, column=col, padx=10)
    card.pack_propagate(False)

    tk.Label(card, text=name,
             font=("Arial", 12, "bold"),
             bg="#1b1f2a", fg="white").pack(pady=5)

    score = tk.Label(card, text="0",
                     font=("Arial", 24, "bold"),
                     bg="#1b1f2a", fg="#00ff99")
    score.pack()

    player_frames[name] = score

for i, p in enumerate(players):
    create_card(p, i)

# ---------------- CLASSEMENT ----------------
tk.Label(right_frame,
         text="🏆 CLASSEMENT",
         font=("Arial", 16, "bold"),
         bg="#1b1f2a",
         fg="white").pack(pady=15)

ranking_labels = {}

# ---------------- LOGIQUE ----------------

def update_scores():
    for p in players:
        player_frames[p].config(text=str(players[p]))
    update_ranking()

def update_ranking():
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)

    for w in ranking_labels.values():
        w.destroy()
    ranking_labels.clear()

    for i, (name, score) in enumerate(sorted_players):
        lbl = tk.Label(right_frame,
                       text=f"{i+1}: {name} : {score}",
                       font=("Arial", 12, "bold"),
                       bg="#1b1f2a",
                       fg="white",
                       anchor="w")
        lbl.pack(anchor="w", padx=10, pady=2)
        ranking_labels[name] = lbl

def get_score(t):
    if t >= 12:
        return 5
    elif t >= 9:
        return 3
    elif t >= 6:
        return 2
    elif t >= 1:
        return 1
    return 0

def clear_ui():
    result_label.config(text="", bg="#0f111a")
    buzzer_label.config(text="")

def stop_timer():
    global timer_job
    if timer_job:
        root.after_cancel(timer_job)

# ---------------- TIMER ----------------

def update_timer():
    global timer_value, timer_running, timer_job

    if not timer_running or paused or joueur_actif:
        return

    timer_label.config(text=f"⏱ {timer_value}")

    width = int((timer_value / TIMER_MAX) * 500)
    canvas.coords(bar, 0, 0, width, 25)

    if timer_value > 0:
        timer_value -= 1
        timer_job = root.after(1000, update_timer)
    else:
        timer_running = False
        result_label.config(text="⏱ TEMPS ÉCOULÉ", fg="orange")
        root.after(1500, next_question)

# ---------------- QUESTIONS ----------------

def set_question():
    global timer_value, timer_running, joueur_actif, paused, wrong_attempts

    stop_timer()
    joueur_actif = None
    paused = False
    wrong_attempts = 0

    clear_ui()

    if index_question < len(questions):
        q = questions[index_question]

        question_label.config(text=q["question"])
        answer_label.config(text="")

        for w in choice_labels:
            w.destroy()
        choice_labels.clear()

    else:
        question_label.config(text="FIN DU JEU")
        answer_label.config(text="")
        return

    timer_value = TIMER_MAX
    timer_running = True
    update_timer()

def next_question():
    global index_question, timer_running

    stop_timer()
    timer_running = False

    index_question += 1
    set_question()

# ---------------- RESET ----------------

def reset_quiz():
    global index_question, timer_value, timer_running, joueur_actif, paused, wrong_attempts

    stop_timer()

    index_question = 0
    timer_value = TIMER_MAX
    timer_running = False
    paused = False
    joueur_actif = None
    wrong_attempts = 0

    for p in players:
        players[p] = 0

    update_scores()
    clear_ui()
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

def show_buzz(name):
    buzzer_label.config(text=f"🔥 {name} a buzzé !")

# ---------------- BOUTONS ----------------

btn_frame = tk.Frame(left_frame, bg="#0f111a")
btn_frame.pack(pady=10)

pause_btn = tk.Button(btn_frame, text="⏸ PAUSE",
                      command=toggle_pause,
                      bg="#ffaa00", fg="black",
                      font=("Arial", 12, "bold"),
                      padx=15, pady=8)
pause_btn.grid(row=0, column=0, padx=5)

tk.Button(btn_frame, text="SUIVANT",
          command=next_question,
          bg="#00aaff", fg="white",
          font=("Arial", 12, "bold"),
          padx=15, pady=8).grid(row=0, column=1, padx=5)

tk.Button(btn_frame, text="RESET QUIZ",
          command=reset_quiz,
          bg="#ff4d4d", fg="white",
          font=("Arial", 12, "bold"),
          padx=15, pady=8).grid(row=0, column=2, padx=5)

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
    global joueur_actif, timer_running, wrong_attempts

    while not event_queue.empty():
        msg = event_queue.get()

        if paused:
            continue

        if msg.startswith("BUZZ:"):
            if not timer_running or joueur_actif:
                continue

            num = msg.split(":")[1]
            joueur = player_names.get(num)

            joueur_actif = joueur
            timer_running = False
            show_buzz(joueur)

        elif msg == "true":
            if joueur_actif:
                players[joueur_actif] += get_score(timer_value)
                update_scores()

            result_label.config(text="✔ BONNE RÉPONSE", fg="green")
            root.after(1200, next_question)

        elif msg == "false":
            if joueur_actif:
                players[joueur_actif] -= 1
                update_scores()

            result_label.config(text="✖ MAUVAISE RÉPONSE", fg="red")

            joueur_actif = None
            wrong_attempts += 1

            show_choices_progressive()

            root.after(1200, clear_ui)

            timer_running = True
            update_timer()

    root.after(50, process_events)

# ---------------- START ----------------
threading.Thread(target=listen_arduino, daemon=True).start()

set_question()
update_scores()
process_events()

root.mainloop()