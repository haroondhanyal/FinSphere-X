const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token =
    typeof window === "undefined"
      ? null
      : window.localStorage.getItem("fsx_token");
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  let response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (
    response.status === 401 &&
    token &&
    !["/auth/login", "/auth/refresh", "/auth/logout"].includes(path)
  ) {
    const refreshToken = window.localStorage.getItem("fsx_refresh");
    if (refreshToken) {
      const refreshed = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshed.ok) {
        const pair = (await refreshed.json()) as {
          access_token: string;
          refresh_token: string;
        };
        window.localStorage.setItem("fsx_token", pair.access_token);
        window.localStorage.setItem("fsx_refresh", pair.refresh_token);
        const retryHeaders = new Headers(init.headers);
        retryHeaders.set("Authorization", `Bearer ${pair.access_token}`);
        if (init.body && !(init.body instanceof FormData))
          retryHeaders.set("Content-Type", "application/json");
        response = await fetch(`${API_URL}${path}`, {
          ...init,
          headers: retryHeaders,
          cache: "no-store",
        });
      } else {
        window.localStorage.removeItem("fsx_token");
        window.localStorage.removeItem("fsx_refresh");
      }
    }
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function decimalScale(amount: string | number) {
  const scale = BigInt(10_000);
  const raw = String(amount);
  const negative = raw.startsWith("-");
  const normalized = raw.replace(/^[+-]/, "");
  const [whole = "0", fraction = ""] = normalized.split(".");
  const scaled =
    BigInt(whole || "0") * scale + BigInt((fraction + "0000").slice(0, 4));
  return { negative, scaled };
}

export function sumMoneyAmounts(amounts: string[]) {
  const scale = BigInt(10_000);
  const scaled = amounts.reduce((total, amount) => {
    const parsed = decimalScale(amount);
    return total + (parsed.negative ? -parsed.scaled : parsed.scaled);
  }, BigInt(0));
  const negative = scaled < BigInt(0);
  const absolute = negative ? -scaled : scaled;
  const whole = absolute / scale;
  const fraction = (absolute % scale).toString().padStart(4, "0");
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}

export function money(amount: string | number, currency = "PKR") {
  const { negative, scaled } = decimalScale(amount);
  const zero = BigInt(0);
  const hundred = BigInt(100);
  const absolute = scaled < zero ? -scaled : scaled;
  const cents = (absolute + BigInt(50)) / hundred;
  const whole = cents / hundred;
  const fraction = (cents % hundred).toString().padStart(2, "0");
  const parts = new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).formatToParts(negative ? -whole : whole);
  if (negative && whole === zero)
    parts.unshift({ type: "minusSign", value: "-" });
  const lastInteger = parts.reduce(
    (last, part, index) => (part.type === "integer" ? index : last),
    -1,
  );
  parts.splice(
    lastInteger + 1,
    0,
    { type: "decimal", value: "." },
    { type: "fraction", value: fraction },
  );
  return parts.map((part) => part.value).join("");
}

export async function downloadStatement(accountId: number) {
  const token = window.localStorage.getItem("fsx_token");
  const response = await fetch(
    `${API_URL}/accounts/${accountId}/statement.csv`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!response.ok) throw new Error("Could not download statement");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `finsphere-statement-${accountId}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
