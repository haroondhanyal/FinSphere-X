import type { FormEvent } from "react";
import type { UseQueryResult } from "@tanstack/react-query";

export type Phase58Query = Pick<
  UseQueryResult<unknown, Error>,
  "data" | "error" | "isLoading"
>;
export type Phase58Submit = (
  handler: (data: FormData) => Promise<unknown>,
  message: string,
) => (event: FormEvent<HTMLFormElement>) => void;
export type Phase58Action = (
  action: () => Promise<unknown>,
  message: string,
) => Promise<boolean>;
export type Phase58ScreenProps = {
  section: string;
  query: Phase58Query;
  working: boolean;
  error: string;
  notice: string;
  perform: Phase58Action;
  submit: Phase58Submit;
};
