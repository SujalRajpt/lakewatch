export default function LatestReadingCard({
  reading,
  loading,
  error,
  onRefresh,
}) {
  const metrics = reading
    ? [
        {
          label: "Temperature",
          value: reading.temperature,
          unit: "°C",
          icon: "🌡️",
          color: "text-orange-300",
        },
        {
          label: "pH Level",
          value: reading.ph,
          unit: "pH",
          icon: "💧",
          color: "text-cyan-300",
        },
        {
          label: "Dissolved Oxygen",
          value: reading.dissolved_oxygen,
          unit: "mg/L",
          icon: "◉",
          color: "text-emerald-300",
        },
        {
          label: "Turbidity",
          value: reading.turbidity,
          unit: "",
          icon: "〰",
          color: "text-violet-300",
        },
        {
          label: "Conductivity",
          value: reading.conductivity,
          unit: "",
          icon: "ϟ",
          color: "text-amber-300",
        },
        {
          label: "Nitrate",
          value: reading.nitrate,
          unit: "",
          icon: "N",
          color: "text-pink-300",
        },
      ]
    : [];

  return (
    <section className="mb-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-teal-950 p-6 text-white sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-teal-400" />
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-300">
                Water Quality Monitor
              </p>
            </div>
            <h2 className="text-2xl font-bold sm:text-3xl">Latest Reading</h2>
            <p className="mt-2 text-sm text-slate-300">
              {reading
                ? `Lake ${reading.lake_id}`
                : "Latest sensor measurements at a glance"}
            </p>
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="rounded-lg border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium transition hover:bg-white/20 disabled:opacity-50"
          >
            {loading ? "Refreshing..." : "↻ Refresh"}
          </button>
        </div>
        {loading && !reading && (
          <p className="mt-8 text-sm text-slate-300">
            Fetching the latest sensor data...
          </p>
        )}
        {error && (
          <div className="mt-6 rounded-lg border border-red-300/20 bg-red-500/10 p-4 text-sm text-red-200">
            Could not load the latest reading: {error}
          </div>
        )}
        {!loading && !error && !reading && (
          <p className="mt-6 text-sm text-slate-300">
            No reading is available yet.
          </p>
        )}
        {reading && (
          <>
            <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
              {metrics.map((metric) => (
                <div
                  key={metric.label}
                  className="rounded-xl border border-white/10 bg-white/[0.06] p-4 transition hover:bg-white/[0.10]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xl">{metric.icon}</span>
                    <span className={`text-xs font-medium ${metric.color}`}>
                      {metric.unit}
                    </span>
                  </div>
                  <p className="mt-4 text-xs leading-5 text-slate-300">
                    {metric.label}
                  </p>
                  <p className="mt-1 break-all text-2xl font-bold tracking-tight sm:text-3xl">
                    {metric.value ?? "—"}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-6 flex flex-col gap-2 border-t border-white/10 pt-4 text-xs text-slate-300 sm:flex-row sm:items-center sm:justify-between">
              <p>
                <span className="text-slate-400">Sensor:</span>{" "}
                <span className="font-medium text-white">
                  {reading.sensor_id}
                </span>
                <span className="mx-2 text-slate-500">·</span>
                <span className="text-slate-400">Sequence:</span>{" "}
                <span className="font-medium text-white">
                  {reading.sequence_number}
                </span>
              </p>
              <p>
                Recorded{" "}
                {reading.event_timestamp
                  ? new Date(reading.event_timestamp).toLocaleString()
                  : "time unavailable"}
              </p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
