import { useState } from "react";
import { Button } from "../ui/button";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "../ui/input-otp";
import { ShieldCheck, Copy, Check } from "lucide-react";
import { copyToClipboard } from "../../utils/clipboard";

interface TwoFactorSetupProps {
  qrCode: string;
  secret: string;
  onComplete: (code: string) => void;
}

export function TwoFactorSetup({ qrCode, secret, onComplete }: TwoFactorSetupProps) {
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(secret);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length === 6) {
      onComplete(code);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-4">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-semibold mb-2">Set up 2FA</h1>
          <p className="text-muted-foreground">
            Scan this QR code with your authenticator app
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
          <div className="space-y-6">
            {/* QR Code */}
            <div className="flex justify-center p-4 bg-white rounded-lg">
              <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
            </div>

            {/* Manual Entry */}
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground text-center">
                Can't scan? Enter this code manually:
              </p>
              <div className="flex items-center gap-2 p-3 bg-muted rounded border border-border">
                <code className="flex-1 text-sm text-center font-mono">
                  {secret}
                </code>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Verification */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-center">
                  Enter the 6-digit code from your app
                </p>
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
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={code.length !== 6}
              >
                Enable 2FA
              </Button>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => onComplete("123456")}
              >
                Skip for Demo
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}