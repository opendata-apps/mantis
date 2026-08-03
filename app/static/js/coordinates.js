// Coordinate helpers shared by the report form and the reviewer modal.
// The accepted range is rendered onto <body> from the Python constants in
// app/tools/coordinate_validation.py — never hardcode the numbers here. The
// keys match the server's coord_type vocabulary: "latitude" / "longitude".
const RANGES = JSON.parse(document.body.dataset.coordRange);

// A German phone puts a comma on the inputmode="decimal" keypad, so accept it
// like the server does. parseFloat("52,52") would silently yield 52 — a 58 km
// error — which is why every manual input goes through here.
export const parseCoordinate = (value) => {
    const number = parseFloat(String(value).replace(',', '.'));
    return Number.isFinite(number) ? number : null;
};

export const inRange = (value, coordType) =>
    value >= RANGES[coordType][0] && value <= RANGES[coordType][1];

export const inCoordRange = (lat, lon) =>
    inRange(lat, 'latitude') && inRange(lon, 'longitude');

// Matches the server-side formatting in coordinate_validation._format_bound
// (30.0 -> "30", 44.83 -> "44,83") without hand-rolling the separator.
const de = new Intl.NumberFormat('de-DE');

export const coordRangeMessage = () =>
    `Fundort liegt außerhalb des gültigen Bereichs (Breitengrad: ${de.format(RANGES.latitude[0])} bis ${de.format(RANGES.latitude[1])}, Längengrad: ${de.format(RANGES.longitude[0])} bis ${de.format(RANGES.longitude[1])}).`;
