export default function Sensors({ sensors, loading, error, onSensorClick }) {
  return (
    <section>
      <div className="mb-5">
        <h2 className="text-xl font-bold">Registered sensors</h2>
        <p className="mt-1 text-sm text-slate-500">
          Select a sensor to view its details.
        </p>
      </div>
      {loading && <p className="text-slate-500">Loading sensors...</p>}
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          Could not load sensors: {error}
        </p>
      )}
      {!loading && !error && sensors.length === 0 && (
        <p className="rounded-xl border border-slate-200 bg-white p-6 text-slate-500">
          No sensors found.
        </p>
      )}
      {!loading && !error && sensors.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {sensors.map((sensor) => (
            <button
              key={sensor.sensor_id}
              type="button"
              onClick={() => onSensorClick(sensor)}
              className="w-full min-w-0 rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-teal-400 hover:shadow-md"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Sensor
                </span>
                <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                  Registered
                </span>
              </div>
              <h3 className="mt-3 break-words text-lg font-bold">
                {sensor.sensor_id}
              </h3>
              <p className="mt-2 text-sm text-slate-500">
                Lake: {sensor.lake_id}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Model: {sensor.model ?? "Not available"}
              </p>
              <p className="mt-4 text-sm font-medium text-teal-700">
                View details →
              </p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
