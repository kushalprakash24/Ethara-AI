"use client";
import { useState, useEffect } from "react";

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [totalMatches, setTotalMatches] = useState(0);
  const [loading, setLoading] = useState(true);

  // View States
  const [currentView, setCurrentView] = useState("center"); // center, projects, maps
  const [selectedFloor, setSelectedFloor] = useState(1);
  const [floorSeats, setFloorSeats] = useState([]);
  const [projectsList, setProjectsList] = useState([]);

  // Form & AI States
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", role: "employee" });
  const [actionMessage, setActionMessage] = useState(null);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiResponse, setAiResponse] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    refreshAllData();
    fetchProjectsSummary();
  }, []);

  useEffect(() => {
    if (currentView === "maps") {
      fetchFloorPlan(selectedFloor);
    }
  }, [currentView, selectedFloor]);

  const refreshAllData = () => {
    fetchMetrics();
    fetchDirectory(searchQuery);
    if (currentView === "maps") fetchFloorPlan(selectedFloor);
  };

  const fetchMetrics = async () => {
    try {
  const res = await fetch("https://ethara-ai-1-ijpl.onrender.com/dashboard/metrics");
      const data = await res.json();
      setMetrics(data.summary);
    } catch (err) { console.error(err); }
  };

  const fetchProjectsSummary = async () => {
    try {
  const res = await fetch("https://ethara-ai-1-ijpl.onrender.com/projects/summary");
      const data = await res.json();
      setProjectsList(data);
    } catch (err) { console.error(err); }
  };

  const fetchFloorPlan = async (floorNum: number) => {
    try {
      const res = await fetch(
        `https://ethara-ai-1-ijpl.onrender.com/seats/floor-plan/${floorNum}`
      );

      const data = await res.json();
      setFloorSeats(data.slice(0, 60));
    } catch (err) {
      console.error(err);
    }
  };

  const fetchDirectory = async (query: string) => {
    setLoading(true);
    try {
      const res = await fetch(`https://ethara-ai-1-ijpl.onrender.com/dashboard/search?q=${query}&limit=8`);
      const data = await res.json();
      setSearchResults(data.results);
      setTotalMatches(data.total_matches);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

const handleAiSubmit = async (
  e: React.FormEvent<HTMLFormElement>
) => {
  e.preventDefault();

  if (!aiPrompt) return;

  setAiLoading(true);
  setAiResponse(null);

  try {
    const res = await fetch(
      `https://ethara-ai-1-ijpl.onrender.com/ai/ask?q=${encodeURIComponent(aiPrompt)}`
    );

    const data = await res.json();
    setAiResponse(data);
  } catch (err) {
    console.error(err);
  } finally {
    setAiLoading(false);
  }
};

  const handleOnboardSubmit = async (e) => {
    e.preventDefault();
    setActionMessage({ type: "info", text: "Processing allocation parameters..." });
    try {
      const url = `https://ethara-ai-1-ijpl.onrender.com/seats/auto-allocate-joiner?name=${encodeURIComponent(formData.name)}&email=${encodeURIComponent(formData.email)}&role=${formData.role}&project_id=00000000-0000-0000-0000-000000000000`;
      const res = await fetch(url, { method: "POST" });
      const data = await res.json();

      if (res.ok) {
        setActionMessage({ type: "success", text: `Success! Allocated to desk ${data.allocated_desk}` });
        setFormData({ name: "", email: "", role: "employee" });
        refreshAllData();
        fetchProjectsSummary();
        setTimeout(() => setShowForm(false), 2000);
      } else { setActionMessage({ type: "error", text: data.detail }); }
    } catch (err) { setActionMessage({ type: "error", text: "Bridge communication failure." }); }
  };

  const handleReleaseSeat = async (seatNumber) => {
    if (!confirm(`Are you sure you want to release desk ${seatNumber}?`)) return;
    try {
      const res = await fetch(`https://ethara-ai-1-ijpl.onrender.com/seats/release-by-code/${seatNumber}`, { method: "DELETE" });
      if (res.ok) {
        refreshAllData();
        fetchProjectsSummary();
      } else { alert("Error releasing seat"); }
    } catch (err) { console.error(err); }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 font-sans">
      
      {/* SIDEBAR NAVIGATION */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col p-6 shadow-xl">
        <div className="text-xl font-black tracking-wider text-indigo-400 mb-8">Base // SEATSYNC</div>
        <nav className="flex-1 space-y-2">
          <button onClick={() => setCurrentView("center")} className={`w-full text-left flex items-center px-4 py-3 rounded-lg font-medium transition ${currentView === "center" ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>🏢 Command Center</button>
          <button onClick={() => setCurrentView("maps")} className={`w-full text-left flex items-center px-4 py-3 rounded-lg font-medium transition ${currentView === "maps" ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>🪑 Floor Plan Maps</button>
          <button onClick={() => setCurrentView("projects")} className={`w-full text-left flex items-center px-4 py-3 rounded-lg font-medium transition ${currentView === "projects" ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}>📁 Projects Ledger</button>
          <div className="pt-4"><button onClick={() => setShowForm(true)} className="w-full text-left flex items-center px-4 py-3 text-emerald-400 bg-emerald-950/40 hover:bg-emerald-900/30 rounded-lg transition border border-emerald-900/50 font-bold">➕ Allocate New Joiner</button></div>
        </nav>
      </aside>

      {/* RENDER BODY VIEW WINDOW */}
      <main className="flex-1 p-8 overflow-y-auto">
        
        {/* VIEW 1: COMMAND CENTER */}
        {currentView === "center" && (
          <>
            <header className="mb-8"><h1 className="text-3xl font-bold text-slate-900">Enterprise Overview</h1></header>
            
            {/* METRICS */}
            <section className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100"><p className="text-xs font-semibold text-slate-400 uppercase">Total Desks</p><p className="text-3xl font-bold mt-2">{metrics?.total_structural_capacity || "..."}</p></div>
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100"><p className="text-xs font-semibold text-slate-400 uppercase">Occupied</p><p className="text-3xl font-bold text-indigo-600 mt-2">{metrics?.allocated_seats || "..."}</p></div>
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100"><p className="text-xs font-semibold text-slate-400 uppercase">Vacant</p><p className="text-3xl font-bold text-emerald-600 mt-2">{metrics?.available_seats || "..."}</p></div>
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 bg-gradient-to-br from-indigo-50 to-white"><p className="text-xs font-semibold text-indigo-400 uppercase">Utilization Rate</p><p className="text-3xl font-black text-indigo-900 mt-2">{metrics?.global_utilization_rate || "..."}</p></div>
            </section>

            {/* AI SYSTEM CARD */}
            <section className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-md mb-8">
              <h2 className="text-lg font-bold text-indigo-300 mb-4">🤖 Command AI Assistant</h2>
              <form onSubmit={handleAiSubmit} className="flex gap-3 mb-4">
                <input type="text" placeholder="e.g., 'Where does John sit?'..." value={aiPrompt} onChange={(e) => setAiPrompt(e.target.value)} className="flex-1 px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 text-sm text-white" />
                <button type="submit" className="px-6 py-2.5 bg-indigo-500 text-white font-semibold rounded-xl text-sm">Ask AI</button>
              </form>
              {(aiLoading || aiResponse) && (
                <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 text-sm font-mono">
                  {aiLoading && <p className="text-slate-400 animate-pulse">Running query...</p>}
                  {aiResponse && <p className="text-indigo-300">💡 Intent Recognized: <span className="text-white font-sans">{aiResponse.interpreted_query}</span></p>}
                </div>
              )}
            </section>

            {/* DIRECTORY LIST TABLE */}
            <section className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-slate-900">Personnel Operations Directory</h2>
                <input type="text" placeholder="Filter profiles..." value={searchQuery} onChange={(e) => {setSearchQuery(e.target.value); fetchDirectory(e.target.value);}} className="px-4 py-2 border rounded-xl bg-slate-50 text-sm" />
              </div>
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-xs font-bold text-slate-500 border-b"><th className="p-4">Employee</th><th className="p-4">Role</th><th className="p-4">Location</th><th className="p-4 text-center">Action</th></tr>
                </thead>
                <tbody className="divide-y text-sm">
                  {searchResults.map((emp) => (
                    <tr key={emp.employee_id} className="hover:bg-slate-50/50">
                      <td className="p-4 font-semibold">{emp.employee_name}<p className="text-xs font-normal text-slate-400">{emp.employee_email}</p></td>
                      <td className="p-4 uppercase text-xs">{emp.employee_role}</td>
                      <td className="p-4 font-mono text-xs">{emp.seat_number ? `Floor ${emp.floor_number} // ${emp.seat_number}` : "Remote"}</td>
                      <td className="p-4 text-center">{emp.seat_number && (<button onClick={() => handleReleaseSeat(emp.seat_number)} className="px-2.5 py-1 bg-rose-50 text-rose-600 rounded-md border text-xs">Release</button>)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}

      {/* VIEW 2: INTERACTIVE VISUAL MAP MAPS */}
        {currentView === "maps" && (
          <>
            <header className="mb-8 flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-slate-900">Floor Seating Blueprint</h1>
                <p className="text-sm text-slate-500">Click a vacant desk to assign personnel, or an occupied desk to release it.</p>
              </div>
              {/* Floor Switch Controller */}
              <div className="flex gap-2 bg-white p-1.5 rounded-xl border border-slate-200 shadow-sm">
                {[1, 2, 3, 4, 5].map((f) => (
                  <button key={f} onClick={() => setSelectedFloor(f)} className={`px-4 py-1.5 rounded-lg text-sm font-bold transition ${selectedFloor === f ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"}`}>
                    Floor {f}
                  </button>
                ))}
              </div>
            </header>

             {/* THE VISUAL ALLOCATION MAP GRID */}
            <section className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Interactive Desk Mapping Layout</h3>
                  <p className="text-xs text-slate-400">Click an occupied desk to release it, or select a vacant desk to instantly allocate a user.</p>
                </div>
                {/* Micro Indicators Legend */}
                <div className="flex gap-4 text-xs font-medium">
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <span className="w-2.5 h-2.5 rounded-md bg-emerald-500 shadow-sm shadow-emerald-200"></span> Vacant
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <span className="w-2.5 h-2.5 rounded-md bg-rose-500 shadow-sm shadow-rose-200"></span> Occupied
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-10 gap-4">
                {floorSeats.map((seat) => (
                  <div 
                    key={seat.id} 
                    className={`p-3.5 rounded-xl border flex flex-col justify-between h-24 group transition-all duration-200 relative cursor-pointer select-none ${
                      seat.status === "occupied" 
                        ? "bg-slate-50/50 border-slate-200/80 hover:border-rose-400 hover:bg-rose-50/30 hover:-translate-y-0.5 hover:shadow-md hover:shadow-rose-50" 
                        : "bg-white border-slate-200/80 hover:border-emerald-400 hover:bg-emerald-50/20 hover:-translate-y-0.5 hover:shadow-md hover:shadow-emerald-50"
                    }`}
                    onClick={async () => {
                      if (seat.status === "occupied") {
                        await handleReleaseSeat(seat.seat_number);
                      } else {
                        // 1. Collect inputs via prompts
                        const employeeId = prompt("Enter existing Employee UUID:");
                        if (!employeeId) return;
                        
                        const projectId = prompt("Enter Project UUID for this assignment:");
                        if (!projectId) return;

                        // 💡 SENIOR DEV TIP: Clean up strings to remove accidental trailing spaces
                        const cleanEmployeeId = employeeId.trim();
                        const cleanProjectId = projectId.trim();
                        const cleanSeatId = seat.id;

                        // Console log to debug exactly what we are sending to FastAPI
                        console.log("Sending Allocation Payload:", {
                          employee_id: cleanEmployeeId,
                          seat_id: cleanSeatId,
                          project_id: cleanProjectId
                        });

                        try {
                          const res = await fetch("http://127.0.0.1:8000/seats/manual-allocate", {
                            method: "POST",
                            headers: {
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                              employee_id: cleanEmployeeId,
                              seat_id: cleanSeatId,
                              project_id: cleanProjectId
                            }),
                          });
                          
                          const data = await res.json();

                          if (res.ok) {
                            alert(`🎉 ${data.message}`);
                            refreshAllData(); 
                          } else {
                            // If FastAPI returns a 422, this will print out exactly which field failed validation
                            console.error("Validation Error Details:", data.detail);
                            alert(`❌ Allocation Failed: ${JSON.stringify(data.detail)}`);
                          }
                        } catch (err) {
                          console.error("Network communication failure:", err);
                          alert("❌ Backend bridge connect nahi ho pa rha hai.");
                        }
                      }
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Desk</span>
                        <span className="font-mono text-xs font-black text-slate-800">{seat.seat_number.split('-')[2]}</span>
                      </div>
                      <span className={`w-1.5 h-1.5 rounded-full ring-4 ${
                        seat.status === "occupied" 
                          ? "bg-rose-500 ring-rose-100" 
                          : "bg-emerald-500 ring-emerald-100"
                      }`}></span>
                    </div>

                    <div className="flex items-center gap-1.5 mt-3 overflow-hidden">
                      {seat.status === "occupied" ? (
                        <div className="w-full flex items-center gap-1 text-[11px] font-semibold text-slate-700 truncate">
                          <span className="text-xs text-rose-500">👤</span> 
                          <span className="truncate">{seat.occupant || "Assigned"}</span>
                        </div>
                      ) : (
                        <div className="w-full text-[10px] font-medium text-emerald-600 flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 rounded-md w-fit">
                          <span className="text-[8px]">●</span> Available
                        </div>
                      )}
                    </div>
                    
                    {/* Hover Tooltip Overlay Descriptor */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2.5 hidden group-hover:block bg-slate-900 text-white text-[10px] font-medium tracking-wide py-1.5 px-3 rounded-lg shadow-xl shadow-slate-900/20 whitespace-nowrap z-20 pointer-events-none transition-all duration-150 animate-fadeIn">
                      {seat.status === "occupied" ? (
                        <span className="flex items-center gap-1 text-rose-300">🗑️ Click to Release <b className="text-white font-semibold">{seat.occupant}</b></span>
                      ) : (
                        <span className="flex items-center gap-1 text-emerald-300">⚡ Click to Allocate Desk</span>
                      )}
                      {/* Tooltip Arrow */}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 w-2 h-2 bg-slate-900 rotate-45"></div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {/* VIEW 3: PROJECTS SUMMARY LEDGER */}
        {currentView === "projects" && (
          <>
            <header className="mb-8"><h1 className="text-3xl font-bold text-slate-900">Project Account Mappings</h1></header>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {projectsList.map((proj) => (
                <div key={proj.project_id} className="p-5 border rounded-2xl bg-white shadow-sm">
                  <div className="flex justify-between items-center mb-4"><span className="text-xl">📁</span><span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded text-xs font-bold">{proj.allocated_headcount} Desks</span></div>
                  <h3 className="text-md font-bold text-slate-900">{proj.project_name}</h3>
                </div>
              ))}
            </div>
          </>
        )}
      </main>

      {/* DRAWER FORM FOR JOINERS */}
      {showForm && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex justify-end z-50 animate-fadeIn">
          {/* Main Backdrop click handling could be added here to close */}
          <div className="w-full max-w-md bg-white h-screen p-6 shadow-2xl flex flex-col justify-between border-l border-slate-100 animate-slideLeft">
            
            <div>
              {/* Drawer Header */}
              <div className="flex justify-between items-center pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Onboard & Allocate</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Provision corporate access and map workspace resources.</p>
                </div>
                <button 
                  onClick={() => setShowForm(false)} 
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition font-medium text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Form Controls */}
              <form onSubmit={handleOnboardSubmit} className="space-y-5">
                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 transform -translate-y-1/2 text-slate-400 text-xs">👤</span>
                    <input 
                      required 
                      type="text" 
                      placeholder="e.g., Rohan Sharma"
                      value={formData.name} 
                      onChange={(e) => setFormData({...formData, name: e.target.value})} 
                      className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50/50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all" 
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                    Corporate Email
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 transform -translate-y-1/2 text-slate-400 text-xs">✉️</span>
                    <input 
                      required 
                      type="email" 
                      placeholder="username@enterprise.com"
                      value={formData.email} 
                      onChange={(e) => setFormData({...formData, email: e.target.value})} 
                      className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm bg-slate-50/50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all" 
                    />
                  </div>
                </div>

                {/* Info Alert Callout within Form */}
                <div className="p-3.5 bg-indigo-50/40 border border-indigo-100 rounded-xl text-[11px] text-indigo-700 leading-relaxed">
                  💡 <b>Automated Pipeline Action:</b> Submission triggers enterprise Active Directory profiling, provisions an active seating lease context, and alerts the respective delivery manager.
                </div>

                <div className="pt-2 flex gap-3">
                  <button 
                    type="button" 
                    onClick={() => setShowForm(false)} 
                    className="flex-1 py-2.5 border border-slate-200 text-slate-600 text-sm font-semibold rounded-xl hover:bg-slate-50 transition"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="flex-1 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-xl shadow-md shadow-indigo-100 hover:bg-indigo-700 transition"
                  >
                    Provision Profile
                  </button>
                </div>
              </form>
            </div>

            {/* Drawer Footer Meta Info */}
            <div className="text-[10px] text-slate-400 tracking-normal border-t border-slate-100 pt-4 flex items-center justify-between">
              <span>Security Policy: Active SSO Session</span>
              <span className="font-mono text-slate-300">Form ID: ONB-2026</span>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}