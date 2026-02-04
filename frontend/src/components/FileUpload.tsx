import { useState, useRef, type DragEvent } from 'react';

interface Props {
  onFileSelected: (file: File) => void;
  file: File | null;
}

export default function FileUpload({ onFileSelected, file }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith('.csv')) {
      onFileSelected(f);
    }
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={() => setDragOver(false)}
      onClick={() => inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
        ${dragOver ? 'border-accent bg-accent/5' : 'border-border-card hover:border-text-secondary'}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFileSelected(f);
        }}
      />
      {file ? (
        <div>
          <p className="text-accent font-medium">{file.name}</p>
          <p className="text-sm text-text-secondary mt-1">
            {(file.size / 1024).toFixed(1)} Ko — Cliquer pour changer
          </p>
        </div>
      ) : (
        <div>
          <p className="text-4xl mb-3">📄</p>
          <p className="font-medium">Glisser-déposer un fichier CSV</p>
          <p className="text-sm text-text-secondary mt-1">ou cliquer pour sélectionner</p>
          <p className="text-xs text-text-secondary mt-3">Format Boursorama / BoursoBank</p>
        </div>
      )}
    </div>
  );
}
