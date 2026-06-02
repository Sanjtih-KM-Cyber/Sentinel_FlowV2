import { screen, waitFor, fireEvent } from '@testing-library/react';
import { render } from './utils';
import Findings from '../pages/Findings';
import { describe, test, expect } from 'vitest';

describe('Findings Integration', () => {
  test('Renders and displays findings list', async () => {
    // Render the Findings component wrapped in test providers
    render(<Findings />);
    
    // Check loading state
    // Wait for the data to resolve and rows to render
    await waitFor(() => {
      expect(screen.getByText('IDOR in User Profile Update')).toBeInTheDocument();
      expect(screen.getByText('Mass Assignment in Registration')).toBeInTheDocument();
      
      // Ensure severity and count text is shown
      expect(screen.getByText('3 Evidences')).toBeInTheDocument();
      expect(screen.getAllByText('CRITICAL').length).toBeGreaterThan(0);
      expect(screen.getAllByText('HIGH').length).toBeGreaterThan(0);
    });

    // Expand a finding to show evidence
    const findingRow = screen.getByText('IDOR in User Profile Update');
    fireEvent.click(findingRow);

    await waitFor(() => {
      // It should display the tabs related to evidence
      expect(screen.getByText(/HTTP Requests/)).toBeInTheDocument();
      expect(screen.getByText(/POST \/api\/user\/123\/profile/)).toBeInTheDocument();
    });
  });
});
