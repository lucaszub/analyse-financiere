import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import type { Transaction } from '../types';

const CATEGORY_COLORS: Record<string, string> = {
  BesoinsEssentiels: '#6366f1',
  Transport: '#f59e0b',
  LoisirsDivertissement: '#ec4899',
  AlimentationBoissons: '#f97316',
  AbonnementsFactures: '#8b5cf6',
  ImpôtsTaxes: '#ef4444',
  SantéAssurance: '#14b8a6',
  ÉpargneInvestissement: '#3b82f6',
  DépensesProfessionnelles: '#64748b',
  Autres: '#a1a1aa',
};

interface Props {
  transactions: Transaction[];
}

export default function CashflowChart({ transactions }: Props) {
  const data = useMemo(() => {
    const grouped: Record<string, Record<string, number>> = {};

    transactions.forEach((t) => {
      const month = t.date.slice(0, 7); // YYYY-MM
      if (!grouped[month]) grouped[month] = { Revenus: 0 };

      if (t.transaction_type === 'credit') {
        grouped[month].Revenus = (grouped[month].Revenus || 0) + Math.abs(t.amount);
      } else {
        const cat = t.parent_category || 'Autres';
        grouped[month][cat] = (grouped[month][cat] || 0) + Math.abs(t.amount);
      }
    });

    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, vals]) => ({ month, ...vals }));
  }, [transactions]);

  const expenseKeys = useMemo(() => {
    const keys = new Set<string>();
    data.forEach((d) => {
      Object.keys(d).forEach((k) => {
        if (k !== 'month' && k !== 'Revenus') keys.add(k);
      });
    });
    return Array.from(keys);
  }, [data]);

  if (data.length === 0) return null;

  return (
    <div className="bg-bg-card border border-border-card rounded-xl p-5">
      <h3 className="text-sm font-medium text-text-secondary mb-4">Cashflow</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
          <XAxis
            dataKey="month"
            tick={{ fill: '#888', fontSize: 12 }}
            axisLine={{ stroke: '#2a2a2a' }}
          />
          <YAxis
            tick={{ fill: '#888', fontSize: 12 }}
            axisLine={{ stroke: '#2a2a2a' }}
            tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 8 }}
            labelStyle={{ color: '#fff' }}
            formatter={(value) =>
              Number(value).toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €'
            }
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#888' }} />
          <Bar dataKey="Revenus" fill="#4ade80" radius={[4, 4, 0, 0]} />
          {expenseKeys.map((key) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="expenses"
              fill={CATEGORY_COLORS[key] || '#666'}
              radius={[0, 0, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
