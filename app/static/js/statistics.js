// Statistics pages: auto-submitting selects, AGS suggestions and Plotly charts.
// Plotly is a global from build/plotly.min.js (see _macros_stats_menu.html).

document.addEventListener('change', (e) => {
  if (e.target.matches('select[data-autosubmit]')) e.target.form.submit();
});

// Pick an AGS suggestion: show the name, submit the code
document.addEventListener('click', (e) => {
  const li = e.target.closest('#vorschlaege li');
  if (!li) return;
  document.getElementById('ags_input').value = li.dataset.gen;
  document.getElementById('ags').value = li.dataset.ags;
  document.getElementById('vorschlaege').innerHTML = '';
});

const barStyle = {
  hoverinfo: 'none',
  textposition: 'auto',
  marker: {
    color: '#5bae31',
    opacity: 0.6,
    line: { color: 'rgb(8,48,107)', width: 1.5 }
  }
};
const transparent = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)'
};

const charts = {
  geschlecht(id, values) {
    const keys = ['Männchen', 'Weibchen', 'Nymphen', 'Ootheken', 'Andere'];
    const x = keys.filter((key) => Object.hasOwn(values, key));
    const y = x.map((key) => values[key]);
    Plotly.newPlot(id, [{ ...barStyle, x, y, type: 'bar', text: y.map(String) }], {
      title: { text: 'Summen Geschlecht/Entwicklungsstadium', font: { size: 18 } },
      barmode: 'stack',
      margin: { l: 40, r: 10, b: 30, t: 40, pad: 4 },
      ...transparent
    }, { displayModeBar: false });
  },

  zeiten(id, daten) {
    const x = Array.from({ length: 24 }, (_, i) => i);
    const y = x.map((h) => daten[h] ?? 0);
    Plotly.newPlot(id, [{
      ...barStyle, x, y, type: 'scatter', mode: 'lines+markers', text: y.map(String)
    }], {
      title: { text: 'Meldungen pro Stunde', font: { size: 18 } },
      xaxis: { type: 'category' },
      margin: { l: 40, r: 10, b: 30, t: 40, pad: 4 },
      ...transparent
    }, { displayModeBar: false });
  },

  datum(id, { x, y }) {
    Plotly.newPlot(id, [{ ...barStyle, x, y, type: 'bar', text: y.map(String) }], {
      showlegend: false,
      margin: { l: 40, r: 10, b: 30, t: 10, pad: 4 },
      ...transparent
    }, { scrollZoom: true, displayModeBar: false });
  },

  'meld-fund'(id, { trace1, trace2 }) {
    Plotly.newPlot(id, [
      { x: trace1.x, y: trace1.y, name: 'Funddatum', type: 'bar' },
      { x: trace2.x, y: trace2.y, name: 'Meldedatum', type: 'bar' }
    ], {
      barmode: 'group',
      margin: { l: 40, r: 10, b: 30, t: 10, pad: 4 },
      ...transparent
    }, { displayModeBar: false });
  }
};

const chart = document.querySelector('[data-chart]');
if (chart) {
  const data = JSON.parse(document.getElementById('chart-data').textContent);
  charts[chart.dataset.chart](chart.id, data);
}
