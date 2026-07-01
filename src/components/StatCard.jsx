export default function StatCard({ icon: Icon, label, value, sub, color = '#101010' }) {
  return (
    <div className="card flex items-center gap-4 animate-fade-in">
      <div
        className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
        style={{ background: `${color}12` }}
      >
        <Icon size={24} color={color} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] text-[#6B7280] font-medium">{label}</p>
        <p className="text-[20px] font-bold text-[#101010] leading-tight">{value}</p>
        {sub && <p className="text-[12px] text-[#9CA3AF] mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
