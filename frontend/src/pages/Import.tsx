import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import { uploadCSV, applyRules, getAccounts } from '../api/client';
import type { ImportStats, Account } from '../types';

export default function Import() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[][]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState(1);
  const [stats, setStats] = useState<ImportStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [rulesResult, setRulesResult] = useState<number | null>(null);

  const handleFileSelected = async (f: File) => {
    setFile(f);
    setStats(null);
    setRulesResult(null);

    // Charger les comptes
    if (accounts.length === 0) {
      try {
        const accs = await getAccounts();
        setAccounts(accs);
        if (accs.length > 0) setSelectedAccount(accs[0].id);
      } catch (err) {
        console.error('Erreur chargement comptes:', err);
      }
    }

    // Preview CSV
    try {
      const text = await f.text();
      const lines = text.split('\n').filter((l) => l.trim());
      const rows = lines.slice(0, 6).map((line) =>
        line.split(';').map((cell) => cell.replace(/^"|"$/g, '').trim())
      );
      setPreview(rows);
    } catch {
      setPreview([]);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const result = await uploadCSV(file, selectedAccount);
      setStats(result);
    } catch (err) {
      console.error('Erreur import:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRules = async () => {
    try {
      const result = await applyRules();
      setRulesResult(result.updated);
    } catch (err) {
      console.error('Erreur application règles:', err);
    }
  };

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-xl font-semibold">Import CSV</h2>

      <FileUpload file={file} onFileSelected={handleFileSelected} />

      {preview.length > 0 && (
        <div className="bg-bg-card border border-border-card rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-border-card">
            <h3 className="text-sm font-medium text-text-secondary">Aperçu</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  {preview[0]?.map((header, i) => (
                    <th
                      key={i}
                      className="text-left px-4 py-2 text-xs text-text-secondary font-medium bg-bg-primary/50"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.slice(1).map((row, ri) => (
                  <tr key={ri} className="border-t border-border-card/50">
                    {row.map((cell, ci) => (
                      <td key={ci} className="px-4 py-2 text-text-secondary whitespace-nowrap">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {file && (
        <div className="flex items-center gap-4">
          {accounts.length > 1 && (
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(Number(e.target.value))}
              className="bg-bg-card border border-border-card rounded-lg px-3 py-2 text-sm text-text-primary"
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          )}
          <button
            onClick={handleImport}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg text-sm font-medium bg-accent text-bg-primary hover:bg-accent/90 disabled:opacity-40 transition-colors"
          >
            {loading ? 'Import en cours...' : 'Importer'}
          </button>
        </div>
      )}

      {stats && (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Total lignes', value: stats.total_rows, color: '' },
              { label: 'Importées', value: stats.imported, color: 'text-green' },
              { label: 'Doublons', value: stats.duplicates, color: 'text-accent' },
              { label: 'Erreurs', value: stats.errors, color: 'text-red' },
            ].map((s) => (
              <div key={s.label} className="bg-bg-card border border-border-card rounded-xl p-4">
                <p className="text-text-secondary text-xs mb-1">{s.label}</p>
                <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              </div>
            ))}
          </div>

          {stats.error_details.length > 0 && (
            <div className="bg-bg-card border border-red/30 rounded-xl p-4">
              <p className="text-sm font-medium text-red mb-2">Détails des erreurs</p>
              <ul className="text-sm text-text-secondary space-y-1">
                {stats.error_details.map((e, i) => (
                  <li key={i}>• {e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="bg-bg-card border border-border-card rounded-xl p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium">Ré-appliquer les règles</h3>
            <p className="text-xs text-text-secondary mt-1">
              Catégorise automatiquement les transactions sans catégorie
            </p>
          </div>
          <button
            onClick={handleApplyRules}
            className="px-4 py-2 rounded-lg text-sm bg-bg-primary border border-border-card text-text-secondary hover:text-text-primary hover:border-accent/50 transition-colors"
          >
            Appliquer
          </button>
        </div>
        {rulesResult !== null && (
          <p className="text-sm text-green mt-3">{rulesResult} transaction(s) mise(s) à jour</p>
        )}
      </div>
    </div>
  );
}
