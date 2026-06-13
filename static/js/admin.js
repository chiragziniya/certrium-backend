// Suppress Django admin's "Note: You are X hours ahead/behind of server time."
// warning on every date/time field.  The backend stores UTC; the browser
// handles local-time display — no user-facing warning is needed.
document.addEventListener('DOMContentLoaded', function () {
    if (window.DateTimeShortcuts) {
        // Replace the function with a no-op so the element is never added.
        DateTimeShortcuts.addTimezoneWarning = function () {};
    }
});
