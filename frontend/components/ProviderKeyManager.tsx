"use client";

import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { ProviderKeyStatus } from "@/lib/types";

const providers: Array<{
  value: "openai" | "anthropic" | "gemini";
  label: string;
  description: string;
}> = [
  { value: "openai", label: "OpenAI", description: "Required for GPT generated runs and OpenAI embeddings." },
  { value: "anthropic", label: "Anthropic", description: "Required for Claude generated runs." },
  { value: "gemini", label: "Google Gemini", description: "Required for Gemini generated runs and Gemini fallback evaluation." },
];

export function ProviderKeyManager() {
  const [statuses, setStatuses] = useState<ProviderKeyStatus[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [status, setStatus] = useState("Loading provider keys...");

  async function load() {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    try {
      const data = await api.providerKeys(token);
      setStatuses(data);
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to load provider keys");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onSave(event: FormEvent, provider: "openai" | "anthropic" | "gemini") {
    event.preventDefault();
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    const apiKey = drafts[provider]?.trim();
    if (!apiKey) {
      setStatus(`Enter a ${provider} API key before saving.`);
      return;
    }
    try {
      setStatus(`Saving ${provider} key...`);
      await api.saveProviderKey(token, { provider, api_key: apiKey });
      setDrafts((current) => ({ ...current, [provider]: "" }));
      setStatus(`${provider} key saved.`);
      await load();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : `Failed to save ${provider} key`);
    }
  }

  async function onDelete(provider: "openai" | "anthropic" | "gemini") {
    const token = window.localStorage.getItem("axiom-token");
    if (!token) {
      setStatus("Login required.");
      return;
    }
    if (!window.confirm(`Delete saved ${provider} key?`)) {
      return;
    }
    try {
      setStatus(`Deleting ${provider} key...`);
      await api.deleteProviderKey(token, provider);
      setStatus(`${provider} key deleted.`);
      await load();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : `Failed to delete ${provider} key`);
    }
  }

  const statusMap = Object.fromEntries(statuses.map((item) => [item.provider, item])) as Record<string, ProviderKeyStatus>;

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Provider Keys</p>
        <h2 className="mt-2 font-display text-4xl text-ink">Configure model providers per user.</h2>
        <p className="mt-3 max-w-3xl text-slate-600">
          Generated runs use your saved provider keys first, then fall back to any server-level environment keys. Imported runs do not need provider keys.
        </p>
      </section>
      <div className="grid gap-4 lg:grid-cols-3">
        {providers.map((provider) => {
          const providerStatus = statusMap[provider.value];
          return (
            <form
              key={provider.value}
              onSubmit={(event) => void onSave(event, provider.value)}
              className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-display text-2xl text-ink">{provider.label}</h3>
                  <p className="mt-2 text-sm text-slate-600">{provider.description}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${providerStatus?.configured ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                  {providerStatus?.configured ? "configured" : "missing"}
                </span>
              </div>
              <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
                <p>Source: {providerStatus?.source ?? "missing"}</p>
                <p className="mt-1">Key hint: {providerStatus?.key_hint ?? "none saved"}</p>
              </div>
              <input
                type="password"
                value={drafts[provider.value] || ""}
                onChange={(event) => setDrafts((current) => ({ ...current, [provider.value]: event.target.value }))}
                placeholder={`Paste ${provider.label} API key`}
                className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3"
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn-primary" type="submit">Save Key</button>
                <button className="btn-secondary" type="button" onClick={() => void onDelete(provider.value)}>
                  Delete Saved Key
                </button>
              </div>
            </form>
          );
        })}
      </div>
      {status ? <p className="text-sm text-slate-500">{status}</p> : null}
    </div>
  );
}
