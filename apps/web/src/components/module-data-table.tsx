import type { ReactNode } from "react";

export type ModuleDataColumn<Row> = {
  key: string;
  label: string;
  render: (row: Row) => ReactNode;
};

export function ModuleDataTable<Row extends { id: number | string }>({
  rows,
  columns,
  empty,
}: {
  rows: Row[];
  columns: ModuleDataColumn<Row>[];
  empty: string;
}) {
  return (
    <div className="panel table-panel">
      {rows.length ? (
        <div className="table-wrap">
          <table>
            <thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
            <tbody>{rows.map((row) => <tr key={row.id}>{columns.map((column) => <td key={column.key}>{column.render(row)}</td>)}</tr>)}</tbody>
          </table>
        </div>
      ) : <p className="muted module-table-empty">{empty}</p>}
    </div>
  );
}

export function ModuleRecordToolbar({
  search,
  onSearch,
  placeholder,
  filter,
  onFilter,
  options,
}: {
  search: string;
  onSearch: (value: string) => void;
  placeholder: string;
  filter: string;
  onFilter: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="module-record-toolbar">
      <input aria-label={placeholder} placeholder={placeholder} value={search} onChange={(event) => onSearch(event.target.value)} />
      <select aria-label="Filter records" value={filter} onChange={(event) => onFilter(event.target.value)}>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </div>
  );
}
