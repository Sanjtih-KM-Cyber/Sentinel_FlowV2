export const mockFindings = [
  {
    id: 'f-1',
    title: 'IDOR in User Profile Update',
    severity: 'CRITICAL',
    confidence: 'HIGH',
    asset: 'api.example.com',
    status: 'open',
    isVerified: true,
    evidenceCount: 3,
    evidence: {
      requests: ['POST /api/user/123/profile HTTP/1.1...'],
      responses: ['HTTP/1.1 200 OK...'],
      oob: [],
      timeline: ['10:00:00: Sent request', '10:00:01: Received 200 OK']
    }
  },
  {
    id: 'f-2',
    title: 'Mass Assignment in Registration',
    severity: 'HIGH',
    confidence: 'HIGH',
    asset: 'auth.example.com',
    status: 'open',
    isVerified: true,
    evidenceCount: 1,
    evidence: {
      requests: ['POST /api/register HTTP/1.1\n{"username": "test", "isAdmin": true}'],
      responses: ['HTTP/1.1 201 Created\n{"username": "test", "isAdmin": true}'],
      oob: [],
      timeline: ['10:05:00: Fuzzed endpoint']
    }
  }
];
