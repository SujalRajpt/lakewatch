const navItems = ["Dashboard", "Lakes", "Sensors", "Readings"];

function Navbar({ activeSection, onNavigate }) {
  return (
    <aside className="w-full border-b border-slate-800 bg-slate-950 p-5 text-white md:min-h-screen md:w-60 md:border-b-0 md:border-r">
      <h1 className="mb-8 text-2xl font-bold text-teal-400">LakeWatch</h1>

      <nav className="flex gap-2 overflow-x-auto md:flex-col">
        {navItems.map((item) => (
          <button
            key={item}
            onClick={() => onNavigate(item)}
            className={`rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
              activeSection === item
                ? "bg-teal-500 text-slate-950"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
}

export default Navbar;
