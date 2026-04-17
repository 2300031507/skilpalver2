import React, { useEffect, useState } from "react";
import { fetchTeacherDashboard, fetchNotifications } from "../api/client";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  Cell, PieChart, Pie 
} from "recharts";
import { FiUsers, FiAlertCircle, FiSearch, FiExternalLink, FiMail, FiCheckCircle } from "react-icons/fi";

const PulseStatus = ({ level }) => {
  const statusMap = {
    high: { color: "text-red-600 bg-red-50", label: "Critical" },
    medium: { color: "text-amber-600 bg-amber-50", label: "Warning" },
    low: { color: "text-emerald-600 bg-emerald-50", label: "Stable" }
  };
  const status = statusMap[level?.toLowerCase()] || statusMap.medium;
  return (
    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${status.color}`}>
      {status.label}
    </span>
  );
};

export function TeacherDashboard({ user }) {
  const [data, setData] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const dashboard = await fetchTeacherDashboard(user.id);
        const notes = await fetchNotifications(user.id, "teacher");
        setData(dashboard);
        setNotifications(notes);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user.id]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-slate-400 font-bold text-xs uppercase tracking-widest">Aggregating Classroom Data...</p>
    </div>
  );

  if (!data) return (
    <div className="bg-white rounded-3xl p-12 text-center shadow-sm border border-slate-100">
      <FiAlertCircle className="text-5xl text-red-400 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-slate-800">Connection Interrupted</h3>
      <p className="text-slate-500 mt-2">Classroom metrics could not be synchronized.</p>
    </div>
  );

  const filteredStudents = data.at_risk_students?.filter(s => 
    s.student_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
    s.name?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const riskStats = data.class_risk_heatmap?.reduce((acc, curr) => {
    acc[curr.level.toLowerCase()] = curr.count;
    return acc;
  }, { high: 0, medium: 0, low: 0 });

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Total Roster</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-black text-slate-800">42</span>
            <FiUsers className="text-emerald-500" />
          </div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <p className="text-red-500 text-[10px] font-black uppercase tracking-widest mb-1">Critical Attention</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-black text-red-600">{riskStats.high}</span>
            <FiAlertCircle className="text-red-500" />
          </div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <p className="text-amber-500 text-[10px] font-black uppercase tracking-widest mb-1">Observation List</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-black text-amber-600">{riskStats.medium}</span>
            <FiAlertCircle className="text-amber-500" />
          </div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
          <p className="text-emerald-500 text-[10px] font-black uppercase tracking-widest mb-1">Healthy Progress</p>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-black text-emerald-600">{riskStats.low}</span>
            <FiCheckCircle className="text-emerald-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-8 border-b border-slate-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-black text-slate-800 tracking-tight">Student Pulse Index</h3>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider">Real-time status monitoring</p>
            </div>
            <div className="relative">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="text" 
                placeholder="Search Student ID or Name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 outline-none transition-all w-full md:w-64"
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Student</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Identity</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Coding Report</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filteredStudents.map((s) => (
                  <tr key={s.student_id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-8 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-black text-indigo-600">
                          {s.name?.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className="text-sm font-bold text-slate-700">{s.name}</span>
                      </div>
                    </td>
                    <td className="px-8 py-4">
                      <span className="text-xs font-mono font-bold text-slate-400">{s.student_id}</span>
                    </td>
                    <td className="px-8 py-4">
                      <PulseStatus level={s.risk_level} />
                    </td>
                    <td className="px-8 py-4">
                      <div className="flex items-center gap-2">
                        <FiCode className="text-indigo-400" />
                        <span className="text-xs font-bold text-slate-600">{s.coding_summary || "No data"}</span>
                      </div>
                    </td>
                    <td className="px-8 py-4 text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 text-slate-400 hover:text-indigo-600 transition-all">
                          <FiExternalLink />
                        </button>
                        <button className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 text-slate-400 hover:text-indigo-600 transition-all">
                          <FiMail />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
            <h3 className="text-lg font-black text-slate-800 tracking-tight mb-6">Class Distribution</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Stable', value: riskStats.low },
                      { name: 'Warning', value: riskStats.medium },
                      { name: 'Critical', value: riskStats.high },
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={8}
                    dataKey="value"
                  >
                    <Cell fill="#10b981" />
                    <Cell fill="#f59e0b" />
                    <Cell fill="#ef4444" />
                  </Pie>
                  <Tooltip 
                    contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 'bold'}}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex justify-between text-[10px] font-black uppercase tracking-widest text-slate-400">
              <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Stable</div>
              <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> Warning</div>
              <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Critical</div>
            </div>
          </div>

          <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
            <h3 className="text-lg font-black text-slate-800 tracking-tight mb-6">Urgent Escalations</h3>
            <div className="space-y-4">
              {notifications.filter(n => n.severity === 'high').map((n) => (
                <div key={n.id} className="p-4 rounded-2xl bg-red-50 border border-red-100 flex gap-3">
                  <FiAlertCircle className="text-red-500 shrink-0 mt-1" />
                  <div>
                    <p className="text-xs font-bold text-slate-800 leading-tight">{n.message}</p>
                    <p className="text-[10px] text-red-400 font-bold uppercase mt-2">Action Required</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
