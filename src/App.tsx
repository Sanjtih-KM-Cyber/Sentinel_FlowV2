import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Assets from './pages/Assets';
import Scans from './pages/Scans';
import Findings from './pages/Findings';
import Reports from './pages/Reports';
import TeamManagement from './pages/TeamManagement';
import Settings from './pages/Settings';
import AuditLogs from './pages/AuditLogs';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="assets" element={<Assets />} />
        <Route path="scans" element={<Scans />} />
        <Route path="findings" element={<Findings />} />
        <Route path="reports" element={<Reports />} />
        <Route path="team" element={<TeamManagement />} />
        <Route path="settings" element={<Settings />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;
