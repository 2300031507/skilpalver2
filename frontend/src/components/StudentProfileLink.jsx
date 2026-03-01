import React, { useEffect, useState } from "react";
import { fetchPlatformConfig, fetchStudentProfiles, linkStudentProfiles } from "../api/client";
import { FiLink, FiCheck, FiExternalLink, FiSave, FiLoader } from "react-icons/fi";

export function StudentProfileLink({ user, universityId = "UNI001" }) {
  const [platforms, setPlatforms] = useState([]);
  const [profiles, setProfiles] = useState({});   // slug → username
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        // Load university platform config
        const cfg = await fetchPlatformConfig(universityId);
        const activePlatforms = (cfg.platforms || []).filter((p) => p.active !== false);
        setPlatforms(activePlatforms);

        // Load existing student profiles
        try {
          const existing = await fetchStudentProfiles(universityId, user.id);
          const map = {};
          (existing.profiles || []).forEach((p) => {
            map[p.platform_slug] = p.username;
          });
          setProfiles(map);
        } catch {
          // No profiles saved yet — that's fine
        }
      } catch (err) {
        console.error("Failed to load platform config:", err);
        setError("Could not load platform configuration. Please contact your admin.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [universityId, user.id]);

  const handleChange = (slug, value) => {
    setProfiles({ ...profiles, [slug]: value });
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const profileList = Object.entries(profiles)
        .filter(([_, username]) => username && username.trim())
        .map(([slug, username]) => ({
          platform_slug: slug,
          username: username.trim(),
        }));

      await linkStudentProfiles(universityId, user.id, profileList);
      setSaved(true);
    } catch (err) {
      setError("Failed to save profiles. Please try again.");
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const getProfileUrl = (platform, username) => {
    if (!username) return null;
    return platform.profile_url_template.replace("{username}", username);
  };

  if (loading)
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 font-bold text-xs uppercase tracking-widest">Loading Platforms...</p>
      </div>
    );

  if (platforms.length === 0)
    return (
      <div className="bg-white rounded-2xl p-8 text-center border border-slate-200">
        <FiLink className="text-4xl text-slate-300 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-700">No Platforms Configured</h3>
        <p className="text-slate-400 text-sm mt-1">
          Your university admin hasn't configured any coding platforms yet.
        </p>
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-black text-slate-800 tracking-tight">Link Your Coding Profiles</h2>
        <p className="text-slate-500 text-sm mt-1">
          Enter your username for each platform. This lets us track your coding activity automatically.
        </p>
      </div>

      <div className="space-y-4">
        {platforms.map((platform) => {
          const username = profiles[platform.slug] || "";
          const url = getProfileUrl(platform, username);
          return (
            <div
              key={platform.slug}
              className="bg-white rounded-2xl border border-slate-200 p-5 flex flex-col sm:flex-row sm:items-center gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-black text-slate-800">{platform.display_name}</span>
                  {username && (
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                      <FiCheck size={12} />
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400">{platform.base_url}</p>
              </div>
              <div className="flex items-center gap-2 flex-1">
                <input
                  value={username}
                  onChange={(e) => handleChange(platform.slug, e.target.value)}
                  placeholder={`Your ${platform.display_name} username`}
                  className="flex-1 px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {url && (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
                    title="Preview profile"
                  >
                    <FiExternalLink size={16} />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-red-600 text-sm font-bold">
          {error}
        </div>
      )}

      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-black text-sm hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-indigo-200"
        >
          {saving ? <FiLoader className="animate-spin" /> : <FiSave />}
          {saving ? "Saving..." : "Save Profiles"}
        </button>
        {saved && (
          <span className="text-emerald-600 text-sm font-bold flex items-center gap-1">
            <FiCheck /> Profiles linked!
          </span>
        )}
      </div>
    </div>
  );
}
