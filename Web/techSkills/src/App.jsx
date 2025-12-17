import { useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE;

export default function App() {
  const [term, setTerm] = useState("software engineer intern");
  const [loading, setLoading] = useState(false);
  const [searchId, setSearchId] = useState(null);
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  const topChartData = useMemo(() => {
    // show top 12 skills for chart
    return [...rows]
      .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
      .slice(0, 12)
      .map((r) => ({ skill: r.skill, count: r.count }));
  }, [rows]);

  async function runPipeline() {
    setError("");
    setLoading(true);
    setRows([]);
    setSearchId(null);

    try {
      // 1) call your backend to run ETL
      // Expected backend response: { search_id: ..., skills: [{skill, count}, ...] }
      const resp = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ search_term: term }),
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Backend error: ${resp.status} ${text}`);
      }

      const data = await resp.json();
      
      if (data.search_id) {
        setSearchId(data.search_id);
      }

      // 2) Use the skills returned directly from the backend
      // Backend returns: [{ skill: "Python", count: 10 }, ...]
      setRows(data.skills || []);

    } catch (e) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Tech Skills Pulse
          </h1>
          <p className="mt-2 text-slate-300">
            Enter a role keyword. We run the ETL, store results, and show the top skills.
          </p>
        </header>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label className="text-sm text-slate-300">Search term</label>
              <input
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                placeholder="e.g. data engineer intern"
                className="mt-1 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-100 outline-none ring-0 focus:border-slate-600"
              />
              <div className="mt-2 text-xs text-slate-400">
                Example: “software engineer intern”, “data engineer intern”, “machine learning intern”
              </div>
            </div>

            <button
              onClick={runPipeline}
              disabled={loading || !term.trim()}
              className="rounded-xl bg-slate-100 px-5 py-3 font-medium text-slate-950 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Running..." : "Run"}
            </button>
          </div>

          {error && (
            <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">
              {error}
            </div>
          )}

          {searchId && (
            <div className="mt-4 text-xs text-slate-400">
              Search ID: <span className="text-slate-200">{String(searchId)}</span>
            </div>
          )}
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow">
            <h2 className="text-lg font-semibold">Top Skills (Chart)</h2>
            <p className="mt-1 text-sm text-slate-300">
              Top 12 extracted skill keywords for this search.
            </p>

            <div className="mt-4 h-72">
              {rows.length === 0 ? (
                <div className="flex h-full items-center justify-center text-slate-400">
                  Run a search to view results
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topChartData} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="skill" tick={{ fontSize: 12 }} interval={0} angle={-25} textAnchor="end" height={60} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow">
            <h2 className="text-lg font-semibold">All Skills (Table)</h2>
            <p className="mt-1 text-sm text-slate-300">
              Full list of extracted skills and counts.
            </p>

            <div className="mt-4 max-h-72 overflow-auto rounded-xl border border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-slate-950">
                  <tr>
                    <th className="px-4 py-3 text-slate-300">Skill</th>
                    <th className="px-4 py-3 text-slate-300">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr>
                      <td className="px-4 py-4 text-slate-400" colSpan={2}>
                        No data yet
                      </td>
                    </tr>
                  ) : (
                    [...rows]
                      .sort((a, b) => b.count - a.count)
                      .map((r, idx) => (
                        <tr key={idx} className="border-t border-slate-800">
                          <td className="px-4 py-3">{r.skill}</td>
                          <td className="px-4 py-3">{r.count}</td>
                        </tr>
                      ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-3 text-xs text-slate-400">
              Tip: later we can add filters (location, company, internship only, etc.).
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
