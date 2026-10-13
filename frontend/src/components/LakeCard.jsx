function LakeCard({ lake, onClick }) {
  return (
    <button
      type="button"
      onClick={() => {
        console.log("Lake card clicked:", lake.lake_id);
        onClick();
      }}
      className="w-full min-w-0 cursor-pointer rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-teal-400 hover:shadow-md"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Lake ID
        </span>

        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
          Registered
        </span>
      </div>

      <h3 className="mt-3 break-words text-lg font-bold text-slate-900">
        {lake.name ?? lake.lake_id}
      </h3>

      <p className="mt-2 break-all text-sm text-slate-500">{lake.lake_id}</p>

      <p className="mt-4 text-sm font-medium text-teal-700">View details →</p>
    </button>
  );
}

export default LakeCard;
