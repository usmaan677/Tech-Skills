import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { searchSkills, getCorpusStats, ApiError } from "./lib/api.js";

const SUGGESTIONS = ["software engineer", "data analyst", "data scientist", "product designer"];

const nf = new Intl.NumberFormat("en-US");

export default function App() {
  const [term, setTerm] = useState("data analyst");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | ready | error
  const [error, setError] = useState(null);
  const [corpus, setCorpus] = useState(null);

  // Holds the in-flight search so a newer one can cancel it. Without this two
  // quick searches can resolve out of order and paint the wrong results.
  const inFlight = useRef(null);

  useEffect(() => {
    const ctrl = new AbortController();
    getCorpusStats({ signal: ctrl.signal })
      .then(setCorpus)
      .catch(() => {}); // masthead detail only; never block the page on it
    return () => ctrl.abort();
  }, []);

  const runSearch = useCallback(async (raw) => {
    const query = raw.trim();
    if (query.length < 2) return;

    inFlight.current?.abort();
    const ctrl = new AbortController();
    inFlight.current = ctrl;

    setStatus("loading");
    setError(null);

    try {
      const data = await searchSkills(query, { signal: ctrl.signal });
      setResult({ ...data, search_term: query });
      setStatus("ready");
    } catch (err) {
      if (err?.name === "AbortError") return; // superseded by a newer search
      setError(err instanceof ApiError ? err : new ApiError("Something went wrong.", 0));
      setResult(null);
      setStatus("error");
    }
  }, []);

  useEffect(() => () => inFlight.current?.abort(), []);

  // Coverage, not raw count: share of matched postings that mention the skill.
  const ranked = useMemo(() => {
    if (!result?.skills?.length) return [];
    const denominator = result.job_count || 0;
    return [...result.skills]
      .sort((a, b) => b.count - a.count)
      .map((r) => ({
        skill: r.skill,
        count: r.count,
        share: denominator ? r.count / denominator : 0,
      }));
  }, [result]);

  const loading = status === "loading";

  return (
    <div className="shell">
      <header className="masthead">
        <h1 className="masthead__name">Tech Skills Pulse</h1>
        {corpus?.job_count ? (
          <p className="masthead__corpus">
            {nf.format(corpus.job_count)} openings from {nf.format(corpus.company_count)} companies
          </p>
        ) : null}
      </header>

      <form
        className="search"
        onSubmit={(e) => {
          e.preventDefault();
          runSearch(term);
        }}
      >
        <label className="visually-hidden" htmlFor="role">
          Job title to search
        </label>
        <input
          id="role"
          className="search__input"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="data analyst"
          autoComplete="off"
          spellCheck="false"
        />
        <button className="search__submit" type="submit" disabled={loading || term.trim().length < 2}>
          {loading ? "Searching" : "Search"}
        </button>
      </form>

      <div aria-live="polite">
        {status === "idle" && <Idle onPick={(s) => { setTerm(s); runSearch(s); }} />}

        {status === "error" && <Failure error={error} />}

        {status === "ready" && result.job_count === 0 && (
          <Empty term={result.search_term} onPick={(s) => { setTerm(s); runSearch(s); }} />
        )}

        {status === "ready" && result.job_count > 0 && (
          <Results result={result} ranked={ranked} corpus={corpus} />
        )}
      </div>
    </div>
  );
}

function Results({ result, ranked, corpus }) {
  const total = corpus?.job_count;

  return (
    <>
      <p className="lede">
        {nf.format(result.job_count)}
        {total ? ` of ${nf.format(total)}` : ""} openings match &ldquo;{result.search_term}&rdquo;.
      </p>
      <p className="lede__note">
        Each bar is the share of those descriptions that mention the skill. The empty
        remainder is postings that never asked for it.
      </p>

      {/* Keyed on the term so the bars re-run their entrance on a new search. */}
      <section className="field" key={result.search_term}>
        <div className="field__head">
          <span />
          <span>Skill</span>
          <span>Coverage</span>
          <span className="field__nums">
            <span>Share</span>
            <span>Jobs</span>
          </span>
        </div>

        <ol className="field__list">
          {ranked.map((row, i) => (
            <li className="row" key={row.skill}>
              <span className="row__rank">{i + 1}</span>
              <span className="row__skill">{row.skill}</span>
              <span className="row__track" aria-hidden="true">
                <span
                  className="row__fill"
                  style={{ "--w": `${row.share * 100}%`, "--i": i }}
                />
              </span>
              <span className="row__nums">
                <span>{Math.round(row.share * 100)}%</span>
                <span className="row__count">{row.count}</span>
              </span>
            </li>
          ))}
        </ol>

        <div className="field__scale" aria-hidden="true">
          <span className="field__ticks">
            {[0, 25, 50, 75].map((t) => (
              <span key={t} style={{ "--p": `${t}%` }}>{t}</span>
            ))}
            <span style={{ "--p": "100%" }}>100%</span>
          </span>
        </div>
      </section>

      <p className="method">
        Skills are matched against a fixed vocabulary using word-boundary patterns, so
        &ldquo;R&rdquo; does not match &ldquo;R&amp;D&rdquo;. Postings are deduplicated by title and
        company first, so a role listed in nineteen cities counts once.
      </p>
    </>
  );
}

function Idle({ onPick }) {
  return (
    <div className="state">
      <h2 className="state__title">Search a role to see what its postings ask for.</h2>
      <p className="state__body">
        Every job description in the corpus is scanned for technical skills. Search a
        title and you get the skills those postings mention, ranked by how many of them
        mention it.
      </p>
      <Suggestions onPick={onPick} />
    </div>
  );
}

function Empty({ term, onPick }) {
  return (
    <div className="state">
      <h2 className="state__title">No openings match &ldquo;{term}&rdquo;.</h2>
      <p className="state__body">
        Titles are matched as written, so a broader one usually helps &mdash; &ldquo;analyst&rdquo;
        rather than &ldquo;senior analyst II&rdquo;.
      </p>
      <Suggestions onPick={onPick} />
    </div>
  );
}

function Suggestions({ onPick }) {
  return (
    <ul className="suggest">
      {SUGGESTIONS.map((s) => (
        <li key={s}>
          <button type="button" className="suggest__btn" onClick={() => onPick(s)}>
            {s}
          </button>
        </li>
      ))}
    </ul>
  );
}

function Failure({ error }) {
  const unreachable = error?.status === 0;

  return (
    <div className="state state--error">
      <h2 className="state__title">
        {unreachable ? "The API isn't responding." : "That search failed."}
      </h2>
      <p className="state__body">{error?.message}</p>
      {unreachable && (
        <p className="state__hint">cd ETL &amp;&amp; uvicorn main:app --reload --port 8000</p>
      )}
    </div>
  );
}
