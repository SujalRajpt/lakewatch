export default function ReadingsTable({
  items = [],
  emptyMessage = "No readings found.",
}) {
  const columns = [
    ["ID", "id"],
    ["Sensor", "sensor_id"],
    ["Lake", "lake_id"],
    ["Sequence", "sequence_number"],
    ["Temperature", "temperature"],
    ["pH", "ph"],
    ["Dissolved O₂", "dissolved_oxygen"],
    ["Turbidity", "turbidity"],
    ["Conductivity", "conductivity"],
    ["Nitrate", "nitrate"],
  ];
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[1100px] text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            {columns.map(([label]) => (
              <th key={label} className="p-4">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((reading) => (
            <tr key={reading.id} className="hover:bg-slate-50">
              {columns.map(([, field]) => (
                <td key={field} className="p-4">
                  {reading[field] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                className="p-6 text-center text-slate-500"
              >
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
