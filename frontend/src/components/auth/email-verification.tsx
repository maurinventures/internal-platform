import { useState } from "react";
import { Button } from "../ui/button";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "../ui/input-otp";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { toast } from "sonner";

interface EmailVerificationProps {
  email: string;
  onVerify: (code: string) => void;
  onBack: () => void;
}

export function EmailVerification({ email, onVerify, onBack }: EmailVerificationProps) {
  const [code, setCode] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length === 6) {
      onVerify(code);
    }
  };

  const handleResend = () => {
    toast.success("Verification code resent", {
      description: "Check your email for a new verification code.",
    });
    // In production, this would call an API to resend the code
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={onBack}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Login
        </Button>

        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <Mail className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-2xl font-semibold mb-2">Check your email</h1>
          <p className="text-muted-foreground">
            We sent a verification code to<br />
            <strong className="text-foreground">{email}</strong>
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            <label className="text-sm font-medium block">Enter verification code</label>
            
            <div className="flex justify-center">
              <InputOTP maxLength={6} value={code} onChange={setCode}>
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
              <CheckCircle className="mr-2 h-4 w-4" />
              Verify Email
            </Button>
          </form>

          <p className="text-center text-[12px] text-muted-foreground mt-8">
            Didn't receive the code?{" "}
            <button className="text-[12px] text-primary hover:underline active:text-primary/80 transition-colors" onClick={handleResend}>Resend</button>
          </p>
        </div>
      </div>
    </div>
  );
}