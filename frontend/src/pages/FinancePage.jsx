import { useState, useEffect, useCallback } from "react";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
  ArcElement, PointElement, LineElement, Filler
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { apiGet, apiPost, apiDelete, apiPatch, apiUpload } from "../api";
import { Upload, Trash2, Plus, RefreshCw, Search, ChevronLeft, ChevronRight, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";

ChartJS.register(
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
  ArcElement, PointElement, LineElement, Filler
);

const CATEGORIES = [
  "Food & Dining", "Transportation", "Shopping", "Entertainment",
  "Bills & Utilities", "Personal Care", "Education & Work", "Transfer", "Cash", "Other"
];

const CAT_COLORS = {
  "Food & Dining":     "#f87171",
  "Transportation":    "#60a5fa",
  "Shopping":          "#f59e0b",
  "Entertainment":     "#a78bfa",
  "Bills & Utilities": "#22c55e",
  "Personal Care":     "#ec4899",
  "Education & Work":  "#fb923c",
  "Transfer":          "#9ca3af",
  "Cash":              "#14b8a6",
  "Other":             "#6b7280",
};

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value" style={{ color }}>{value}</div>
    </div>
  );
}

const fmt = (n) => `₹${(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const fmtShort = (n) => n >= 1000 ? `₹${(n / 1000).toFixed(1)}k` : `₹${n}`;

const chartBase = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#888', font: { size: 11 } } } },
};
const axisX = { grid: { display: false }, ticks: { color: '#555', font: { size: 11 } } };
const axisY = { grid: { color: '#222', drawTicks: false }, border: { dash: [3, 3] }, ticks: { color: '#555', font: { size: 11 }, callback: fmtShort } };

export default function FinancePage() {
  const [tab, setTab] = useState("overview");
  const [period, setPeriod] = useState("month");
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState({});
  const [report, setReport] = useState(null);
  const [empty, setEmpty] = useState(true);
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  const [accounts, setAccounts] = useState(["Main"]);
  const [activeAccount, setActiveAccount] = useState("All");
  const [uploadAccount, setUploadAccount] = useState("Main");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);

  const [transactions, setTransactions] = useState([]);
  const [txnPage, setTxnPage] = useState(1);
  const [txnTotal, setTxnTotal] = useState(0);
  const [txnPages, setTxnPages] = useState(1);
  const [txnFilter, setTxnFilter] = useState("");
  const [debouncedFilter, setDebouncedFilter] = useState("");
  const [txnCategory, setTxnCategory] = useState("");
  const [txnSort, setTxnSort] = useState("date_desc");
  const [txnLoading, setTxnLoading] = useState(false);
  const [editingCat, setEditingCat] = useState(null);
  const [editingNote, setEditingNote] = useState(null);
  const [noteValue, setNoteValue] = useState("");

  // Debounce search input to only query API when typing finishes
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilter(txnFilter);
      setTxnPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [txnFilter]);

  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [ambiguous, setAmbiguous] = useState([]);
  const [confirmForms, setConfirmForms] = useState({});

  const [showManual, setShowManual] = useState(false);
  const [manualForm, setManualForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    description: "", debit: "", credit: "", category: "Other", account: "Main"
  });

  const loadAccounts = useCallback(async () => {
    try { const data = await apiGet("/api/finance/accounts"); setAccounts(data.accounts || ["Main"]); } catch {}
  }, []);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet(`/api/finance/dashboard?period=${period}&account=${encodeURIComponent(activeAccount)}`);
      setEmpty(data.empty); setStats(data.stats || {}); setChartData(data.chart_data || {});
    } catch (err) { setStatus({ type: "error", text: err.message }); }
    finally { setLoading(false); }
  }, [period, activeAccount]);

  const loadReport = useCallback(async () => {
    try { const data = await apiGet(`/api/finance/report?account=${encodeURIComponent(activeAccount)}`); setReport(data.empty ? null : data); } catch {}
  }, [activeAccount]);

  const loadTransactions = useCallback(async () => {
    setTxnLoading(true);
    try {
      const params = new URLSearchParams({ page: txnPage, limit: 50, search: debouncedFilter, category: txnCategory, sort_by: txnSort, account: activeAccount });
      const data = await apiGet(`/api/finance/transactions?${params}`);
      setTransactions(data.transactions || []); setTxnTotal(data.total || 0); setTxnPages(data.pages || 1);
    } catch {}
    finally { setTxnLoading(false); }
  }, [txnPage, debouncedFilter, txnCategory, txnSort, activeAccount]);

  const loadAmbiguous = useCallback(async () => {
    try {
      const data = await apiGet("/api/finance/ambiguous");
      setAmbiguous(data.transactions || []);
      const forms = {};
      data.transactions.forEach(t => forms[t.id] = { category: "Other", note: "" });
      setConfirmForms(forms);
    } catch {}
  }, []);

  const loadInsights = async () => {
    setInsightsLoading(true); setInsights(null);
    try { setInsights(await apiGet("/api/finance/insights")); }
    catch (err) { setStatus({ type: "error", text: "AI Insights failed: " + err.message }); }
    finally { setInsightsLoading(false); }
  };

  useEffect(() => { loadAccounts(); }, []);
  useEffect(() => { loadDashboard(); }, [period, activeAccount]);
  useEffect(() => { if (tab === "report") loadReport(); }, [tab, activeAccount]);
  useEffect(() => {
    if (tab === "transactions") { loadTransactions(); loadAmbiguous(); }
  }, [tab, txnPage, debouncedFilter, txnCategory, txnSort, activeAccount]);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadFile(file); setShowUploadModal(true); e.target.value = "";
  };

  const handleUploadConfirm = async () => {
    if (!uploadFile) return;
    setShowUploadModal(false); setUploading(true);
    setStatus({ type: "info", text: `Parsing "${uploadFile.name}"…` });
    try {
      const data = await apiUpload("/api/finance/upload", uploadFile, { account: uploadAccount });
      setStatus({ type: "success", text: `${data.count} transactions imported.` });
      loadAccounts(); loadDashboard();
      if (tab === "report") loadReport();
      if (tab === "transactions") { loadTransactions(); loadAmbiguous(); }
    } catch (err) { setStatus({ type: "error", text: err.message }); }
    finally { setUploading(false); setUploadFile(null); }
  };

  const handleClear = async () => {
    if (!confirm("Clear all finance data? This cannot be undone.")) return;
    await apiDelete("/api/finance/clear");
    setStats(null); setChartData({}); setReport(null); setTransactions([]); setEmpty(true);
    setInsights(null); setAmbiguous([]);
    setStatus({ type: "info", text: "All data cleared." });
  };

  const updateCategory = async (txn, newCat) => {
    setEditingCat(null);
    setTransactions(prev => prev.map(t => t.id === txn.id ? { ...t, Category: newCat } : t));
    try { await apiPatch(`/api/finance/transactions/${txn.id}`, { category: newCat }); loadAmbiguous(); }
    catch { setTransactions(prev => prev.map(t => t.id === txn.id ? { ...t, Category: txn.Category } : t)); }
  };

  const updateNote = async (txn) => {
    setEditingNote(null);
    setTransactions(prev => prev.map(t => t.id === txn.id ? { ...t, note: noteValue } : t));
    try { await apiPatch(`/api/finance/transactions/${txn.id}`, { note: noteValue }); }
    catch { setTransactions(prev => prev.map(t => t.id === txn.id ? { ...t, note: txn.note } : t)); }
  };

  const confirmAmbiguous = async (txn) => {
    const form = confirmForms[txn.id];
    try {
      await apiPost(`/api/finance/transactions/${txn.id}/confirm`, { category: form.category, note: form.note });
      setAmbiguous(prev => prev.filter(t => t.id !== txn.id));
      loadTransactions(); loadDashboard();
      setStatus({ type: "success", text: "Transaction confirmed." });
    } catch (err) { setStatus({ type: "error", text: err.message }); }
  };

  const addManual = async () => {
    try {
      await apiPost("/api/finance/transactions/manual", {
        date: manualForm.date, description: manualForm.description,
        debit: parseFloat(manualForm.debit) || 0, credit: parseFloat(manualForm.credit) || 0,
        category: manualForm.category, account: manualForm.account,
      });
      setShowManual(false);
      setManualForm({ date: new Date().toISOString().slice(0, 10), description: "", debit: "", credit: "", category: "Other", account: "Main" });
      setStatus({ type: "success", text: "Transaction added." });
      loadDashboard();
      if (tab === "transactions") loadTransactions();
    } catch (err) { setStatus({ type: "error", text: err.message }); }
  };

  // ── Tab button style ──
  const tabStyle = (t) => ({
    padding: "8px 18px", border: "none", background: "transparent", cursor: "pointer",
    color: tab === t ? "var(--text-0)" : "var(--text-2)", fontWeight: tab === t ? 600 : 400,
    fontSize: 13, borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
    transition: "all .15s",
  });

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 className="page-title">Finance</h1>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
            <span className="page-subtitle" style={{ marginBottom: 0 }}>Account:</span>
            <select className="input" style={{ width: 140, padding: "4px 8px", fontSize: 13 }} value={activeAccount} onChange={e => setActiveAccount(e.target.value)}>
              <option value="All">All Accounts</option>
              {accounts.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <label className="btn btn-outline" style={{ cursor: "pointer" }}>
            <Upload size={14} /> {uploading ? "Parsing…" : "Upload"}
            <input type="file" accept=".csv,.pdf,.txt" style={{ display: "none" }} onChange={handleFileSelect} disabled={uploading} />
          </label>
          <button className="btn btn-ghost" onClick={() => setShowManual(true)}><Plus size={14} /> Manual</button>
          <button className="btn btn-ghost" onClick={handleClear} title="Clear all data"><Trash2 size={14} /></button>
        </div>
      </div>

      {status && <div className={`status-msg ${status.type}`} style={{ marginBottom: 14 }}>{status.text}</div>}

      {/* Tabs */}
      <div style={{ display: "flex", alignItems: "center", gap: 2, marginBottom: 24, borderBottom: "1px solid var(--border)" }}>
        {["overview", "report", "transactions"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={tabStyle(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {t === "transactions" && ambiguous.length > 0 && (
              <span style={{ marginLeft: 6, background: "var(--red)", color: "#fff", padding: "1px 6px", borderRadius: 8, fontSize: 10 }}>{ambiguous.length}</span>
            )}
          </button>
        ))}
        {!empty && (
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <select className="input" style={{ width: 120, padding: "5px 10px" }} value={period} onChange={e => setPeriod(e.target.value)}>
              <option value="month">Monthly</option>
              <option value="week">Weekly</option>
              <option value="quarter">Quarterly</option>
            </select>
            <button className="btn btn-ghost" style={{ padding: 6 }} onClick={loadDashboard} title="Refresh">
              <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            </button>
          </div>
        )}
      </div>

      {/* ── OVERVIEW ── */}
      {tab === "overview" && (
        <>
          {!empty && stats && (
            <div className="stats-row">
              <StatCard label="Transactions" value={stats.txn_count?.toLocaleString() || "—"} color="var(--accent)" />
              <StatCard label="Total Spent" value={fmt(stats.total_debit)} color="var(--red)" />
              <StatCard label="Total Credited" value={fmt(stats.total_credit)} color="var(--green)" />
              <StatCard label="Net Flow" value={`${stats.net_flow >= 0 ? "+" : ""}${fmt(stats.net_flow)}`} color="var(--amber)" />
              <StatCard label="Date Range" value={stats.date_range || "—"} color="var(--purple)" />
            </div>
          )}

          {!empty && (
            <div className="card" style={{ marginBottom: 24, border: "1px solid rgba(34,197,94,.2)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: insights ? 14 : 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--green)", fontWeight: 600, fontSize: 13 }}>
                  <Sparkles size={15} /> AI Insights
                </div>
                {!insights && !insightsLoading && (
                  <button className="btn btn-ghost" onClick={loadInsights} style={{ fontSize: 12 }}>Generate</button>
                )}
                {insightsLoading && <div style={{ fontSize: 12, color: "var(--text-2)", display: "flex", alignItems: "center", gap: 6 }}><RefreshCw size={12} style={{ animation: "spin 1s linear infinite" }} /> Analyzing…</div>}
              </div>
              {insights && (
                <div className="fade-in">
                  <ul style={{ paddingLeft: 18, margin: 0, color: "var(--text-1)", fontSize: 13, display: "flex", flexDirection: "column", gap: 6, marginBottom: 14 }}>
                    {insights.insights.map((ins, i) => <li key={i}>{ins}</li>)}
                  </ul>
                  {insights.alert && (
                    <div style={{ padding: "8px 12px", background: "rgba(239,68,68,.08)", borderRadius: 6, color: "var(--red)", fontSize: 12, display: "flex", gap: 8, marginBottom: 10 }}>
                      <AlertCircle size={15} /> {insights.alert}
                    </div>
                  )}
                  {insights.tip && (
                    <div style={{ padding: "8px 12px", background: "rgba(245,158,11,.08)", borderRadius: 6, color: "var(--amber)", fontSize: 12, display: "flex", gap: 8 }}>
                      <Sparkles size={15} /> <b>Tip:</b> {insights.tip}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Spending vs Income chart */}
          {chartData.period?.length > 0 && (
            <div className="card" style={{ padding: 20, marginBottom: 20 }}>
              <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Spending vs Income</div>
              <div style={{ height: 260 }}>
                <Bar
                  data={{
                    labels: chartData.period?.map(d => d.label) || [],
                    datasets: [
                      { label: 'Spent', data: chartData.period?.map(d => d.debit) || [], backgroundColor: '#ef4444', borderRadius: 4, barPercentage: 0.6 },
                      { label: 'Received', data: chartData.period?.map(d => d.credit) || [], backgroundColor: '#22c55e', borderRadius: 4, barPercentage: 0.6 }
                    ]
                  }}
                  options={{ ...chartBase, scales: { x: axisX, y: axisY }, plugins: { ...chartBase.plugins, tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${fmt(ctx.raw)}` } } } }}
                />
              </div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
            {chartData.category?.length > 0 && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>By Category</div>
                <div style={{ height: 240 }}>
                  <Pie
                    data={{
                      labels: chartData.category?.map(d => d.category) || [],
                      datasets: [{ data: chartData.category?.map(d => d.amount) || [], backgroundColor: chartData.category?.map(d => CAT_COLORS[d.category] || '#555') || [], borderWidth: 0, cutout: '65%' }]
                    }}
                    options={{ ...chartBase, plugins: { legend: { position: 'bottom', labels: { color: '#888', font: { size: 11 }, usePointStyle: true } }, tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${fmt(ctx.raw)}` } } } }}
                  />
                </div>
              </div>
            )}
            {chartData.weekday?.length > 0 && (
              <div className="card" style={{ padding: 20 }}>
                <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Avg Spend by Day</div>
                <div style={{ height: 240 }}>
                  <Bar
                    data={{
                      labels: chartData.weekday?.map(d => d.day) || [],
                      datasets: [{ label: 'Avg', data: chartData.weekday?.map(d => d.avg) || [], backgroundColor: '#f59e0b', borderRadius: 4, barThickness: 36 }]
                    }}
                    options={{ ...chartBase, scales: { x: axisX, y: axisY }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => fmt(ctx.raw) } } } }}
                  />
                </div>
              </div>
            )}
          </div>

          {chartData.balance?.length > 0 && (
            <div className="card" style={{ padding: 20, marginBottom: 20 }}>
              <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Balance Trend</div>
              <div style={{ height: 200 }}>
                <Line
                  data={{
                    labels: chartData.balance?.map(d => d.date?.slice(5)) || [],
                    datasets: [{ label: 'Balance', data: chartData.balance?.map(d => d.balance) || [], borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,.15)', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0, pointHoverRadius: 4 }]
                  }}
                  options={{ ...chartBase, scales: { x: axisX, y: axisY }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => fmt(ctx.raw) } } }, interaction: { intersect: false, mode: 'index' } }}
                />
              </div>
            </div>
          )}

          {empty && (
            <div className="chat-empty" style={{ marginTop: 60 }}>
              <div className="empty-mark" aria-hidden="true" />
              <div className="chat-empty-text">No financial data yet.</div>
              <div style={{ color: "var(--text-2)", fontSize: 13, marginTop: 4 }}>Upload a bank statement to get started.</div>
            </div>
          )}
        </>
      )}

      {/* ── REPORT ── */}
      {tab === "report" && (
        <>
          {report ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {/* Summary banner */}
              <div className="card" style={{ padding: 24 }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, textAlign: "center" }}>
                  {[
                    { label: "Total Spent", value: fmt(report.total_spent), color: "var(--red)", sub: `${report.txn_count} transactions` },
                    { label: "Total Credited", value: fmt(report.total_credited), color: "var(--green)" },
                    { label: "Net Flow", value: `${report.net_flow >= 0 ? "+" : ""}${fmt(report.net_flow)}`, color: report.net_flow >= 0 ? "var(--green)" : "var(--red)" },
                  ].map(s => (
                    <div key={s.label}>
                      <div style={{ fontSize: 11, color: "var(--text-2)", textTransform: "uppercase", letterSpacing: ".04em" }}>{s.label}</div>
                      <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
                      {s.sub && <div style={{ fontSize: 12, color: "var(--text-2)" }}>{s.sub}</div>}
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {/* Category breakdown */}
                <div className="card" style={{ padding: 20 }}>
                  <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 13 }}>Where Your Money Goes</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {report.category_breakdown.map(cat => (
                      <div key={cat.category}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <span style={{ fontSize: 12, color: CAT_COLORS[cat.category] || "#aaa", fontWeight: 600 }}>{cat.category}</span>
                          <span style={{ fontSize: 12 }}>{fmt(cat.amount)} <span style={{ color: "var(--text-2)" }}>({cat.percentage}%)</span></span>
                        </div>
                        <div style={{ height: 5, background: "var(--bg-3)", borderRadius: 3 }}>
                          <div style={{ height: 5, width: `${cat.percentage}%`, background: CAT_COLORS[cat.category] || "#555", borderRadius: 3, transition: "width .6s ease" }} />
                        </div>
                        <div style={{ fontSize: 10, color: "var(--text-2)", marginTop: 2 }}>{cat.count} txn{cat.count !== 1 ? "s" : ""}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Category bar chart */}
                <div className="card" style={{ padding: 20 }}>
                  <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Category Chart</div>
                  <div style={{ height: 280 }}>
                    <Bar
                      data={{
                        labels: report.category_breakdown?.map(d => d.category) || [],
                        datasets: [{ label: 'Amount', data: report.category_breakdown?.map(d => d.amount) || [], backgroundColor: report.category_breakdown?.map(d => CAT_COLORS[d.category] || '#555') || [], borderRadius: 4, barThickness: 20 }]
                      }}
                      options={{ ...chartBase, indexAxis: 'y', scales: { x: { ...axisY }, y: { grid: { display: false }, ticks: { color: '#aaa', font: { size: 11 } } } }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => fmt(ctx.raw) } } } }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {/* Top Merchants */}
                <div className="card" style={{ padding: 20 }}>
                  <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Top Merchants</div>
                  {report.top_merchants_by_spend.slice(0, 8).map((m, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, fontSize: 13 }}>
                      <span style={{ color: "var(--text-1)" }}>
                        <span style={{ color: "var(--text-2)", marginRight: 8, fontSize: 11 }}>{i + 1}.</span>{m.payee}
                      </span>
                      <span style={{ fontWeight: 600, color: "var(--red)" }}>{fmt(m.amount)}</span>
                    </div>
                  ))}
                </div>

                {/* Weekday */}
                <div className="card" style={{ padding: 20 }}>
                  <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 13 }}>Spending by Day of Week</div>
                  <div style={{ height: 220 }}>
                    <Bar
                      data={{
                        labels: report.weekday_spending?.map(d => d.day) || [],
                        datasets: [{ label: 'Amount', data: report.weekday_spending?.map(d => d.amount) || [], backgroundColor: '#f59e0b', borderRadius: 4, barThickness: 32 }]
                      }}
                      options={{ ...chartBase, scales: { x: axisX, y: axisY }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => fmt(ctx.raw) } } } }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="chat-empty" style={{ marginTop: 60 }}>
              <div className="empty-mark" />
              <div className="chat-empty-text">No report yet.</div>
              <div style={{ color: "var(--text-2)", fontSize: 13, marginTop: 4 }}>Upload a bank statement first.</div>
            </div>
          )}
        </>
      )}

      {/* ── TRANSACTIONS ── */}
      {tab === "transactions" && (
        <>
          {/* Ambiguous */}
          {ambiguous.length > 0 && (
            <div className="card fade-in" style={{ marginBottom: 20, border: "1px solid rgba(239,68,68,.3)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--red)", fontWeight: 600, fontSize: 13, marginBottom: 14 }}>
                <AlertCircle size={16} /> {ambiguous.length} unrecognized transaction{ambiguous.length !== 1 ? "s" : ""}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {ambiguous.map(txn => (
                  <div key={txn.id} style={{ display: "flex", alignItems: "center", gap: 10, background: "var(--bg-0)", padding: "10px 12px", borderRadius: 8, border: "1px solid var(--border)" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>{txn.payee_display || "Unknown"}</div>
                      <div style={{ fontSize: 11, color: "var(--text-2)" }}>{txn.Date} · {txn.Description}</div>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: txn.Debit > 0 ? "var(--red)" : "var(--green)", width: 80, textAlign: "right" }}>
                      {txn.Debit > 0 ? `−${fmt(txn.Debit)}` : `+${fmt(txn.Credit)}`}
                    </div>
                    <select className="input" style={{ width: 140, padding: "5px 8px", fontSize: 12 }}
                      value={confirmForms[txn.id]?.category || "Other"}
                      onChange={e => setConfirmForms(prev => ({ ...prev, [txn.id]: { ...prev[txn.id], category: e.target.value } }))}>
                      {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                    </select>
                    <input className="input" placeholder="Note" style={{ width: 140, padding: "5px 8px", fontSize: 12 }}
                      value={confirmForms[txn.id]?.note || ""}
                      onChange={e => setConfirmForms(prev => ({ ...prev, [txn.id]: { ...prev[txn.id], note: e.target.value } }))} />
                    <button className="btn btn-primary" style={{ padding: "5px 10px", fontSize: 12 }} onClick={() => confirmAmbiguous(txn)}>
                      <CheckCircle2 size={13} /> Save
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Filters */}
          <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
            <div style={{ position: "relative", flex: 1, minWidth: 200 }}>
              <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-2)", pointerEvents: "none" }} />
              <input className="input" placeholder="Search descriptions…" value={txnFilter}
                onChange={e => setTxnFilter(e.target.value)}
                style={{ paddingLeft: 32 }} />
            </div>
            <select className="input" style={{ width: 170 }} value={txnCategory} onChange={e => { setTxnCategory(e.target.value); setTxnPage(1); }}>
              <option value="">All Categories</option>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ fontSize: 12, color: "var(--text-2)", marginBottom: 10 }}>
            {txnTotal.toLocaleString()} transaction{txnTotal !== 1 ? "s" : ""}
            {txnCategory && ` · ${txnCategory}`}
            {txnFilter && ` · "${txnFilter}"`}
          </div>

          {/* Table */}
          <div className="card" style={{ padding: 0, overflow: "auto" }}>
            {txnLoading ? (
              <div style={{ padding: 40, textAlign: "center", color: "var(--text-2)", fontSize: 13 }}>Loading…</div>
            ) : transactions.length === 0 ? (
              <div style={{ padding: 40, textAlign: "center", color: "var(--text-2)", fontSize: 13 }}>No transactions found.</div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 800 }}>
                <thead>
                  <tr style={{ background: "var(--bg-2)", borderBottom: "1px solid var(--border)" }}>
                    {["Date", "Description", "Category", "Note", "Debit", "Credit", "Balance", "Account"].map(h => {
                      const sortKey = h.toLowerCase();
                      const isSorted = txnSort.startsWith(sortKey);
                      const isDesc = txnSort === `${sortKey}_desc`;
                      return (
                        <th key={h}
                          onClick={() => { if (isSorted && isDesc) setTxnSort(`${sortKey}_asc`); else setTxnSort(`${sortKey}_desc`); setTxnPage(1); }}
                          style={{
                            padding: "10px 14px", fontSize: 10, fontWeight: 600,
                            color: isSorted ? "var(--accent)" : "var(--text-2)",
                            textTransform: "uppercase", letterSpacing: ".03em", cursor: "pointer",
                            textAlign: ["Debit", "Credit", "Balance"].includes(h) ? "right" : "left",
                          }}>
                          {h} {isSorted ? (isDesc ? "↓" : "↑") : ""}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((txn, i) => (
                    <tr key={txn.id || i} style={{ borderBottom: "1px solid var(--border)", transition: "background .1s" }}
                      onMouseEnter={e => e.currentTarget.style.background = "var(--bg-2)"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <td style={{ padding: "8px 14px", fontSize: 12, color: "var(--text-2)", whiteSpace: "nowrap" }}>{txn.Date?.slice(0, 10)}</td>
                      <td style={{ padding: "8px 14px", fontSize: 12, maxWidth: 240 }}>
                        <span style={{ display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={txn.Description}>{txn.Description}</span>
                      </td>
                      <td style={{ padding: "8px 14px" }}>
                        {editingCat === txn.id ? (
                          <select autoFocus className="input" style={{ padding: "3px 6px", fontSize: 11, width: 140 }}
                            defaultValue={txn.Category} onChange={e => updateCategory(txn, e.target.value)} onBlur={() => setEditingCat(null)}>
                            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                          </select>
                        ) : (
                          <span onClick={() => setEditingCat(txn.id)} title="Click to edit" style={{
                            cursor: "pointer", fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 4,
                            background: `${CAT_COLORS[txn.Category] || "#555"}1a`,
                            color: CAT_COLORS[txn.Category] || "#aaa", userSelect: "none",
                          }}>{txn.Category || "Other"}</span>
                        )}
                      </td>
                      <td style={{ padding: "8px 10px", maxWidth: 160 }}>
                        {editingNote === txn.id ? (
                          <input autoFocus className="input" style={{ padding: "3px 6px", fontSize: 11, width: 130 }}
                            value={noteValue} onChange={e => setNoteValue(e.target.value)}
                            onBlur={() => updateNote(txn)} onKeyDown={e => { if (e.key === "Enter") updateNote(txn); if (e.key === "Escape") setEditingNote(null); }}
                            placeholder="Add note…" />
                        ) : (
                          <span onClick={() => { setEditingNote(txn.id); setNoteValue(txn.note || ""); }} title="Click to edit" style={{
                            cursor: "pointer", fontSize: 11, color: txn.note ? "var(--amber)" : "var(--text-2)",
                            fontStyle: txn.note ? "normal" : "italic", userSelect: "none",
                          }}>{txn.note || "—"}</span>
                        )}
                      </td>
                      <td style={{ padding: "8px 14px", fontSize: 12, textAlign: "right", fontWeight: txn.Debit > 0 ? 600 : 400, color: txn.Debit > 0 ? "var(--red)" : "var(--text-2)" }}>
                        {txn.Debit > 0 ? `−₹${txn.Debit.toLocaleString("en-IN")}` : ""}
                      </td>
                      <td style={{ padding: "8px 14px", fontSize: 12, textAlign: "right", fontWeight: txn.Credit > 0 ? 600 : 400, color: txn.Credit > 0 ? "var(--green)" : "var(--text-2)" }}>
                        {txn.Credit > 0 ? `+₹${txn.Credit.toLocaleString("en-IN")}` : ""}
                      </td>
                      <td style={{ padding: "8px 14px", fontSize: 12, textAlign: "right", color: "var(--text-1)" }}>
                        {txn.Balance > 0 ? `₹${txn.Balance.toLocaleString("en-IN")}` : ""}
                      </td>
                      <td style={{ padding: "8px 14px", fontSize: 11, color: "var(--text-2)" }}>{txn.Account || "Main"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {txnPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 14, marginTop: 16 }}>
              <button className="btn btn-ghost" disabled={txnPage === 1} onClick={() => setTxnPage(p => p - 1)} style={{ padding: 7 }}>
                <ChevronLeft size={14} />
              </button>
              <span style={{ fontSize: 13, color: "var(--text-2)" }}>Page {txnPage} of {txnPages}</span>
              <button className="btn btn-ghost" disabled={txnPage === txnPages} onClick={() => setTxnPage(p => p + 1)} style={{ padding: 7 }}>
                <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}

      {/* Manual Modal */}
      {showManual && (
        <div className="modal-overlay">
          <div className="modal-content fade-in">
            <h3>Add Transaction</h3>
            <input className="input" type="date" value={manualForm.date} onChange={e => setManualForm(f => ({ ...f, date: e.target.value }))} style={{ marginBottom: 10 }} />
            <input className="input" placeholder="Description" value={manualForm.description} onChange={e => setManualForm(f => ({ ...f, description: e.target.value }))} style={{ marginBottom: 10 }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
              <input className="input" type="number" placeholder="Debit ₹" value={manualForm.debit} onChange={e => setManualForm(f => ({ ...f, debit: e.target.value }))} />
              <input className="input" type="number" placeholder="Credit ₹" value={manualForm.credit} onChange={e => setManualForm(f => ({ ...f, credit: e.target.value }))} />
            </div>
            <select className="input" value={manualForm.category} onChange={e => setManualForm(f => ({ ...f, category: e.target.value }))} style={{ marginBottom: 10 }}>
              {CATEGORIES.map(c => <option key={c}>{c}</option>)}
            </select>
            <input className="input" list="account-list" value={manualForm.account} onChange={e => setManualForm(f => ({ ...f, account: e.target.value }))} placeholder="Account" style={{ marginBottom: 16 }} />
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setShowManual(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={addManual}>Add</button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Account Modal */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content fade-in" style={{ width: 380 }}>
            <h3>Select Account</h3>
            <p style={{ fontSize: 13, color: "var(--text-2)", marginBottom: 16 }}>
              Which account is this statement for?
            </p>
            <input className="input" list="account-list" value={uploadAccount} onChange={e => setUploadAccount(e.target.value)} placeholder="e.g. HDFC, SBI, Cash" style={{ marginBottom: 16 }} />
            <datalist id="account-list">
              {accounts.map(a => <option key={a} value={a} />)}
            </datalist>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => { setShowUploadModal(false); setUploadFile(null); }}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUploadConfirm}>Upload</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
