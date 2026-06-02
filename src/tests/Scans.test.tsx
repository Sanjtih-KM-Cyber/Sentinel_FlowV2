import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import Scans from '../pages/Scans';
import { describe, test, expect } from 'vitest';

describe('Scans Integration', () => {
  test('Renders and displays scans list', async () => {
    render(<Scans />);
    
    await waitFor(() => {
      expect(screen.getByText('api.example.com')).toBeInTheDocument();
      expect(screen.getByText('auth.example.com')).toBeInTheDocument();
      expect(screen.getByText('staging-internal')).toBeInTheDocument();
      
      // workers
      expect(screen.getByText('12 / 20')).toBeInTheDocument();
    });
  });
});
