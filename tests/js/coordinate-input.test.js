import { describe, expect, test } from 'bun:test';
import { coordinatesInRange, parseCoordinateInput } from '../../app/static/js/coordinate-input.js';

// Mirrors COORDINATE_RANGES in app/tools/coordinate_validation.py.
const RANGES = { latitude: [24.6, 60.0], longitude: [-20.0, 44.83] };

describe('coordinatesInRange', () => {
    test('accepts a German sighting', () => {
        expect(coordinatesInRange(52.3906, 13.0645, RANGES)).toBe(true);
    });

    test.each([
        ['null island — a camera with no GPS fix', 0, 0],
        ['transposed German pair', 13.0645, 52.3906],
        ['flipped hemisphere', -52.3906, 13.0645],
        ['Sydney', -33.8688, 151.2093],
    ])('rejects %s', (_label, lat, lng) => {
        expect(coordinatesInRange(lat, lng, RANGES)).toBe(false);
    });

    test('rejects NaN instead of treating it as a bound', () => {
        expect(coordinatesInRange(NaN, 13.0645, RANGES)).toBe(false);
        expect(coordinatesInRange(52.3906, NaN, RANGES)).toBe(false);
    });

    // The pair every rejected case used to be clamped onto.
    test('the box corner is only reachable by asking for it', () => {
        expect(coordinatesInRange(24.6, 44.83, RANGES)).toBe(true);
        expect(coordinatesInRange(24.59, 44.84, RANGES)).toBe(false);
    });
});

describe('parseCoordinateInput', () => {
    test.each([
        ['52.833451', 24.6, 60, 52.833451],
        ['52,833451', 24.6, 60, 52.833451],
        ['13,819727', -20, 44.83, 13.819727],
        [' +52,5 ', 24.6, 60, 52.5],
        ['5.25e1', 24.6, 60, 52.5],
    ])('parses %s without truncating the decimal part', (raw, min, max, expected) => {
        expect(parseCoordinateInput(raw, min, max)).toBe(expected);
    });

    test.each([
        '',
        '52,5km',
        '52,5.1',
        '52,5,1',
        'NaN',
        'Infinity',
    ])('rejects %s instead of accepting a numeric prefix', (raw) => {
        expect(parseCoordinateInput(raw, 24.6, 60)).toBeNull();
    });

    test('enforces the server-provided range', () => {
        expect(parseCoordinateInput('24,6', 24.6, 60)).toBe(24.6);
        expect(parseCoordinateInput('60', 24.6, 60)).toBe(60);
        expect(parseCoordinateInput('24.59', 24.6, 60)).toBeNull();
        expect(parseCoordinateInput('60.01', 24.6, 60)).toBeNull();
    });
});
