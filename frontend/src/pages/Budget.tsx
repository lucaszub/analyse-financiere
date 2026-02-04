import { useState, useEffect, useCallback, useMemo } from 'react';
import DateRangePicker from '../components/DateRangePicker';
import SummaryCards from '../components/SummaryCards';
import DistributionDonut from '../components/DistributionDonut';
import CategoryAccordion from '../components/CategoryAccordion';
import RecatModal from '../components/RecatModal';
import { getTransactionsByRange, getCategories } from '../api/client';
import type { Transaction, Category, CategoryTree } from '../types';

function startOfMonth(d: Date): string {
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function endOfMonth(d: Date): string {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0).toISOString().slice(0, 10);
}

const INTERNAL_FILTERS = ['Mouvements internes débiteurs', 'Mouvements internes créditeurs'];

function isInternalTransfer(t: Transaction): boolean {
  return INTERNAL_FILTERS.includes(t.category_parent_csv || '');
}

function buildTree(transactions: Transaction[]): CategoryTree {
  const tree: CategoryTree = {};
  transactions.forEach((t) => {
    if (t.transaction_type === 'credit' || isInternalTransfer(t)) return;
    const parent = t.parent_category || 'Non catégorisé';
    const sub = t.sub_category || 'Non catégorisé';
    if (!tree[parent]) tree[parent] = { total: 0, subs: {} };
    if (!tree[parent].subs[sub]) tree[parent].subs[sub] = { total: 0, transactions: [] };
    tree[parent].total += Math.abs(t.amount);
    tree[parent].subs[sub].total += Math.abs(t.amount);
    tree[parent].subs[sub].transactions.push(t);
  });
  return tree;
}

export default function Budget() {
  const now = new Date();
  const [startDate, setStartDate] = useState(startOfMonth(now));
  const [endDate, setEndDate] = useState(endOfMonth(now));
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [recatTxn, setRecatTxn] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [txns, cats] = await Promise.all([
        getTransactionsByRange(startDate, endDate),
        getCategories(),
      ]);
      setTransactions(txns);
      setCategories(cats);
    } catch (err) {
      console.error('Erreur chargement:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filtered = useMemo(
    () => transactions.filter((t) => !isInternalTransfer(t)),
    [transactions]
  );

  const income = useMemo(
    () => filtered.filter((t) => t.transaction_type === 'credit').reduce((s, t) => s + Math.abs(t.amount), 0),
    [filtered]
  );

  const expenses = useMemo(
    () => filtered.filter((t) => t.transaction_type === 'debit').reduce((s, t) => s + Math.abs(t.amount), 0),
    [filtered]
  );

  const tree = useMemo(() => buildTree(transactions), [transactions]);

  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  const handleRecatDone = () => {
    setRecatTxn(null);
    fetchData();
  };

  return (
    <div className="space-y-6 max-w-7xl">
      <DateRangePicker startDate={startDate} endDate={endDate} onChange={handleDateChange} />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <SummaryCards income={income} expenses={expenses} />

              <div>
                <p className="text-sm text-text-secondary mb-3">
                  {Object.keys(tree).length} catégories de sorties
                </p>
                <CategoryAccordion tree={tree} onRecategorize={setRecatTxn} />
              </div>

              {filtered.filter((t) => t.transaction_type === 'credit').length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-text-secondary mb-3">Détail des entrées</h3>
                  <div className="bg-bg-card border border-border-card rounded-xl divide-y divide-border-card">
                    {filtered
                      .filter((t) => t.transaction_type === 'credit')
                      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                      .map((txn) => (
                        <div key={txn.id} className="flex items-center justify-between px-5 py-3">
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-text-secondary w-20">
                              {new Date(txn.date).toLocaleDateString('fr-FR')}
                            </span>
                            <span className="text-sm">{txn.description}</span>
                          </div>
                          <span className="text-sm font-medium text-green">
                            +{Math.abs(txn.amount).toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-1">
              <div className="sticky top-6">
                <DistributionDonut tree={tree} totalExpenses={expenses} />
              </div>
            </div>
          </div>
        </>
      )}

      {recatTxn && (
        <RecatModal
          transaction={recatTxn}
          categories={categories}
          onClose={() => setRecatTxn(null)}
          onDone={handleRecatDone}
        />
      )}
    </div>
  );
}
