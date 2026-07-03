// Reset pagination to page 1 whenever any GET filter/search form is submitted.
// This prevents the stale-page bug where a user on page 2 submits a new search
// and sees page 2 of the new results (missing page 1 matches).
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form[method="get"]').forEach(function (form) {
        form.addEventListener('submit', function () {
            form.querySelectorAll('input[name="page"]').forEach(function (el) { el.remove(); });
        });
    });
});
