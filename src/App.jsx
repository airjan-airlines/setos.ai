import React, { useState } from "react";

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  async function onSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResults(null);
    try {
      const res = await fetch(
        `https://dummyjson.com/posts/search?q=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError("Placeholder API request failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0d0b12] text-white">
      <Style />
      {/* Top Nav */}
      <header className="max-w-6xl mx-auto flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-full bg-white/90" />
          <span className="font-semibold tracking-tight">ScholarSage</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm text-white/80">
          <a className="hover:text-white" href="#">Home</a>
          <a className="hover:text-white" href="#">Explore</a>
          <a className="hover:text-white" href="#">Library</a>
        </nav>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 border border-white/10 text-sm">Log In</button>
          <button className="px-4 py-2 rounded-xl bg-[#8b5cf6] hover:bg-[#7c3aed] text-sm">Sign Up</button>
        </div>
      </header>

      {/* Hero Card */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="rounded-2xl p-10 md:p-14 bg-gradient-to-br from-[#ff6cd9] via-[#6ea8ff] to-[#4ade80] text-center shadow-2xl">
          <h1 className="text-3xl md:text-5xl font-extrabold leading-tight drop-shadow-sm">
            Unlock the Power of Scientific
            <br />
            Knowledge
          </h1>
          <p className="mt-4 text-white/90 max-w-3xl mx-auto">
            Explore a vast collection of research papers and get instant answers to your questions.
            Dive deep into the world of science with ScholarSage.
          </p>

          <form onSubmit={onSearch} className="mt-8 mx-auto max-w-2xl">
            <div className="flex items-stretch bg-black/30 backdrop-blur rounded-xl border border-white/20 overflow-hidden">
              <div className="pl-4 flex items-center text-white/70">🔍</div>
              <input
                aria-label="Search"
                className="flex-1 bg-transparent outline-none px-4 py-3 text-white placeholder-white/70"
                placeholder="Ask a question or enter a topic"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] px-5 py-3 font-medium"
                disabled={loading}
              >
                {loading ? "Searching…" : "Search"}
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-4 mt-14">
        <h2 className="text-2xl md:text-3xl font-bold">How ScholarSage Works</h2>
        <p className="mt-2 text-white/70 max-w-3xl">
          Our platform simplifies the process of understanding complex scientific literature. Here's how you can benefit:
        </p>

        <div className="grid md:grid-cols-3 gap-5 mt-6">
          <InfoCard
            icon="❓"
            title="Ask Questions"
            body="Input your questions or topics of interest in the search bar."
          />
          <InfoCard
            icon="📚"
            title="Explore Papers"
            body="Browse our extensive library of research papers across various scientific disciplines."
          />
          <InfoCard
            icon="💬"
            title="Learn and Share"
            body="Gain insights from scientific papers and share your knowledge with others."
          />
        </div>
      </section>

      {/* Placeholder results */}
      <section className="max-w-6xl mx-auto px-4 mt-10 mb-20">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-4 rounded-xl">{error}</div>
        )}

        {results && (
          <div className="bg-white/5 border border-white/10 p-5 rounded-2xl">
            <h3 className="font-semibold mb-2">Placeholder Results</h3>
            <p className="text-sm text-white/70 mb-4">
              {`Fetched ${results?.total ?? 0} items from the placeholder API for "${query}".`}
            </p>
            <ul className="space-y-2">
              {(results.posts || []).slice(0, 5).map((p) => (
                <li key={p.id} className="p-3 rounded-lg bg-black/30 border border-white/10">
                  <div className="text-sm opacity-80">Post #{p.id}</div>
                  <div className="font-medium">{p.title}</div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-10 mt-10">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center md:items-start justify-between gap-6 text-sm text-white/60">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-white/80" />
              <span>ScholarSage</span>
            </div>
            <div>©2024 ScholarSage. All rights reserved.</div>
          </div>
          <div className="flex gap-8">
            <a className="hover:text-white" href="#">About</a>
            <a className="hover:text-white" href="#">Contact</a>
            <a className="hover:text-white" href="#">Terms of Service</a>
            <a className="hover:text-white" href="#">Privacy Policy</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function InfoCard({ icon, title, body }) {
  return (
    <div className="rounded-2xl bg-white/5 border border-white/10 p-5">
      <div className="text-2xl">{icon}</div>
      <div className="mt-2 font-semibold">{title}</div>
      <div className="mt-1 text-sm text-white/70">{body}</div>
    </div>
  );
}

function Style() {
  return (
    <style>{`
      :root { color-scheme: dark; }
      *{ box-sizing: border-box; }
      html, body, #root { height: 100%; }
      body {
        margin: 0;
        font-family: 'Source Sans 3', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
      }
      /* utility classes same as before */
    `}</style>
  );
}

