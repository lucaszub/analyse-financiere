import { useState, useMemo } from 'react';
import type { Transaction, Category } from '../types';
import { updateTransactionCategory, createCategory, createRule } from '../api/client';

interface Props {
  transaction: Transaction;
  categories: Category[];
  onClose: () => void;
  onDone: () => void;
}

export default function RecatModal({ transaction, categories, onClose, onDone }: Props) {
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(transaction.category_id);
  const [wantRule, setWantRule] = useState(false);
  const [ruleKeyword, setRuleKeyword] = useState('');
  const [ruleMatchField, setRuleMatchField] = useState('description');
  const [wantNewCategory, setWantNewCategory] = useState(false);
  const [newCatName, setNewCatName] = useState('');
  const [newCatParent, setNewCatParent] = useState('');
  const [newCatSub, setNewCatSub] = useState('');
  const [loading, setLoading] = useState(false);

  const grouped = useMemo(() => {
    const map: Record<string, Record<string, Category[]>> = {};
    categories.forEach((c) => {
      const p = c.parent_category || 'Autres';
      const s = c.sub_category || 'Autres';
      if (!map[p]) map[p] = {};
      if (!map[p][s]) map[p][s] = [];
      map[p][s].push(c);
    });
    return map;
  }, [categories]);

  const parentCategories = useMemo(() => Object.keys(grouped).sort(), [grouped]);
  const subCategories = useMemo(() => {
    if (!newCatParent || !grouped[newCatParent]) return [];
    return Object.keys(grouped[newCatParent]).sort();
  }, [grouped, newCatParent]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let catId = selectedCategoryId;

      if (wantNewCategory && newCatName && newCatParent && newCatSub) {
        const newCat = await createCategory({
          name: newCatName,
          parent_category: newCatParent,
          sub_category: newCatSub,
        });
        catId = newCat.id;
      }

      if (catId) {
        await updateTransactionCategory(transaction.id, catId);

        if (wantRule && ruleKeyword) {
          await createRule({
            keyword: ruleKeyword,
            category_id: catId,
            match_field: ruleMatchField,
          });
        }
      }

      onDone();
    } catch (err) {
      console.error('Erreur recatégorisation:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-bg-card border border-border-card rounded-2xl w-full max-w-lg p-6 space-y-5 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recatégoriser</h2>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary text-xl">×</button>
        </div>

        <div className="text-sm text-text-secondary space-y-1">
          <p><span className="text-text-primary">{transaction.description}</span></p>
          <p>
            {new Date(transaction.date).toLocaleDateString('fr-FR')} —{' '}
            <span className={transaction.transaction_type === 'credit' ? 'text-green' : 'text-red'}>
              {Math.abs(transaction.amount).toLocaleString('fr-FR', { minimumFractionDigits: 2 })} €
            </span>
          </p>
          {transaction.category_name && (
            <p>Catégorie actuelle : {transaction.parent_category} › {transaction.sub_category} › {transaction.category_name}</p>
          )}
        </div>

        {!wantNewCategory && (
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Nouvelle catégorie</label>
            <select
              value={selectedCategoryId ?? ''}
              onChange={(e) => setSelectedCategoryId(Number(e.target.value))}
              className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
            >
              <option value="">-- Choisir --</option>
              {parentCategories.map((p) => (
                <optgroup key={p} label={p}>
                  {Object.entries(grouped[p]).map(([sub, cats]) =>
                    cats.map((c) => (
                      <option key={c.id} value={c.id}>
                        {sub} › {c.name}
                      </option>
                    ))
                  )}
                </optgroup>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={wantNewCategory}
              onChange={(e) => setWantNewCategory(e.target.checked)}
              className="accent-accent"
            />
            <span className="text-text-secondary">Créer une nouvelle catégorie</span>
          </label>

          {wantNewCategory && (
            <div className="mt-3 space-y-3 pl-6">
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Catégorie parente</label>
                <input
                  type="text"
                  list="parent-cats"
                  value={newCatParent}
                  onChange={(e) => setNewCatParent(e.target.value)}
                  className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
                />
                <datalist id="parent-cats">
                  {parentCategories.map((p) => <option key={p} value={p} />)}
                </datalist>
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Sous-catégorie</label>
                <input
                  type="text"
                  list="sub-cats"
                  value={newCatSub}
                  onChange={(e) => setNewCatSub(e.target.value)}
                  className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
                />
                <datalist id="sub-cats">
                  {subCategories.map((s) => <option key={s} value={s} />)}
                </datalist>
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Nom</label>
                <input
                  type="text"
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
                />
              </div>
            </div>
          )}
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={wantRule}
              onChange={(e) => setWantRule(e.target.checked)}
              className="accent-accent"
            />
            <span className="text-text-secondary">Créer une règle automatique</span>
          </label>

          {wantRule && (
            <div className="mt-3 space-y-3 pl-6">
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Mot-clé</label>
                <input
                  type="text"
                  value={ruleKeyword}
                  onChange={(e) => setRuleKeyword(e.target.value)}
                  placeholder={transaction.merchant || transaction.description || ''}
                  className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary/40"
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Champ de correspondance</label>
                <select
                  value={ruleMatchField}
                  onChange={(e) => setRuleMatchField(e.target.value)}
                  className="w-full bg-bg-primary border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
                >
                  <option value="description">Description</option>
                  <option value="merchant">Commerçant</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary border border-border-card hover:border-text-secondary transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || (!selectedCategoryId && !wantNewCategory)}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-accent text-bg-primary hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'En cours...' : 'Valider'}
          </button>
        </div>
      </div>
    </div>
  );
}
