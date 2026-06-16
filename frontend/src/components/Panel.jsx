function Panel({ title, icon, actions, children, className = '' }) {
  return (
    <section className={`rounded-lg border border-slate-800 bg-[#161b22] ${className}`}>
      <div className="flex min-h-11 items-center justify-between border-b border-slate-800 px-4">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          {icon}
          {title}
        </h2>
        {actions}
      </div>
      {children}
    </section>
  );
}

export default Panel;
