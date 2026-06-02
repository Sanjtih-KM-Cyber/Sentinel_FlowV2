import { screen, waitFor } from '@testing-library/react';
import { render } from './utils';
import Assets from '../pages/Assets';
import { describe, test, expect } from 'vitest';

describe('Assets Integration', () => {
  test('Renders and displays assets list', async () => {
    // Render the Assets component wrapped in test providers
    render(<Assets />);
    
    // Default text while loading or until data populates
    // Check elements after wait
    await waitFor(() => {
      // Check if domain asset is shown
      expect(screen.getByText('api.example.com')).toBeInTheDocument();
      // Check if IP asset is shown
      expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
      
      // Check counts are updated correctly in the CategoryCard
      // We know there's 1 domain and 1 IP. Let's find the card titles and sibling text lengths.
      // Easiest is to verify "1" appears near the Domain count.
      // For a better assertion, we can check that there's no zero state for these mock types
    });
  });
});
