import { expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { Window } from 'happy-dom';

const source = readFileSync(new URL('../../app/static/js/admin-modal.js', import.meta.url), 'utf8');

test('clearing filters submits the default selection and preserves the search', async () => {
    const window = new Window({ settings: { enableJavaScriptEvaluation: true, suppressInsecureJavaScriptEnvironmentWarning: true } });
    try {
        const document = window.document;
        document.body.innerHTML = `
            <form>
                <select id="statusInput" name="statusInput">
                    <option value="offen">Offen</option><option value="all" selected>Alle</option>
                </select>
                <select id="typeInput" name="typeInput">
                    <option value="all">Alle</option><option value="maennlich" selected>Männlich</option>
                </select>
                <input id="dateFrom" name="dateFrom" value="01.01.2025">
                <input id="dateTo" name="dateTo" value="31.12.2025">
                <input id="dateType" name="dateType" value="meld" type="hidden">
                <input name="q" value="existing search" type="hidden">
                <input name="sort_order" value="id_desc" type="hidden">
                <input name="search_type" value="full_text" type="hidden">
                <button id="clearFilters" type="button">Filter löschen</button>
            </form>`;
        const submissions = [];
        const form = document.querySelector('form');
        form.submit = () => submissions.push(Object.fromEntries(new window.FormData(form)));
        window.eval(source);
        document.dispatchEvent(new window.Event('DOMContentLoaded'));
        document.getElementById('clearFilters').click();

        expect(submissions).toEqual([{
            statusInput: 'offen', typeInput: 'all', dateFrom: '', dateTo: '',
            dateType: 'fund', q: 'existing search', sort_order: 'id_desc', search_type: 'full_text',
        }]);
    } finally {
        await window.happyDOM.close();
    }
});
