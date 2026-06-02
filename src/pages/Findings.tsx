import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ShieldAlert, ShieldCheck, Shield, ChevronDown, ChevronRight, CheckCircle2, Activity, Clock } from 'lucide-react';
import { useFindingsStore } from '../store/findingsStore';
import { cn } from '../lib/utils';
import { getFindings } from '../api/findings';
import { Finding } from '../types';

const severityColors = {
  CRITICAL: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800',
  HIGH: 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/40 dark:text-orange-300 dark:border-orange-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/40 dark:text-yellow-300 dark:border-yellow-800',
  LOW: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-800'
};

export default function Findings() {
  const { showVerifiedOnly, setShowVerifiedOnly, selectedFindingId, setSelectedFindingId } = useFindingsStore();
  
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['findings', showVerifiedOnly],
    queryFn: () => getFindings(showVerifiedOnly),
  });

  const findings = Array.isArray(data) ? data : [];

  if (isLoading) {
    return <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-brand-200 dark:border-gray-800">Loading findings...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500 bg-white dark:bg-gray-900 rounded-xl border border-red-200 dark:border-red-900">
        <h3 className="font-semibold text-lg mb-2">Backend Unavailable or Connection Error</h3>
        <p>Failed to load findings. The server might be down or unreachable.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-brand-900 dark:text-gray-100 tracking-tight">Active Findings</h1>
        
        <div className="flex items-center space-x-2 bg-white dark:bg-gray-900 rounded-lg p-1 shadow-sm border border-brand-200 dark:border-gray-800">
          <button 
            onClick={() => setShowVerifiedOnly(true)}
            className={cn("px-4 py-1.5 text-sm font-medium rounded-md transition-colors", showVerifiedOnly ? "bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300" : "text-brand-600 dark:text-gray-400 hover:bg-brand-50 dark:hover:bg-gray-800")}
          >
            Verified Only
          </button>
          <button 
            onClick={() => setShowVerifiedOnly(false)}
            className={cn("px-4 py-1.5 text-sm font-medium rounded-md transition-colors", !showVerifiedOnly ? "bg-indigo-50 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300" : "text-brand-600 dark:text-gray-400 hover:bg-brand-50 dark:hover:bg-gray-800")}
          >
            All Findings
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-brand-200 dark:border-gray-800 overflow-hidden divide-y divide-brand-100 dark:divide-gray-800">
        {findings.map(finding => (
          <FindingRow 
            key={finding.id} 
            finding={finding} 
            isExpanded={selectedFindingId === finding.id}
            onToggle={() => setSelectedFindingId(selectedFindingId === finding.id ? null : finding.id)}
          />
        ))}
        
        {(!findings || findings.length === 0) && (
          <div className="p-8 text-center text-brand-500 dark:text-gray-400">
            No findings match your current filters.
          </div>
        )}
      </div>
    </div>
  );
}

type FindingRowProps = { finding: Finding, isExpanded: boolean, onToggle: () => void, key?: React.Key };
function FindingRow({ finding, isExpanded, onToggle }: FindingRowProps) {
  return (
    <div className="flex flex-col">
      <div 
        className={cn("px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer hover:bg-brand-50/50 dark:hover:bg-gray-800/50 transition-colors", isExpanded && "bg-brand-50/50 dark:bg-gray-800/50")}
        onClick={onToggle}
      >
        <div className="flex items-center gap-4 flex-1">
          <button className="text-brand-400 dark:text-gray-500 hover:text-brand-600 dark:hover:text-gray-300">
            {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-brand-900 dark:text-gray-100">{finding.title}</h3>
              {finding.isVerified && <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" title="Verified by Scanner" />}
            </div>
            <div className="flex items-center gap-3 text-sm text-brand-500 dark:text-gray-400 mt-1">
              <span>{finding.asset}</span>
              <span>•</span>
              <span className="flex items-center"><Activity className="w-3 h-3 mr-1" /> {finding.confidence}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-sm font-medium text-brand-500 dark:text-gray-400">
            {finding.evidenceCount} Evidences
          </div>
          <span className={cn("px-2.5 py-1 text-xs font-semibold rounded-full border", severityColors[finding.severity as keyof typeof severityColors])}>
            {finding.severity}
          </span>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-brand-100 dark:border-gray-800 bg-brand-50/30 dark:bg-gray-900/30 p-6">
          <EvidenceViewer evidence={finding.evidence} />
        </div>
      )}
    </div>
  );
}

function EvidenceViewer({ evidence }: { evidence: Finding['evidence'] }) {
  const [activeTab, setActiveTab] = useState<'req' | 'res' | 'oob' | 'time'>('req');

  if (!evidence) {
    return <div className="text-brand-500 dark:text-gray-400 italic text-sm">No evidence provided.</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-brand-200 dark:border-gray-800 overflow-hidden shadow-sm">
      <div className="flex border-b border-brand-200 dark:border-gray-800 overflow-x-auto">
        <TabButton active={activeTab === 'req'} onClick={() => setActiveTab('req')}>HTTP Requests ({(evidence.requests || []).length})</TabButton>
        <TabButton active={activeTab === 'res'} onClick={() => setActiveTab('res')}>HTTP Responses ({(evidence.responses || []).length})</TabButton>
        <TabButton active={activeTab === 'oob'} onClick={() => setActiveTab('oob')}>OOB Interactions ({(evidence.oob || []).length})</TabButton>
        <TabButton active={activeTab === 'time'} onClick={() => setActiveTab('time')}>Timeline</TabButton>
      </div>
      
      <div className="p-4 bg-brand-900 dark:bg-gray-950 text-brand-50 dark:text-gray-300 font-mono text-sm overflow-x-auto rounded-b-lg">
        {activeTab === 'req' && (
          (evidence.requests || []).map((req: string, i: number) => (
            <pre key={i} className="whitespace-pre-wrap mb-4">{req}</pre>
          ))
        )}
        {activeTab === 'res' && (
          (evidence.responses || []).map((res: string, i: number) => (
            <pre key={i} className="whitespace-pre-wrap mb-4">{res}</pre>
          ))
        )}
        {activeTab === 'oob' && (
          (evidence.oob || []).length > 0 ? evidence.oob.map((o: string, i: number) => (
            <pre key={i} className="whitespace-pre-wrap text-green-400 mb-4">{o}</pre>
          )) : <div className="text-brand-400 dark:text-gray-500 italic">No Out-of-Band interactions recorded.</div>
        )}
        {activeTab === 'time' && (
          <div className="space-y-2 font-sans text-brand-100 dark:text-gray-300">
            {(evidence.timeline || []).map((event: string, i: number) => (
              <div key={i} className="flex items-center">
                <Clock className="w-4 h-4 mr-2 text-brand-400 dark:text-gray-500 shrink-0" />
                <span>{event}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean, onClick: () => void, children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors focus:outline-none",
        active ? "border-indigo-600 text-indigo-700 bg-indigo-50/50 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-500" : "border-transparent text-brand-600 dark:text-gray-400 hover:text-brand-900 dark:hover:text-gray-200 hover:bg-brand-50 dark:hover:bg-gray-800"
      )}
    >
      {children}
    </button>
  );
}
