import { describe, expect, test } from 'bun:test';
import { parseCoordinateInput } from '../../app/static/js/coordinate-input.js';

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
