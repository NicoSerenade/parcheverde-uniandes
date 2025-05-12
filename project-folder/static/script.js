// static/script.js

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
            <button class="btn btn-secondary cancel-btn">Cancelar</button>
            <button class="btn btn-danger confirm-btn">Confirmar</button>
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
        link.addEventListener('click', () => showLoader());
    });

    // Logout confirmation
    const logoutBtn = document.querySelector('a[href="{{ url_for(\'logout\') }}"]');
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
    const createEventForm = document.querySelector('form[action="{{ url_for(\'create_event\') }}"]');
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
    const addItemForm = document.querySelector('form[action="{{ url_for(\'add_item\') }}"]');
    if (addItemForm) {
        addItemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const dialog = createConfirmationDialog(
                '¿Desea agregar este ítem?',
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
                '¿Está seguro que desea eliminar este ítem?',
                () => window.location.href = this.href
            );
            this.parentNode.appendChild(dialog);
            setTimeout(() => dialog.classList.add('show'), 10);
        });
    });

    const isLoggedIn = document.body.dataset.loggedIn === 'true';
    if (isLoggedIn) {
        changeBackground('../static/backgrounds/parche-verde-background.png');
    } else {
        changeBackground('../static/backgrounds/parche-verde-background-not-logged.png');
    }

    // Auto-hide flash messages after 4s
    document.querySelectorAll('.flash-message').forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 4000);
    });
});
