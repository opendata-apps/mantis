const COORDINATE_PATTERN = /^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?$/;

export const parseCoordinateInput = (raw, min, max) => {
    const text = String(raw ?? '').trim();
    if (!COORDINATE_PATTERN.test(text)) return null;

    const value = Number(text.replace(',', '.'));
    return Number.isFinite(value) && value >= min && value <= max ? value : null;
};
