const COORDINATE_PATTERN = /^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?$/;

export const parseCoordinateInput = (raw, min, max) => {
    const text = String(raw ?? '').trim();
    if (!COORDINATE_PATTERN.test(text)) return null;

    const value = Number(text.replace(',', '.'));
    return Number.isFinite(value) && value >= min && value <= max ? value : null;
};

// The same check for a pair that arrives as numbers rather than typed text:
// EXIF tags, map events, prefilled fields.
export const coordinatesInRange = (lat, lng, ranges) =>
    Number.isFinite(lat) && Number.isFinite(lng)
    && lat >= ranges.latitude[0] && lat <= ranges.latitude[1]
    && lng >= ranges.longitude[0] && lng <= ranges.longitude[1];
