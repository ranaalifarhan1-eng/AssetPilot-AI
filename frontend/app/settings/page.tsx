import React from 'react';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold text-gray-100">System Settings & API Keys</h2>
        <p className="text-xs text-gray-400 mt-1">Configure read-only exchange credentials, LLM keys, and notification thresholds.</p>
      </div>

      <Card title="Security & Integrations" badge={<Badge variant="amber">PHASE 1 MODULE</Badge>}>
        <div className="p-8 text-center text-xs text-gray-400 space-y-2">
          <p className="font-semibold text-gray-200">Settings panel scheduled for Phase 1.</p>
          <p>Will enforce read-only exchange policies and secure backend-only API key configuration.</p>
        </div>
      </Card>
    </div>
  );
}
