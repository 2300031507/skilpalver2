import React, { useEffect, useState } from "react";
import { fetchStudentDashboard, fetchNotifications } from "../api/client";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar 
} from "recharts";
import { FiActivity, FiCode, FiBookOpen, FiClock, FiAlertCircle, FiCheckCircle, FiTrendingUp, FiZap, FiCalendar } from "react-icons/fi";

const PulseBadge = ({ level }) => {
  const configs = {
    high: { color: "text-red-600 bg-red-50 border-red-200", label: "Critical Risk" },
    medium: { color: "text-amber-600 bg-amber-50 border-amber-200", label: "At Risk" },
    low: { color: "text-emerald-600 bg-emerald-50 border-emerald-200", label: "Healthy Pulse" }
  };
  const config = configs[level?.toLowerCase()] || configs.medium;
  return (
    <div className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest border shadow-sm inline-flex items-center gap-2 ${config.color}`}>
      <span className="relative flex h-2 w-2">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${level === 'high' ? 'bg-red-400' : 'bg-emerald-400'}`}></span>
        <span className={`relative inline-flex rounded-full h-2 w-2 ${level === 'high' ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
      </span>
      {config.label}
    </div>
  );
};

const MetricCard = ({ title, value, unit, trend, icon: Icon, colorClass }) => (
  <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between mb-4">
      <div className={`p-2 rounded-lg ${colorClass} bg-opacity-10 text-xl`}>
        <Icon className={colorClass.replace('bg-', 'text-')} />
      </div>
      {trend && (
        <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${trend > 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
          {trend > 0 ? '+' : ''}{trend}%
        </span>
      )}
    </div>
    <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
    <div className="flex items-baseline gap-1">
      <span className="text-2xl font-black text-slate-800">{value}</span>
      {unit && <span className="text-xs font-bold text-slate-400">{unit}</span>}
    </div>
  </div>
);

export function StudentDashboard({ user }) {
  const [data, setData] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const dashboard = await fetchStudentDashboard(user.id);
        const notes = await fetchNotifications(user.id, "student");
        setData(dashboard);
        setNotifications(notes);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    }
    load();

    // Add listener for profile updates to refresh dashboard
    const handleUpdate = () => {
      console.log("Refreshing dashboard due to profile update...");
      load();
    };
    window.addEventListener("profile-updated", handleUpdate);
    return () => window.removeEventListener("profile-updated", handleUpdate);
  }, [user.id]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-slate-400 font-bold text-xs uppercase tracking-widest">Synchronizing Pulse...</p>
    </div>
  );

  if (!data) return (
    <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100">
      <FiAlertCircle className="text-5xl text-red-400 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-slate-800">Connection Interrupted</h3>
      <p className="text-slate-500 mt-2">We couldn't retrieve your academic pulse data. Please try again later.</p>
    </div>
  );

  // Calculate total problems solved from all platforms
  const totalProblemsSolved = data.coding_platforms?.reduce((acc, p) => acc + p.problems_solved, 0) || 0;
  const codingRadarData = data.coding_platforms?.map(p => ({
    subject: p.display_name,
    A: p.problems_solved,
    fullMark: Math.max(150, p.problems_solved + 20)
  })) || [
    { subject: 'LeetCode', A: 0, fullMark: 150 },
    { subject: 'CodeChef', A: 0, fullMark: 150 },
    { subject: 'CodeForces', A: 0, fullMark: 150 },
  ];

  const attendanceValue = data.attendance_trend?.[0]?.attendance_percent * 100 || 0;
  const lmsValue = data.lms_engagement?.find(e => e.name === "time_spent_minutes")?.value || 0;

  return (
    <div className="space-y-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className="text-indigo-600 font-black text-xs uppercase tracking-[0.2em] mb-2">Student Identity: {user.id}</p>
          <h1 className="text-4xl font-black text-slate-800 tracking-tight">Welcome back, {user.name.split(' ')[0]}!</h1>
        </div>
        <PulseBadge level={data.risk_level} />
      </div>

      {/* Daily Progress Report Card */}
      {data.daily_report && (
        <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-3xl p-8 text-white shadow-xl shadow-indigo-200">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-4">
                <FiZap className="text-yellow-400 fill-yellow-400" />
                <span className="text-xs font-black uppercase tracking-widest opacity-80">Daily Progress Report</span>
              </div>
              <h2 className="text-2xl font-black mb-2">{data.daily_report.summary}</h2>
              <div className="flex gap-6 mt-6">
                <div className="text-center">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">Solved</p>
                  <p className="text-xl font-black">{data.daily_report.problems_solved}</p>
                </div>
                <div className="w-px h-10 bg-white/20"></div>
                <div className="text-center">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">Active</p>
                  <p className="text-xl font-black">{data.daily_report.active_minutes}m</p>
                </div>
                <div className="w-px h-10 bg-white/20"></div>
                <div className="text-center">
                  <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">Streak</p>
                  <p className="text-xl font-black">{data.daily_report.streak_days} days</p>
                </div>
              </div>
            </div>
            <div className="hidden lg:block">
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20">
                <FiCalendar className="text-4xl" />
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Attendance" 
          value={attendanceValue.toFixed(0)} 
          unit="%" 
          trend={2.4} 
          icon={FiCheckCircle} 
          colorClass="bg-emerald-500" 
        />
        <MetricCard 
          title="LMS Engagement" 
          value={(lmsValue / 60).toFixed(1)} 
          unit="hrs" 
          trend={-1.2} 
          icon={FiBookOpen} 
          colorClass="bg-indigo-500" 
        />
        <MetricCard 
          title="Daily Practice" 
          value="120" 
          unit="min" 
          trend={15} 
          icon={FiClock} 
          colorClass="bg-amber-500" 
        />
        <MetricCard 
          title="Problems Solved" 
          value={totalProblemsSolved} 
          unit="total" 
          trend={8} 
          icon={FiCode} 
          colorClass="bg-purple-500" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-lg font-black text-slate-800 tracking-tight">Engagement Pulse</h3>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">Weekly activity overview</p>
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.lms_engagement}>
                <defs>
                  <linearGradient id="colorEngage" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10, fontWeight: 'bold'}} dy={10} />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '12px', fontWeight: 'bold'}}
                />
                <Area type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={4} fillOpacity={1} fill="url(#colorEngage)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
          <h3 className="text-lg font-black text-slate-800 tracking-tight mb-2">Coding Proficiency</h3>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-6">Cross-platform skills</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={codingRadarData}>
                <PolarGrid stroke="#f1f5f9" />
                <PolarAngleAxis dataKey="subject" tick={{fill: '#64748b', fontSize: 10, fontWeight: 'bold'}} />
                <Radar name="Skills" dataKey="A" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
          <div className="flex items-center gap-2 mb-6">
            <FiTrendingUp className="text-indigo-600 text-xl" />
            <h3 className="text-lg font-black text-slate-800 tracking-tight">Personalized Growth Path</h3>
          </div>
          <div className="space-y-4">
            {data.recovery_suggestions?.map((s, i) => (
              <div key={i} className="flex items-start gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 group hover:border-indigo-200 transition-colors">
                <div className="p-2 bg-white rounded-lg shadow-sm group-hover:text-indigo-600">
                  <FiCheckCircle />
                </div>
                <div>
                  <p className="text-sm font-black text-slate-800">{s.title}</p>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{s.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
          <div className="flex items-center gap-2 mb-6">
            <FiActivity className="text-amber-500 text-xl" />
            <h3 className="text-lg font-black text-slate-800 tracking-tight">Recent Alerts</h3>
          </div>
          <div className="space-y-4">
            {notifications.length > 0 ? notifications.map((n) => (
              <div key={n.id} className={`flex items-start gap-4 p-4 rounded-2xl border ${n.severity === 'high' ? 'bg-red-50 border-red-100' : 'bg-blue-50 border-blue-100'}`}>
                <FiAlertCircle className={n.severity === 'high' ? 'text-red-500 mt-1' : 'text-blue-500 mt-1'} />
                <div>
                  <p className="text-sm font-bold text-slate-800">{n.message}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase mt-1">{new Date(n.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            )) : (
              <p className="text-slate-400 text-sm font-bold text-center py-10 italic">No active alerts. Keep up the good work!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
