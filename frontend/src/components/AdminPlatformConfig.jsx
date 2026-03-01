import React, { useEffect, useState } from "react";
import { fetchPlatformRegistry, fetchPlatformConfig, savePlatformConfig } from "../api/client";
import { FiCheck, FiX, FiPlus, FiSave, FiGlobe, FiLoader } from "react-icons/fi";

export function AdminPlatformConfig({ user }) {
  const [registry, setRegistry] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [universityId, setUniversityId] = useState("UNI001");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [customSlug, setCustomSlug] = useState("");
  const [customName, setCustomName] = useState("");
  const [customUrl, setCustomUrl] = useState("");
  const [customTemplate, setCustomTemplate] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const reg = await fetchPlatformRegistry();
        setRegistry(reg);
        try {
          const cfg = await fetchPlatformConfig(universityId);
          setSelectedPlatforms(cfg.platforms || []);
        } catch {
          setSelectedPlatforms([]);
        }
      } catch (err) {
        console.error("Failed to load platform config:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [universityId]);

  const isSelected = (slug) => selectedPlatforms.some((p) => p.slug === slug);

  const togglePlatform = (platform) => {
    if (isSelected(platform.slug)) {
      setSelectedPlatforms(selectedPlatforms.filter((p) => p.slug !== platform.slug));
    } else {
      setSelectedPlatforms([
        ...selectedPlatforms,
        { ...platform, active: true },
      ]);
    }
    setSaved(false);
  };

  const addCustomPlatform = () => {
    if (!customSlug || !customName || !customUrl || !customTemplate) return;
    const newPlatform = {
      slug: customSlug.toLowerCase().replace(/\s+/g, "-"),
      display_name: customName,
      base_url: customUrl,
      profile_url_template: customTemplate,
      active: true,
    };
    setSelectedPlatforms([...selectedPlatforms, newPlatform]);
    setCustomSlug("");
    setCustomName("");
    setCustomUrl("");
    setCustomTemplate("");
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await savePlatformConfig(universityId, selectedPlatforms);
      setSaved(true);
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 font-bold text-xs uppercase tracking-widest">Loading Platform Config...</p>
      </div>
    );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <p className="text-orange-600 font-black text-xs uppercase tracking-[0.2em] mb-2">Admin Console</p>
        <h1 className="text-3xl font-black text-slate-800 tracking-tight">Coding Platform Configuration</h1>
        <p className="text-slate-500 mt-1">Select the coding platforms your university uses. Students will link their profiles to these.</p>
      </div>

      {/* University selector */}
      <div className="flex items-center gap-3">
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">University</label>
        <input
          value={universityId}
          onChange={(e) => setUniversityId(e.target.value)}
          className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-orange-500 outline-none w-48"
        />
      </div>

      {/* Platform registry — checkbox grid */}
      <div>
        <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-4">Available Platforms</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {registry.map((platform) => {
            const active = isSelected(platform.slug);
            return (
              <button
                key={platform.slug}
                onClick={() => togglePlatform(platform)}
                className={`relative p-5 rounded-2xl border-2 transition-all text-left ${
                  active
                    ? "border-orange-500 bg-orange-50 shadow-md"
                    : "border-slate-200 bg-white hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base font-black text-slate-800">{platform.display_name}</span>
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      active ? "bg-orange-500 text-white" : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {active ? <FiCheck size={14} /> : <FiPlus size={14} />}
                  </span>
                </div>
                <p className="text-xs text-slate-400 truncate">{platform.base_url}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom platform form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
        <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">Add Custom Platform</h3>
        <p className="text-xs text-slate-400">If your university uses a platform not listed above, add it manually.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            value={customSlug}
            onChange={(e) => setCustomSlug(e.target.value)}
            placeholder="Slug (e.g. skillrack)"
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-orange-500"
          />
          <input
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            placeholder="Display Name (e.g. SkillRack)"
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-orange-500"
          />
          <input
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
            placeholder="Base URL (e.g. https://skillrack.com)"
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-orange-500"
          />
          <input
            value={customTemplate}
            onChange={(e) => setCustomTemplate(e.target.value)}
            placeholder="Profile URL Template (use {username})"
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <button
          onClick={addCustomPlatform}
          disabled={!customSlug || !customName || !customUrl || !customTemplate}
          className="px-5 py-2 bg-slate-800 text-white rounded-xl text-sm font-bold hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <FiPlus /> Add Platform
        </button>
      </div>

      {/* Selected platforms summary */}
      {selectedPlatforms.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider mb-4">
            Selected Platforms ({selectedPlatforms.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {selectedPlatforms.map((p) => (
              <span
                key={p.slug}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-orange-50 text-orange-700 rounded-full text-xs font-bold border border-orange-200"
              >
                <FiGlobe size={12} />
                {p.display_name}
                <button
                  onClick={() => setSelectedPlatforms(selectedPlatforms.filter((x) => x.slug !== p.slug))}
                  className="hover:text-red-500 transition-colors"
                >
                  <FiX size={12} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Save button */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-8 py-3 bg-orange-600 text-white rounded-xl font-black text-sm hover:bg-orange-700 disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-orange-200"
        >
          {saving ? <FiLoader className="animate-spin" /> : <FiSave />}
          {saving ? "Saving..." : "Save Configuration"}
        </button>
        {saved && (
          <span className="text-emerald-600 text-sm font-bold flex items-center gap-1">
            <FiCheck /> Saved successfully!
          </span>
        )}
      </div>
    </div>
  );
}
