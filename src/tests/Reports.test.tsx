import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import Reports from '../pages/Reports';
import { describe, test, expect } from 'vitest';

describe('Reports Integration', () => {
  test('Renders without crashing', async () => {
    render(<Reports />);
    
    await waitFor(() => {
      expect(screen.getByText('Reports & Exports')).toBeInTheDocument();
      expect(screen.getByText('Executive Report')).toBeInTheDocument();
    });
  });
});
