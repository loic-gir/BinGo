// === CONFIGURATION ===
const UBIDOTS_TOKEN = "BBUS-AoGq5fswhdE5DvDQv670osyzoGLAsY";
const DEVICE = "BinGo";
const NGROK_API_URL = "https://9194-79-174-206-181.ngrok-free.app"; // URL de l'API Flask via ngrok

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
let updateInterval;

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

// Fonction principale pour récupérer toutes les données
async function fetchAllData() {
    isUsingMockData = false;

    try {
        // Récupération des données des bacs
        const res = await fetch(`${NGROK_API_URL}/api/data`, {
            headers: NGROK_HEADERS
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log("Données reçues:", data);

        // Mise à jour des niveaux des bacs
        for (let i = 0; i < LEVEL_VARS.length; i++) {
            const level = data[LEVEL_VARS[i]] || 0;
            updateBinDisplay(i, level);
        }

        // Récupération des statistiques
        await fetchStats();

    } catch (error) {
        console.error("Erreur connexion API:", error);
        useMockData();
    }

    updateStatus();
}

// Récupérer les statistiques depuis l'API Flask
async function fetchStats() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/stats`, {
            headers: NGROK_HEADERS
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const stats = await res.json();
        console.log("Statistiques reçues:", stats);
        updateStatsDisplay(stats);
        return stats;
    } catch (error) {
        console.error("Erreur connexion stats:", error);
        // En cas d'erreur, utiliser les données simulées pour les stats
        useSimulatedStats();
        return null;
    }
}

// Mettre à jour l'affichage des statistiques
function updateStatsDisplay(stats) {
    // Mettre à jour le total
    const totalElement = document.getElementById('totalWaste');
    if (totalElement) {
        totalElement.textContent = `Total déchets triés: ${stats.total}`;
    }

    // Mapping corrigé pour correspondre aux données Python
    const categoryMapping = {
        "papier": 0,           // Correspond à "papier_carton" dans l'affichage
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
        
        // Optionnel : afficher dans l'interface
        displayLastDetection(lastDetection);
    }
}

// Afficher la dernière détection (optionnel)
function displayLastDetection(detection) {
    const lastDetectionElement = document.getElementById('lastDetection');
    if (lastDetectionElement) {
        const labelMapping = {
            "cardboard_paper": "Papier/Carton",
            "plastic": "Plastique",
            "metal": "Métal", 
            "glass": "Verre",
            "trash": "Non recyclable"
        };
        
        const frenchLabel = labelMapping[detection.type] || detection.type;
        lastDetectionElement.textContent = `Dernière détection: ${frenchLabel} (${detection.confidence}%)`;
    }
}

// Fonction de fallback avec statistiques simulées
function useMockData() {
    isUsingMockData = true;

    // Données simulées pour les bacs
    for (let i = 0; i < LEVEL_VARS.length; i++) {
        updateBinDisplay(i, getRandomLevel());
    }

    // Utiliser les statistiques simulées
    useSimulatedStats();
}

// Statistiques simulées
function useSimulatedStats() {
    const simulatedStats = {
        total: Math.floor(Math.random() * 100) + 20,
        papier: Math.floor(Math.random() * 30),
        plastique: Math.floor(Math.random() * 25),
        verre: Math.floor(Math.random() * 20),
        metal: Math.floor(Math.random() * 15),
        non_recyclable: Math.floor(Math.random() * 10)
    };
    
    updateStatsDisplay(simulatedStats);
}

// Tester la connexion à l'API
async function testConnection() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/status`, {
            headers: NGROK_HEADERS
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const status = await res.json();
        console.log("Statut API:", status);
        return true;
    } catch (error) {
        console.error("Test connexion échoué:", error);
        return false;
    }
}

// Fonctions utilitaires
function getRandomLevel() {
    return Math.floor(Math.random() * 100);
}

function getRandomWasteCount() {
    return Math.floor(Math.random() * 50);
}

// Mise à jour de l'affichage des bacs
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

// Fonction de compatibilité pour les données simulées
function updateStatDisplay(index, count) {
    const statValue = document.getElementById(`stat-value-${index}`);
    if (statValue) statValue.textContent = count;
}

// Mise à jour du statut
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

// Fonction pour arrêter les mises à jour
function stopUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
        console.log("Mises à jour arrêtées");
    }
}

// Fonction pour remettre à zéro les statistiques (optionnel)
async function resetStats() {
    try {
        const res = await fetch(`${NGROK_API_URL}/api/stats/reset`, {
            method: 'POST',
            headers: NGROK_HEADERS
        });

        if (res.ok) {
            const result = await res.json();
            console.log("Statistiques remises à zéro:", result);
            // Rafraîchir l'affichage
            fetchStats();
        }
    } catch (error) {
        console.error("Erreur reset stats:", error);
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
    fetchNotifications();
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

    // Premier appel (fetchStats est déjà appelé dans fetchAllData)
    fetchAllData();

    // Mise à jour toutes les 5 secondes
    updateInterval = setInterval(fetchAllData, 5000);
});

// Nettoyer lors de la fermeture de la page
window.addEventListener('beforeunload', stopUpdates);
