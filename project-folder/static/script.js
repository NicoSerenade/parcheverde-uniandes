function changeBackground(newBackground) {
    const backgroundContainer = document.getElementById('background-container');
    backgroundContainer.style.background = `url("${newBackground}") no-repeat center center fixed`;
    backgroundContainer.style.backgroundSize = 'cover';
}

document.addEventListener('DOMContentLoaded', function() {
    const isLoggedIn = document.body.dataset.loggedIn === 'true';

    // Verificar sesión
    if (!isLoggedIn) {
        changeBackground('../static/fondo_logout.png');
        return;
    }

    // Event Listeners para los botones
    const homeLink = document.querySelector('a[href="/"]');
    homeLink?.addEventListener('click', function(e) {
        e.preventDefault();
        changeBackground('../static/fondo_home.png');
        window.location.href = this.href;
    });

    const profileLink = document.querySelector('a[href*="profile"]');
    profileLink?.addEventListener('click', function(e) {
        e.preventDefault();
        changeBackground('../static/fondo_5.png');
        setTimeout(() => window.location.href = this.href, 600);
    });

    const eventsLink = document.querySelector('a[href*="events"]');
    eventsLink?.addEventListener('click', function(e) {
        e.preventDefault();
        changeBackground('../static/fondo_3.png');
        setTimeout(() => window.location.href = this.href, 600);
    });

    const itemsLink = document.querySelector('a[href*="items"]');
    itemsLink?.addEventListener('click', function(e) {
        e.preventDefault();
        changeBackground('../static/fondo_4.png');
        setTimeout(() => window.location.href = this.href, 600);
    });

    const organizationsLink = document.querySelector('a[href*="organizations"]');
    organizationsLink?.addEventListener('click', function(e) {
        e.preventDefault();
        changeBackground('../static/fondo_2.png');
        setTimeout(() => window.location.href = this.href, 600);
    });

    // Verificar la página actual para establecer el fondo inicial
    if (window.location.pathname === '/') {
        changeBackground('../static/fondo_home.png');
    } else if (window.location.pathname.includes('profile')) {
        changeBackground('../static/fondo_5.png');
    } else if (window.location.pathname.includes('events')) {
        changeBackground('../static/fondo_3.png');
    } else if (window.location.pathname.includes('items')) {
        changeBackground('../static/fondo_4.png');
    } else if (window.location.pathname.includes('organizations')) {
        changeBackground('../static/fondo_2.png');
    } else if (window.location.pathname.includes('map')) {
        changeBackground('../static/fondo_9.jpg');
    } else if (window.location.pathname.includes('add')) {
        changeBackground('../static/fondo_6.png');
    } else if (window.location.pathname.includes('register')) {
        changeBackground('../static/fondo_7.jpg');
    } else if (window.location.pathname.includes('create')) {
        changeBackground('../static/fondo_8.jpg');
    }

    document.querySelectorAll('.protected').forEach(button => {
        button.classList.add('hidden');
    });
});