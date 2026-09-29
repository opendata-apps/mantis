// Nominatim allows at most 1 request per second:
// https://operations.osmfoundation.org/policies/nominatim/
// Callers that geocode repeatedly are responsible for that spacing.
export async function reverseGeocode(lat, lng, { agsUrl, signal } = {}) {
    const url = new URL('https://nominatim.openstreetmap.org/reverse');
    url.search = new URLSearchParams({
        format: 'jsonv2', lat, lon: lng, zoom: 18, addressdetails: 1, 'accept-language': 'de',
    });
    const [nominatimRes, ags] = await Promise.all([
        fetch(url, { signal }),
        agsUrl ? fetchAgs(`${agsUrl}?lat=${lat}&lon=${lng}`, signal) : {},
    ]);
    if (!nominatimRes.ok) throw new Error(`Nominatim HTTP ${nominatimRes.status}`);
    const data = await nominatimRes.json();
    if (data.error) throw new Error(`Nominatim: ${data.error}`);

    const a = data.address || {};
    const street = a.road || a.pedestrian || a.cycleway || a.path || a.footway || '';
    return {
        plz: a.postcode || '',
        ort: a.city || a.town || a.village || a.hamlet || '',
        strasse: a.house_number ? `${street} ${a.house_number}`.trim() : street,
        // AGS spatial data is authoritative for land/kreis; Nominatim as fallback
        kreis: ags.kreis || a.county || a.borough || '',
        land: ags.land || a.state || a.city || '',
    };
}

async function fetchAgs(url, signal) {
    try {
        const res = await fetch(url, { signal });
        return res.ok ? await res.json() : {};
    } catch {
        return {};
    }
}
