import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/registry.json')
LOG_PATH = os.path.join(BASE_DIR, '../data/completion.log')

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f: return json.load(f)
    return {}

def save_db(db):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w') as f: json.dump(db, f, indent=4)

def log_completion(name):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{now_str}] Rutine fuldført: {name}\n"
    with open(LOG_PATH, 'a') as f: f.write(log_line)

def update_crontab(name, run_dt):
    # Format i crontab: minut time dag måned ugedag
    cron_time = f"{run_dt.minute} {run_dt.hour} {run_dt.day} {run_dt.month} *"
    script_path = os.path.abspath(__file__)
    python_exec = sys.executable

    # Kommandoen cron skal køre
    cmd = f"{python_exec} {script_path} --action trigger --name '{name}'"
    marker = f"# OPENCLAW_ROUTINE:{name}"
    new_job = f"{cron_time} {cmd} {marker}"

    # Hent nuværende crontab (ignorer fejl hvis den er tom)
    try:
        current_cron = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode('utf-8')
    except subprocess.CalledProcessError:
        current_cron = ""

    # Fjern det gamle job for denne rutine (hvis det eksisterer)
    lines = [line for line in current_cron.splitlines() if marker not in line and line.strip() != ""]
    lines.append(new_job)
    new_cron = "\n".join(lines) + "\n"

    # Skriv den nye crontab tilbage
    proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    proc.communicate(new_cron.encode('utf-8'))

def calculate_next_run(time_str, days_ahead):
    now = datetime.now()
    t = datetime.strptime(time_str, "%H:%M").time()
    next_dt = datetime.combine(now.date() + timedelta(days=days_ahead), t)
    return next_dt

def add_routine(name, primary, deadline, time_of_day):
    db = load_db()
    next_dt = calculate_next_run(time_of_day, primary)
    db[name] = {
        "primary_period": primary,
        "deadline_period": deadline,
        "time_of_day": time_of_day
    }
    save_db(db)
    update_crontab(name, next_dt)
    return f"Rutine '{name}' oprettet. Cron sat til {next_dt.strftime('%Y-%m-%d %H:%M')}."

def trigger_routine(name):
    db = load_db()
    if name not in db:
        print(f"Fejl: Rutine '{name}' findes ikke i databasen.")
        return

    data = db[name]

    # Skift automatisk til frist-perioden (deadline mode)
    next_dt = calculate_next_run(data['time_of_day'], data['deadline_period'])
    update_crontab(name, next_dt)

    # Send besked til LLM/standard output
    print(f"SYSTEM PROMPT: Rutinen '{name}' er forfalden. Spørg brugeren om den er udført. Hvis de bekræfter, kør 'complete_routine' værktøjet for '{name}'. Ellers vil systemet rykke dem igen automatisk d. {next_dt.strftime('%Y-%m-%d %H:%M')}.")

def complete_routine(name):
    db = load_db()
    if name not in db: return "Fejl: Rutine findes ikke."
    data = db[name]

    # Brugeren har bekræftet: Skift tilbage til primær periode
    next_dt = calculate_next_run(data['time_of_day'], data['primary_period'])
    update_crontab(name, next_dt)
    log_completion(name)

    return f"Succes: '{name}' er markeret som fuldført og logget i completion.log. Næste cron-kørsel er sat til {next_dt.strftime('%Y-%m-%d %H:%M')} (Primær periode)."

def check_routines():
    db = load_db()
    if not db:
        return "Ingen rutiner fundet i databasen."

    try:
        current_cron = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode('utf-8')
    except subprocess.CalledProcessError:
        current_cron = ""
    except FileNotFoundError:
        return "Fejl: 'crontab' kommandoen findes ikke i miljøet."

    report = []
    report.append(f"Status rapport for {len(db)} rutiner:")
    report.append("-" * 40)

    for name, data in db.items():
        marker = f"# OPENCLAW_ROUTINE:{name}"
        if marker in current_cron:
            # Find linjen med markøren for at se tidspunktet
            for line in current_cron.splitlines():
                if marker in line:
                    parts = line.split()
                    # Cron format: m h dom mon dow command
                    cron_schedule = f"{parts[1]}:{parts[0]} d. {parts[2]}/{parts[3]}"
                    report.append(f"[OK]   {name:<20} (Planlagt: {cron_schedule})")
                    break
        else:
            report.append(f"[FEJL] {name:<20} (Mangler i crontab!)")

    return "\n".join(report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["add", "trigger", "complete", "check"], required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--primary", type=int, help="Primær periode i dage")
    parser.add_argument("--deadline", type=int, help="Frist periode i dage")
    parser.add_argument("--time", default="07:00", help="Tidspunkt HH:MM")

    args = parser.parse_args()

    if args.action == "add":
        if not args.primary or not args.deadline:
            print("Fejl: --primary og --deadline argumenter kræves ved 'add' handling.")
            sys.exit(1)
        print(add_routine(args.name, args.primary, args.deadline, args.time))
    elif args.action == "trigger":
        trigger_routine(args.name)
    elif args.action == "complete":
        print(complete_routine(args.name))
    elif args.action == "check":
        print(check_routines())