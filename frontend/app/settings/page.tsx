import { AuthGuard } from "@/components/AuthGuard";
import { ProviderKeyManager } from "@/components/ProviderKeyManager";
import { Shell } from "@/components/Shell";

export default async function SettingsPage() {
  return (
    <Shell>
      <AuthGuard>
        <ProviderKeyManager />
      </AuthGuard>
    </Shell>
  );
}
