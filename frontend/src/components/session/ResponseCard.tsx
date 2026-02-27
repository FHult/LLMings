/**
 * ResponseCard component for displaying individual AI responses
 */
import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import type { CouncilResponse, ConsensusStructure } from '@/types';
import ReactMarkdown from 'react-markdown';

interface ResponseCardProps {
  response: CouncilResponse;
  isMerged?: boolean;
}

const providerColors: Record<string, string> = {
  openai: 'bg-green-100 text-green-800 border-green-300',
  anthropic: 'bg-purple-100 text-purple-800 border-purple-300',
  google: 'bg-blue-100 text-blue-800 border-blue-300',
  grok: 'bg-orange-100 text-orange-800 border-orange-300',
};

const providerNames: Record<string, string> = {
  openai: 'ChatGPT',
  anthropic: 'Claude',
  google: 'Gemini',
  grok: 'Grok',
};

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? 'bg-green-100 text-green-700' :
    pct >= 60 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700';
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${color}`}>
      {pct}% confidence
    </span>
  );
}

function ConsensusPanel({ structure }: { structure: ConsensusStructure }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-4 border-t pt-3 space-y-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <span className="text-primary">{open ? '▾' : '▸'}</span>
        Council analysis
        <ConfidenceBadge value={structure.confidence} />
      </button>

      {open && (
        <div className="space-y-3 text-sm">
          {structure.key_agreements.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1">
                Agreements
              </p>
              <ul className="space-y-0.5">
                {structure.key_agreements.map((a, i) => (
                  <li key={i} className="flex gap-1.5 text-muted-foreground">
                    <span className="text-green-500 shrink-0">✓</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {structure.key_disagreements.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">
                Disagreements
              </p>
              <ul className="space-y-0.5">
                {structure.key_disagreements.map((d, i) => (
                  <li key={i} className="flex gap-1.5 text-muted-foreground">
                    <span className="text-amber-500 shrink-0">△</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {structure.reasoning && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                Chair reasoning
              </p>
              <p className="text-muted-foreground italic">{structure.reasoning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const ResponseCard: React.FC<ResponseCardProps> = ({ response, isMerged = false }) => {
  const colorClass = providerColors[response.provider] || 'bg-gray-100 text-gray-800 border-gray-300';
  const providerDisplayName = providerNames[response.provider] || response.provider;

  // Use member_role if available, otherwise fall back to provider name
  const displayName = response.member_role || providerDisplayName;

  return (
    <Card className={`p-4 ${isMerged ? 'border-2 border-primary bg-primary/5' : 'border'}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${colorClass}`}>
            {displayName}
          </span>
          {isMerged && (
            <span className="px-2 py-1 rounded bg-primary text-primary-foreground text-xs font-semibold">
              MERGED CONSENSUS
            </span>
          )}
          {response.type === 'feedback' && (
            <span className="px-2 py-1 rounded bg-secondary text-secondary-foreground text-xs">
              Feedback
            </span>
          )}
        </div>
        <div className="flex flex-col items-end text-xs text-muted-foreground">
          <div>
            {response.tokens.input.toLocaleString()} in / {response.tokens.output.toLocaleString()} out
          </div>
          <div className="font-semibold">${response.cost.toFixed(4)}</div>
        </div>
      </div>

      <div className="prose prose-sm max-w-none">
        <ReactMarkdown>{response.content}</ReactMarkdown>
      </div>

      {isMerged && response.structure && (
        <ConsensusPanel structure={response.structure} />
      )}
    </Card>
  );
};
