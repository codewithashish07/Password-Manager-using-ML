import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from manager import generate_key, encrypt_password, decrypt_password
from database import init_db, save_password, get_all_passwords, delete_password
from ml_model import predict_strength, train_model
from breach_check import check_breach
from generator import generate_password, calculate_entropy, suggest_passwords

# ── Setup ──────────────────────────────────────────────
generate_key()
init_db()
train_model()

# ── Colors ─────────────────────────────────────────────
BG      = "#1e1e2e"
SIDEBAR = "#181825"
CARD    = "#2a2a3e"
PURPLE  = "#7c3aed"
LPURPLE = "#a78bfa"
TEXT    = "#cdd6f4"
MUTED   = "#6c7086"
GREEN   = "#a6e3a1"
YELLOW  = "#f9e2af"
RED     = "#f38ba8"
BLUE    = "#89b4fa"

# ── Root Window ────────────────────────────────────────
root = tk.Tk()
root.title("ML Password Manager — Ashish and Harsh")
root.geometry("820x580")
root.configure(bg=BG)
root.resizable(False, False)

# ── Helpers ────────────────────────────────────────────
def lbl(parent, text, size=11, color=TEXT, bold=False, bg=None):
    bg = bg or parent["bg"]
    w  = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=bg, fg=color,
                    font=("Segoe UI", size, w))

def entry(parent, show=None, width=32):
    e = tk.Entry(parent, bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Segoe UI", 11),
                 highlightthickness=1, highlightbackground=MUTED,
                 highlightcolor=PURPLE, width=width)
    if show:
        e.config(show=show)
    return e

def btn(parent, text, cmd, bg=PURPLE, fg="white", w=16, pad=6):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     font=("Segoe UI", 10, "bold"), relief="flat",
                     padx=10, pady=pad, cursor="hand2", width=w,
                     activebackground=MUTED, activeforeground="white")

# ── Animated Page Transition ───────────────────────────
current_alpha = [1.0]

def fade_transition(callback):
    """Fade out → switch content → fade in"""
    def fade_out(alpha=1.0):
        if alpha >= 0:
            # Simulate fade by rapidly clearing and redrawing
            content_frame.configure(bg=BG)
            for w in content_frame.winfo_children():
                try:
                    w.configure(bg=BG, fg=BG)
                except:
                    pass
            alpha = round(alpha - 0.25, 2)
            root.after(30, lambda: fade_out(alpha))
        else:
            clear_content()
            callback()
            fade_in()

    def fade_in(step=0):
        colors = [BG, "#22223a", "#262640", "#2a2a3e", BG]
        if step < 5:
            content_frame.configure(bg=colors[step % len(colors)])
            root.after(40, lambda: fade_in(step + 1))

    fade_out()

def clear_content():
    for w in content_frame.winfo_children():
        w.destroy()

# ── Sidebar Nav Highlight ──────────────────────────────
nav_btns = {}

def set_active(name):
    for n, b in nav_btns.items():
        if n == name:
            b.configure(bg=CARD, fg=LPURPLE,
                        font=("Segoe UI", 10, "bold"))
        else:
            b.configure(bg=SIDEBAR, fg=TEXT,
                        font=("Segoe UI", 10, "normal"))

# ── Live Strength Meter ────────────────────────────────
def make_strength_meter(parent):
    """Returns (frame, update_function)"""
    frame = tk.Frame(parent, bg=BG)

    bar_bg = tk.Frame(frame, bg=CARD, height=6, width=340)
    bar_bg.pack(fill="x", pady=(4, 2))
    bar_bg.pack_propagate(False)

    bar_fill = tk.Frame(bar_bg, bg=RED, height=6, width=0)
    bar_fill.place(x=0, y=0, height=6)

    info_row = tk.Frame(frame, bg=BG)
    info_row.pack(fill="x")
    strength_lbl = lbl(info_row, "Type a password...", 9, MUTED)
    strength_lbl.pack(side="left")
    entropy_lbl  = lbl(info_row, "", 9, MUTED)
    entropy_lbl.pack(side="right")

    def animate_bar(target_w, current_w=0, color=RED):
        if current_w < target_w:
            current_w = min(current_w + 8, target_w)
            bar_fill.place(x=0, y=0, height=6, width=current_w)
            root.after(12, lambda: animate_bar(target_w, current_w, color))
        bar_fill.configure(bg=color)

    def update(password):
        if not password:
            animate_bar(0)
            strength_lbl.configure(text="Type a password...", fg=MUTED)
            entropy_lbl.configure(text="")
            return
        result  = predict_strength(password)
        entropy = calculate_entropy(password)
        total_w = 340
        widths  = {0: int(total_w * 0.25),
                   1: int(total_w * 0.65),
                   2: total_w}
        colors  = {0: RED, 1: YELLOW, 2: GREEN}
        animate_bar(widths[result["raw"]], color=colors[result["raw"]])
        strength_lbl.configure(text=f"{result['label']}  "
                               f"(confidence: {result['score']})",
                               fg=colors[result["raw"]])
        entropy_lbl.configure(text=f"Entropy: {entropy} bits", fg=MUTED)

    return frame, update

# ── Typing Animation ───────────────────────────────────
def type_text(widget, text, delay=18):
    widget.configure(state="normal")
    widget.delete(0, tk.END)
    def _type(i=0):
        if i <= len(text):
            widget.delete(0, tk.END)
            widget.insert(0, text[:i])
            root.after(delay, lambda: _type(i + 1))
    _type()

# ── Toast Notification ─────────────────────────────────
def toast(message, color=GREEN):
    t = tk.Toplevel(root)
    t.overrideredirect(True)
    t.attributes("-topmost", True)
    t.configure(bg=CARD)
    rx = root.winfo_x() + root.winfo_width()  - 320
    ry = root.winfo_y() + root.winfo_height() - 70
    t.geometry(f"300x46+{rx}+{ry}")
    tk.Label(t, text=message, bg=CARD, fg=color,
             font=("Segoe UI", 10, "bold"),
             padx=16).pack(expand=True)
    # Slide in
    def slide(y_offset=40):
        if y_offset > 0:
            t.geometry(f"300x46+{rx}+{ry + y_offset}")
            root.after(15, lambda: slide(y_offset - 4))
    slide()
    root.after(2200, t.destroy)

# ══════════════════════════════════════════════════════
# PAGE 1 — ADD PASSWORD
# ══════════════════════════════════════════════════════
def show_add():
    set_active("add")
    fade_transition(_build_add)

def _build_add():
    lbl(content_frame, "Add New Password", 16, TEXT, True).pack(
        anchor="w", pady=(0, 4))
    lbl(content_frame, "Encrypt & store with ML strength analysis",
        10, MUTED).pack(anchor="w", pady=(0, 16))

    # Site
    lbl(content_frame, "WEBSITE / APP", 9, MUTED).pack(anchor="w")
    site_e = entry(content_frame)
    site_e.pack(anchor="w", pady=(3, 10))

    # Username
    lbl(content_frame, "USERNAME / EMAIL", 9, MUTED).pack(anchor="w")
    user_e = entry(content_frame)
    user_e.pack(anchor="w", pady=(3, 10))

    # Password row
    lbl(content_frame, "PASSWORD", 9, MUTED).pack(anchor="w")
    pw_row = tk.Frame(content_frame, bg=BG)
    pw_row.pack(anchor="w", pady=(3, 4))
    pw_e = entry(pw_row, show="•", width=28)
    pw_e.pack(side="left")

    show_var = tk.BooleanVar()
    def toggle():
        pw_e.config(show="" if show_var.get() else "•")
    tk.Checkbutton(pw_row, text="Show", variable=show_var,
                   command=toggle, bg=BG, fg=MUTED,
                   selectcolor=CARD,
                   font=("Segoe UI", 9),
                   activebackground=BG).pack(side="left", padx=8)

    # Live strength meter
    meter_frame, update_meter = make_strength_meter(content_frame)
    meter_frame.pack(anchor="w", fill="x", pady=(4, 12))

    # Bind live update
    def on_type(event=None):
        update_meter(pw_e.get())
    pw_e.bind("<KeyRelease>", on_type)

    breach_lbl = lbl(content_frame, "", 9, MUTED)
    breach_lbl.pack(anchor="w", pady=(0, 10))

    def check_b():
        pw = pw_e.get()
        if not pw:
            return
        breach_lbl.configure(text="Checking breach database...", fg=MUTED)
        def _check():
            result = check_breach(pw)
            if result.get("breached"):
                breach_lbl.configure(
                    text=f"⚠  Found {result['count']} times in breaches!",
                    fg=RED)
            else:
                breach_lbl.configure(
                    text="✓  Not found in any known breaches", fg=GREEN)
        threading.Thread(target=_check, daemon=True).start()

    def auto_gen():
        pw = generate_password()
        type_text(pw_e, pw)
        root.after(500, lambda: update_meter(pw))
        root.after(600, check_b)

    def save():
        site = site_e.get().strip()
        user = user_e.get().strip()
        pw   = pw_e.get().strip()
        if not site or not user or not pw:
            toast("⚠  Please fill all fields!", RED)
            return
        strength  = predict_strength(pw)
        encrypted = encrypt_password(pw)
        save_password(site, user, encrypted, strength["raw"])
        toast(f"✓  Password for {site} saved!")
        site_e.delete(0, tk.END)
        user_e.delete(0, tk.END)
        pw_e.delete(0, tk.END)
        update_meter("")
        breach_lbl.configure(text="")
        refresh_count()

    btn_row = tk.Frame(content_frame, bg=BG)
    btn_row.pack(anchor="w")
    btn(btn_row, "💾  Save", save, w=12).pack(side="left", padx=(0, 8))
    btn(btn_row, "✨  Generate", auto_gen, CARD, LPURPLE, 14).pack(
        side="left", padx=(0, 8))
    btn(btn_row, "🔍  Check Breach", check_b, CARD, YELLOW, 16).pack(
        side="left")

# ══════════════════════════════════════════════════════
# PAGE 2 — VIEW + SEARCH
# ══════════════════════════════════════════════════════
def show_view():
    set_active("view")
    fade_transition(_build_view)

def _build_view():
    lbl(content_frame, "All Saved Passwords", 16, TEXT, True).pack(
        anchor="w", pady=(0, 4))

    # Search bar
    search_row = tk.Frame(content_frame, bg=BG)
    search_row.pack(fill="x", pady=(0, 12))
    lbl(search_row, "🔍", 12, MUTED, bg=BG).pack(side="left", padx=(0, 6))
    search_e = entry(search_row, width=36)
    search_e.pack(side="left")
    lbl(search_row, "  Filter:", 10, MUTED, bg=BG).pack(side="left", padx=(12, 4))
    filter_var = tk.StringVar(value="All")
    filter_cb  = ttk.Combobox(search_row, textvariable=filter_var,
                               values=["All", "Strong 🟢", "Medium 🟡", "Weak 🔴"],
                               width=12, state="readonly")
    filter_cb.pack(side="left")

    # Table
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=30,
                    font=("Segoe UI", 10))
    style.configure("Treeview.Heading", background=SIDEBAR,
                    foreground=LPURPLE,
                    font=("Segoe UI", 10, "bold"))
    style.map("Treeview", background=[("selected", PURPLE)])

    cols = ("ID", "Site", "Username", "Strength", "Created")
    tree = ttk.Treeview(content_frame, columns=cols,
                        show="headings", height=10)
    widths = {"ID": 40, "Site": 160, "Username": 190,
              "Strength": 110, "Created": 130}
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=widths[c],
                    anchor="center" if c in ("ID","Strength") else "w")
    tree.pack(fill="both", expand=True)

    smap = {0: "Weak 🔴", 1: "Medium 🟡", 2: "Strong 🟢"}

    def load_data(filter_str="All", search=""):
        tree.delete(*tree.get_children())
        for row in get_all_passwords():
            s = smap.get(int(row[4] or 0), "Unknown")
            created = str(row[5])[:10] if len(row) > 5 else ""
            if filter_str != "All" and filter_str not in s:
                continue
            if search and search.lower() not in row[1].lower() \
                      and search.lower() not in row[2].lower():
                continue
            tree.insert("", "end", values=(row[0], row[1], row[2], s, created))

    load_data()

    def on_search(*_):
        load_data(filter_var.get(), search_e.get())

    search_e.bind("<KeyRelease>", on_search)
    filter_cb.bind("<<ComboboxSelected>>", on_search)

    # Double click to copy password
    def on_double_click(event):
        item = tree.focus()
        if not item:
            return
        rid = int(tree.item(item)["values"][0])
        for row in get_all_passwords():
            if row[0] == rid:
                plain = decrypt_password(row[3])
                root.clipboard_clear()
                root.clipboard_append(plain)
                toast("📋  Password copied to clipboard!")
                return

    tree.bind("<Double-1>", on_double_click)
    lbl(content_frame, "💡  Double-click any row to copy its password",
        9, MUTED).pack(anchor="w", pady=(6, 0))

# ══════════════════════════════════════════════════════
# PAGE 3 — DASHBOARD
# ══════════════════════════════════════════════════
def show_dashboard():
    set_active("dash")
    fade_transition(_build_dashboard)

def _build_dashboard():
    lbl(content_frame, "Password Health Dashboard", 16, TEXT, True).pack(
        anchor="w", pady=(0, 4))
    lbl(content_frame, "Overview of your password security",
        10, MUTED).pack(anchor="w", pady=(0, 16))

    records = get_all_passwords()
    total   = len(records)
    strong  = sum(1 for r in records if int(r[4] or 0) == 2)
    medium  = sum(1 for r in records if int(r[4] or 0) == 1)
    weak    = sum(1 for r in records if int(r[4] or 0) == 0)
    score   = int((strong * 100 + medium * 50) / total) if total else 0

    # Metric cards
    card_row = tk.Frame(content_frame, bg=BG)
    card_row.pack(fill="x", pady=(0, 16))

    def metric_card(parent, title, value, color):
        f = tk.Frame(parent, bg=CARD, padx=16, pady=12,
                     highlightthickness=1,
                     highlightbackground=color)
        f.pack(side="left", expand=True, fill="x", padx=(0, 10))
        lbl(f, title, 9, MUTED, bg=CARD).pack(anchor="w")
        lbl(f, str(value), 22, color, True, CARD).pack(anchor="w")
        return f

    metric_card(card_row, "Total Saved",   total,  BLUE)
    metric_card(card_row, "Strong",        strong, GREEN)
    metric_card(card_row, "Medium",        medium, YELLOW)
    metric_card(card_row, "Weak",          weak,   RED)

    # Health score bar
    lbl(content_frame, "OVERALL SECURITY SCORE", 9, MUTED).pack(anchor="w")
    bar_bg = tk.Frame(content_frame, bg=CARD, height=20, width=580)
    bar_bg.pack(anchor="w", pady=(4, 2))
    bar_bg.pack_propagate(False)
    score_color = GREEN if score > 70 else YELLOW if score > 40 else RED
    bar_fill = tk.Frame(bar_bg, bg=score_color, height=20, width=0)
    bar_fill.place(x=0, y=0, height=20)
    lbl(content_frame, f"{score}% security score", 10, score_color).pack(
        anchor="w", pady=(0, 16))

    # Animate score bar
    def animate(w=0):
        target = int(580 * score / 100)
        if w < target:
            bar_fill.place(x=0, y=0, height=20, width=w)
            root.after(8, lambda: animate(w + 4))
        else:
            bar_fill.place(x=0, y=0, height=20, width=target)
    animate()

    # Strength breakdown chart (canvas bars)
    lbl(content_frame, "STRENGTH BREAKDOWN", 9, MUTED).pack(
        anchor="w", pady=(0, 6))
    chart = tk.Canvas(content_frame, bg=BG, height=130,
                      width=580, highlightthickness=0)
    chart.pack(anchor="w")

    categories = [("Strong", strong, GREEN),
                  ("Medium", medium, YELLOW),
                  ("Weak",   weak,   RED)]
    bar_w  = 100
    gap    = 60
    start_x = 60

    def draw_bars(step=0):
        chart.delete("all")
        max_val = max(total, 1)
        for i, (label, val, color) in enumerate(categories):
            x     = start_x + i * (bar_w + gap)
            max_h = 80
            h     = int((val / max_val) * max_h * min(step / 20, 1))
            y_top = 90 - h
            chart.create_rectangle(x, y_top, x + bar_w, 90,
                                   fill=color, outline="")
            chart.create_text(x + bar_w // 2, 105,
                              text=label, fill=TEXT,
                              font=("Segoe UI", 10))
            chart.create_text(x + bar_w // 2, y_top - 10,
                              text=str(val), fill=color,
                              font=("Segoe UI", 10, "bold"))
        if step < 20:
            root.after(30, lambda: draw_bars(step + 1))

    draw_bars()

# ══════════════════════════════════════════════════════
# PAGE 4 — SUGGEST
# ══════════════════════════════════════════════════════
def show_suggest():
    set_active("suggest")
    fade_transition(_build_suggest)

def _build_suggest():
    lbl(content_frame, "Password Generator", 16, TEXT, True).pack(
        anchor="w", pady=(0, 4))
    lbl(content_frame, "ML-scored cryptographically secure suggestions",
        10, MUTED).pack(anchor="w", pady=(0, 16))

    list_frame = tk.Frame(content_frame, bg=BG)
    list_frame.pack(fill="both", expand=True)

    def generate(animate=True):
        for w in list_frame.winfo_children():
            w.destroy()
        passwords = suggest_passwords(5)

        def add_row(i, pw):
            entropy  = calculate_entropy(pw)
            strength = predict_strength(pw)
            colors   = {0: RED, 1: YELLOW, 2: GREEN}
            c        = colors[strength["raw"]]

            row = tk.Frame(list_frame, bg=CARD, pady=10, padx=14,
                           highlightthickness=1, highlightbackground=CARD)
            row.pack(fill="x", pady=3)

            pw_lbl = tk.Label(row, text=pw, bg=CARD, fg=c,
                              font=("Courier New", 11, "bold"))
            pw_lbl.pack(side="left")

            info = f"{strength['label']}  |  {entropy} bits"
            tk.Label(row, text=info, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=12)

            def copy_pw(p=pw):
                root.clipboard_clear()
                root.clipboard_append(p)
                toast("📋  Password copied!")

            tk.Button(row, text="Copy", command=copy_pw,
                      bg=PURPLE, fg="white", relief="flat",
                      font=("Segoe UI", 9, "bold"),
                      padx=10, cursor="hand2").pack(side="right")

            if animate:
                row.configure(bg=BG)
                def fade_card(r=row, step=0):
                    shades = [BG, "#22223a", "#262640", CARD]
                    if step < len(shades):
                        r.configure(bg=shades[step])
                        for c_ in r.winfo_children():
                            try:
                                c_.configure(bg=shades[step])
                            except:
                                pass
                        root.after(40, lambda: fade_card(r, step + 1))
                root.after(i * 120, fade_card)

        for i, pw in enumerate(passwords):
            add_row(i, pw)

    generate()
    btn(content_frame, "🔄  Regenerate", lambda: generate(True),
        w=14).pack(anchor="w", pady=12)

# ══════════════════════════════════════════════════════
# PAGE 5 — DELETE
# ══════════════════════════════════════════════════════
def show_delete():
    set_active("delete")
    fade_transition(_build_delete)

def _build_delete():
    lbl(content_frame, "Delete Password", 16, TEXT, True).pack(
        anchor="w", pady=(0, 16))

    lbl(content_frame, "RECORD ID", 9, MUTED).pack(anchor="w")
    id_e = entry(content_frame, width=10)
    id_e.pack(anchor="w", pady=(3, 12))

    def delete():
        try:
            rid = int(id_e.get())
            if messagebox.askyesno("Confirm",
                    f"Delete record ID {rid}? This cannot be undone."):
                delete_password(rid)
                toast(f"🗑  Record {rid} deleted.", RED)
                id_e.delete(0, tk.END)
                refresh_count()
        except ValueError:
            toast("⚠  Enter a valid numeric ID.", RED)

    btn(content_frame, "🗑  Delete", delete, RED, "white", 12).pack(
        anchor="w")

# ══════════════════════════════════════════════════════
# LAYOUT
# ═════════════════════════════════════════════════════

# ── Sidebar ────────────────────────────────────────────
sidebar_frame = tk.Frame(root, bg=SIDEBAR, width=180)
sidebar_frame.pack(side="left", fill="y")
sidebar_frame.pack_propagate(False)

tk.Label(sidebar_frame, text="🔐", bg=SIDEBAR, fg=PURPLE,
         font=("Segoe UI", 28)).pack(pady=(20, 2))
tk.Label(sidebar_frame, text="ML Password", bg=SIDEBAR, fg=TEXT,
         font=("Segoe UI", 11, "bold")).pack()

count_lbl = tk.Label(sidebar_frame, text="", bg=SIDEBAR,
                     fg=MUTED, font=("Segoe UI", 9))
count_lbl.pack(pady=(2, 16))

def refresh_count():
    n = len(get_all_passwords())
    count_lbl.configure(text=f"{n} password{'s' if n != 1 else ''} saved")

refresh_count()

ttk.Separator(sidebar_frame, orient="horizontal").pack(
    fill="x", padx=14, pady=6)

nav_items = [
    ("add",     "➕   Add Password",   show_add),
    ("view",    "📋   View All",        show_view),
    ("dash",    "📊   Dashboard",       show_dashboard),
    ("suggest", "✨   Suggest",         show_suggest),
    ("delete",  "🗑    Delete",         show_delete),
]

for key, label, cmd in nav_items:
    b = tk.Button(sidebar_frame, text=label, command=cmd,
                  bg=SIDEBAR, fg=TEXT, relief="flat",
                  font=("Segoe UI", 10), anchor="w",
                  padx=18, pady=9, cursor="hand2",
                  activebackground=CARD,
                  activeforeground=LPURPLE)
    b.pack(fill="x")
    nav_btns[key] = b

# ── Content ────────────────────────────────────────────
content_frame = tk.Frame(root, bg=BG, padx=28, pady=22)
content_frame.pack(side="left", fill="both", expand=True)

# Start on Add page
show_add()
root.mainloop()