export type ViewMode = 'depenses' | 'revenus';

interface Props {
  income: number;
  expenses: number;
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}

function fmt(n: number): string {
  return Math.abs(n).toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
}

export default function SummaryCards({ income, expenses, mode, onModeChange }: Props) {
  const available = income - expenses;

  return (
    <div className="flex items-center gap-10">
      <button
        onClick={() => onModeChange('revenus')}
        className="text-left group"
      >
        <div className={`flex items-center gap-1.5 text-xs mb-1 ${mode === 'revenus' ? 'text-accent' : 'text-text-secondary'}`}>
          <span className="text-sm">↙</span>
          <span>Entrées</span>
        </div>
        <p className={`text-2xl font-bold ${mode === 'revenus' ? 'text-accent' : 'text-text-primary'}`}>
          +{fmt(income)}
        </p>
      </button>

      <button
        onClick={() => onModeChange('depenses')}
        className="text-left group"
      >
        <div className={`flex items-center gap-1.5 text-xs mb-1 ${mode === 'depenses' ? 'text-accent' : 'text-text-secondary'}`}>
          <span className="text-sm">↗</span>
          <span>Sorties</span>
        </div>
        <p className={`text-2xl font-bold ${mode === 'depenses' ? 'text-accent' : 'text-red'}`}>
          -{fmt(expenses)}
        </p>
      </button>

      <div>
        <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
          <span className="text-sm">◈</span>
          <span>Disponible</span>
        </div>
        <p className="text-2xl font-bold text-text-primary">
          {available >= 0 ? '+' : '-'}{fmt(Math.abs(available))}
        </p>
      </div>
    </div>
  );
}
