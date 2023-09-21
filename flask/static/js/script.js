/**
* Creates a new toast element and displays it
* @param {string} message - message to be displayed.
*/
const alertToast = (message) => {
    const newToastEl = Object.assign(document.createElement('div'), {
        className: 'w-100 toast',
        role: 'alert',
        'aria-live': 'assertive',
        'aria-atomic': 'true',
        innerHTML: `<div class="d-flex"><span class="m-auto px-2">
                                    <i class="bi bi-bell-fill"></i>
                                </span>
                                <div class="toast-body">
                                    <h4>${message}</h4>
                                </div>
                                <a href="" class="me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"><i
                                        class="bi bi-x-circle"></i></a></div>`
    });
    toastContainer.insertBefore(newToastEl, toastContainer.firstChild);
    const newToast = new bootstrap.Toast(newToastEl, toastSettings);
    newToast.show();
};

/** 
* Prevents default action for the event in which was called.
* @param {obj} e - event object.
*/
const preventDefaults = (e) => {
    e.preventDefault();
    e.stopPropagation();
}

/** 
* Prevents event's default action if is not confirmed by user.
* @param {obj} e - Event
*/
const confirmIt = (e) => {
    if (!confirm('Are you sure?')) {
        preventDefaults(e);
    }
};

// Offcanvas toggle click event listener
document.querySelectorAll('[data-toggle="offcavas"]').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelector('.offcanvas-collapse').classList.toggle('open');
        document.querySelector('#navbar-toggler .bi').classList.toggle('bi-x');
    })
});

// Declare used variables
const toastContainer = document.querySelectorAll('.toast-container')[0];
const toastSettings = {
    autohide: true,
    delay: 5000
};

// Create Botstrap toasts from existing DOM elements
const toastElList = [].slice.call(document.querySelectorAll('.toast'));
const toastList = toastElList.map((toastEl) => {
    return new bootstrap.Toast(toastEl, toastSettings);
});

// Show toasts
toastList.forEach(toast => {
    toast.show();
});

// Confirm action event listener for items with class .confirm
document.querySelectorAll('.confirm').forEach(item => {
    item.addEventListener('click', confirmIt, false);
});

// Prevent Double Submits
// CREDIT: https://www.bram.us/2020/11/04/preventing-double-form-submissions/
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
        // Prevent if already submitting
        if (form.classList.contains('is-submitting')) {
            preventDefaults(e);
        } else {
            const overlay = Object.assign(document.createElement('div'), {
                id: "spin-overlay-contain"
            });
            const spinnerEl = Object.assign(document.createElement('div'), {
                id: "spinner",
                className: 'spinner-border',
                innerHTML: `<span class="visually-hidden">Loading...</span>`
            });
            form.appendChild(overlay);
            form.appendChild(spinnerEl);
        }

        // Add class to hook our visual indicator on
        form.classList.add('is-submitting');
    });
});