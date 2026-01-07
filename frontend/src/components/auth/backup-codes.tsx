import { useState } from "react";
import { Button } from "../ui/button";
import { Copy, Download, Check, ShieldCheck } from "lucide-react";
import { copyToClipboard } from "../../utils/clipboard";

interface BackupCodesProps {
  codes: string[];
  onComplete: () => void;
}

export function BackupCodes({ codes, onComplete }: BackupCodesProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(codes.join("\n"));
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([codes.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resonance-backup-codes.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-4">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-3xl font-semibold mb-2">Save your backup codes</h1>
          <p className="text-muted-foreground">
            Store these codes in a safe place. You can use them to access your account if you lose your device.
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
          <div className="space-y-6">
            <div className="bg-muted rounded-lg p-4 border border-border">
              <div className="grid grid-cols-2 gap-2">
                {codes.map((code, index) => (
                  <div
                    key={index}
                    className="font-mono text-sm text-center p-2 bg-background rounded border border-border"
                  >
                    {code}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={handleCopy}
              >
                {copied ? (
                  <>
                    <Check className="mr-2 h-4 w-4 text-green-500" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={handleDownload}
              >
                <Download className="mr-2 h-4 w-4" />
                Download
              </Button>
            </div>

            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 rounded-lg p-4">
              <p className="text-sm text-amber-900 dark:text-amber-200">
                <strong>Important:</strong> Each code can only be used once. Keep them secure and never share them.
              </p>
            </div>

            <Button type="button" className="w-full" size="lg" onClick={onComplete}>
              I've saved my codes
            </Button>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={onComplete}
            >
              Skip for Demo
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}