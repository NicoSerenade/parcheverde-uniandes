function changeBackground(newBackground) {
    const backgroundContainer = document.getElementById('background-container');
    backgroundContainer.style.background = `url("${newBackground}") no-repeat center center fixed`;
    backgroundContainer.style.backgroundSize = 'cover';
}

function createConfirmationDialog(message, onConfirm) {
    const dialog = document.createElement('div');
    dialog.className = 'confirmation-dialog';
    dialog.innerHTML = `
        <p>${message}</p>
        <div class="confirmation-buttons">
            <button class="cancel-btn">Cancelar</button>
            <button class="confirm-btn">Confirmar</button>
        </div>
    `;

    const cancelBtn = dialog.querySelector('.cancel-btn');
    const confirmBtn = dialog.querySelector('.confirm-btn');

    cancelBtn.onclick = () => dialog.remove();
    confirmBtn.onclick = () => {
        onConfirm();
        dialog.remove();
    };

    return dialog;
}

document.addEventListener('DOMContentLoaded', function() {
    const loader = document.querySelector('.central-loader');
    
    // Loader functionality
    const showLoader = () => loader.classList.remove('hidden');
    const hideLoader = () => loader.classList.add('hidden');

    window.addEventListener('load', hideLoader);

    // Navigation with loader
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function() {
            showLoader();
        });
    });

    // Logout confirmation
    const logoutBtn = document.querySelector('a[href="/logout"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const dialog = createConfirmationDialog(
                '¿Está seguro que desea cerrar sesión?',
                () => window.location.href = this.href
            );
            this.parentNode.appendChild(dialog);
            setTimeout(() => dialog.classList.add('show'), 10);
        });
    }

    // Add Event confirmation
    const createEventForm = document.querySelector('form[action="/create_event"]');
    if (createEventForm) {
        createEventForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const dialog = createConfirmationDialog(
                '¿Desea crear este evento?',
                () => this.submit()
            );
            this.appendChild(dialog);
            setTimeout(() => dialog.classList.add('show'), 10);
        });
    }

    // Add Item confirmation
    const addItemForm = document.querySelector('form[action="/add_item"]');
    if (addItemForm) {
        addItemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const dialog = createConfirmationDialog(
                '¿Desea agregar este item?',
                () => this.submit()
            );
            this.appendChild(dialog);
            setTimeout(() => dialog.classList.add('show'), 10);
        });
    }

    // Delete Item confirmation
    document.querySelectorAll('.delete-item-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const dialog = createConfirmationDialog(
                '¿Está seguro que desea eliminar este item?',
                () => window.location.href = this.href
            );
            this.parentNode.appendChild(dialog);
            setTimeout(() => dialog.classList.add('show'), 10);
        });
    });

    const isLoggedIn = document.body.dataset.loggedIn === 'true';
    
    // Verificar sesión y establecer fondo
    if (!isLoggedIn) {
        changeBackground('../static/fondo_logout.png');
        return;
    }

    // Auto-hide flash messages after 4 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 4000);
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
        changeBackground('../static/Fondo_10_creo.png');
    } else if (window.location.pathname.includes('about')) {
        changeBackground('../static/fondo_acerca_de.png');
    }
});