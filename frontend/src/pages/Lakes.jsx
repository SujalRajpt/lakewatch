import LakeCard from "../components/LakeCard";

export default function Lakes({ lakes, loading, error, onLakeClick }) {
  if (loading) return <p className="text-slate-500">Loading lakes...</p>;
  if (error)
    return (
      <p className="rounded-lg bg-red-50 p-4 text-red-700">
        Could not load lakes: {error}
      </p>
    );
  return (
    <section>
      <h2 className="mb-4 text-xl font-bold">All lakes ({lakes.length})</h2>
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
  );
}
