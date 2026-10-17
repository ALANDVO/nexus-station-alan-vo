import { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate } from "react-router-dom";
import MemoryDashboard from "./components/MemoryDashboard";
import SearchDashboard from "./components/SearchDashboard";
import HandoffPage from "./components/HandoffPage";
import { apiClient, HealthCheck } from "./api/client";
import "./App.css";

export default function App() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.health().then(setHealth).catch(setError);
  }, []);

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-container">
          <Link to="/" className="nav-brand">
            Nexus Station
          </Link>
          <div className="nav-links">
            <Link to="/">Memories</Link>
            <Link to="/search">Search</Link>
            <Link to="/handoff">Handoff</Link>
          </div>
          {health && (
            <span className="health-badge">
              v{health.version} • {health.status}
            </span>
          )}
        </div>
      </nav>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<MemoryDashboard />} />
          <Route path="/search" element={<SearchDashboard />} />
          <Route path="/handoff" element={<HandoffPage />} />
        </Routes>
      </main>
    </div>
  );
}