# ClubCyber ; VeilleAutomatisée en Cybersécurité et IA

ClubCyber est un outil de veille automatisée qui scrute quotidiennement des sources spécialisées en cybersécurité et intelligence artificielle (IA/LLM). Il utilise un agent Mistral pour générer des résumés, filtre les articles selon des mots-clés et limites l’envoi à 3 articles par jour via un webhook Discord.

## 📋 Cahier des charges

1. **Objectif** : Automatiser la collecte, la synthèse et la diffusion d’articles de veille cyber/IA sur Discord.
2. **Fréquence** : Exécution planifiée à 6h UTC chaque jour (via GitHub Actions).
3. **Sources** : Liste configurable de sites (Korben, LeMondeInformatique, BleepingComputer, TheRegister, etc.).
4. **Extraction** : Parsing RSS prioritaire, fallback `newspaper3k` si RSS indisponible.
5. **Filtres** : Mots-clés génériques et critiques, double passe (strict puis fallback), contenu > 200 caractères.
6. **Déduplication** : Historique d’URLs dans `processed_articles.txt`, doublons de titres via comparaison de mots.
7. **Résumé IA** : Appel API Mistral avec résumé en quelques phrases.
8. **Notification** : Envoi JSON à Discord via webhook, gestion des erreurs HTTP.
9. **Limite** : Maximum 3 articles envoyés par exécution, priorité aux plus pertinents.
10. **Logging** : Fichier `App.log` + console, suivi des erreurs et des statistiques.
11. **CI/CD** : GitHub Actions pour planification, injection de secrets et commit automatique des logs.

## ⚙️ Fonctionnalités principales

- **Configuration dynamique** : Ajout/Suppression de sources dans `SITES_SOURCES`.
- **Double extraction** : RSS → Newspaper3k.
- **Filtrage avancé** : mots-clés, contenu, doublons URL & titre.
- **Synthèse IA** : résumé automatique via Mistral.
- **Multi-threading** : traitement parallèle des sources.
- **Limitateur** : 3 articles max/jour.
- **Persistance** : historique dans `processed_articles.txt`.
- **Notification Discord** : via `send_to_discord()`.
- **Automatisation GitHub** : exécution cron, push logs & cache.

## 📄 Usage

- **Local** : `python main.py`
- **CI/CD** : déclenchement quotidien via `.github/workflows/veille.yml`.

created by rapatt
