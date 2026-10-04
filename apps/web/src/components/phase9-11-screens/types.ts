import type { FormEvent, ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";

export type Phase911Query = Pick<
  UseQueryResult<unknown, Error>,
  "data" | "error" | "isLoading"
>;
export type Phase911Form = (
  handler: (data: FormData) => Promise<unknown>,
  success: string,
) => (event: FormEvent<HTMLFormElement>) => void;
export type Phase911Action = (
  request: () => Promise<unknown>,
  success: string,
  refresh?: boolean,
) => Promise<void>;
export type Phase911ScreenProps = {
  query: Phase911Query;
  busy: boolean;
  result: unknown;
  notice: ReactNode;
  form: Phase911Form;
  act: Phase911Action;
};
