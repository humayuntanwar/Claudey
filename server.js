require('dotenv').config();
const express = require('express');
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');
const Anthropic = require('@anthropic-ai/sdk').default || require('@anthropic-ai/sdk');

const app = express();
const PORT = 3000;

const WATCHLIST_FILE = path.join(__dirname, 'data', 'watchlist.json');
const LOG_FILE = path.join(__dirname, 'data', 'log.json');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

function readJSON(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function writeJSON(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function daysBetween(dateStr) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  return Math.round((target - today) / (1000 * 60 * 60 * 24));
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}

function formatMarketCap(val) {
  if (!val) return 'N/A';
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(0)}M`;
  return `$${val}`;
}

// GET /api/feed — fetch upcoming earnings from Polygon
app.get('/api/feed', async (req, res) => {
  const key = process.env.POLYGON_API_KEY;
  if (!key) return res.status(500).json({ error: 'POLYGON_API_KEY not set' });

  const today = new Date();
  const dateFrom = addDays(today, 14);
  const dateTo = addDays(today, 45);

  try {
    const earningsUrl = `https://api.polygon.io/v2/reference/earnings?apiKey=${key}&from=${dateFrom}&to=${dateTo}&limit=50`;
    const earningsResp = await fetch(earningsUrl);
    const earningsData = await earningsResp.json();

    if (!earningsData.results || !Array.isArray(earningsData.results)) {
      return res.json({ results: [] });
    }

    const tickers = earningsData.results;
    const enriched = [];

    for (const item of tickers) {
      const ticker = item.ticker;
      const earningsDate = item.eps_reporting_date || item.report_date;
      if (!ticker || !earningsDate) continue;

      try {
        const detailsUrl = `https://api.polygon.io/v3/reference/tickers/${ticker}?apiKey=${key}`;
        const detailsResp = await fetch(detailsUrl);
        const detailsData = await detailsResp.json();
        const marketCap = detailsData.results?.market_cap || null;

        if (marketCap !== null) {
          if (marketCap < 300_000_000 || marketCap > 50_000_000_000) continue;
        }

        const days = daysBetween(earningsDate);
        enriched.push({
          ticker,
          company: detailsData.results?.name || item.company_name || ticker,
          earningsDate,
          daysUntil: days,
          marketCap: formatMarketCap(marketCap),
          marketCapRaw: marketCap,
        });
      } catch {
        // skip tickers that fail detail lookup
      }
    }

    enriched.sort((a, b) => a.daysUntil - b.daysUntil);
    res.json({ results: enriched });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/watchlist
app.get('/api/watchlist', (req, res) => {
  const list = readJSON(WATCHLIST_FILE);
  const updated = list.map(item => ({
    ...item,
    daysUntil: daysBetween(item.earningsDate),
  }));
  res.json(updated);
});

// POST /api/watchlist — add ticker
app.post('/api/watchlist', (req, res) => {
  const list = readJSON(WATCHLIST_FILE);
  const { ticker, company, earningsDate, daysUntil, marketCap } = req.body;

  if (list.find(t => t.ticker === ticker)) {
    return res.status(409).json({ error: 'Ticker already on watchlist' });
  }

  const today = new Date().toISOString().split('T')[0];
  const entry = {
    ticker,
    company,
    earningsDate,
    daysUntil,
    marketCap,
    dateAdded: today,
    status: 'WATCH',
    thesis: '',
    killDeadline: addDays(today, 30),
  };

  list.push(entry);
  writeJSON(WATCHLIST_FILE, list);
  res.json(entry);
});

// PATCH /api/watchlist/:ticker — update thesis/status
app.patch('/api/watchlist/:ticker', (req, res) => {
  const list = readJSON(WATCHLIST_FILE);
  const idx = list.findIndex(t => t.ticker === req.params.ticker);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });

  const { thesis, status } = req.body;
  if (thesis !== undefined) list[idx].thesis = thesis;
  if (status !== undefined) list[idx].status = status;

  writeJSON(WATCHLIST_FILE, list);
  res.json(list[idx]);
});

// DELETE /api/watchlist/:ticker
app.delete('/api/watchlist/:ticker', (req, res) => {
  let list = readJSON(WATCHLIST_FILE);
  const before = list.length;
  list = list.filter(t => t.ticker !== req.params.ticker);
  if (list.length === before) return res.status(404).json({ error: 'Not found' });
  writeJSON(WATCHLIST_FILE, list);
  res.json({ ok: true });
});

// POST /api/analyse/:ticker — Claude analysis
app.post('/api/analyse/:ticker', async (req, res) => {
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (!anthropicKey) return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set' });

  const list = readJSON(WATCHLIST_FILE);
  const item = list.find(t => t.ticker === req.params.ticker);
  if (!item) return res.status(404).json({ error: 'Ticker not on watchlist' });

  const days = daysBetween(item.earningsDate);
  const thesis = item.thesis || 'No thesis provided.';

  const client = new Anthropic({ apiKey: anthropicKey });

  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      system: `You are a pre-catalyst stock analyst. Rules: if catalyst is under 14 days, verdict must be ENTER or KILL, never WATCH. If 14-45 days away, evaluate thesis and return ENTER or WATCH or KILL. If over 45 days, WATCH or KILL only. Never recommend WATCH inside 14 days.`,
      messages: [
        {
          role: 'user',
          content: `Ticker: ${item.ticker}. Earnings in ${days} days. Thesis: ${thesis}. Evaluate and return: VERDICT (ENTER/WATCH/KILL), 3 bullet reasons, confidence 1-10.`,
        },
      ],
    });

    const text = message.content[0]?.text || '';

    // Parse verdict and confidence from response
    const verdictMatch = text.match(/\b(ENTER|WATCH|KILL)\b/i);
    const confidenceMatch = text.match(/confidence[:\s]+(\d+)/i) || text.match(/(\d+)\/10/);
    const verdict = verdictMatch ? verdictMatch[1].toUpperCase() : 'WATCH';
    const confidence = confidenceMatch ? parseInt(confidenceMatch[1]) : null;

    // Append to log
    const log = readJSON(LOG_FILE);
    const logEntry = {
      timestamp: new Date().toISOString(),
      ticker: item.ticker,
      verdict,
      reasoning: text,
      confidence,
    };
    log.unshift(logEntry);
    writeJSON(LOG_FILE, log);

    res.json({ verdict, reasoning: text, confidence });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/log
app.get('/api/log', (req, res) => {
  const log = readJSON(LOG_FILE);
  res.json(log);
});

app.listen(PORT, () => {
  console.log(`Stock scanner running at http://localhost:${PORT}`);
});
