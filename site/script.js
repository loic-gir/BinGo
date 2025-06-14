// === CONFIGURATION ===
const UBIDOTS_TOKEN = "BBUS-AoGq5fswhdE5DvDQv670osyzoGLAsY";
const DEVICE = "BinGo";

const LEVEL_VARS = ["niveau_bac1", "niveau_bac2", "niveau_bac3", "niveau_bac4", "niveau_bac5"];
const WASTE_VARS = ["plastique", "papier_carton", "verre", "metal", "non_recyclable"];

const SPREADSHEET_ID = "1H5oOlzpMnm91YhuOPa82Yi_8R4Vn2gIJLphG5Lt5HSU";
const API_KEY = "AIzaSyAt5tmQzLb91C7SgmYozzOLh72XmCNbxpc";
const SHEET_NAME = "Feuille 1";

// Icônes et labels
const WASTE_CONFIG = {
    "plastique": { icon: "🧴", label: "Plastique" },
    "papier_carton": { icon: "📄", label: "Papier/Carton" },
    "verre": { icon: "🍾", label: "Verre" },
    "metal": { icon: "🥫", label: "Métal" },
    "non_recyclable": { icon: "🗑️", label: "Non recyclable" }
};

// Variables globales
let isUsingMockData = false;

// Initialisation de l'affichage
function initDisplay() {
    initBins();
    initStats();
}

function initBins() {
    const binsContainer = document.getElementById('bins');
    binsContainer.innerHTML = LEVEL_VARS.map((_, i) => `
    <div class="bin" id="bin-${i}">
      <div class="bin-label" id="label-${i}">🗑️ Bac ${i + 1} : 0%</div>
      <div class="progress">
        <div class="progress-bar" id="bar-${i}" style="width:0%">0%</div>
      </div>
    </div>
  `).join('');
}

function initStats() {
    const statsContainer = document.getElementById('stats');
    statsContainer.innerHTML = WASTE_VARS.map((waste, i) => `
    <div class="stat-item" id="stat-${i}">
      <div class="stat-icon">${WASTE_CONFIG[waste].icon}</div>
      <div class="stat-info">
        <div class="stat-label">${WASTE_CONFIG[waste].label}</div>
        <div class="stat-value" id="stat-value-${i}">0</div>
      </div>
    </div>
  `).join('');
}

// Fonction pour récupérer les données
async function fetchAllData() {
    let totalWaste = 0;
    isUsingMockData = false;

    // Récupération des niveaux des bacs
    for (let i = 0; i < LEVEL_VARS.length; i++) {
        try {
            const res = await fetch(
                `https://stem.ubidots.com/api/v1.6/devices/${DEVICE}/${LEVEL_VARS[i]}/lv`,
                { headers: { "X-Auth-Token": UBIDOTS_TOKEN } }
            );

            let value = 0;
            if (res.ok) {
                const text = await res.text();
                value = parseInt(text);
                if (isNaN(value)) {
                    value = getRandomLevel();
                    isUsingMockData = true;
                }
            } else {
                value = getRandomLevel();
                isUsingMockData = true;
            }

            updateBinDisplay(i, value);
        } catch (e) {
            updateBinDisplay(i, getRandomLevel());
            isUsingMockData = true;
            console.error(`Erreur niveau bac ${i + 1}:`, e);
        }
    }

    // Récupération des statistiques de déchets
    for (let i = 0; i < WASTE_VARS.length; i++) {
        try {
            const res = await fetch(
                `https://stem.ubidots.com/api/v1.6/devices/${DEVICE}/${WASTE_VARS[i]}/lv`,
                { headers: { "X-Auth-Token": UBIDOTS_TOKEN } }
            );

            let count = 0;
            if (res.ok) {
                const text = await res.text();
                count = parseInt(text);
                if (isNaN(count)) {
                    count = getRandomWasteCount();
                    isUsingMockData = true;
                }
            } else {
                count = getRandomWasteCount();
                isUsingMockData = true;
            }

            totalWaste += count;
            updateStatDisplay(i, count);
        } catch (e) {
            const count = getRandomWasteCount();
            totalWaste += count;
            updateStatDisplay(i, count);
            isUsingMockData = true;
            console.error(`Erreur statistique ${WASTE_VARS[i]}:`, e);
        }
    }

    // Mise à jour de l'affichage
    document.getElementById('totalWaste').textContent = `Total déchets: ${totalWaste}`;
    updateStatus();
}

function getRandomLevel() {
    return Math.floor(Math.random() * 100);
}

function getRandomWasteCount() {
    return Math.floor(Math.random() * 50);
}

// Mise à jour de l'affichage
function updateBinDisplay(index, value) {
    const label = document.getElementById(`label-${index}`);
    const bar = document.getElementById(`bar-${index}`);

    if (label && bar) {
        label.textContent = `🗑️ Bac ${index + 1} : ${value}%`;
        bar.style.width = `${value}%`;
        bar.textContent = `${value}`;

        bar.style.backgroundColor = value >= 95 ? "#e53935" :
            value >= 60 ? "#ff9800" : "#4caf50";
    }
}

function updateStatDisplay(index, count) {
    const statValue = document.getElementById(`stat-value-${index}`);
    if (statValue) statValue.textContent = count;
}

function updateStatus() {
    const now = new Date();
    const statusElement = document.getElementById('updateStatus');

    if (statusElement) {
        statusElement.textContent = isUsingMockData
            ? `⚠ Données simulées - Dernière tentative: ${now.toLocaleString()}`
            : `✓ Données mises à jour: ${now.toLocaleString()}`;

        statusElement.className = isUsingMockData ? 'update-status error' : 'update-status success';
    }
}

// === NOTIFICATIONS GOOGLE SHEETS ===
async function fetchNotifications() {
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${SHEET_NAME}?key=${API_KEY}`;
    const notifContent = document.getElementById("notifContent");

    try {
        const response = await fetch(url);
        const data = await response.json();
        const rows = data.values;

        notifContent.innerHTML = rows.length > 1
            ? rows.slice(1).reverse().slice(0, 10).map(row => `
                <p>📩 ${row[0]} a atteint ${row[1]}% à ${row[2]}</p>
            `).join('')
            : "<p>Aucune notification trouvée</p>";

    } catch (error) {
        console.error("Erreur notifications :", error);
        notifContent.innerHTML = "<p>Erreur lors de la récupération des notifications.</p>";
    }
}

function displayLog() {
    document.getElementById("notifLog").style.display = "block";
    document.getElementById("shadow").style.display = "block";

    fetchNotifications(); // Rafraîchit les notifications à chaque ouverture
}

function hideLog() {
    document.getElementById("notifLog").style.display = "none";
    document.getElementById("shadow").style.display = "none";
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    initDisplay();
    fetchAllData();

    // Mise à jour toutes les 10 secondes
    setInterval(fetchAllData, 10000);
});