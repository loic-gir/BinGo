// === CONFIGURATION ===
const NGROK_API_URL = "https://5043-79-174-206-181.ngrok-free.app"; // URL de l'API Flask via ngrok

const NGROK_HEADERS = {
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json'
};

const LEVEL_VARS = ["niveau_bac1", "niveau_bac2", "niveau_bac3", "niveau_bac4", "niveau_bac5"];
const WASTE_VARS = ["plastique", "papier_carton", "verre", "metal", "non_recyclable"];

const EMAILJS_SERVICE_ID = "service_e3jidvj";
const EMAILJS_TEMPLATE_ID = "template_khtq26c";
const EMAILJS_USER_ID = "VqdRukFY9mMrez9Kh";
const DESTINATAIRE_EMAIL = "xingtong.lin@edu.esiee.fr";

emailjs.init({
    publicKey: EMAILJS_USER_ID,
    blockHeadless: true // Empêche les robots d'utiliser votre clé
});
// emailjs.init(EMAILJS_USER_ID);

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
// Variables d'état admin
let isAdmin = false;
let isPublic = false;

// Configuration Supabase
const _supabaseUrl = 'https://umrlwpojlfvqawgyooqr.supabase.co';
const _supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVtcmx3cG9qbGZ2cWF3Z3lvb3FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwNzM3NDEsImV4cCI6MjA2NTY0OTc0MX0.Y25eExN0JKgbEyB20vAV-6_-zqndYp29s3AWayJ6GSA';
const supabaseCli = supabase.createClient(_supabaseUrl, _supabaseKey);

// Fonctions d'administration
async function showAdminLogin() {
    if (isAdmin) {
        showAdminPanel();
    }
    else {
        document.getElementById('adminLogin').style.display = 'block';
        document.getElementById('shadow').style.display = 'block';
    }
}

function hideAdminLogin() {
    document.getElementById('adminLogin').style.display = 'none';
    document.getElementById('shadow').style.display = 'none';
}

function showAdminPanel() {
    document.getElementById('adminPanel').style.display = 'block';
    document.getElementById('shadow').style.display = 'block';
}

function hideAdminPanel() {
    document.getElementById('adminPanel').style.display = 'none';
    document.getElementById('shadow').style.display = 'none';
}

async function loginAdmin() {
    const id = document.getElementById('adminId').value.trim();;
    const password = document.getElementById('adminPassword').value.trim();;

    try {
        const { data, error } = await supabaseCli
            .from('admins')
            .select('*')
            .eq('id_admin', id)
            .eq('mdp_admin', password);

        if (data && data.length > 0) {
            // alert("Connecté !");
            isAdmin = true;
            hideAdminLogin();
            initDisplay();
            showAdminPanel();
            checkAccessSetting();
        } else {
            alert('Identifiant ou mot de passe incorrect');
        }
    } catch (error) {
        console.error('Erreur de connexion:', error);
        alert('Erreur de connexion');
    }
}

async function checkAccessSetting() {
    try {
        const { data, error } = await supabaseCli
            .from('settings')
            .select('*')
            .eq('id', "suivi")
            .single();

        if (error) throw error;

        isPublic = data.public_access;
        document.getElementById('publicAccess').checked = isPublic;
    } catch (error) {
        console.error('Erreur récupération paramètre:', error);
    }
}

async function togglePublicAccess() {
    const isChecked = document.getElementById('publicAccess').checked;

    try {
        const { error } = await supabaseCli
            .from('settings')
            .update({ public_access: isChecked })
            .eq('id', "suivi");

        if (error) throw error;

        isPublic = isChecked;
        // alert('Paramètre mis à jour avec succès');

        await initDisplay();

        if (isPublic) {
            hideAdminPanel();
        }

    } catch (error) {
        console.error('Erreur mise à jour paramètre:', error);
        document.getElementById('publicAccess').checked = !isChecked;
    }
}

function logoutAdmin() {
    isAdmin = false;
    hideAdminPanel();
    initDisplay();
}

function stillConnect() {
    hideAdminPanel();
}

// Initialisation de l'affichage
async function initDisplay() {
    await checkAccessSetting();

    if (isAdmin || isPublic) {
        initBins();
        initStats();
        fetchAllData();
    } else {
        document.getElementById('bins').innerHTML = '<p>Connectez-vous en tant qu\'admin pour voir les statistiques</p>';
        document.getElementById('stats').innerHTML = '<p>Connectez-vous en tant qu\'admin pour voir les statistiques</p>';
        document.getElementById('totalWaste').style.display = 'none';
    }
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

            if (level >= 98) {
                await sendEmail(
                    `Alerte Bac ${i + 1} - BinGo!`,
                    `Le bac ${i + 1} est presque plein (${level}%)! Intervention humaine requise dans les plus brefs délais.`
                );
            }
        }

        // Récupération des statistiques
        await fetchStats();

    } catch (error) {
        console.error("Erreur connexion API:", error);
        useMockData();
    }

    updateStatus();
}

async function sendEmail(title, message) {
    try {
        const response = await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, {
            to_email: DESTINATAIRE_EMAIL,
            title: title,
            message: message
        });
        console.log("Email envoyé à", DESTINATAIRE_EMAIL, ". Status:", response.status);
        return response;
    } catch (error) {
        console.error("Échec d'envoi :", error);
        throw error;
    }
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
    const totalElement = document.getElementById('totalWaste');
    if (!totalElement) return;

    // Mettre à jour le total
    if (isAdmin || isPublic) {
        totalElement.style.display = 'block';
        totalElement.textContent = `Total déchets triés: ${stats.total}`;
    } else {
        totalElement.style.display = 'none';
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
    updateStatus(); // Ajoutez cette ligne
}

function getRandomLevel() {
    return Math.floor(Math.random() * 100);
}

// Statistiques simulées
function useSimulatedStats() {
    const papier = Math.floor(Math.random() * 30);
    const plastique = Math.floor(Math.random() * 25);
    const verre = Math.floor(Math.random() * 20);
    const metal = Math.floor(Math.random() * 15);
    const non_recyclable = Math.floor(Math.random() * 10);

    const simulatedStats = {
        papier, 
        plastique, 
        verre, 
        metal, 
        non_recyclable, 
        total:papier+plastique+verre+metal+non_recyclable
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

document.addEventListener('DOMContentLoaded', async () => {

    // Tester la connexion avant de commencer
    const connected = await testConnection();
    if (connected) {
        console.log("✅ Connexion API établie");
    } else {
        console.log("⚠️ API non accessible, mode simulation");
    }

    // nbr d'envoie limité donc pas tester chaque fois
    // try {
    //     await sendEmail("Notification Test - BinGo!", "Ceci est un message test technique pour vérifier le bon fonctionnement du système d'alertes.");
    //     console.log("✅ Test OK - Vérifiez vos emails");
    // } catch (error) {
    //     console.error("❌ Échec critique :", error);
    // }

    // Initialiser l'affichage (fetchAllData inclus)
    await initDisplay();

    // Mise à jour toutes les 5 secondes
    updateInterval = setInterval(fetchAllData, 5000);

    // Initialisation au chargement
    document.getElementById('loginForm').addEventListener('submit', (e) => {
        e.preventDefault();
        loginAdmin();
    });

    document.getElementById('publicAccess').addEventListener('change', togglePublicAccess);
});

// Nettoyer lors de la fermeture de la page
window.addEventListener('beforeunload', stopUpdates);
