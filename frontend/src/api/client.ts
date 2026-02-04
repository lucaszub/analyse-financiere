import axios from 'axios';
import type { Transaction, Category, Account, ImportStats, CategorizationRule } from '../types';

const api = axios.create({
  baseURL: '/api',
});

export async function getTransactionsByRange(
  startDate: string,
  endDate: string,
  accountId?: number
): Promise<Transaction[]> {
  const params: Record<string, string | number> = {
    start_date: startDate,
    end_date: endDate,
  };
  if (accountId) params.account_id = accountId;
  const { data } = await api.get<Transaction[]>('/transactions/range', { params });
  return data;
}

export async function updateTransactionCategory(
  txnId: number,
  categoryId: number
): Promise<Transaction> {
  const { data } = await api.patch<Transaction>(`/transactions/${txnId}/category`, {
    category_id: categoryId,
  });
  return data;
}

export async function getCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>('/categories');
  return data;
}

export async function createCategory(payload: {
  name: string;
  parent_category: string;
  sub_category: string;
}): Promise<Category> {
  const { data } = await api.post<Category>('/categories', payload);
  return data;
}

export async function getAccounts(): Promise<Account[]> {
  const { data } = await api.get<Account[]>('/accounts');
  return data;
}

export async function uploadCSV(file: File, accountId: number = 1): Promise<ImportStats> {
  const form = new FormData();
  form.append('file', file);
  form.append('account_id', String(accountId));
  const { data } = await api.post<ImportStats>('/upload', form);
  return data;
}

export async function getRules(): Promise<CategorizationRule[]> {
  const { data } = await api.get<CategorizationRule[]>('/rules');
  return data;
}

export async function createRule(payload: {
  keyword: string;
  category_id: number;
  match_field: string;
}): Promise<CategorizationRule> {
  const { data } = await api.post<CategorizationRule>('/rules', payload);
  return data;
}

export async function applyRules(): Promise<{ updated: number }> {
  const { data } = await api.post<{ updated: number }>('/rules/apply');
  return data;
}
