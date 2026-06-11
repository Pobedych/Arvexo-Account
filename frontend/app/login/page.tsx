import { AuthForm } from "@/components/AuthForm";
import { AuthShell } from "@/components/AuthShell";

export default function LoginPage() {
  return (
    <AuthShell mode="login">
      <AuthForm mode="login" />
    </AuthShell>
  );
}
