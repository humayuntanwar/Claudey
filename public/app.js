// Shared utilities
function daysBadgeClass(days) {
  if (days < 14) return 'urgent';
  if (days <= 45) return 'mid';
  return 'far';
}

function fmtDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtTimestamp(ts) {
  const d = new Date(ts);
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── PAGE 1: Daily Feed ──────────────────────────────────────────────────────
const Feed = {
  async init() {
    const status = document.getElementById('feed-status');
    const table  = document.getElementById('feed-table');
    const tbody  = document.getElementById('feed-tbody');
    const meta   = document.getElementById('feed-meta');

    try {
      const resp = await fetch('/api/feed');
      const data = await resp.json();

      if (data.error) {
        status.textContent = 'Error: ' + data.error;
        status.classList.add('error');
        return;
      }

      const results = data.results || [];
      meta.textContent = `${results.length} tickers found · earnings in 14–45 days`;

      if (results.length === 0) {
        status.textContent = 'No earnings events found in the 14–45 day window.';
        return;
      }

      status.style.display = 'none';
      table.style.display = 'table';
      tbody.innerHTML = '';

      for (const item of results) {
        const tr = document.createElement('tr');
        const badgeClass = daysBadgeClass(item.daysUntil);
        tr.innerHTML = `
          <td class="ticker-sym">${escHtml(item.ticker)}</td>
          <td class="company-name" title="${escHtml(item.company)}">${escHtml(item.company)}</td>
          <td>${fmtDate(item.earningsDate)}</td>
          <td><span class="days-badge ${badgeClass}">${item.daysUntil}d</span></td>
          <td>${escHtml(item.marketCap || 'N/A')}</td>
          <td>
            <button class="btn btn-add" data-ticker="${escHtml(item.ticker)}">+ Add</button>
          </td>
        `;
        tbody.appendChild(tr);
      }

      tbody.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-add');
        if (!btn) return;
        const ticker = btn.dataset.ticker;
        const row = results.find(r => r.ticker === ticker);
        if (row) Feed.addToWatchlist(row, btn);
      });

    } catch (err) {
      status.textContent = 'Failed to load feed: ' + err.message;
      status.classList.add('error');
    }
  },

  async addToWatchlist(item, btn) {
    btn.disabled = true;
    btn.textContent = '...';
    try {
      const resp = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item),
      });
      const data = await resp.json();
      if (resp.status === 409) {
        btn.textContent = 'Added';
        btn.style.color = 'var(--text-dim)';
      } else if (!resp.ok) {
        btn.textContent = data.error || 'Error';
        btn.style.color = 'var(--red)';
        btn.disabled = false;
      } else {
        btn.textContent = 'Saved';
        btn.style.color = 'var(--green)';
        btn.style.borderColor = 'var(--green)';
      }
    } catch (err) {
      btn.textContent = 'Error';
      btn.style.color = 'var(--red)';
      btn.disabled = false;
    }
  },
};

// ─── PAGE 2: Watchlist ───────────────────────────────────────────────────────
const Watchlist = {
  items: [],

  async init() {
    await Watchlist.load();
  },

  async load() {
    const status = document.getElementById('wl-status');
    const table  = document.getElementById('wl-table');
    const tbody  = document.getElementById('wl-tbody');
    const meta   = document.getElementById('wl-meta');

    try {
      const resp = await fetch('/api/watchlist');
      Watchlist.items = await resp.json();

      meta.textContent = `${Watchlist.items.length}/2 slots used`;

      if (Watchlist.items.length === 0) {
        status.textContent = 'Watchlist is empty. Add tickers from the Daily Feed.';
        status.style.display = '';
        table.style.display = 'none';
        return;
      }

      status.style.display = 'none';
      table.style.display = 'table';
      tbody.innerHTML = '';

      for (const item of Watchlist.items) {
        Watchlist.renderRow(item, tbody);
      }

    } catch (err) {
      status.textContent = 'Failed to load watchlist: ' + err.message;
      status.classList.add('error');
    }
  },

  renderRow(item, tbody) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const deadline = new Date(item.killDeadline + 'T00:00:00');
    const deadlineExpired = today > deadline && item.status === 'WATCH';
    const deadlineClass = deadlineExpired ? 'deadline-expired' : 'deadline-ok';
    const badgeClass = daysBadgeClass(item.daysUntil);

    const tr = document.createElement('tr');
    tr.dataset.ticker = item.ticker;
    tr.innerHTML = `
      <td class="ticker-sym">${escHtml(item.ticker)}</td>
      <td>${fmtDate(item.earningsDate)}</td>
      <td><span class="days-badge ${badgeClass}">${item.daysUntil}d</span></td>
      <td>
        <input class="thesis-input" type="text"
          placeholder="Enter thesis..."
          value="${escHtml(item.thesis || '')}"
          data-ticker="${escHtml(item.ticker)}">
      </td>
      <td>
        <select class="status-select" data-ticker="${escHtml(item.ticker)}">
          <option value="WATCH" ${item.status === 'WATCH' ? 'selected' : ''} class="status-WATCH">WATCH</option>
          <option value="ENTER" ${item.status === 'ENTER' ? 'selected' : ''} class="status-ENTER">ENTER</option>
          <option value="KILL"  ${item.status === 'KILL'  ? 'selected' : ''} class="status-KILL">KILL</option>
        </select>
      </td>
      <td class="${deadlineClass}">${fmtDate(item.killDeadline)}</td>
      <td style="white-space:nowrap">
        <button class="btn btn-analyse" data-ticker="${escHtml(item.ticker)}">Analyse</button>
        &nbsp;
        <button class="btn btn-remove" data-ticker="${escHtml(item.ticker)}">Remove</button>
      </td>
    `;
    tbody.appendChild(tr);

    // Analysis result row (hidden)
    const trResult = document.createElement('tr');
    trResult.classList.add('analysis-row');
    trResult.dataset.resultFor = item.ticker;
    trResult.style.display = 'none';
    trResult.innerHTML = `<td colspan="7"></td>`;
    tbody.appendChild(trResult);

    // Wire up events
    const thesisInput = tr.querySelector('.thesis-input');
    let thesisTimer;
    thesisInput.addEventListener('input', () => {
      clearTimeout(thesisTimer);
      thesisTimer = setTimeout(() => {
        Watchlist.updateField(item.ticker, { thesis: thesisInput.value });
      }, 600);
    });

    const statusSelect = tr.querySelector('.status-select');
    statusSelect.addEventListener('change', () => {
      Watchlist.updateField(item.ticker, { status: statusSelect.value });
      statusSelect.className = `status-select status-${statusSelect.value}`;
    });
    statusSelect.className = `status-select status-${item.status}`;

    tr.querySelector('.btn-analyse').addEventListener('click', () => {
      Watchlist.analyse(item.ticker);
    });

    tr.querySelector('.btn-remove').addEventListener('click', () => {
      Watchlist.remove(item.ticker);
    });
  },

  async updateField(ticker, fields) {
    try {
      await fetch(`/api/watchlist/${ticker}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fields),
      });
    } catch (err) {
      console.error('Update failed:', err);
    }
  },

  async remove(ticker) {
    try {
      await fetch(`/api/watchlist/${ticker}`, { method: 'DELETE' });
      await Watchlist.load();
    } catch (err) {
      console.error('Remove failed:', err);
    }
  },

  async analyse(ticker) {
    const btn = document.querySelector(`.btn-analyse[data-ticker="${ticker}"]`);
    const resultRow = document.querySelector(`tr[data-result-for="${ticker}"]`);

    if (btn) { btn.disabled = true; btn.textContent = 'Analysing...'; }

    // Save current thesis before analysing
    const thesisInput = document.querySelector(`.thesis-input[data-ticker="${ticker}"]`);
    if (thesisInput) {
      await Watchlist.updateField(ticker, { thesis: thesisInput.value });
    }

    try {
      const resp = await fetch(`/api/analyse/${ticker}`, { method: 'POST' });
      const data = await resp.json();

      if (btn) { btn.disabled = false; btn.textContent = 'Analyse'; }

      if (!resp.ok) {
        if (resultRow) {
          resultRow.style.display = '';
          resultRow.querySelector('td').innerHTML =
            `<span class="msg error">Error: ${escHtml(data.error)}</span>`;
        }
        return;
      }

      if (resultRow) {
        resultRow.style.display = '';
        const verdictColor = data.verdict === 'ENTER' ? 'var(--green)'
                           : data.verdict === 'KILL'  ? 'var(--red)'
                           : 'var(--yellow)';
        resultRow.querySelector('td').innerHTML = `
          <div class="verdict-line" style="color:${verdictColor}">
            VERDICT: ${escHtml(data.verdict)}${data.confidence ? ` · Confidence: ${data.confidence}/10` : ''}
          </div>
          <div class="log-reasoning">${escHtml(data.reasoning)}</div>
        `;
      }

    } catch (err) {
      if (btn) { btn.disabled = false; btn.textContent = 'Analyse'; }
      if (resultRow) {
        resultRow.style.display = '';
        resultRow.querySelector('td').innerHTML =
          `<span class="msg error">Error: ${escHtml(err.message)}</span>`;
      }
    }
  },
};

// ─── PAGE 3: Log ─────────────────────────────────────────────────────────────
const Log = {
  async init() {
    const status = document.getElementById('log-status');
    const feed   = document.getElementById('log-feed');
    const meta   = document.getElementById('log-meta');

    try {
      const resp = await fetch('/api/log');
      const entries = await resp.json();

      meta.textContent = `${entries.length} entries`;

      if (entries.length === 0) {
        status.textContent = 'No analysis entries yet. Use Analyse on the Watchlist page.';
        return;
      }

      status.style.display = 'none';

      for (const entry of entries) {
        const verdictColor = entry.verdict === 'ENTER' ? 'var(--green)'
                           : entry.verdict === 'KILL'  ? 'var(--red)'
                           : 'var(--yellow)';
        const div = document.createElement('div');
        div.classList.add('log-entry');
        div.innerHTML = `
          <div class="log-meta">
            <span class="log-ticker">${escHtml(entry.ticker)}</span>
            <span class="verdict-line" style="color:${verdictColor};font-size:12px;">
              ${escHtml(entry.verdict)}
            </span>
            ${entry.confidence ? `<span class="log-confidence">confidence: ${entry.confidence}/10</span>` : ''}
            <span class="log-time">${fmtTimestamp(entry.timestamp)}</span>
          </div>
          <div class="log-reasoning">${escHtml(entry.reasoning)}</div>
        `;
        feed.appendChild(div);
      }

    } catch (err) {
      status.textContent = 'Failed to load log: ' + err.message;
      status.classList.add('error');
    }
  },
};
