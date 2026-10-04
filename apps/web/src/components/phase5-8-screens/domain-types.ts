export type Loan = {
  id: number;
  purpose: string;
  amount: string;
  currency: string;
  term_months: number;
  estimated_monthly_payment: string;
  status: string;
  disclosure: string;
  illustrative_score?: number;
  score_reasons?: string;
  can_review?: boolean;
  installments?: {
    id: number;
    installment_number: number;
    due_at: string;
    amount: string;
    status: string;
  }[];
};
export type KycCase = {
  id: number;
  customer_id: number;
  category: string;
  summary: string;
  score: number;
  status: string;
  decision: string;
  notes?: string;
  evidence_reference?: string;
};
export type Bnpl = {
  id: number;
  merchant_name: string;
  purchase_amount: string;
  currency: string;
  installment_count: number;
  installment_amount: string;
  status: string;
  installments: {
    id: number;
    installment_number: number;
    due_at: string;
    amount: string;
    status: string;
  }[];
  disclosure: string;
};
export type LoanProduct = {
  code: string;
  name: string;
  description: string;
  annual_rate: string;
  minimum_amount: string;
  maximum_amount: string;
  minimum_term_months: number;
  maximum_term_months: number;
};
