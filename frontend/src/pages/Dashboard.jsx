import LatestReadingCard from "../components/LatestReadingCard";
import LakeCard from "../components/LakeCard";

export default function Dashboard({
  lakes,
  loading,
  error,
  latestReading,
  latestLoading,
  latestError,
  onRefreshLatest,
  onLakeClick,
}) {
  return (
    <>
      <LatestReadingCard
        reading={latestReading}
        loading={latestLoading}
        error={latestError}
        onRefresh={onRefreshLatest}
      />
      {loading ? (
        <p className="text-slate-500">Loading lakes...</p>
      ) : error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          Could not load lakes: {error}
        </p>
      ) : (
        <>
          <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-xl bg-slate-900 p-6 text-white">
              <p className="text-sm text-slate-300">Registered lakes</p>
              <p className="mt-3 text-4xl font-bold">{lakes.length}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <p className="text-sm text-slate-500">Monitoring platform</p>
              <p className="mt-3 text-xl font-bold">LakeWatch</p>
            </div>
          </section>
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Your lakes</h2>
              <span className="text-sm text-slate-500">
                {lakes.length} total
              </span>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {lakes.map((lake) => (
                <LakeCard
                  key={lake.lake_id}
                  lake={lake}
                  onClick={() => onLakeClick(lake)}
                />
              ))}
            </div>
          </section>
        </>
      )}
    </>
  );
}
