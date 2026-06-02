import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import Settings from '../pages/Settings';
import { describe, test, expect } from 'vitest';

describe('Settings Integration', () => {
  test('Renders and displays correct config fetched from API', async () => {
    render(<Settings />);
    
    await waitFor(() => {
      // Check Plan rendering
      expect(screen.getByText('Enterprise Pro')).toBeInTheDocument();
      // Check limit text
      expect(screen.getByText('42 / 200 hrs')).toBeInTheDocument();
      // Check api keys
      expect(screen.getByText('GitHub Actions CI')).toBeInTheDocument();
      expect(screen.getByText(/3600s/)).toBeInTheDocument();
    });
  });
});
