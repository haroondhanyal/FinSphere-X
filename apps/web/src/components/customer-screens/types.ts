import type {
  Account,
  Beneficiary,
  Card,
  Profile,
  Transaction,
} from "../screen-types";

export type CustomerScreenProps = {
  pathname: string;
  accountData: Account[];
  beneficiaryData: Beneficiary[];
  transactionData: Transaction[];
  cardData: Card[];
  walletData?: {
    currency: string;
    balance: string;
    level: string;
    status: string;
  };
  profileData?: Profile;
  kycQueue: { id: number; full_name: string; email?: string; kyc_status: string; document_count?: number }[];
  balance: string | number;
  error: string;
  success: string;
  accountQuery: { error: Error | null };
  walletQuery: { error: Error | null };
  cardsQuery: { error: Error | null };
  transactionsQuery: { error: Error | null };
  kycQueueQuery: { error: Error | null; isLoading: boolean };
  run: (action: () => Promise<unknown>, message: string) => Promise<void>;
};
