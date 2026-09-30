/* Auto-fill certificate fields when a cohort is selected.
 *
 * The server-side prefill (CertificateAdmin.get_changeform_initial_data) only
 * runs at page load from ?cohort=<id>, i.e. when arriving via "Issue certificate"
 * on the cohort list. A registrar who instead opens Certificates > Add and picks
 * a cohort from the dropdown got nothing, and had to retype the same programme
 * details for every recipient. This fills them in on change.
 *
 * Only EMPTY fields are populated, so anything deliberately typed is never
 * overwritten. Fields filled automatically are flagged so that changing the
 * cohort again can safely replace them.
 */
(function () {
    'use strict';

    var FIELDS = [
        'program_slug', 'program_title', 'program_type_label', 'credential_title',
        'duration_text', 'format', 'venue',
        'signatory_1_name', 'signatory_1_title',
        'signatory_2_name', 'signatory_2_title',
        'completion_date', 'issue_date'
    ];

    function ready(fn) {
        if (document.readyState !== 'loading') { fn(); }
        else { document.addEventListener('DOMContentLoaded', fn); }
    }

    ready(function () {
        var cohort = document.getElementById('id_cohort');
        if (!cohort) { return; }

        var endpoint = cohort.getAttribute('data-cohort-defaults-url');
        if (!endpoint) { return; }

        function inputFor(name) {
            return document.getElementById('id_' + name);
        }

        function applyDefaults(data) {
            var filled = [];
            FIELDS.forEach(function (name) {
                var el = inputFor(name);
                if (!el) { return; }
                var value = data[name];
                if (value === null || value === undefined || value === '') { return; }

                // Leave anything the user typed alone; only replace blanks and
                // values this script put there on a previous selection.
                var isAuto = el.dataset.cohortAutofilled === '1';
                if (el.value !== '' && !isAuto) { return; }

                el.value = value;
                el.dataset.cohortAutofilled = '1';
                filled.push(name);
            });
            announce(filled.length);
        }

        function clearAutofilled() {
            FIELDS.forEach(function (name) {
                var el = inputFor(name);
                if (el && el.dataset.cohortAutofilled === '1') {
                    el.value = '';
                    delete el.dataset.cohortAutofilled;
                }
            });
        }

        var note = document.createElement('p');
        note.className = 'help';
        note.setAttribute('role', 'status');
        note.style.marginTop = '4px';
        cohort.parentNode.appendChild(note);

        function announce(count) {
            note.textContent = count
                ? count + ' field(s) filled from this cohort — edit any of them if this certificate differs.'
                : '';
        }

        cohort.addEventListener('change', function () {
            clearAutofilled();
            if (!cohort.value) { return; }

            fetch(endpoint + '?cohort=' + encodeURIComponent(cohort.value), {
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (data) { if (data) { applyDefaults(data); } })
                .catch(function () {
                    // Autofill is a convenience: if it fails the form still works,
                    // and save() fills blank snapshot fields from the cohort anyway.
                    note.textContent = 'Could not load cohort defaults — fill the fields manually.';
                });
        });
    });
})();
