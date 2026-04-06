/**
 * static/script.js — Pro v4
 */

// ── State ─────────────────────────────────────
let priceChart = null, volumeChart = null, compareChart = null;
let currentTicker = "", currentTimeframe = "1m";
let currentPriceData = [], chartType = "line";
let showSMA20 = false, showSMA50 = false, acIndex = -1;
let recentSearches = JSON.parse(localStorage.getItem("rs") || "[]");
let debounceTimer = null;
const WL = ["NVDA","AAPL","TSLA","AMZN","META","GOOGL","MSFT","AMD"];

const FACTOR_TIPS = {
    "RSI Trend": "Relative Strength Index measures momentum on a 0-100 scale. Above 70 = overbought, below 30 = oversold.",
    "MACD Signal": "Moving Average Convergence Divergence tracks trend direction. Bullish when MACD crosses above signal line.",
    "Price Momentum": "Compares current price to 50-day moving average. Above = uptrend, below = downtrend.",
    "Volume Trend": "Compares current volume to 10-day average. High volume confirms price moves.",
    "Volatility": "10-day standard deviation of returns. Higher values mean more price uncertainty.",
    "Bollinger Position": "Shows where price sits within Bollinger Bands. Near top = potential resistance, near bottom = potential support.",
};

const IC = {
    bullish: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round"><polyline points="17 7 7 17"/><polyline points="7 7 7 17 17 17"/></svg>`,
    bearish: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round"><polyline points="7 7 17 17"/><polyline points="17 7 17 17 7 17"/></svg>`,
    neutral: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
    high: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2.5" stroke-linecap="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`,
    low: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>`,
    normal: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4f596d" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/></svg>`,
};

// ── Init ──────────────────────────────────────
renderRecent();
loadWL();
loadPredLog();

const $i = document.getElementById("ticker-input");
const $btn = document.getElementById("predict-btn");
const $err = document.getElementById("error-msg");
const $load = document.getElementById("loading");
const $dash = document.getElementById("dashboard");
const $ac = document.getElementById("autocomplete-list");
const $spin = document.getElementById("search-spinner");

$i.addEventListener("keydown", (e) => {
    const items = $ac.querySelectorAll(".autocomplete-item");
    if (e.key === "ArrowDown") { e.preventDefault(); acIndex = Math.min(acIndex + 1, items.length - 1); hlAc(items); }
    else if (e.key === "ArrowUp") { e.preventDefault(); acIndex = Math.max(acIndex - 1, -1); hlAc(items); }
    else if (e.key === "Enter") { e.preventDefault(); if (acIndex >= 0 && items[acIndex]) items[acIndex].click(); else { $ac.classList.add("hidden"); handlePredict(); } }
    else if (e.key === "Escape") { $ac.classList.add("hidden"); acIndex = -1; }
});

$i.addEventListener("input", () => {
    clearTimeout(debounceTimer); acIndex = -1;
    const q = $i.value.trim();
    if (!q) { $ac.classList.add("hidden"); return; }
    $spin.classList.remove("hidden");
    debounceTimer = setTimeout(() => fetchAc(q), 180);
});

document.addEventListener("click", (e) => { if (!e.target.closest(".search-section")) { $ac.classList.add("hidden"); acIndex = -1; } });

document.querySelectorAll(".tf-btn").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".tf-btn").forEach((x) => x.classList.remove("active"));
    b.classList.add("active"); currentTimeframe = b.dataset.tf;
    if (currentTicker) fetchChart(currentTicker, currentTimeframe);
}));

function hlAc(items) { items.forEach((el, i) => el.classList.toggle("active", i === acIndex)); }
function setChartType(t) { chartType = t; document.querySelectorAll(".ct-btn").forEach((b) => b.classList.toggle("active", b.dataset.type === t)); if (currentPriceData.length) renderChart(currentPriceData); }

// ── Autocomplete ──────────────────────────────
async function fetchAc(q) {
    try {
        const r = await fetch(`/search?q=${encodeURIComponent(q)}`);
        const d = await r.json(); $spin.classList.add("hidden");
        if (!d.length) { $ac.classList.add("hidden"); return; }
        const u = q.toUpperCase();
        $ac.innerHTML = d.map((s) => `<div class="autocomplete-item" onclick="sel('${s.ticker}')"><span class="ac-ticker">${hl(s.ticker,u)}</span><span class="ac-name">${hl(s.name,u)}</span>${s.exchange?`<span class="ac-exchange">${s.exchange}</span>`:""}</div>`).join("");
        $ac.classList.remove("hidden");
    } catch { $spin.classList.add("hidden"); }
}

function hl(t, q) { const i = t.toUpperCase().indexOf(q); if (i === -1) return t; return t.slice(0,i)+`<span class="ac-highlight">${t.slice(i,i+q.length)}</span>`+t.slice(i+q.length); }
function sel(t) { $i.value = t; $ac.classList.add("hidden"); acIndex = -1; handlePredict(); }
function qs(t) { $i.value = t; handlePredict(); }

// ── Main ──────────────────────────────────────
async function handlePredict() {
    const t = $i.value.trim().toUpperCase();
    if (!t) { showErr("Enter a ticker or company name."); return; }
    hideErr(); $dash.classList.add("hidden"); showLoad();
    currentTicker = t; addRecent(t);

    try {
        const [pR, iR, nR, hR] = await Promise.all([
            fetch("/predict", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ticker:t}) }),
            fetch(`/info/${t}`), fetch(`/news/${t}`), fetch(`/history/${t}?tf=${currentTimeframe}`),
        ]);
        const [pD, iD, nD, hD] = await Promise.all([pR.json(), iR.json(), nR.json(), hR.json()]);
        if (!pR.ok) { showErr(pD.error || "Failed."); return; }

        renderHeader(iD, pD); renderPred(pD); renderStats(iD);
        renderChart(hD); renderExpl(pD); renderNews(nD); loadPredLog();
        $dash.classList.remove("hidden");
    } catch (e) { showErr("Network error. Is the server running?"); console.error(e); }
    finally { hideLoad(); }
}

// ── Header ────────────────────────────────────
function renderHeader(i, p) {
    document.getElementById("company-name").textContent = i.company_name || p.company_name || p.ticker;
    document.getElementById("company-ticker").textContent = p.ticker;
    document.getElementById("company-exchange").textContent = i.exchange || "";
    document.getElementById("company-sector").textContent = i.sector || "";
    document.getElementById("company-industry").textContent = i.industry || "";
    document.getElementById("header-price").textContent = `$${Number(i.current_price || p.current_price).toFixed(2)}`;

    const aE = document.getElementById("header-change-abs"), pE = document.getElementById("header-change-pct");
    if (i.day_change != null) { const s = i.day_change >= 0 ? "+" : ""; aE.textContent = `${s}${i.day_change.toFixed(2)}`; aE.className = "price-change-abs " + (i.day_change >= 0 ? "up" : "down"); } else aE.textContent = "";
    if (i.day_change_pct != null) { const s = i.day_change_pct >= 0 ? "+" : ""; pE.textContent = `(${s}${i.day_change_pct.toFixed(2)}%)`; pE.className = "price-change-pct " + (i.day_change_pct >= 0 ? "up" : "down"); } else pE.textContent = "";
}

// ── Prediction ────────────────────────────────
function renderPred(d) {
    const up = d.direction === "UP";
    const dir = document.getElementById("result-direction");
    dir.textContent = up ? "▲ UP" : "▼ DOWN";
    dir.className = "result-direction " + (up ? "up" : "down");

    document.getElementById("prediction-subtitle").textContent = "Next day direction forecast";
    document.getElementById("horizon-badge").textContent = d.model_info?.prediction_horizon || "Next Trading Day";

    const upPct = (d.prob_up * 100).toFixed(1), dnPct = (d.prob_down * 100).toFixed(1);
    document.getElementById("prob-breakdown").innerHTML = `
        <div class="prob-item">
            <div class="prob-label">Bullish</div>
            <div class="prob-value up">${upPct}%</div>
            <div class="prob-bar-wrapper"><div class="prob-bar-fill up" style="width:${upPct}%"></div></div>
        </div>
        <div class="prob-item">
            <div class="prob-label">Bearish</div>
            <div class="prob-value down">${dnPct}%</div>
            <div class="prob-bar-wrapper"><div class="prob-bar-fill down" style="width:${dnPct}%"></div></div>
        </div>`;

    const pct = Math.round(d.confidence * 100);
    const bar = document.getElementById("confidence-bar");
    bar.style.width = pct + "%"; bar.style.background = up ? "var(--green)" : "var(--red)";
    document.getElementById("confidence-value").textContent = pct + "%";
    document.getElementById("prediction-summary").textContent = d.summary || "";

    const mi = d.model_info || {};
    const acc = mi.accuracy != null ? `Accuracy: <span class="accuracy-highlight">${(mi.accuracy * 100).toFixed(1)}%</span> · ` : "";
    document.getElementById("model-info").innerHTML = `Model: ${mi.model_type || "N/A"} · ${acc}Features: ${mi.num_features || "—"} · Loaded: ${mi.last_loaded || "—"}`;
}

// ── Stats ─────────────────────────────────────
function renderStats(i) {
    const f = (v) => { if (v == null) return "—"; if (typeof v === "number") { if (Math.abs(v) >= 1e12) return `$${(v/1e12).toFixed(2)}T`; if (Math.abs(v) >= 1e9) return `$${(v/1e9).toFixed(2)}B`; if (Math.abs(v) >= 1e6) return `${(v/1e6).toFixed(1)}M`; return v.toLocaleString(); } return v; };
    const s = [
        {l:"Market Cap", v:f(i.market_cap)}, {l:"P/E Ratio", v:i.pe_ratio!=null?i.pe_ratio.toFixed(2):"—"},
        {l:"EPS", v:i.eps!=null?`$${i.eps.toFixed(2)}`:"—"}, {l:"Beta", v:i.beta!=null?i.beta.toFixed(2):"—"},
        {l:"Volume", v:f(i.volume)}, {l:"Avg Volume", v:f(i.avg_volume)},
        {l:"Div Yield", v:i.dividend_yield!=null?`${(i.dividend_yield*100).toFixed(2)}%`:"—"},
        {l:"Open", v:i.open_price!=null?`$${i.open_price.toFixed(2)}`:"—"},
        {l:"Day High", v:i.day_high!=null?`$${i.day_high.toFixed(2)}`:"—"},
        {l:"Day Low", v:i.day_low!=null?`$${i.day_low.toFixed(2)}`:"—"},
        {l:"52W High", v:i.week_52_high!=null?`$${i.week_52_high.toFixed(2)}`:"—"},
        {l:"52W Low", v:i.week_52_low!=null?`$${i.week_52_low.toFixed(2)}`:"—"},
    ];
    document.getElementById("stats-grid").innerHTML = s.map((x) => `<div class="stat-item"><span class="stat-label">${x.l}</span><span class="stat-value">${x.v}</span></div>`).join("");
}

// ── Chart ─────────────────────────────────────
function sma(d, p) { return d.map((_,i) => i<p-1?null:d.slice(i-p+1,i+1).reduce((a,b)=>a+b,0)/p); }

function grad(ctx, c, h) {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, c.replace(",1)", ",0.20)"));
    g.addColorStop(0.35, c.replace(",1)", ",0.08)"));
    g.addColorStop(0.7, c.replace(",1)", ",0.02)"));
    g.addColorStop(1, c.replace(",1)", ",0)"));
    return g;
}

// Crosshair plugin
const crosshairPlugin = {
    id: "crosshair",
    afterDraw(chart) {
        const active = chart.tooltip?.getActiveElements();
        if (!active || !active.length) return;
        const { ctx, chartArea: { top, bottom, left, right } } = chart;
        const x = active[0].element.x;
        const y = active[0].element.y;
        ctx.save();
        ctx.setLineDash([3, 3]);
        // Vertical line
        ctx.strokeStyle = "rgba(134,144,166,0.25)";
        ctx.lineWidth = 0.8;
        ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
        // Horizontal line
        ctx.strokeStyle = "rgba(134,144,166,0.18)";
        ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
        ctx.restore();
    }
};

function renderChart(hist) {
    if (!Array.isArray(hist) || !hist.length) return;
    currentPriceData = hist;

    const labels = hist.map(d => d.date);
    const closes = hist.map(d => d.close);
    const vols = hist.map(d => d.volume);

    const first = closes[0], last = closes[closes.length - 1];
    const chg = ((last - first) / first) * 100;
    const cEl = document.getElementById("chart-change");
    cEl.textContent = `${chg >= 0 ? "+" : ""}${chg.toFixed(2)}%`;
    cEl.className = "chart-change " + (chg >= 0 ? "up" : "down");

    const pos = chg >= 0;
    const lnC = pos ? "rgba(34,197,94,1)" : "rgba(239,68,68,1)";

    if (priceChart) priceChart.destroy();
    const pCtx = document.getElementById("price-chart").getContext("2d");
    const gFill = grad(pCtx, lnC, 380);

    let ds;
    if (chartType === "candle") {
        // Candlestick — brighter, wider, clearer
        const bodyC = hist.map(d => d.close >= d.open ? "#22c55e" : "#ef4444");
        const wickC = hist.map(d => d.close >= d.open ? "#4ade80" : "#f87171");
        ds = [
            {
                label: "OHLC", type: "bar",
                data: hist.map(d => [Math.min(d.open, d.close), Math.max(d.open, d.close)]),
                backgroundColor: bodyC, borderColor: bodyC,
                borderWidth: 1, barPercentage: 0.75, categoryPercentage: 0.9, order: 2,
            },
            {
                label: "Wick", type: "bar",
                data: hist.map(d => [d.low, d.high]),
                backgroundColor: wickC, borderColor: wickC,
                borderWidth: 0, barPercentage: 0.06, categoryPercentage: 0.9, order: 1,
            },
        ];
    } else {
        // Line chart — thicker, glowing, stronger gradient
        ds = [{
            label: "Close", data: closes,
            borderColor: lnC,
            backgroundColor: gFill,
            fill: true, tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: lnC,
            pointHoverBorderColor: "#fff",
            pointHoverBorderWidth: 2,
            borderWidth: 2.2,
            order: 1,
        }];
    }

    // SMA overlays — thinner, dashed, clear hierarchy
    if (showSMA20 && closes.length >= 20) {
        ds.push({
            label: "SMA 20", data: sma(closes, 20),
            borderColor: "rgba(234,179,8,0.55)", borderWidth: 0.9,
            borderDash: [4, 3], pointRadius: 0, fill: false, tension: 0.4, order: 10,
        });
    }
    if (showSMA50 && closes.length >= 50) {
        ds.push({
            label: "SMA 50", data: sma(closes, 50),
            borderColor: "rgba(139,92,246,0.45)", borderWidth: 0.9,
            borderDash: [4, 3], pointRadius: 0, fill: false, tension: 0.4, order: 11,
        });
    }

    // Grid — very subtle, horizontal > vertical
    const hGridC = "rgba(24,32,48,0.35)";
    const vGridC = "rgba(24,32,48,0.18)";
    const tickC = "#48526a";

    priceChart = new Chart(pCtx, {
        type: chartType === "candle" ? "bar" : "line",
        data: { labels, datasets: ds },
        plugins: [crosshairPlugin],
        options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            hover: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    display: ds.length > 1 && chartType === "line",
                    labels: { color: "#8690a6", font: { size: 10.5 }, boxWidth: 8, padding: 16 },
                },
                tooltip: {
                    backgroundColor: "rgba(6,9,16,0.96)",
                    titleColor: "#e2e7f0",
                    bodyColor: "#9aa3b8",
                    borderColor: "#1a2540",
                    borderWidth: 1,
                    displayColors: false,
                    padding: { top: 10, bottom: 10, left: 14, right: 14 },
                    titleFont: { size: 12, weight: "600" },
                    bodyFont: { size: 11.5 },
                    cornerRadius: 8,
                    caretSize: 5,
                    callbacks: {
                        title: (items) => {
                            if (!items[0]) return "";
                            // Format date nicely
                            try {
                                const d = new Date(items[0].label);
                                return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
                            } catch { return items[0].label; }
                        },
                        label: (ctx) => {
                            if (chartType === "candle") {
                                const d = hist[ctx.dataIndex];
                                if (!d) return "";
                                return [
                                    `Open: ${d.open.toFixed(2)}    High: ${d.high.toFixed(2)}`,
                                    `Low:  ${d.low.toFixed(2)}    Close: ${d.close.toFixed(2)}`,
                                ];
                            }
                            return ctx.parsed.y != null ? `Price: ${ctx.parsed.y.toFixed(2)}` : "";
                        },
                        afterLabel: (ctx) => {
                            if (ctx.datasetIndex === 0 && ctx.dataIndex > 0) {
                                const prev = closes[ctx.dataIndex - 1];
                                const cur = chartType === "candle" ? hist[ctx.dataIndex]?.close : ctx.parsed.y;
                                if (prev && cur) {
                                    const pctChg = ((cur - prev) / prev * 100);
                                    return `Change: ${pctChg >= 0 ? "+" : ""}${pctChg.toFixed(2)}%`;
                                }
                            }
                            return "";
                        },
                        afterBody: (items) => {
                            if (!items[0]) return "";
                            const idx = items[0].dataIndex;
                            const v = vols[idx];
                            if (v == null) return "";
                            return v >= 1e6 ? `Volume: ${(v / 1e6).toFixed(1)}M` : `Volume: ${v.toLocaleString()}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: tickC, maxTicksLimit: 6, font: { size: 10.5 }, maxRotation: 0 },
                    grid: { color: vGridC, lineWidth: 0.5 },
                },
                y: {
                    ticks: { color: tickC, font: { size: 10.5 }, callback: v => "$" + v.toFixed(0), padding: 6 },
                    grid: { color: hGridC, lineWidth: 0.5 },
                },
            },
        },
    });

    // ── Volume bars — softer, thinner ──────────
    if (volumeChart) volumeChart.destroy();
    const vCtx = document.getElementById("volume-chart").getContext("2d");
    const vC = hist.map(d => d.close >= d.open ? "rgba(34,197,94,0.18)" : "rgba(239,68,68,0.18)");

    volumeChart = new Chart(vCtx, {
        type: "bar",
        data: { labels, datasets: [{ data: vols, backgroundColor: vC, borderWidth: 0, barPercentage: 0.6, categoryPercentage: 0.9 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(6,9,16,0.96)", titleColor: "#e2e7f0", bodyColor: "#9aa3b8",
                    borderColor: "#1a2540", borderWidth: 1, displayColors: false, cornerRadius: 8,
                    callbacks: { label: (c) => { const v = c.parsed.y; return v >= 1e6 ? `Vol: ${(v / 1e6).toFixed(1)}M` : `Vol: ${v.toLocaleString()}`; } },
                },
            },
            scales: { x: { display: false }, y: { display: false, grid: { display: false } } },
        },
    });
}

async function fetchChart(t,tf) {
    try { const r=await fetch(`/history/${t}?tf=${tf}`); const d=await r.json(); if(Array.isArray(d))renderChart(d); } catch(e){console.error(e);}
}

function toggleIndicator(i) {
    const b = document.getElementById(`toggle-${i}`);
    if(i==="sma20"){showSMA20=!showSMA20;b.classList.toggle("active",showSMA20);}
    else{showSMA50=!showSMA50;b.classList.toggle("active",showSMA50);}
    if(currentPriceData.length) renderChart(currentPriceData);
}

// ── Compare ───────────────────────────────────
async function handleCompare() {
    const a=document.getElementById("compare-a").value.trim().toUpperCase();
    const b=document.getElementById("compare-b").value.trim().toUpperCase();
    if(!a||!b)return;

    try {
        const r=await fetch("/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tickers:[a,b],timeframe:currentTimeframe})});
        const data=await r.json();
        const w=document.getElementById("compare-chart-wrapper"); w.style.display="block";
        if(compareChart) compareChart.destroy();

        const colors = [{ l: "rgba(59,130,246,1)" }, { l: "rgba(234,179,8,1)" }];
        const tks = Object.keys(data);
        const perfs = {};

        const datasets = tks.map((t, i) => {
            const p = data[t].map(d => d.close); const base = p[0] || 1;
            const pctFinal = ((p[p.length - 1] - base) / base * 100);
            perfs[t] = pctFinal;
            return { label: `${t}`, data: p.map(v => ((v - base) / base) * 100), borderColor: colors[i].l, fill: false, tension: 0.35, pointRadius: 0, borderWidth: 2.2 };
        });

        const labels = data[tks[0]]?.map(d => d.date) || [];
        const ctx = document.getElementById("compare-chart").getContext("2d");

        compareChart = new Chart(ctx, {
            type: "line", data: { labels, datasets },
            plugins: [crosshairPlugin],
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { intersect: false, mode: "index" },
                plugins: {
                    legend: { labels: { color: "#8690a6", font: { size: 11 }, boxWidth: 10, padding: 16 } },
                    tooltip: {
                        backgroundColor: "rgba(6,9,16,0.96)", titleColor: "#e2e7f0", bodyColor: "#9aa3b8",
                        borderColor: "#1a2540", borderWidth: 1, cornerRadius: 8,
                        titleFont: { size: 12, weight: "600" }, bodyFont: { size: 11.5 },
                        padding: { top: 10, bottom: 10, left: 14, right: 14 },
                        callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.y >= 0 ? "+" : ""}${c.parsed.y.toFixed(2)}%` },
                    },
                },
                scales: {
                    x: { ticks: { color: "#48526a", maxTicksLimit: 6, font: { size: 10.5 }, maxRotation: 0 }, grid: { color: "rgba(24,32,48,0.18)" } },
                    y: { ticks: { color: "#48526a", font: { size: 10.5 }, callback: v => (v >= 0 ? "+" : "") + v.toFixed(1) + "%" }, grid: { color: "rgba(24,32,48,0.35)" } },
                },
            },
        });

        // Summary
        const sEl = document.getElementById("compare-summary");
        if (tks.length === 2) {
            const diff = Math.abs(perfs[tks[0]] - perfs[tks[1]]).toFixed(1);
            const winner = perfs[tks[0]] > perfs[tks[1]] ? tks[0] : tks[1];
            const loser = winner === tks[0] ? tks[1] : tks[0];
            sEl.innerHTML = `<strong>${winner}</strong> outperformed <strong>${loser}</strong> by ${diff}% over this period &nbsp;·&nbsp; ${tks[0]}: ${perfs[tks[0]]>=0?"+":""}${perfs[tks[0]].toFixed(1)}% &nbsp;·&nbsp; ${tks[1]}: ${perfs[tks[1]]>=0?"+":""}${perfs[tks[1]].toFixed(1)}%`;
            sEl.classList.remove("hidden");
        }
    } catch(e){console.error(e);}
}

// ── Explanations ──────────────────────────────
function renderExpl(d) {
    const el=document.getElementById("explanations-list");
    if(d.explanations?.length){
        el.innerHTML=d.explanations.map(ex=>{
            const tip=FACTOR_TIPS[ex.factor]||"";
            const factorHtml=tip?`<span class="factor-tooltip" data-tip="${tip}">${ex.factor}</span>`:ex.factor;
            return `<div class="explanation-item ${ex.signal}"><div class="explanation-icon-wrap">${IC[ex.signal]||IC.neutral}</div><div class="explanation-content"><div class="explanation-factor">${factorHtml}</div><div class="explanation-detail">${ex.detail}</div></div></div>`;
        }).join("");
    } else el.innerHTML=`<p style="color:var(--text-muted);font-size:0.78rem;">No data available.</p>`;

    document.getElementById("features-list").innerHTML=`<details><summary>All features (${d.features_used.length})</summary><div class="tags">${d.features_used.map(f=>`<span class="tag">${f}</span>`).join("")}</div></details>`;
}

// ── News ──────────────────────────────────────
function renderNews(articles) {
    const list=document.getElementById("news-list");
    const sumEl=document.getElementById("news-summary");

    if(!Array.isArray(articles)||!articles.length){
        list.innerHTML=`<p style="color:var(--text-muted);font-size:0.78rem;">No recent news.</p>`;
        sumEl.textContent=""; return;
    }

    // Sentiment summary
    let pos=0, neg=0, neu=0;
    const rendered = articles.map(a=>{
        const s=guessSentiment(a.title);
        if(s==="positive")pos++; else if(s==="negative")neg++; else neu++;
        return `<a class="news-item" href="${a.link}" target="_blank" rel="noopener"><div class="news-title">${a.title}</div><div class="news-meta"><span class="news-source">${a.publisher}</span><span class="news-time">${timeAgo(a.published)}</span><span class="news-sentiment ${s}">${s}</span></div></a>`;
    });

    const total = articles.length;
    const dominant = pos>=neg&&pos>=neu?"Mostly Positive":neg>=pos&&neg>=neu?"Mostly Negative":"Mostly Neutral";
    sumEl.textContent = `${total} articles analyzed · Sentiment: ${dominant}`;

    list.innerHTML = rendered.join("");
}

function guessSentiment(t) {
    t=t.toLowerCase();
    if(["surge","soar","jump","rise","gain","bull","record","beat","boost","upgrade","rally","profit","growth","strong","outperform"].some(w=>t.includes(w)))return"positive";
    if(["fall","drop","crash","sink","plunge","bear","loss","miss","cut","downgrade","decline","risk","weak","sell","warn","fear"].some(w=>t.includes(w)))return"negative";
    return"neutral";
}

function timeAgo(s) {
    if(!s)return"";
    try{const d=Math.floor((Date.now()-new Date(s))/1000);if(d<3600)return`${Math.floor(d/60)}m ago`;if(d<86400)return`${Math.floor(d/3600)}h ago`;if(d<604800)return`${Math.floor(d/86400)}d ago`;return new Date(s).toLocaleDateString("en-US",{month:"short",day:"numeric"});}catch{return"";}
}

// ── Watchlist ─────────────────────────────────
async function loadWL() {
    const c=document.getElementById("watchlist");
    c.innerHTML=WL.map(t=>`<button class="wl-item" onclick="qs('${t}')"><span class="wl-ticker">${t}</span><span class="wl-price">···</span><span class="wl-change">—</span></button>`).join("");
    try {
        const r=await fetch("/watchlist_prices",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({tickers:WL})});
        const d=await r.json();
        c.innerHTML=d.map(s=>{
            const p=s.price!=null?`$${s.price.toFixed(0)}`:"—";
            const pct=s.change_pct; const sign=pct!=null&&pct>=0?"+":"";
            const ps=pct!=null?`${sign}${pct.toFixed(1)}%`:"—";
            const cls=pct!=null?(pct>=0?"up":"down"):"";
            const arrow=pct!=null?(pct>=0?`<span class="wl-arrow"> ↑</span>`:`<span class="wl-arrow"> ↓</span>`):"";
            return `<button class="wl-item" onclick="qs('${s.ticker}')"><span class="wl-ticker">${s.ticker}</span><span class="wl-price">${p}</span><span class="wl-change ${cls}">${ps}${arrow}</span></button>`;
        }).join("");
    }catch{}
}

// ── Prediction Log ────────────────────────────
async function loadPredLog() {
    const c=document.getElementById("prediction-log");
    try{const r=await fetch("/prediction_history");const d=await r.json();
    if(!d.length){c.innerHTML=`<span style="color:var(--text-muted);font-size:0.68rem;">No predictions yet</span>`;return;}
    c.innerHTML=d.slice(0,10).map(p=>`<div class="pred-log-item"><span class="pred-log-ticker">${p.ticker}</span><span class="pred-log-dir ${p.direction.toLowerCase()}">${p.direction}</span><span class="pred-log-conf">${(p.confidence*100).toFixed(0)}%</span></div>`).join("");}catch{}
}

// ── Recent ────────────────────────────────────
function addRecent(t) { recentSearches=[t,...recentSearches.filter(x=>x!==t)].slice(0,8); localStorage.setItem("rs",JSON.stringify(recentSearches)); renderRecent(); }

function renderRecent() {
    const c=document.getElementById("recent-searches"); if(!c)return;
    if(!recentSearches.length){c.innerHTML=`<span style="color:var(--text-muted);font-size:0.68rem;">No recent searches</span>`;return;}
    c.innerHTML=recentSearches.map(t=>`<button class="recent-item" onclick="qs('${t}')">${t}</button>`).join("");
}

// ── UI ────────────────────────────────────────
function showErr(m){$err.textContent=m;$err.classList.remove("hidden");}
function hideErr(){$err.classList.add("hidden");}
function showLoad(){$load.classList.remove("hidden");$btn.disabled=true;}
function hideLoad(){$load.classList.add("hidden");$btn.disabled=false;}