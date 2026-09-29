import { afterEach, expect, test } from 'bun:test';
import { reverseGeocode } from '../../app/static/js/geocode.js';

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

async function geocode(address) {
    globalThis.fetch = async (url) => Response.json(
        String(url).includes('nominatim') ? { address } : { land: 'Brandenburg', kreis: 'Potsdam-Mittelmark' },
    );
    return reverseGeocode(52.4, 13.0, { agsUrl: '/melden/ags-lookup' });
}

test('city address fills all fields, AGS wins for land and kreis', async () => {
    expect(await geocode({
        house_number: '12', road: 'Brandenburger Straße', postcode: '14467', city: 'Potsdam',
        state: 'Brandenburg', county: 'Potsdam', borough: 'Nördliche Vorstadt',
    })).toEqual({
        plz: '14467', ort: 'Potsdam', strasse: 'Brandenburger Straße 12',
        kreis: 'Potsdam-Mittelmark', land: 'Brandenburg',
    });
});

test('village-only point uses the village as city', async () => {
    expect((await geocode({ road: 'Dorfstraße', postcode: '14547', village: 'Fichtenwalde', state: 'Brandenburg' })))
        .toMatchObject({ ort: 'Fichtenwalde', strasse: 'Dorfstraße', plz: '14547' });
});

test('hamlet and footway are used when nothing more specific exists', async () => {
    expect((await geocode({ footway: 'Waldweg', hamlet: 'Kleinhausen', postcode: '14822' })))
        .toMatchObject({ ort: 'Kleinhausen', strasse: 'Waldweg', plz: '14822' });
});
