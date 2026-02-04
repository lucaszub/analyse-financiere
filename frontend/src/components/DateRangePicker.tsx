import { useMemo } from 'react';

interface Props {
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
}

function formatMonthLabel(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const months = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
  ];
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
    return `${months[s.getMonth()]} ${s.getFullYear()}`;
  }
  return `${months[s.getMonth()]} ${s.getFullYear()} — ${months[e.getMonth()]} ${e.getFullYear()}`;
}

function shiftMonth(dateStr: string, delta: number): string {
  const d = new Date(dateStr);
  d.setMonth(d.getMonth() + delta);
  return d.toISOString().slice(0, 10);
}

function startOfMonth(d: Date): string {
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function endOfMonth(d: Date): string {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().slice(0, 10);
}

export default function DateRangePicker({ startDate, endDate, onChange }: Props) {
  const label = useMemo(() => formatMonthLabel(startDate, endDate), [startDate, endDate]);

  const navigateMonth = (delta: number) => {
    onChange(shiftMonth(startDate, delta), shiftMonth(endDate, delta));
  };

  const setPreset = (months: number) => {
    const now = new Date();
    const end = endOfMonth(now);
    const start = startOfMonth(new Date(now.getFullYear(), now.getMonth() - months + 1, 1));
    onChange(start, end);
  };

  return (
    <div className="flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigateMonth(-1)}
          className="w-8 h-8 rounded-lg bg-bg-card border border-border-card flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-accent/50 transition-colors"
        >
          ‹
        </button>
        <span className="text-lg font-semibold min-w-48 text-center">{label}</span>
        <button
          onClick={() => navigateMonth(1)}
          className="w-8 h-8 rounded-lg bg-bg-card border border-border-card flex items-center justify-center text-text-secondary hover:text-text-primary hover:border-accent/50 transition-colors"
        >
          ›
        </button>
      </div>
      <div className="flex gap-2">
        {[
          { label: '1M', months: 1 },
          { label: '3M', months: 3 },
          { label: '6M', months: 6 },
          { label: '1A', months: 12 },
        ].map((p) => (
          <button
            key={p.label}
            onClick={() => setPreset(p.months)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-bg-card border border-border-card text-text-secondary hover:text-accent hover:border-accent/50 transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2 ml-auto">
        <input
          type="date"
          value={startDate}
          onChange={(e) => onChange(e.target.value, endDate)}
          className="bg-bg-card border border-border-card rounded-lg px-3 py-1.5 text-sm text-text-primary [color-scheme:dark]"
        />
        <span className="text-text-secondary">→</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => onChange(startDate, e.target.value)}
          className="bg-bg-card border border-border-card rounded-lg px-3 py-1.5 text-sm text-text-primary [color-scheme:dark]"
        />
      </div>
    </div>
  );
}
