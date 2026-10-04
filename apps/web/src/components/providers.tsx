"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 15_000, retry: 1 } },
      }),
  );
  useEffect(() => {
    document.documentElement.dataset.theme = localStorage.getItem("fsx_theme") || "ocean";
  }, []);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
