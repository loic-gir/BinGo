function initAnim() {

    // Initialisation de ScrollReveal
    ScrollReveal({
        // Configuration globale
        easing: 'ease-in-out',
        reset: true,
        opcity: 0.5,
        scale: 0.2
    });

    // Animation pour les membres à droite
    ScrollReveal().reveal('.pers', {
        origin: 'top',
        distance: '2rem',
    });

    // Animation pour les paroles à gauche
    ScrollReveal().reveal('.parole-left', {
        origin: 'left',
        distance: '50rem',
        duration: 1600,
        delay: 500
    });

    // Animation pour les paroles à droite
    ScrollReveal().reveal('.parole-right', {
        origin: 'right',
        distance: '50rem',
        duration: 1600,
        delay: 500
    });

}
document.addEventListener('DOMContentLoaded', initAnim);
