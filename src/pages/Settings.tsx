import { useState } from "react";
import { Save, Key, Globe, Bell, Shield } from "lucide-react";

export default function Settings() {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-foreground">Settings</h2>
        <p className="mt-1 text-sm text-foreground/50">
          Configure your deployment preferences and credentials
        </p>
      </div>

      {/* Cloud Provider Credentials */}
      <section className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
            <Key className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Cloud Provider Credentials</h3>
            <p className="text-xs text-foreground/50">Manage your AWS, GCP, or Azure credentials</p>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-foreground/70">AWS Access Key ID</label>
            <input className="input-field" type="password" placeholder="AKIAIOSFODNN7EXAMPLE" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-foreground/70">AWS Secret Access Key</label>
            <input className="input-field" type="password" placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-foreground/70">Default Region</label>
            <select className="input-field">
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">EU West (Ireland)</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
            </select>
          </div>
        </div>
      </section>

      {/* Deployment Preferences */}
      <section className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10">
            <Globe className="h-4 w-4 text-accent" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Deployment Preferences</h3>
            <p className="text-xs text-foreground/50">Default deployment behaviour</p>
          </div>
        </div>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Auto-rollback on deployment failure</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Notify on deployment completion</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Enable verbose agent logging</span>
          </label>
        </div>
      </section>

      {/* Notifications */}
      <section className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-foreground/5">
            <Bell className="h-4 w-4 text-foreground/70" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
            <p className="text-xs text-foreground/50">Configure when you receive alerts</p>
          </div>
        </div>
        <div className="space-y-4">
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Deployment failures</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Container build completions</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" className="h-4 w-4 accent-primary" />
            <span className="text-sm text-foreground/80">Weekly digest</span>
          </label>
        </div>
      </section>

      {/* Save button */}
      <div className="flex justify-end">
        <button onClick={handleSave} className="btn-primary">
          <Save className="h-4 w-4" />
          {saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}