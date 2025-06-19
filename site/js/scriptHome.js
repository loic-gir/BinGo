function initAnim() {

    // Initialisation de ScrollReveal
    ScrollReveal({
        // Configuration globale
        easing: 'ease-in-out',
        reset: true,
        opcity: 0.5
    });

    // Animation pour les membres à droite
    ScrollReveal().reveal('.pers', {
        origin: 'top',
        distance: '2rem',
        scale: 0.2
    });

    // Animation pour les paroles à gauche
    ScrollReveal().reveal('.parole-left', {
        origin: 'left',
        distance: '10rem',
        duration: 1600,
        scale: 0.1,
        delay: 500
    });

    // Animation pour les paroles à droite
    ScrollReveal().reveal('.parole-right', {
        origin: 'right',
        distance: '10rem',
        duration: 1600,
        scale: 0.1,
        delay: 500
    });

}
document.addEventListener('DOMContentLoaded', initAnim);
