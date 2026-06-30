import re
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, jsonify

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DB_PATH = BASE_DIR / "birthday_site.db"
ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTS = {"mp4", "webm", "mov", "m4v"}
MAX_CONTENT_LENGTH = 250 * 1024 * 1024

app = Flask(__name__)
app.secret_key = "birthday-wish-secret-key"
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            recipient_name TEXT NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT,
            intro_text TEXT,
            accent_color TEXT,
            secondary_color TEXT,
            background_style TEXT,
            surprise_prompt TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_id INTEGER NOT NULL,
            sender_name TEXT NOT NULL,
            message_text TEXT NOT NULL,
            FOREIGN KEY(party_id) REFERENCES parties(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            media_type TEXT NOT NULL,
            original_name TEXT NOT NULL,
            FOREIGN KEY(party_id) REFERENCES parties(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def slugify(text: str) -> str:
    text = (text or "party").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "party"


def unique_slug(recipient_name: str) -> str:
    base = slugify(recipient_name)
    return f"{base}-{uuid.uuid4().hex[:6]}"


def allowed_file(filename, media_kind=None):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if media_kind == "image":
        return ext in ALLOWED_IMAGE_EXTS
    if media_kind == "video":
        return ext in ALLOWED_VIDEO_EXTS
    return ext in ALLOWED_IMAGE_EXTS.union(ALLOWED_VIDEO_EXTS)


def party_with_children(slug: str):
    conn = get_db()
    party = conn.execute("SELECT * FROM parties WHERE slug = ?", (slug,)).fetchone()
    if not party:
        conn.close()
        return None
    messages = conn.execute(
        "SELECT sender_name, message_text FROM messages WHERE party_id = ? ORDER BY id ASC",
        (party["id"],),
    ).fetchall()
    media = conn.execute(
        "SELECT file_name, media_type, original_name FROM media WHERE party_id = ? ORDER BY id ASC",
        (party["id"],),
    ).fetchall()
    conn.close()
    return {
        "party": party,
        "messages": messages,
        "media": media,
    }


init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/customize")
def customize():
    return render_template("customize.html")


@app.route("/api/randomize")
def randomize_party():
    recipient = request.args.get("recipient", "Bestie")
    seed = uuid.uuid4().hex
    palettes = [
        {"accent": "#d9778f", "secondary": "#f6d5de", "background_style": "rose-glow"},
        {"accent": "#9b7bff", "secondary": "#efe7ff", "background_style": "lavender-dream"},
        {"accent": "#e09f3e", "secondary": "#fdf0d5", "background_style": "golden-hour"},
        {"accent": "#2a9d8f", "secondary": "#d9f6f1", "background_style": "mint-bloom"},
    ]
    headlines = [
        f"Happy Birthday, {recipient}!",
        f"Today is all about {recipient}",
        f"A little universe made for {recipient}",
        f"Your people showed up for you, {recipient}",
    ]
    subtitles = [
        "A modern love-filled birthday experience made with heart.",
        "Warm memories, soft colors, and people who adore you.",
        "A classy celebration full of messages, flowers, and happy chaos.",
        "Your surprise room is glowing with love and sweet moments.",
    ]
    prompts = [
        "Please enter your name for a secure guest welcome.",
        "A quick guest check before we open something special for you.",
        "Just one elegant step before your surprise begins.",
    ]
    message_sets = [
        [
            {"sender": "Your Favorite Human", "text": f"{recipient}, you make ordinary days feel softer, brighter, and kinder. Never stop being you."},
            {"sender": "Someone Who Loves You", "text": "May this year bring peaceful nights, loud laughter, and all the love you deserve."},
            {"sender": "Your Chaos Crew", "text": "We brought flowers, hearts, and way too many feelings just for your day."},
        ],
        [
            {"sender": "Best Friend", "text": f"Happy birthday, {recipient}! Thank you for being the safest place, funniest voice note, and sweetest soul."},
            {"sender": "Family", "text": "You are deeply loved, endlessly celebrated, and forever precious to us."},
            {"sender": "Secret Admirer", "text": "Your smile deserves standing ovations and your heart deserves the gentlest kind of joy."},
        ],
    ]
    palette = palettes[int(seed[0], 16) % len(palettes)]
    headline = headlines[int(seed[1], 16) % len(headlines)]
    subtitle = subtitles[int(seed[2], 16) % len(subtitles)]
    prompt = prompts[int(seed[3], 16) % len(prompts)]
    messages = message_sets[int(seed[4], 16) % len(message_sets)]
    return jsonify(
        {
            "title": headline,
            "subtitle": subtitle,
            "intro_text": "This page was designed to feel calm, modern, and deeply personal — like a private celebration from your people.",
            "accent_color": palette["accent"],
            "secondary_color": palette["secondary"],
            "background_style": palette["background_style"],
            "surprise_prompt": prompt,
            "messages": messages,
        }
    )


@app.route("/create-party", methods=["POST"])
def create_party():
    recipient_name = request.form.get("recipient_name", "Beautiful Soul").strip() or "Beautiful Soul"
    title = request.form.get("title", f"Happy Birthday, {recipient_name}!").strip() or f"Happy Birthday, {recipient_name}!"
    subtitle = request.form.get("subtitle", "A soft, stylish birthday moment made just for you.").strip()
    intro_text = request.form.get("intro_text", "").strip()
    accent_color = request.form.get("accent_color", "#d9778f").strip() or "#d9778f"
    secondary_color = request.form.get("secondary_color", "#f6d5de").strip() or "#f6d5de"
    background_style = request.form.get("background_style", "rose-glow").strip() or "rose-glow"
    surprise_prompt = request.form.get("surprise_prompt", "Please enter your name to continue.").strip() or "Please enter your name to continue."
    created_by = request.form.get("created_by", "Someone who loves you").strip() or "Someone who loves you"

    slug = unique_slug(recipient_name)
    created_at = datetime.utcnow().isoformat()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO parties (slug, recipient_name, title, subtitle, intro_text, accent_color, secondary_color, background_style, surprise_prompt, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            slug,
            recipient_name,
            title,
            subtitle,
            intro_text,
            accent_color,
            secondary_color,
            background_style,
            surprise_prompt,
            created_by,
            created_at,
        ),
    )
    party_id = cur.lastrowid

    senders = request.form.getlist("sender_name[]")
    messages = request.form.getlist("message_text[]")
    for sender, message in zip(senders, messages):
        sender = sender.strip()
        message = message.strip()
        if sender and message:
            cur.execute(
                "INSERT INTO messages (party_id, sender_name, message_text) VALUES (?, ?, ?)",
                (party_id, sender, message),
            )

    files = request.files.getlist("media_files")
    for file in files:
        if not file or not file.filename:
            continue
        original_name = file.filename
        if not allowed_file(original_name):
            continue
        ext = original_name.rsplit('.', 1)[-1].lower()
        media_type = "image" if ext in ALLOWED_IMAGE_EXTS else "video"
        stored_name = secure_filename(f"{uuid.uuid4().hex}.{ext}")
        file.save(UPLOAD_DIR / stored_name)
        cur.execute(
            "INSERT INTO media (party_id, file_name, media_type, original_name) VALUES (?, ?, ?, ?)",
            (party_id, stored_name, media_type, original_name),
        )

    conn.commit()
    conn.close()
    return redirect(url_for("party_entry", slug=slug, created=1))


@app.route("/p/<slug>")
def party_entry(slug):
    data = party_with_children(slug)
    if not data:
        return render_template("not_found.html"), 404
    return render_template("entry.html", data=data, created=request.args.get("created"))


@app.route("/celebrate/<slug>")
def celebrate(slug):
    data = party_with_children(slug)
    if not data:
        return render_template("not_found.html"), 404
    visitor_name = request.args.get("guest_name", "Guest").strip() or "Guest"
    return render_template("party.html", data=data, visitor_name=visitor_name)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
