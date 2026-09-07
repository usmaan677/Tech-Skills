import { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE;

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      padding: "6px 12px",
      fontSize: 13,
      color: "#111",
      boxShadow: "0 4px 12px rgba(0,0,0,0.08)"
    }}>
      <span style={{ fontWeight: 600 }}>{payload[0].payload.skill}</span>
      <span style={{ color: "#6b7280", marginLeft: 10 }}>{payload[0].value} jobs</span>
    </div>
  );
};

export default function App() {
  const [term, setTerm] = useState("software engineer intern");
  const [country, setCountry] = useState("ca");
  const [loading, setLoading] = useState(false);
  const [searchId, setSearchId] = useState(null);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  const topChartData = useMemo(() =>
    [...rows]
      .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
      .slice(0, 12)
      .map((r) => ({ skill: r.skill, count: r.count })),
    [rows]
  );

  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => b.count - a.count),
    [rows]
  );

  const maxCount = sortedRows[0]?.count ?? 1;

  async function runPipeline() {
    setError("");
    setLoading(true);
    setRows([]);
    setSearchId(null);
    try {
      const resp = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ search_term: term, country }),
      });
      if (!resp.ok) throw new Error(`Backend error: ${resp.status} ${await resp.text()}`);
      const data = await resp.json();
      if (data.search_id) setSearchId(data.search_id);
      setRows(data.skills || []);
    } catch (e) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", minHeight: "100vh", background: "#f9fafb", color: "#111827" }}>

      {/* Sidebar + main layout */}
      <div style={{ display: "flex", minHeight: "100vh" }}>

        {/* Sidebar */}
        <aside style={{
          width: 240,
          flexShrink: 0,
          background: "#111827",
          color: "#f9fafb",
          padding: "36px 24px",
          display: "flex",
          flexDirection: "column",
          gap: 32,
        }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.3px", color: "#fff" }}>
              Tech Skills Pulse
            </div>
            <div style={{ fontSize: 13, color: "#6b7280", marginTop: 6, lineHeight: 1.5 }}>
              What skills do jobs actually ask for?
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "#4b5563" }}>
              Search
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#9ca3af", display: "block", marginBottom: 6 }}>Role</label>
              <input
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && term.trim() && !loading && runPipeline()}
                placeholder="e.g. data engineer"
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  background: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  padding: "9px 12px",
                  fontSize: 13,
                  color: "#f3f4f6",
                  outline: "none",
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#9ca3af", display: "block", marginBottom: 6 }}>Country</label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  background: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  padding: "9px 12px",
                  fontSize: 13,
                  color: "#f3f4f6",
                  outline: "none",
                }}
              >
                <option value="ca">Canada</option>
                <option value="us">USA</option>
                <option value="gb">UK</option>
                <option value="au">Australia</option>
                <option value="in">India</option>
                <option value="de">Germany</option>
                <option value="fr">France</option>
              </select>
            </div>

            <button
              onClick={runPipeline}
              disabled={loading || !term.trim()}
              style={{
                marginTop: 4,
                background: loading || !term.trim() ? "#374151" : "#fff",
                color: loading || !term.trim() ? "#6b7280" : "#111827",
                border: "none",
                borderRadius: 8,
                padding: "10px 0",
                fontFamily: "inherit",
                fontSize: 13,
                fontWeight: 600,
                cursor: loading || !term.trim() ? "not-allowed" : "pointer",
                width: "100%",
                transition: "background 0.15s",
              }}
            >
              {loading ? "Running…" : "Run"}
            </button>
          </div>

          {searchId && (
            <div style={{ fontSize: 11, color: "#4b5563", marginTop: "auto" }}>
              Search #{String(searchId)}
            </div>
          )}
        </aside>

        {/* Main content */}
        <main style={{ flex: 1, padding: "40px 40px", overflowY: "auto" }}>

          {error && (
            <div style={{
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: 8,
              padding: "12px 16px",
              fontSize: 13,
              color: "#b91c1c",
              marginBottom: 24,
            }}>
              {error}
            </div>
          )}

          {rows.length === 0 && !error ? (
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "60vh",
              color: "#9ca3af",
              fontSize: 14,
              gap: 12,
              textAlign: "center",
            }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zm6.75-9.75C9.75 2.754 10.254 2.25 10.875 2.25h2.25c.621 0 1.125.504 1.125 1.125v16.5c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 019.75 19.875V3.375zm6.75 5.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v10.875c0 .621-.504 1.125-1.125 1.125h-2.25A1.125 1.125 0 0116.5 19.875V9z" />
              </svg>
              <div>Run a search to see results</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>

              {/* Chart */}
              <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", padding: "28px 28px 16px" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 4 }}>Top 12 Skills</div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 24 }}>By frequency in job descriptions</div>
                <div style={{ height: 280 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={topChartData} margin={{ top: 4, right: 8, left: -16, bottom: 48 }}>
                      <XAxis
                        dataKey="skill"
                        tick={{ fontSize: 11, fill: "#9ca3af", fontFamily: "Inter, sans-serif" }}
                        interval={0}
                        angle={-35}
                        textAnchor="end"
                        height={60}
                        axisLine={{ stroke: "#f3f4f6" }}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: "#d1d5db", fontFamily: "Inter, sans-serif" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f9fafb" }} />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={40}>
                        {topChartData.map((_, i) => (
                          <Cell key={i} fill={i === 0 ? "#111827" : "#e5e7eb"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Table */}
              <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e5e7eb", overflow: "hidden" }}>
                <div style={{ padding: "20px 24px 16px", borderBottom: "1px solid #f3f4f6" }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#374151" }}>All Skills</span>
                  <span style={{ fontSize: 12, color: "#9ca3af", marginLeft: 8 }}>{sortedRows.length} extracted</span>
                </div>
                <div style={{ overflowY: "auto", maxHeight: 360 }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <th style={{ padding: "10px 24px", textAlign: "left", fontSize: 11, fontWeight: 500, color: "#9ca3af", width: 32 }}>#</th>
                        <th style={{ padding: "10px 24px", textAlign: "left", fontSize: 11, fontWeight: 500, color: "#9ca3af" }}>Skill</th>
                        <th style={{ padding: "10px 24px", textAlign: "right", fontSize: 11, fontWeight: 500, color: "#9ca3af" }}>Jobs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedRows.map((r, idx) => (
                        <tr key={idx} style={{ borderTop: "1px solid #f9fafb" }}
                          onMouseEnter={e => e.currentTarget.style.background = "#f9fafb"}
                          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                        >
                          <td style={{ padding: "10px 24px", color: "#d1d5db", fontVariantNumeric: "tabular-nums" }}>{idx + 1}</td>
                          <td style={{ padding: "10px 24px", color: "#111827", fontWeight: 500 }}>{r.skill}</td>
                          <td style={{ padding: "10px 24px", textAlign: "right" }}>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10 }}>
                              <div style={{ width: 60, height: 4, background: "#f3f4f6", borderRadius: 4, overflow: "hidden" }}>
                                <div style={{ height: "100%", width: `${Math.round((r.count / maxCount) * 100)}%`, background: "#111827", borderRadius: 4 }} />
                              </div>
                              <span style={{ color: "#6b7280", fontVariantNumeric: "tabular-nums", minWidth: 20, textAlign: "right" }}>{r.count}</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}
        </main>
      </div>
    </div>
  );
}
