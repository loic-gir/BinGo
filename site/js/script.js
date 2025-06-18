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

            // Récupération des statistiques
            await fetchStats();

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

// Récupérer les statistiques 
async function fetchStats() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/stats`, {
            headers: NGROK_HEADERS
        });

        if (res.ok) {
            const stats = await res.json();
            console.log("Statistiques reçues:", stats);
            updateStatsDisplay(stats);
            return stats;
        } else {
            console.error("Erreur récupération stats:", res.status);
            return null;
        }
    } catch (error) {
        console.error("Erreur connexion stats:", error);
        return null;
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

function updateStatsDisplay(stats) {
    // Mettre à jour le total
    const totalElement = document.getElementById('totalWaste');
    if (totalElement) {
        totalElement.textContent = `Total déchets triés: ${stats.total}`;
    }

    // Mettre à jour chaque catégorie
    const categoryMapping = {
        "papier": 0,
        "plastique": 1,
        "verre": 2,
        "metal": 3,
        "non_recyclable": 4
    };

    Object.keys(categoryMapping).forEach(category => {
        const index = categoryMapping[category];
        const statElement = document.getElementById(`stat-value-${index}`);
        if (statElement) {
            statElement.textContent = stats[category] || 0;
        }
    });

    // Afficher la dernière détection si disponible
    if (stats.derniere_detection) {
        const lastDetection = stats.derniere_detection;
        console.log(`Dernière détection: ${lastDetection.type} (${lastDetection.confidence}%) à ${lastDetection.timestamp}`);
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
    fetchStats();

    // Mise à jour toutes les 5 secondes
    setInterval(fetchAllData, 5000);
});