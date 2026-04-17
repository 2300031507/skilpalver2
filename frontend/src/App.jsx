import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { StudentDashboard } from "./components/StudentDashboard";
import { TeacherDashboard } from "./components/TeacherDashboard";
import { AdminPlatformConfig } from "./components/AdminPlatformConfig";
import { StudentProfileLink } from "./components/StudentProfileLink";
import { Login } from "./components/Login";
import { FiMenu, FiX, FiLogOut, FiUser, FiSettings, FiLink, FiCode } from "react-icons/fi";
import { SiGithub } from "react-icons/si";
import { clearToken } from "./api/client";

function App() {
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
      } catch (e) {
        localStorage.removeItem("user");
      }
    }
  }, []);

  const handleLogin = (userData) => {
    console.log("Setting user in App:", userData);
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
    const role = userData.role;
    if (role === "student") navigate("/student");
    else if (role === "admin") navigate("/admin");
    else navigate("/teacher");
  };

  const handleLogout = () => {
    setUser(null);
    clearToken();
    localStorage.removeItem("user");
    navigate("/login");
  };

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const roleColors = {
    student: "from-indigo-600 to-blue-500",
    teacher: "from-emerald-600 to-teal-500",
    admin: "from-orange-600 to-red-500"
  };

  const currentGradient = roleColors[user.role];

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-screen bg-white shadow-2xl transition-all duration-300 ${
          sidebarOpen ? "w-72" : "w-20"
        } z-40 border-r border-slate-200`}
      >
        {/* Logo */}
        <div className="h-20 flex items-center justify-between px-6 border-b border-slate-100 bg-white sticky top-0">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-600 rounded-lg shadow-md">
                <FiUser className="text-white text-xl" />
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-slate-800 tracking-tight">ScholarPulse</h1>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Platform</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-500"
          >
            {sidebarOpen ? <FiX size={20} /> : <FiMenu size={20} />}
          </button>
        </div>

        {/* Navigation */}
        <div className="p-4 space-y-2">
          {user.role === "student" && (
            <>
              <button
                onClick={() => navigate("/student")}
                className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl font-semibold transition-all ${
                  location.pathname === "/student"
                    ? "bg-indigo-50 text-indigo-600 shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                }`}
              >
                <FiUser size={20} />
                {sidebarOpen && <span>My Dashboard</span>}
              </button>
              <button
                onClick={() => navigate("/student/profiles")}
                className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl font-semibold transition-all ${
                  location.pathname === "/student/profiles"
                    ? "bg-indigo-50 text-indigo-600 shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                }`}
              >
                <FiLink size={20} />
                {sidebarOpen && <span>Link Profiles</span>}
              </button>
            </>
          )}

          {user.role === "teacher" && (
            <button
              onClick={() => navigate("/teacher")}
              className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl font-semibold transition-all ${
                location.pathname === "/teacher"
                  ? "bg-emerald-50 text-emerald-600 shadow-sm"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
              }`}
            >
              <FiUser size={20} />
              {sidebarOpen && <span>Student Overview</span>}
            </button>
          )}

          {user.role === "admin" && (
            <>
              <button
                onClick={() => navigate("/admin")}
                className={`w-full flex items-center gap-3 py-3 px-4 rounded-xl font-semibold transition-all ${
                  location.pathname === "/admin"
                    ? "bg-orange-50 text-orange-600 shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                }`}
              >
                <FiSettings size={20} />
                {sidebarOpen && <span>Platform Config</span>}
              </button>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-white">
          <div className="space-y-1">
            {sidebarOpen && (
              <div className="px-4 py-3 mb-2 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Signed in as</p>
                <p className="text-sm font-bold text-slate-700 truncate">{user.name}</p>
                <p className="text-[10px] text-indigo-600 font-bold">{user.id}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 py-3 px-4 rounded-xl text-red-500 hover:bg-red-50 font-bold transition-all"
            >
              <FiLogOut size={20} />
              {sidebarOpen && <span>Sign Out</span>}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? "ml-72" : "ml-20"}`}>
        {/* Top Bar */}
        <div className="bg-white/80 backdrop-blur-md sticky top-0 z-30 border-b border-slate-200 h-20 flex items-center px-10">
          <div className="flex-1">
            <h2 className="text-2xl font-black text-slate-800">
              {user.role === "student" ? "My Academic Pulse" : user.role === "teacher" ? "Class Performance Hub" : "System Administration"}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className={`h-10 px-4 rounded-full flex items-center justify-center font-bold text-xs uppercase tracking-widest text-white bg-gradient-to-r ${currentGradient} shadow-lg`}>
              {user.role}
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="p-10">
          <Routes>
            <Route path="/student" element={<StudentDashboard user={user} />} />
            <Route path="/student/profiles" element={<StudentProfileLink user={user} />} />
            <Route path="/teacher" element={<TeacherDashboard user={user} />} />
            <Route path="/admin" element={<AdminPlatformConfig user={user} />} />
            <Route path="*" element={<Navigate to={user.role === "student" ? "/student" : user.role === "admin" ? "/admin" : "/teacher"} replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;

