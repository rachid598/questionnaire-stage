# Questionnaire de fin de stage (octobre 2026)

Page statique (`index.html`, GitHub Pages) qui envoie les réponses dans une table Supabase `reponses`.
- `supabase.sql` : création de la table + règle « envoi seul, dans une fenêtre horaire » (aucune lecture publique).
- Résultats : tableau de bord Supabase → Table Editor → `reponses` → Export CSV.
- `index.html` est généré depuis `templates/form.html` ; la clé `anon` y est publique par conception.
- `app.py` & co : ancienne version Flask/SQLite, non utilisée.
