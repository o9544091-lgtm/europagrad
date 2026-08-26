"use client";
/* Scholarly Ledger style: compact tabular score signal using a circular evidence-weighted progress ring. */
export function ScoreRing({ score }: { score: number }) {
  const circumference = 213.6;
  const offset = circumference - (score / 100) * circumference;
  return <div className="relative grid h-24 w-24 place-items-center" aria-label={`Sample programme score ${score} out of 100`}><svg className="h-24 w-24 -rotate-90" viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" className="text-secondary" strokeWidth="7" /><circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" className="text-primary" strokeWidth="7" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} /></svg><span className="absolute tabular text-xl font-extrabold text-primary">{score}</span></div>;
}
