interface Props {
  income: number;
  expenses: number;
}

function fmt(n: number): string {
  return Math.abs(n).toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' €';
}

export default function SummaryCards({ income, expenses }: Props) {
  const available = income - expenses;

  const cards = [
    { label: 'Entrées', value: income, prefix: '+', colorClass: 'text-text-primary', icon: '↙' },
    { label: 'Sorties', value: expenses, prefix: '-', colorClass: 'text-red', icon: '↗' },
    { label: 'Disponible', value: Math.abs(available), prefix: available >= 0 ? '+' : '-', colorClass: 'text-text-primary', icon: '◈' },
  ];

  return (
    <div className="flex items-center gap-10">
      {cards.map((c) => (
        <div key={c.label}>
          <div className="flex items-center gap-1.5 text-text-secondary text-xs mb-1">
            <span className="text-sm">{c.icon}</span>
            <span>{c.label}</span>
          </div>
          <p className={`text-2xl font-bold ${c.colorClass}`}>
            {c.prefix}{fmt(c.value)}
          </p>
        </div>
      ))}
    </div>
  );
}
