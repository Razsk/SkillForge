---
name: RoutineFollowUp
description: Administrerer rutiner via cron-jobs. Agenten lytter efter system-prompts og opdaterer perioder baseret på brugerens svar.
version: 1.1.0
dependencies:
  - python3
---
# RoutineFollowUp

Denne skill bruger et push-baseret cron-system. Agenten skal ikke manuelt overvåge rutinerne, men blot reagere proaktivt, når systemet sender en trigger-besked via terminalen/loggen.

## Triggers
Når du (agenten) modtager en systembesked fra scriptet, der starter med: "SYSTEM PROMPT: Rutinen '[Rutine Navn]' er forfalden...", skal du gøre følgende:
1. Spørg brugeren naturligt og høfligt, om de har fuldført den specifikke opgave.
2. Hvis brugeren siger NEJ eller ignorerer spørgsmålet: Gør intet yderligere. Systemet rykker dem automatisk igen.
3. Hvis brugeren bekræfter (siger JA, "det er fikset", etc.): Kald straks værktøjet `complete_routine`.

## Tools

### complete_routine
Brug udelukkende dette værktøj, når brugeren bekræfter, at en rutine er fuldført. Værktøjet sætter automatisk cron-jobbet tilbage til den primære periode og logger handlingen.

**Kommando der skal udføres:**
```bash
python3 scripts/routine_engine.py --action complete --name "<rutinens_navn>"

```

*Bemærk: `<rutinens_navn>` skal matche præcis det navn, der blev givet i system-prompten.*

### add_routine
Brug dette værktøj, når brugeren beder om at få oprettet en ny rutine.

**Parametre:**
- `name`: Navnet på rutinen (string).
- `primary`: Hvor ofte den skal udføres (int, antal dage).
- `deadline`: Hvor hurtigt systemet skal rykke, hvis den overskrides (int, antal dage).
- `time`: (Valgfri) Tidspunkt på dagen (string, format "HH:MM", default "07:00").

**Kommando der skal udføres:**
```bash
python3 scripts/routine_engine.py --action add --name "<name>" --primary <primary> --deadline <deadline> --time "<time>"
```
