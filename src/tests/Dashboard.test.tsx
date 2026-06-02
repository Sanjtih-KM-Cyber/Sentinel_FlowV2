import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import Dashboard from '../pages/Dashboard';
import { describe, test, expect } from 'vitest';

describe('Dashboard Integration', () => {
  test('Renders dashboard stats from API', async () => {
    // Render the Dashboard component wrapped in test providers
    render(<Dashboard />);
    
    // Check loading state
    // Once data is loaded, we should see the correct values from our MSW mock
    await waitFor(() => {
      expect(screen.getByText('Active Projects')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('Assets Discovered')).toBeInTheDocument();
      expect(screen.getByText('154')).toBeInTheDocument();
      expect(screen.getByText('Verified Findings')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      
      // Check recent activity
      expect(screen.getByText('api.example.com')).toBeInTheDocument();
      expect(screen.getByText('Q2 Security Assessment')).toBeInTheDocument();
    });
  });
});
