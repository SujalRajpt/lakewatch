import ReadingsTable from "../components/ReadingsTable";

export default function LakeDetails({
  lake,
  details,
  detailsLoading,
  detailsError,
  readings,
  readingsLoading,
  readingsError,
  page,
  onPageChange,
  onRefresh,
  onBack,
}) {
  const pages = readings.pages ?? 0;
  return (
    <section className="mb-8 space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <button
          onClick={onBack}
          className="mb-5 text-sm font-medium text-teal-700 hover:text-teal-900"
        >
          ← Back to lakes
        </button>
        <h2 className="break-words text-2xl font-bold">
          {lake.name ?? lake.lake_id}
        </h2>
        <p className="mt-1 text-sm text-slate-500">Lake ID: {lake.lake_id}</p>
        {detailsLoading && (
          <p className="mt-5 text-slate-500">Loading lake details...</p>
        )}
        {detailsError && (
          <p className="mt-5 rounded-lg bg-red-50 p-4 text-red-700">
            Could not load lake details: {detailsError}
          </p>
        )}
        {details && (
          <pre className="mt-5 overflow-x-auto rounded-lg bg-slate-50 p-4 text-sm">
            {JSON.stringify(details, null, 2)}
          </pre>
        )}
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">Readings for {lake.lake_id}</h2>
            <p className="mt-1 text-sm text-slate-500">
              Measurements recorded for this lake.
            </p>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={readingsLoading}
            className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            {readingsLoading ? "Refreshing..." : "↻ Refresh"}
          </button>
        </div>
        {readingsLoading && (
          <p className="mb-4 text-slate-500">Loading lake readings...</p>
        )}
        {readingsError && (
          <p className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            Could not load lake readings: {readingsError}
          </p>
        )}
        {!readingsLoading && !readingsError && (
          <>
            <div className="mb-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-900 p-5 text-white">
                <p className="text-sm text-slate-300">Total lake readings</p>
                <p className="mt-2 text-3xl font-bold">
                  {(readings.total ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 p-5">
                <p className="text-sm text-slate-500">Current page</p>
                <p className="mt-2 text-3xl font-bold">
                  {page} of {pages}
                </p>
              </div>
            </div>
            <ReadingsTable items={readings.items ?? []} />
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-slate-500">
                Page {page} of {pages} · Showing {(readings.items ?? []).length}{" "}
                readings
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1 || readingsLoading}
                  onClick={() => onPageChange((p) => p - 1)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm disabled:opacity-40"
                >
                  ← Previous
                </button>
                <button
                  type="button"
                  disabled={page >= pages || readingsLoading}
                  onClick={() => onPageChange((p) => p + 1)}
                  className="rounded-lg bg-teal-600 px-4 py-2 text-sm text-white disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
