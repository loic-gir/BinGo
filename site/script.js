// === CONFIGURATION ===
const UBIDOTS_TOKEN = "BBUS-AoGq5fswhdE5DvDQv670osyzoGLAsY";
const DEVICE = "BinGo";
const NGROK_API_URL = "https://f8b2-79-174-206-181.ngrok-free.app"; // URL de l'API Ubidots via ngrok

const LEVEL_VARS = ["niveau_bac1", "niveau_bac2", "niveau_bac3", "niveau_bac4", "niveau_bac5"];
const WASTE_VARS = ["plastique", "papier_carton", "verre", "metal", "non_recyclable"];

const SPREADSHEET_ID = "1H5oOlzpMnm91YhuOPa82Yi_8R4Vn2gIJLphG5Lt5HSU";
const API_KEY = "AIzaSyAt5tmQzLb91C7SgmYozzOLh72XmCNbxpc";
const SHEET_NAME = "Feuille 1";

const NGROK_HEADERS = {
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json'
};
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

// Fonction pour récupérer les données depuis ton API Flask
async function fetchAllData() {
    let totalWaste = 0;
    isUsingMockData = false;

    try {
        // Récupération des données depuis ton API Flask
        const res = await fetch(`${NGROK_API_URL}/api/data`, {
            headers: NGROK_HEADERS
        });

        if (res.ok) {
            const data = await res.json();
            console.log("Données reçues:", data);

            // Mise à jour des niveaux des bacs
            for (let i = 0; i < LEVEL_VARS.length; i++) {
                const level = data[LEVEL_VARS[i]] || 0;
                updateBinDisplay(i, level);
            }

            // Pour les statistiques, utilise les données d'historique si disponibles
            await fetchWasteStats();

        } else {
            console.error("Erreur API:", res.status);
            useMockData();
        }
    } catch (error) {
        console.error("Erreur connexion API:", error);
        useMockData();
    }

    updateStatus();
}

// Récupérer les statistiques depuis l'historique
async function fetchWasteStats() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/history`, {
            headers: NGROK_HEADERS
        });

        if (res.ok) {
            const history = await res.json();
           
            // Compter les types de déchets depuis l'historique
            // (Tu devras adapter selon la structure de tes données d'historique)
            const wasteCounts = {
                "plastique": Math.floor(Math.random() * 50),
                "papier_carton": Math.floor(Math.random() * 50),
                "verre": Math.floor(Math.random() * 50),
                "metal": Math.floor(Math.random() * 50),
                "non_recyclable": Math.floor(Math.random() * 50)
            };

            // Mise à jour de l'affichage des statistiques
            let totalWaste = 0;
            WASTE_VARS.forEach((waste, i) => {
                const count = wasteCounts[waste] || 0;
                totalWaste += count;
                updateStatDisplay(i, count);
            });

            document.getElementById('totalWaste').textContent = `Total déchets: ${totalWaste}`;
        }
    } catch (error) {
        console.error("Erreur récupération statistiques:", error);
    }
}

// Fonction de fallback en cas d'erreur
function useMockData() {
    isUsingMockData = true;
   
    // Données simulées pour les bacs
    for (let i = 0; i < LEVEL_VARS.length; i++) {
        updateBinDisplay(i, getRandomLevel());
    }
   
    // Données simulées pour les statistiques
    let totalWaste = 0;
    for (let i = 0; i < WASTE_VARS.length; i++) {
        const count = getRandomWasteCount();
        totalWaste += count;
        updateStatDisplay(i, count);
    }
   
    document.getElementById('totalWaste').textContent = `Total déchets: ${totalWaste}`;
}

// Tester la connexion à l'API
async function testConnection() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/status`, {
            headers: NGROK_HEADERS
        });
       
        if (res.ok) {
            const status = await res.json();
            console.log("Statut API:", status);
            return true;
        }
    } catch (error) {
        console.error("Test connexion échoué:", error);
    }
    return false;
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
        if (isUsingMockData) {
            statusElement.textContent = `⚠ Connexion API échouée - Données simulées - ${now.toLocaleString()}`;
            statusElement.className = 'update-status error';
        } else {
            statusElement.textContent = `✓ Données temps réel via ngrok - ${now.toLocaleString()}`;
            statusElement.className = 'update-status success';
        }
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
document.addEventListener('DOMContentLoaded', async () => {
    initDisplay();

     // Tester la connexion avant de commencer
    const connected = await testConnection();
    if (connected) {
        console.log("✅ Connexion API établie");
    } else {
        console.log("⚠️ API non accessible, mode simulation");
    }

    fetchAllData();

    // Mise à jour toutes les 5 secondes
    setInterval(fetchAllData, 5000);
});