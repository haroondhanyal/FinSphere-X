"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { defaultCountries, parseCountry, PhoneInput } from "react-international-phone";

const countries = defaultCountries.map(parseCountry);

function flagEmoji(countryCode: string) {
  return String.fromCodePoint(
    ...countryCode
      .toUpperCase()
      .split("")
      .map((letter) => letter.charCodeAt(0) + 127397),
  );
}

export function CountrySelect({
  value,
  onChange,
  search,
  onSearch,
}: {
  value: string;
  onChange: (countryCode: string, countryName: string, dialCode: string) => void;
  search?: string;
  onSearch?: (value: string) => void;
}) {
  const visibleCountries = countries.filter((country) =>
    country.name.toLowerCase().includes((search || "").toLowerCase()),
  );
  return (
    <>
    {onSearch && <input aria-label="Search countries by name" placeholder="Search country by name" value={search} onChange={(event) => onSearch(event.target.value)} />}
    <select
      name="country"
      value={value}
      autoComplete="country-name"
      onChange={(event) => {
        const country = countries.find((item) => item.iso2 === event.target.value);
        if (country) onChange(country.iso2, country.name, country.dialCode);
      }}
      required
    >
      <option value="">Choose your country</option>
      {visibleCountries.map((country) => (
        <option key={country.iso2} value={country.iso2}>
          {flagEmoji(country.iso2)} {country.name}
        </option>
      ))}
    </select>
    </>
  );
}

export function InternationalPhoneField({
  countryCode,
  value,
  onChange,
}: {
  countryCode: string;
  value: string;
  onChange: (phone: string) => void;
}) {
  return (
    <div className="phone-input-wrap">
      <PhoneInput
        key={countryCode}
        defaultCountry={countryCode || "pk"}
        value={value}
        onChange={onChange}
        name="phone"
        placeholder="Phone number"
        inputProps={{ autoComplete: "tel", "aria-label": "Phone number with country code" }}
      />
      <small className="form-hint">Choose a flag to change the international calling code.</small>
    </div>
  );
}

export function PasswordField({
  name,
  label,
  autoComplete,
  minLength = 12,
}: {
  name: string;
  label: string;
  autoComplete: string;
  minLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="password-field">
      {label}
      <span className="password-control">
        <input
          name={name}
          type={visible ? "text" : "password"}
          required
          minLength={minLength}
          autoComplete={autoComplete}
          placeholder={name === "password" ? "At least 12 characters" : undefined}
        />
        <button
          className="password-toggle"
          type="button"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          aria-pressed={visible}
        >
          {visible ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </span>
    </label>
  );
}
