'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/Badge';
import { Card } from '@/components/Card';
import { AIAnalysisResponse, AIStatusResponse, EvidencePackage, fetchAIStatus, fetchEvidence, generateAIAnalysis } from '@/lib/api';

const assets = ['BTC', 'ETH', 'SOL'];
const show = (value: unknown) => value === null || value === undefined ? 'Unavailable' : String(value);

export default function AIAdvisorPage() {
  const [asset, setAsset] = useState('BTC');
  const [status, setStatus] = useState<AIStatusResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidencePackage | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setLoading(true); setError(null); setAnalysis(null);
    Promise.all([fetchAIStatus(), fetchEvidence(asset)])
      .then(([nextStatus, nextEvidence]) => { if (current) { setStatus(nextStatus); setEvidence(nextEvidence); } })
      .catch((reason) => { if (current) setError(reason instanceof Error ? reason.message : 'Unable to load evidence'); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [asset]);

  async function generate() {
    setGenerating(true); setError(null);
    try { setAnalysis(await generateAIAnalysis(asset)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to generate reasoning'); }
    finally { setGenerating(false); }
  }

  const reasoning = analysis?.reasoning;
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">Evidence Fusion & AI Reasoning</h2>
        <p className="mt-1 text-xs text-gray-400">Read-only, provenance-aware market reasoning for human review. No trade actions or investment recommendations.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {assets.map((item) => <button key={item} onClick={() => setAsset(item)} className={`rounded-md border px-3 py-1.5 text-xs ${asset === item ? 'border-blue-500 bg-blue-500/10 text-blue-300' : 'border-gray-700 text-gray-400'}`}>{item}</button>)}
        <span className="ml-auto"><Badge variant={status?.configured ? 'green' : 'gray'}>{status?.configured ? `${status.ai_provider} configured` : 'AI provider not configured'}</Badge></span>
      </div>

      {error && <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">{error}</div>}
      {loading && <Card><p className="text-xs text-gray-400">Assembling deterministic evidence…</p></Card>}

      {evidence && <>
        <Card title={`${asset} Evidence Package`} subtitle={`Fingerprint ${evidence.evidence_fingerprint.slice(0, 12)}…`} badge={<Badge variant={evidence.evidence_status === 'complete' ? 'green' : 'amber'}>{evidence.evidence_status}</Badge>}>
          <div className="mb-4 h-1.5 overflow-hidden rounded bg-gray-800"><div className="h-full bg-blue-500" style={{ width: `${evidence.evidence_completeness_pct}%` }} /></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <EvidenceCard title="Market" state={evidence.market.data_status} lines={[`Price: ${show(evidence.market.price)}`, `24h: ${show(evidence.market.change_24h_pct)}%`]} />
            <EvidenceCard title="Technical" state={evidence.technical.data_status} lines={[`Trend: ${show(evidence.technical.trend)}`, `RSI: ${show(evidence.technical.rsi_14)}`, `Alignment: ${show(evidence.technical.multi_timeframe_alignment)}`]} />
            <EvidenceCard title="News" state={evidence.news.source_status} lines={[`Relevant: ${evidence.news.relevant_story_count}`, `High impact: ${evidence.news.high_impact_count}`]} />
            <EvidenceCard title="Macro" state={evidence.macro.source_status} lines={[`Next: ${show(evidence.macro.next_high_impact_event?.name)}`, `10Y: ${show(evidence.macro.yield_10y)}`]} />
            <EvidenceCard title="Portfolio" state={evidence.portfolio.data_status} lines={[`Held: ${show(evidence.portfolio.held)}`, `Allocation: ${show(evidence.portfolio.allocation_pct)}%`]} />
          </div>
          <p className="mt-4 text-xs text-gray-500">Completeness {evidence.evidence_completeness_pct}% · Freshness {evidence.freshness.overall_state} · Missing: {evidence.missing_components.join(', ') || 'none'}</p>
        </Card>

        <Card title="Structured AI Reasoning" badge={<Badge variant="purple">HUMAN DECISION SUPPORT</Badge>} action={<button disabled={!status?.configured || generating} onClick={generate} className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-40">{generating ? 'Generating…' : 'Generate reasoning'}</button>}>
          {!status?.configured && <div className="rounded-lg border border-gray-700 bg-gray-900/40 p-4 text-xs text-gray-400">AI reasoning is inactive. Configure the documented backend environment variables to enable explicit, on-demand generation. Secrets are never sent to this browser.</div>}
          {analysis && !reasoning && <p className="text-xs text-amber-300">Reasoning unavailable: {analysis.data_limitations.join(' ')}</p>}
          {reasoning && <div className="space-y-5 text-sm text-gray-300">
            <section><h4 className="mb-1 font-semibold text-gray-100">Market summary</h4><p>{reasoning.market_summary}</p></section>
            <ReasoningList title="Bull case" items={reasoning.bull_case} /><ReasoningList title="Bear case" items={reasoning.bear_case} />
            <ReasoningList title="Key risks" items={reasoning.key_risks} />
            <section><h4 className="mb-1 font-semibold text-gray-100">Portfolio context</h4><p>{reasoning.portfolio_context}</p></section>
            <ReasoningList title="Important upcoming events" items={reasoning.important_upcoming_events} />
            <ReasoningList title="Thesis invalidation conditions" items={reasoning.thesis_invalidation_conditions} />
            <ReasoningList title="Data limitations" items={reasoning.data_limitations} />
            <section><h4 className="mb-1 font-semibold text-gray-100">Evidence used</h4><ul className="list-disc space-y-1 pl-5">{reasoning.evidence_used.map((item, index) => <li key={`${item.component}-${index}`}><span className="text-blue-300">{item.component}</span>: {item.reference}</li>)}</ul></section>
          </div>}
        </Card>
      </>}
    </div>
  );
}

function EvidenceCard({ title, state, lines }: { title: string; state: string; lines: string[] }) {
  return <div className="rounded-lg border border-gray-800 bg-gray-900/40 p-3"><div className="mb-2 flex items-center justify-between"><h4 className="text-xs font-semibold text-gray-200">{title}</h4><Badge size="sm" variant={state === 'unavailable' || state === 'insufficient_data' ? 'gray' : state === 'stale' || state === 'fallback' ? 'amber' : 'blue'}>{state}</Badge></div>{lines.map((line) => <p key={line} className="truncate text-xs text-gray-400">{line}</p>)}</div>;
}

function ReasoningList({ title, items }: { title: string; items: string[] }) {
  return <section><h4 className="mb-1 font-semibold text-gray-100">{title}</h4>{items.length ? <ul className="list-disc space-y-1 pl-5">{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p className="text-gray-500">No supported observations.</p>}</section>;
}
