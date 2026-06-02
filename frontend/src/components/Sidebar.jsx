import { NavLink } from "react-router-dom";
import {
  MessageSquare,
  BarChart3,
  CheckSquare,
  StickyNote,
  Calendar,
  Settings,
  Shield,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: MessageSquare, label: "Chat" },
  { to: "/finance", icon: BarChart3, label: "Finance" },
  { to: "/todos", icon: CheckSquare, label: "Tasks" },
  { to: "/notes", icon: StickyNote, label: "Sticky Notes" },
  { to: "/calendar", icon: Calendar, label: "Calendar" },
  { to: "/vault", icon: Shield, label: "Vault" },
];

export default function Sidebar() {
  
  return (
    <aside className="sidebar">
      <div className="sidebar-brand" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <img src="/logo.png" alt="Logo" style={{ height: "24px", width: "24px", borderRadius: "4px" }} />
        <div className="sidebar-brand-title" style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.5px" }}>AI Assistant</div>
      </div>

      <div className="sidebar-section-label">Tools</div>

      {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `sidebar-nav-btn${isActive ? " active" : ""}`
          }
        >
          <Icon />
          {label}
        </NavLink>
      ))}

      <div className="sidebar-spacer" />
      <div className="sidebar-separator" />

      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `sidebar-nav-btn${isActive ? " active" : ""}`
        }
      >
        <Settings />
        Settings
      </NavLink>

      <div style={{ height: 8 }} />
    </aside>
  );
}
