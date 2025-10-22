import React, { useState, useEffect } from "react";
import { useSession, useSupabaseClient } from '@supabase/auth-ui-react';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';

// This is the new PaperItem component
function PaperItem({ item }) {
  const [showAbstract, setShowAbstract] = useState(false);
  const [abstract, setAbstract] = useState('');
  const [summary, setSummary] = useState('');
  const [jargon, setJargon] = useState('');
  const [loading, setLoading] = useState({ abstract: false, summary: false, jargon: false });
  const [error, setError] = useState('');

  const fetchAbstract = async () => {
    if (showAbstract) {
      setShowAbstract(false);
      return;
    }

    setShowAbstract(true);
    if (abstract) return; // Don't fetch if we already have it

    setLoading(prev => ({ ...prev, abstract: true }));
    setError('');
    try {
      const res = await fetch(`/api/paper/${item.paper.paper_id}/abstract`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setAbstract(data.abstract || 'No abstract available.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(prev => ({ ...prev, abstract: false }));
    }
  };

  const fetchSummary = async () => {
    if (summary) {
      setSummary('');
      return;
    }
    setLoading(prev => ({ ...prev, summary: true }));
    setError('');
    try {
      const res = await fetch(`/api/paper/${item.paper.paper_id}/summary`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setSummary(data.summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(prev => ({ ...prev, summary: false }));
    }
  };

  const fetchJargon = async () => {
    if (jargon) {
      setJargon('');
      return;
    }
    setLoading(prev => ({ ...prev, jargon: true }));
    setError('');
    try {
      const res = await fetch(`/api/paper/${item.paper.paper_id}/jargon`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setJargon(data.jargon);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(prev => ({ ...prev, jargon: false }));
    }
  };

  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl">
      <h3 className="font-semibold text-lg cursor-pointer" onClick={fetchAbstract}>
        {item.paper.title}
      </h3>
      <p className="text-sm text-white/70">{item.paper.authors.join(', ')} - {item.paper.year}</p>
      
      {loading.abstract && <p className="mt-2 text-white/70">Loading abstract...</p>}
      {showAbstract && abstract && <p className="mt-2 text-white/90">{abstract}</p>}
      
      <div className="mt-4 flex gap-2 flex-wrap">
        <button onClick={fetchSummary} className="px-3 py-1 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-sm text-blue-300">
          {loading.summary ? 'Loading...' : (summary ? 'Hide Summary' : 'AI Summary')}
        </button>
        <button onClick={fetchJargon} className="px-3 py-1 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-sm text-purple-300">
          {loading.jargon ? 'Loading...' : (jargon ? 'Hide Jargon' : 'Explain Jargon')}
        </button>
        <a href={item.paper.url} target="_blank" rel="noopener noreferrer" className="px-3 py-1 rounded-lg bg-gray-500/20 hover:bg-gray-500/30 text-sm text-gray-300">
          Read Paper
        </a>
      </div>

      {summary && <div className="mt-4 p-4 rounded-lg bg-white/5"><h4 className="font-bold">Summary:</h4><p>{summary}</p></div>}
      {jargon && <div className="mt-4 p-4 rounded-lg bg-white/5"><h4 className="font-bold">Jargon:</h4><p>{jargon}</p></div>}
      {error && <div className="mt-4 text-red-400">{error}</div>}
    </div>
  );
}


export default function App() {
  // We always render the AppContent for the demo version
  return <AppContent />;
}

function AppContent() {
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
      const headers = { 'Content-Type': 'application/json' };
      // No auth needed for demo
      const res = await fetch(`/api/roadmap`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setResults(data.roadmap);
    } catch (err) {
      setError(err.message);
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
          <span className="font-semibold tracking-tight">ScholarSage (Demo)</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm text-white/80">
          <a className="hover:text-white" href="#">Home</a>
          <a className="hover:text-white" href="#">Explore</a>
          <a className="hover:text-white" href="#">Library</a>
        </nav>
        <div className="flex items-center gap-3">
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
            icon="add an icon here"
            title="Ask Questions"
            body="Input your questions or topics of interest in the search bar."
          />
          <InfoCard
            icon="add an icon here"
            title="Explore Papers"
            body="Browse our extensive library of research papers across various scientific disciplines."
          />
          <InfoCard
            icon="add an icon here"
            title="Learn and Share"
            body="Gain insights from scientific papers and share your knowledge with others."
          />
        </div>
      </section>

      {/* Results */}
      <section className="max-w-6xl mx-auto px-4 mt-10 mb-20">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-4 rounded-xl">{error}</div>
        )}

        {results && (
          <div className="space-y-4">
            {results.map((item, index) => (
              <PaperItem key={index} item={item} />
            ))}
          </div>
        )}
      </section>

      {/* footer */}
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