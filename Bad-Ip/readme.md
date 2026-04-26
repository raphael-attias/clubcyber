# 🐟 Barracuda : IP Malveillantes Automatisées via Webhook Discord

## 📌 Objectif

**Barracuda** est un projet automatisé qui surveille une blocklist publique d’adresses IP malveillantes (principalement actives sur les réseaux en France et Belgique) et alerte automatiquement via un **webhook Discord** toutes les 2 heures.

Ce projet est conçu pour les équipes de cybersécurité, les administrateurs système ou les passionnés de threat intelligence souhaitant recevoir des alertes en temps réel sur des menaces potentielles.

---

## 🔗 Source de la blocklist

Le projet s’appuie sur une liste publique maintenue par **Duggy Tuxy**, contenant des adresses IPv4 détectées comme malveillantes selon différents TTPs :

> **Blocklist** : [prod_data-shield_ipv4_blocklist.txt](https://raw.githubusercontent.com/duggytuxy/Data-Shield_IPv4_Blocklist/refs/heads/main/prod_data-shield_ipv4_blocklist.txt)

### 🧠 Types de menaces couvertes :
- Botnets
- Remote Access Trojans (RaT)
- Remote Code Execution (CVE)
- Brute-force (SSH, FTP, IMAP, etc.)
- Scanners (Web, Port, Directory)
- Tor exit nodes
- VOIP attacks
- Apache/Web Traversal
- Et bien d'autres...

> ⚠️ Mise à jour toutes les **24/48h**.  
> 📜 Licence : [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

---

## ⚙️ Fonctionnement

### ✔️ Étapes :
1. Téléchargement de la blocklist IP à intervalle régulier.
2. Comparaison avec la dernière version enregistrée (logs).
3. Identification des nouvelles IP non encore signalées.
4. Envoi d’un message **formaté automatiquement** dans un **salon Discord** via un Webhook.
5. Mise à jour du journal local pour la prochaine exécution.

---

## 🚀 Déploiement via GitHub Actions

La tâche est planifiée pour s’exécuter toutes les **2 heures** grâce à un cron dans le workflow GitHub.

### 🔐 Secrets requis :

- BLOCKLIST_URL : URL brute du fichier .txt (ex. https://raw.githubusercontent.com/...)
- WEBHOOK_URL_IP : URL de ton webhook Discord

### 🛠 Exemple de configuration du workflow

Le fichier .github/workflows/barracuda.yml gère toute l’automatisation, depuis le téléchargement jusqu’à l’envoi Discord.

---

## ✅ Avantages

- Aucune dépendance externe lourde
- Facilement personnalisable (filtrage, enrichissement, etc.)
- Peut s'intégrer dans des dashboards ou SIEM
- Résistant aux faux-positifs grâce à l'origine communautaire de la blocklist

---

## 💬 Remerciements

- Merci à **Duggy Tuxy** pour la blocklist en accès libre.
- Merci à l’équipe Discord pour l’API Webhook très simple à utiliser.

---

## 🧪 Avenir

Idées d’évolution :
- Ajout d’un enrichissement via AbuseIPDB ou VirusTotal
- Envoi vers plusieurs canaux (Mail, Telegram, Slack)
- Export JSON/CSV pour exploitation SIEM
- Dashboard Web ou CLI interactif

---

## 🐟 Pourquoi “Barracuda” ?

Le **barracuda** est un poisson prédateur rapide, précis et redoutable. Un nom parfaitement adapté à un outil de veille proactive et réactive en cybersécurité.

---

## 📜 Licence

Ce projet est sous licence **MIT** voir [LICENSE](./LICENSE) pour plus de détails.
