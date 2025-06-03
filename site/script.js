// === CONFIGURATION ===
const UBIDOTS_TOKEN = "BBUS-AoGq5fswhdE5DvDQv670osyzoGLAsY";
const DEVICE = "BinGo";
const variables = ["niveau_bac1", "niveau_bac2", "niveau_bac3", "niveau_bac4", "niveau_bac5"];

const SPREADSHEET_ID = "1H5oOlzpMnm91YhuOPa82Yi_8R4Vn2gIJLphG5Lt5HSU";
const API_KEY = "AIzaSyAt5tmQzLb91C7SgmYozzOLh72XmCNbxpc";
const SHEET_NAME = "Feuille 1";

// === BACS UBIDOTS ===
async function fetchData() {
    let dataRecu = false;

    for (let i = 0; i < variables.length; i++) {
        let valAffiche;

        try {
            const res = await fetch(
                `https://stem.ubidots.com/api/v1.6/devices/${DEVICE}/${variables[i]}/lv`,
                { headers: { "X-Auth-Token": UBIDOTS_TOKEN } }
            );
            const value = await res.text();
            const val = parseInt(value);

            valAffiche = !isNaN(val) ? val : Math.floor(Math.random() * 100);
            if (!isNaN(val)) dataRecu = true;

        } catch {
            valAffiche = Math.floor(Math.random() * 100);
        }

        const label = document.getElementById(`label-${i}`);
        const bar = document.getElementById(`bar-${i}`);

        if (label && bar) {
            label.textContent = `🗑️ Bac ${i + 1} : ${valAffiche}%`;
            bar.style.width = `${valAffiche}%`;
            bar.textContent = `${valAffiche}%`;

            bar.style.backgroundColor = valAffiche >= 95 ? "#e53935" : valAffiche >= 60 ? "#ff9800" : "#4caf50";
        }
    }

    const updateText = dataRecu
        ? "Données Ubidots récupérées avec succès."
        : "⚠️ Données simulées : Ubidots non joignable.";

    document.getElementById("lastUpdate").textContent =
        `${updateText} — Dernière mise à jour : ` + new Date().toLocaleString();
}

// === NOTIFICATIONS GOOGLE SHEETS ===
async function fetchNotifications() {
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${SHEET_NAME}?key=${API_KEY}`;
    const notifContent = document.getElementById("notifContent");

    try {
        const response = await fetch(url);
        const data = await response.json();
        const rows = data.values;

        notifContent.innerHTML = "";

        if (rows && rows.length > 1) {
            for (let i = 1; i < rows.length; i++) {
                const [nom, valeur, datetime] = rows[i];
                const p = document.createElement("p");
                p.textContent = `📩 ${nom} a atteint ${valeur}% à ${datetime}`;

                notifContent.appendChild(p);
            }
        } else {
            notifContent.innerHTML = "<p>Aucune notification trouvée.</p>";
        }
    } catch (error) {
        console.error("Erreur lors de la récupération des notifications :", error);
        notifContent.innerHTML = "<p>Erreur lors de la récupération des notifications.</p>";
    }
}

function displayLog() {
    const log = document.getElementById("notifLog");
    const shadow = document.getElementById("shadow");
    log.style.display = "block";
    shadow.style.display = "block";
    fetchNotifications(); // Rafraîchit les notifications à chaque ouverture
}

function hideLog() {
    const log = document.getElementById("notifLog");
    const shadow = document.getElementById("shadow");
    log.style.display = "none";
    shadow.style.display = "none";
}

// === Initialisation ===
fetchData();
setInterval(fetchData, 10000); // Mise à jour toutes les 10s