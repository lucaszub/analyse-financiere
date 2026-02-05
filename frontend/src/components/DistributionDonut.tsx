import { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { CategoryTree } from '../types';
import { CATEGORY_COLORS } from '../constants/colors';

interface Props {
  tree: CategoryTree;
  total: number;
  mode: 'depenses' | 'revenus';
}

export default function DistributionDonut({ tree, total, mode }: Props) {
  const data = useMemo(() => {
    return Object.entries(tree)
      .map(([name, { total }]) => ({ name, value: Math.abs(total) }))
      .filter((d) => d.value > 0)
      .sort((a, b) => b.value - a.value);
  }, [tree]);

  if (data.length === 0) {
    return (
      <div className="bg-bg-card border border-border-card rounded-xl p-5">
        <h3 className="text-sm font-medium text-text-secondary mb-2">Distribution</h3>
        <div className="flex items-center justify-center h-48 text-text-secondary text-sm">
          Aucune donnée
        </div>
      </div>
    );
  }

  return (
    <div className="bg-bg-card border border-border-card rounded-xl p-5">
      <h3 className="text-sm font-medium text-text-secondary mb-2">Distribution</h3>
      <div className="relative">
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={85}
              outerRadius={105}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: '#1a1a1a',
                border: '1px solid #2a2a2a',
                borderRadius: 8,
                color: '#fff',
              }}
              formatter={(value) =>
                Number(value).toLocaleString('fr-FR', { minimumFractionDigits: 2 }) + ' €'
              }
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <p className="text-xs text-text-secondary mb-1">
              {mode === 'depenses' ? 'Somme sorties' : 'Somme entrées'}
            </p>
            <p className="text-xl font-bold text-text-primary">
              {mode === 'depenses' ? '-' : '+'}
              {total.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
