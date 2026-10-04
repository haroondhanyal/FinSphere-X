export type Account = {
  id: number;
  account_number_masked: string;
  account_type: string;
  currency: string;
  balance: string;
  status: string;
};
export type Beneficiary = {
  id: number;
  name: string;
  account_number_masked: string;
  bank_name: string;
  currency: string;
  is_verified: boolean;
};
export type Transaction = {
  id: number;
  reference: string;
  type: string;
  amount: string;
  currency: string;
  status: string;
  created_at: string;
};
export type Card = {
  id: number;
  masked_number: string;
  last4: string;
  card_type: string;
  status: string;
  daily_limit: string;
};
export type Profile = {
  full_name: string;
  email: string;
  phone: string;
  country?: string;
  state?: string;
  city?: string;
  has_profile_image?: boolean;
  nationality: string;
  kyc_status: string;
};
