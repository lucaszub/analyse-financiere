import { useState } from 'react';
import type { Transaction, CategoryTree } from '../types';
import { CATEGORY_COLORS } from '../constants/colors';

function fmt(n: number): string {
  return Math.abs(n).toLocaleString('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' €';
}

interface Props {
  tree: CategoryTree;
  onRecategorize: (txn: Transaction) => void;
}

export default function CategoryAccordion({ tree, onRecategorize }: Props) {
  const [openParent, setOpenParent] = useState<string | null>(null);
  const [openSub, setOpenSub] = useState<string | null>(null);

  const sorted = Object.entries(tree).sort(([, a], [, b]) => Math.abs(b.total) - Math.abs(a.total));

  return (
    <div className="bg-bg-card border border-border-card rounded-xl overflow-hidden divide-y divide-border-card">
      {sorted.map(([parent, { total, subs }], index) => {
        const color = CATEGORY_COLORS[index % CATEGORY_COLORS.length];
        const isOpen = openParent === parent;

        return (
          <div key={parent}>
            <button
              onClick={() => setOpenParent(isOpen ? null : parent)}
              className="w-full flex items-center justify-between px-5 py-4 hover:bg-white/3 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span
                  className="w-9 h-9 rounded-full shrink-0 flex items-center justify-center"
                  style={{ backgroundColor: color + '20' }}
                >
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                </span>
                <span className="font-medium">{parent}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-semibold">-{fmt(total)}</span>
                <span className="text-text-secondary text-lg">›</span>
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-border-card">
                {Object.entries(subs)
                  .sort(([, a], [, b]) => Math.abs(b.total) - Math.abs(a.total))
                  .map(([sub, { total: subTotal, transactions }]) => {
                    const subKey = `${parent}/${sub}`;
                    const subIsOpen = openSub === subKey;

                    return (
                      <div key={sub} className="border-b border-border-card last:border-b-0">
                        <button
                          onClick={() => setOpenSub(subIsOpen ? null : subKey)}
                          className="w-full flex items-center justify-between px-5 py-3 pl-16 hover:bg-white/3 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-text-secondary">{sub}</span>
                            <span className="text-xs text-text-secondary/60">
                              ({transactions.length})
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-medium">-{fmt(subTotal)}</span>
                            <span className={`text-xs text-text-secondary transition-transform ${subIsOpen ? 'rotate-90' : ''}`}>
                              ›
                            </span>
                          </div>
                        </button>

                        {subIsOpen && (
                          <div className="bg-bg-primary/50">
                            {transactions
                              .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                              .map((txn) => (
                                <div
                                  key={txn.id}
                                  className="flex items-center justify-between px-5 py-2.5 pl-20 border-t border-border-card/50 hover:bg-white/3"
                                >
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3">
                                      <span className="text-xs text-text-secondary w-20 shrink-0">
                                        {new Date(txn.date).toLocaleDateString('fr-FR')}
                                      </span>
                                      <span className="text-sm truncate">
                                        {txn.description}
                                      </span>
                                    </div>
                                    {txn.category_name && (
                                      <span className="text-xs text-text-secondary/60 ml-[5.75rem]">
                                        {txn.category_name}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 shrink-0 ml-4">
                                    <span className={`text-sm font-medium ${txn.transaction_type === 'credit' ? 'text-green' : 'text-red'}`}>
                                      {txn.transaction_type === 'credit' ? '+' : '-'}{fmt(txn.amount)}
                                    </span>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        onRecategorize(txn);
                                      }}
                                      className="text-xs px-2 py-1 rounded-md bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                                    >
                                      Recat
                                    </button>
                                  </div>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
