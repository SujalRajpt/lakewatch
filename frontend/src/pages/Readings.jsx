import ReadingsTable from "../components/ReadingsTable";

export default function Readings({
  data,
  loading,
  error,
  page,
  onPageChange,
  onRefresh,
}) {
  const pages = data.pages ?? 0;
  return (
    <section>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">Sensor Readings</h2>
          <p className="mt-1 text-sm text-slate-500">
            Water-quality measurements received from your sensors.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>
      {loading && <p className="mb-4 text-slate-500">Loading readings...</p>}
      {error && (
        <p className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          Could not load readings: {error}
        </p>
      )}
      {!loading && !error && (
        <>
          <div className="mb-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-900 p-5 text-white">
              <p className="text-sm text-slate-300">Total readings</p>
              <p className="mt-2 text-3xl font-bold">
                {(data.total ?? 0).toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <p className="text-sm text-slate-500">Current page</p>
              <p className="mt-2 text-3xl font-bold">
                {page} of {pages}
              </p>
            </div>
          </div>
          <ReadingsTable items={data.items ?? []} />
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">
              Page {page} of {pages} · Showing {(data.items ?? []).length}{" "}
              readings
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => onPageChange((p) => p - 1)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm disabled:opacity-40"
              >
                ← Previous
              </button>
              <button
                type="button"
                disabled={page >= pages || loading}
                onClick={() => onPageChange((p) => p + 1)}
                className="rounded-lg bg-teal-600 px-4 py-2 text-sm text-white disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
