export interface Transaction {
  id: number;
  account_id: number;
  category_id: number | null;
  transaction_type: 'debit' | 'credit';
  amount: number;
  description: string | null;
  date: string;
  merchant: string | null;
  notes: string | null;
  category_parent_csv: string | null;
  import_id?: string;
  created_at: string;
  category_name: string | null;
  parent_category: string | null;
  sub_category: string | null;
}

export interface Category {
  id: number;
  name: string;
  parent_category: string | null;
  sub_category: string | null;
}

export interface Account {
  id: number;
  name: string;
  account_type: string | null;
  balance: number;
  is_active: boolean;
}

export interface ImportStats {
  total_rows: number;
  imported: number;
  duplicates: number;
  errors: number;
  error_details: string[];
}

export interface CategorizationRule {
  id: number;
  keyword: string;
  category_id: number;
  match_field: string;
  is_active: boolean;
  created_at: string;
}

export interface CategoryTree {
  [parentCategory: string]: {
    total: number;
    subs: {
      [subCategory: string]: {
        total: number;
        transactions: Transaction[];
      };
    };
  };
}
