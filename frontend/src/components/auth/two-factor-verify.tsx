import { useState } from "react";
import { Button } from "../ui/button";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "../ui/input-otp";
import { ArrowLeft, ShieldCheck } from "lucide-react";

interface TwoFactorVerifyProps {
  email: string;
  onVerify: (code: string) => void;
  onBack: () => void;
  onUseBackupCode: () => void;
}

export function TwoFactorVerify({ email, onVerify, onBack, onUseBackupCode }: TwoFactorVerifyProps) {
  const [code, setCode] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length === 6) {
      onVerify(code);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <button
          onClick={onBack}
          className="flex items-center text-xs text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </button>

        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-4">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-semibold mb-2">Two-factor authentication</h1>
          <p className="text-muted-foreground">
            Enter the 6-digit code from your authenticator app
          </p>
          <p className="text-sm text-muted-foreground mt-1">{email}</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex justify-center">
              <InputOTP
                maxLength={6}
                value={code}
                onChange={(value) => setCode(value)}
              >
                <InputOTPGroup>
                  <InputOTPSlot index={0} />
                  <InputOTPSlot index={1} />
                  <InputOTPSlot index={2} />
                  <InputOTPSlot index={3} />
                  <InputOTPSlot index={4} />
                  <InputOTPSlot index={5} />
                </InputOTPGroup>
              </InputOTP>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={code.length !== 6}
            >
              Verify
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground mt-6">
            Lost your device?{" "}
            <button onClick={onUseBackupCode} className="text-xs text-primary hover:underline active:text-primary/80 transition-colors">
              Use a backup code
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}