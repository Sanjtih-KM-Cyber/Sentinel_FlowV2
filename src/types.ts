export interface Asset {
  id: string;
  domain: string;
  isVerified: boolean;
  type: string;
  lastScanned: string;
  name?: string;
  tag?: string;
  count?: number;
}

export interface Finding {
  id: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: 'CERTAIN' | 'FIRM' | 'TENTATIVE';
  asset: string;
  isVerified: boolean;
  evidenceCount: number;
  discoveredAt: string;
  evidence: {
    requests: string[];
    responses: string[];
    oob: string[];
    timeline: string[];
  };
}
