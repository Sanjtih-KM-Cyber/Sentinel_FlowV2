import { screen, waitFor, fireEvent } from '@testing-library/react';
import { render } from './utils';
import Layout from '../components/layout/Layout';
import { describe, test, expect, beforeEach } from 'vitest';
import { useWorkspaceStore } from '../store/workspaceStore';

describe('Workspace Integration', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ workspaceType: 'SOLO' });
  });

  test('Loads workspace type from API and persists on change', async () => {
    render(<Layout />);
    
    // Check loading/initial state is populated from MSW
    await waitFor(() => {
      expect(screen.getByText('Workspace: SOLO')).toBeInTheDocument();
    });

    // Find the select element and change it
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'AGENCY' } });

    // Wait for the update mutation to succeed and UI to update
    await waitFor(() => {
      expect(screen.getByText('Workspace: AGENCY')).toBeInTheDocument();
    });
    
    // Verify it updated the store
    expect(useWorkspaceStore.getState().workspaceType).toBe('AGENCY');
  });
});
